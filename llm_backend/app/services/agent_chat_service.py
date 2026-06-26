import asyncio
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Optional

import requests
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger
from app.services.agent_trace_service import TraceRecorder
from app.services.embedding_service import EmbeddingService
from app.services.user_profile_service import UserProfileService
from app.tools.search import SearchTool

logger = get_logger(service="agent_chat")

MAX_RETRIES = 2


@dataclass
class RouterPlan:
    route: str
    reason: str
    objective: str
    tools: List[str] = field(default_factory=list)
    answer_style: str = "balanced"
    confidence: float = 0.8
    requires_memory_update: bool = True


@dataclass
class ToolExecutionResult:
    tool: str
    success: bool
    summary: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    evidence_blocks: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    error: str = ""


@dataclass
class ResearchResult:
    route: str
    sources: List[Dict[str, Any]] = field(default_factory=list)
    evidence_blocks: List[str] = field(default_factory=list)
    research_notes: List[str] = field(default_factory=list)
    tool_results: List[ToolExecutionResult] = field(default_factory=list)


@dataclass
class CodeReviewResult:
    enabled: bool = False
    summary: str = ""
    formatted_answer: str = ""
    language: str = "text"
    notes: List[str] = field(default_factory=list)
    formatter_used: str = ""


class ToolRegistry:
    """统一维护工具注册和调用入口。"""

    def __init__(self):
        self._tools: Dict[str, Callable[..., Awaitable[ToolExecutionResult]]] = {}

    def register(self, name: str, handler: Callable[..., Awaitable[ToolExecutionResult]]):
        self._tools[name] = handler

    def has(self, name: str) -> bool:
        return name in self._tools

    async def execute(self, name: str, *args, **kwargs) -> ToolExecutionResult:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")
        return await self._tools[name](*args, **kwargs)

    @property
    def names(self) -> List[str]:
        return list(self._tools.keys())


class AgentChatService:
    """Router -> Research -> Code -> Response -> Memory 的轻量多 Agent 工作流。"""

    SEARCH_TOOL = "search_web"
    DOCUMENT_TOOL = "search_documents"
    WORKSPACE_TOOL = "search_workspace"
    WEATHER_TOOL = "get_weather"

    def __init__(self):
        # 这里把多 Agent 流程依赖的能力一次性准备好：
        # - router_client：负责生成结构化路由计划
        # - response_client：负责最终面向用户的回答
        # - code_client：负责代码场景下的补充检查和格式化建议
        # - embedding_service：负责文档 / 工作区向量检索
        # - tool_registry：统一管理工具调用入口
        self.router_client = AsyncOpenAI(
            api_key=settings.AGENT_API_KEY or settings.CHAT_API_KEY,
            base_url=settings.AGENT_BASE_URL or settings.CHAT_BASE_URL,
        )
        self.response_client = AsyncOpenAI(
            api_key=settings.CHAT_API_KEY,
            base_url=settings.CHAT_BASE_URL,
        )
        self.code_client = AsyncOpenAI(
            api_key=settings.AGENT_API_KEY or settings.CHAT_API_KEY,
            base_url=settings.AGENT_BASE_URL or settings.CHAT_BASE_URL,
        )

        self.route_model = settings.AGENT_MODEL_NAME or settings.CHAT_MODEL_NAME
        self.answer_model = settings.CHAT_MODEL_NAME
        self.code_model = settings.AGENT_MODEL_NAME or settings.CHAT_MODEL_NAME

        self.embedding_service = EmbeddingService()
        self.search_tool: Optional[SearchTool] = None
        try:
            self.search_tool = SearchTool()
        except Exception as exc:
            logger.warning(f"Search tool unavailable: {str(exc)}")

        self.tool_registry = ToolRegistry()
        if self.search_tool:
            self.tool_registry.register(self.SEARCH_TOOL, self._run_search_tool)
        self.tool_registry.register(self.DOCUMENT_TOOL, self._run_document_tool)
        self.tool_registry.register(self.WORKSPACE_TOOL, self._run_workspace_tool)
        self.tool_registry.register(self.WEATHER_TOOL, self._run_weather_tool)

    async def _is_cancelled(
        self,
        should_stop: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> bool:
        if not should_stop:
            return False
        try:
            return await should_stop()
        except Exception as exc:
            logger.warning(f"Cancellation check failed: {str(exc)}")
            return False

    def _emit_event(self, payload: Dict[str, Any]) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def _emit_trace(
        self,
        *,
        stage: str,
        title: str,
        detail: str,
        status: str = "completed",
        tool: str = "",
        attempt: int = 1,
    ) -> str:
        return self._emit_event(
            {
                "type": "trace",
                "stage": stage,
                "title": title,
                "detail": detail,
                "status": status,
                "tool": tool,
                "attempt": attempt,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
        )

    def _tool_display_name(self, tool_name: str) -> str:
        mapping = {
            self.SEARCH_TOOL: "联网搜索",
            self.DOCUMENT_TOOL: "文档检索",
            self.WORKSPACE_TOOL: "工作区检索",
            self.WEATHER_TOOL: "天气查询",
        }
        return mapping.get(tool_name, tool_name or "工具执行")

    def _build_tool_progress_detail(self, tool_result: ToolExecutionResult) -> str:
        lines = [tool_result.summary]

        if tool_result.sources:
            lines.append("结果预览：")
            for index, item in enumerate(tool_result.sources[:2], start=1):
                title = (
                    item.get("title")
                    or item.get("source")
                    or item.get("city")
                    or item.get("url")
                    or "结果"
                )
                snippet = (
                    item.get("snippet")
                    or item.get("content")
                    or item.get("summary")
                    or ""
                )
                snippet = str(snippet).replace("\n", " ").strip()
                if len(snippet) > 100:
                    snippet = f"{snippet[:100]}..."
                lines.append(f"{index}. {title}")
                if snippet:
                    lines.append(f"   {snippet}")

        if tool_result.notes:
            lines.append(f"备注：{tool_result.notes[0]}")

        return "\n".join(lines)

    def _should_show_verbose_trace(
        self,
        plan: RouterPlan,
        query: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> bool:
        source_type = str((options or {}).get("knowledge_source_type") or "")
        if plan.tools:
            return True
        if plan.route != "chat":
            return True
        if source_type == "workspace":
            return True
        if self._looks_like_code_query(query):
            return True
        return False

    def _latest_user_message(self, messages: List[Dict[str, str]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""

    def _looks_like_search_query(self, query: str) -> bool:
        lowered = query.lower()
        keywords = [
            "今天",
            "最新",
            "实时",
            "最近",
            "新闻",
            "股价",
            "汇率",
            "current",
            "latest",
            "today",
            "news",
        ]
        return any(keyword in query or keyword in lowered for keyword in keywords)

    def _looks_like_weather_query(self, query: str) -> bool:
        lowered = query.lower()
        return "天气" in query or "weather" in lowered or "气温" in query

    def _looks_like_document_query(self, query: str) -> bool:
        lowered = query.lower()
        keywords = [
            "这份文档",
            "这个文档",
            "这个pdf",
            "这份pdf",
            "附件",
            "上传的",
            "根据文档",
            "根据资料",
            "document",
            "pdf",
        ]
        return any(keyword in query or keyword in lowered for keyword in keywords)

    def _looks_like_code_query(self, query: str) -> bool:
        lowered = query.lower()
        keywords = [
            "代码",
            "函数",
            "报错",
            "文件",
            "项目",
            "组件",
            "接口",
            "脚本",
            "修复",
            "bug",
            "module",
            "code",
            "function",
            "error",
            "file",
            "traceback",
            "python",
            "vue",
            "react",
            "js",
        ]
        return any(keyword in query or keyword in lowered for keyword in keywords)

    def _extract_city_name(self, query: str) -> str:
        match = re.search(r"([\u4e00-\u9fffA-Za-z]{2,20})(?:天气|气温)", query)
        if match:
            return match.group(1)
        city_match = re.search(r"(?:weather in|temperature in)\s+([A-Za-z\s]{2,40})", query.lower())
        if city_match:
            return city_match.group(1).strip().title()
        return settings.WEATHER_DEFAULT_CITY or "Beijing"

    def _infer_code_language(self, query: str, messages: List[Dict[str, str]]) -> str:
        sample = f"{query}\n" + "\n".join(message.get("content", "") for message in messages[-6:])
        lowered = sample.lower()
        if "vue" in lowered:
            return "vue"
        if "react" in lowered or "tsx" in lowered or "jsx" in lowered:
            return "tsx"
        if "javascript" in lowered or "js" in lowered:
            return "javascript"
        if "typescript" in lowered or "ts" in lowered:
            return "typescript"
        if "python" in lowered or "traceback" in lowered:
            return "python"
        if "html" in lowered:
            return "html"
        if "css" in lowered:
            return "css"
        if "sql" in lowered:
            return "sql"
        return "text"

    def _extract_code_context(self, messages: List[Dict[str, str]]) -> str:
        blocks: List[str] = []
        for message in messages[-8:]:
            content = (message.get("content") or "").strip()
            if not content:
                continue
            if "```" in content or self._looks_like_code_query(content):
                blocks.append(f"{message.get('role', 'user')}: {content}")
        return "\n\n".join(blocks).strip()

    def _prettier_parser_for_language(self, language: str) -> str:
        mapping = {
            "javascript": "babel",
            "js": "babel",
            "typescript": "typescript",
            "ts": "typescript",
            "jsx": "babel",
            "tsx": "typescript",
            "json": "json",
            "html": "html",
            "vue": "vue",
            "css": "css",
            "scss": "scss",
            "markdown": "markdown",
            "md": "markdown",
            "yaml": "yaml",
            "yml": "yaml",
        }
        return mapping.get(language.lower(), "")

    def _format_python_code(self, code: str) -> Optional[str]:
        commands = []
        if shutil.which("black"):
            commands.append(["black", "-q", "-"])
        commands.append([sys.executable, "-m", "black", "-q", "-"])

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    input=code,
                    text=True,
                    capture_output=True,
                    timeout=8,
                    check=True,
                )
                return result.stdout or code
            except Exception:
                continue
        return None

    def _format_with_prettier(self, code: str, language: str) -> Optional[str]:
        parser = self._prettier_parser_for_language(language)
        if not parser:
            return None

        commands = []
        if shutil.which("prettier"):
            commands.append(["prettier", "--parser", parser])
        if shutil.which("npx"):
            commands.append(["npx", "prettier", "--parser", parser])

        for command in commands:
            try:
                result = subprocess.run(
                    command,
                    input=code,
                    text=True,
                    capture_output=True,
                    timeout=10,
                    check=True,
                )
                return result.stdout or code
            except Exception:
                continue
        return None

    def _format_sql_code(self, code: str) -> str:
        # 轻量兜底：没有外部格式化器时，至少把常见 SQL 关键字规范成大写并保留缩进。
        keywords = [
            "select",
            "from",
            "where",
            "order by",
            "group by",
            "left join",
            "right join",
            "inner join",
            "join",
            "insert into",
            "update",
            "delete",
            "values",
            "limit",
        ]
        formatted = code
        for keyword in sorted(keywords, key=len, reverse=True):
            formatted = re.sub(
                rf"\b{re.escape(keyword)}\b",
                keyword.upper(),
                formatted,
                flags=re.IGNORECASE,
            )
        return formatted

    def _format_code_by_language(self, code: str, language: str) -> tuple[str, str]:
        normalized_language = (language or "text").strip().lower()

        if normalized_language in {"python", "py"}:
            formatted = self._format_python_code(code)
            if formatted is not None:
                return formatted.rstrip() + "\n", "black"
            return code, ""

        if normalized_language in {
            "javascript",
            "js",
            "typescript",
            "ts",
            "jsx",
            "tsx",
            "json",
            "html",
            "vue",
            "css",
            "scss",
            "markdown",
            "md",
            "yaml",
            "yml",
        }:
            formatted = self._format_with_prettier(code, normalized_language)
            if formatted is not None:
                return formatted.rstrip() + "\n", "prettier"
            return code, ""

        if normalized_language == "sql":
            return self._format_sql_code(code), "builtin-sql"

        return code, ""

    def _format_markdown_code_blocks(self, content: str) -> tuple[str, List[str]]:
        formatter_notes: List[str] = []

        def replace(match: re.Match[str]) -> str:
            language = (match.group(1) or "text").strip()
            raw_code = match.group(2).rstrip("\n")
            formatted_code, formatter = self._format_code_by_language(raw_code, language)
            if formatter:
                formatter_notes.append(f"{language or 'text'} 代码块已使用 {formatter} 格式化。")
            return f"```{language}\n{formatted_code.rstrip()}\n```"

        formatted_content = re.sub(
            r"```([\w-]*)\n([\s\S]*?)```",
            replace,
            content,
        )
        return formatted_content, formatter_notes

    def _should_enable_code_agent(
        self,
        query: str,
        messages: List[Dict[str, str]],
        plan: RouterPlan,
        options: Dict[str, Any],
    ) -> bool:
        source_type = str(options.get("knowledge_source_type") or "")
        if self._looks_like_code_query(query):
            return True
        if source_type == "workspace":
            return True
        if plan.route == "rag" and any(tool == self.WORKSPACE_TOOL for tool in plan.tools):
            return True
        return any("```" in (message.get("content") or "") for message in messages[-6:])

    def _heuristic_plan(
        self,
        query: str,
        *,
        has_index: bool,
        enable_search: bool,
        source_type: str,
        response_style: str,
    ) -> Optional[RouterPlan]:
        tools: List[str] = []
        route = "chat"

        if self._looks_like_weather_query(query):
            route = "weather"
            tools.append(self.WEATHER_TOOL)

        if enable_search and self._looks_like_search_query(query):
            tools.append(self.SEARCH_TOOL)
            route = "search"

        if has_index and self._looks_like_document_query(query):
            if source_type == "workspace":
                tools.append(self.WORKSPACE_TOOL)
            else:
                tools.append(self.DOCUMENT_TOOL)
            route = "rag"

        if has_index and source_type == "workspace" and self._looks_like_code_query(query):
            if self.WORKSPACE_TOOL not in tools:
                tools.append(self.WORKSPACE_TOOL)
            route = "rag"

        if len(tools) > 1:
            route = "hybrid"

        if tools:
            return RouterPlan(
                route=route,
                reason="基于问题关键词和当前上下文做出的启发式规划。",
                objective="先收集相关证据，再生成最终回答。",
                tools=tools,
                answer_style=response_style,
                confidence=0.82,
            )

        return RouterPlan(
            route="chat",
            reason="问题偏向通用回答，暂不需要调用外部工具。",
            objective="基于会话上下文直接回答用户问题。",
            tools=[],
            answer_style=response_style,
            confidence=0.72,
        )

    def _normalize_plan(
        self,
        raw_plan: Dict[str, Any],
        *,
        has_index: bool,
        enable_search: bool,
        source_type: str,
        response_style: str,
    ) -> RouterPlan:
        route = str(raw_plan.get("route") or "chat").strip().lower()
        allowed_routes = {"chat", "search", "rag", "weather", "hybrid"}
        if route not in allowed_routes:
            route = "chat"

        candidate_tools = []
        for name in raw_plan.get("tools") or []:
            tool_name = str(name).strip()
            if self.tool_registry.has(tool_name):
                candidate_tools.append(tool_name)

        if route in {"search", "hybrid"} and enable_search and self.search_tool:
            if self.SEARCH_TOOL not in candidate_tools:
                candidate_tools.append(self.SEARCH_TOOL)

        if route in {"rag", "hybrid"} and has_index:
            if source_type == "workspace":
                if self.WORKSPACE_TOOL not in candidate_tools:
                    candidate_tools.append(self.WORKSPACE_TOOL)
            else:
                if self.DOCUMENT_TOOL not in candidate_tools:
                    candidate_tools.append(self.DOCUMENT_TOOL)

        if route == "weather" and self.WEATHER_TOOL not in candidate_tools:
            candidate_tools.append(self.WEATHER_TOOL)

        if route == "chat":
            candidate_tools = []

        confidence = raw_plan.get("confidence", 0.8)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.8

        return RouterPlan(
            route=route,
            reason=str(raw_plan.get("reason") or "模型给出了默认规划。"),
            objective=str(raw_plan.get("objective") or "回答用户问题。"),
            tools=candidate_tools,
            answer_style=str(raw_plan.get("answer_style") or response_style),
            confidence=max(0.0, min(confidence, 1.0)),
            requires_memory_update=bool(raw_plan.get("requires_memory_update", True)),
        )

    async def _call_router_model(
        self,
        query: str,
        *,
        has_index: bool,
        enable_search: bool,
        source_type: str,
        attachment_name: str,
        response_style: str,
    ) -> RouterPlan:
        system_prompt = (
            "你是 Router Agent，只负责输出一个 JSON 计划。\n"
            "你需要在 chat/search/rag/weather/hybrid 中选择 route。\n"
            "可用工具：search_web、search_documents、search_workspace、get_weather。\n"
            "如果没有必要，不要调用工具。\n"
            "输出必须是 JSON，字段包含：route, reason, objective, tools, answer_style, confidence, requires_memory_update。"
        )
        user_prompt = (
            f"用户问题：{query}\n"
            f"是否存在可检索索引：{has_index}\n"
            f"是否允许联网搜索：{enable_search}\n"
            f"知识源类型：{source_type}\n"
            f"附件名称：{attachment_name or 'none'}\n"
            f"回答风格：{response_style}\n"
        )

        response = await self.router_client.chat.completions.create(
            model=self.route_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or "{}"
        raw_plan = json.loads(content)
        return self._normalize_plan(
            raw_plan,
            has_index=has_index,
            enable_search=enable_search,
            source_type=source_type,
            response_style=response_style,
        )

    async def route_query(
        self,
        query: str,
        *,
        has_index: bool,
        options: Dict[str, Any],
    ) -> RouterPlan:
        # 路由判断不是直接全交给模型。
        # 这里先用规则快速命中明显场景，再在必要时让 Router 模型补结构化计划。
        enable_search = bool(options.get("enable_search", True))
        source_type = str(options.get("knowledge_source_type") or "document")
        attachment_name = str(options.get("attachment_name") or "")
        response_style = str(options.get("response_style") or "balanced")

        heuristic = self._heuristic_plan(
            query,
            has_index=has_index,
            enable_search=enable_search,
            source_type=source_type,
            response_style=response_style,
        )
        if heuristic and heuristic.route != "chat":
            return heuristic

        try:
            return await self._call_router_model(
                query,
                has_index=has_index,
                enable_search=enable_search,
                source_type=source_type,
                attachment_name=attachment_name,
                response_style=response_style,
            )
        except Exception as exc:
            logger.warning(f"Router model fallback to heuristic: {str(exc)}")
            return heuristic or RouterPlan(
                route="chat",
                reason="Router 模型不可用，已回退为默认直接回答。",
                objective="直接回答用户问题。",
                tools=[],
                answer_style=response_style,
                confidence=0.6,
            )

    async def _execute_with_retry(
        self,
        operation: Callable[[], Awaitable[ToolExecutionResult]],
        *,
        title: str,
        tool: str,
        stage: str,
        trace: TraceRecorder,
    ) -> ToolExecutionResult:
        # 所有工具执行统一收口到这里，方便管理重试和轨迹记录。
        last_error = ""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                trace.add_step(
                    title,
                    f"{title}开始执行，第 {attempt} 次尝试。",
                    stage=stage,
                    status="running",
                    tool=tool,
                    attempt=attempt,
                )
                return await operation()
            except Exception as exc:
                last_error = str(exc)
                trace.add_step(
                    title,
                    f"{title}第 {attempt} 次执行失败：{last_error}",
                    stage=stage,
                    status="retrying" if attempt < MAX_RETRIES else "failed",
                    tool=tool,
                    attempt=attempt,
                )
                if attempt >= MAX_RETRIES:
                    return ToolExecutionResult(
                        tool=tool,
                        success=False,
                        summary=f"{title}执行失败。",
                        error=last_error,
                        notes=[f"{title}已重试 {MAX_RETRIES} 次但仍失败。"],
                    )
                await asyncio.sleep(0.6)
        return ToolExecutionResult(tool=tool, success=False, summary=f"{title}执行失败。")

    async def _run_search_tool(self, query: str) -> ToolExecutionResult:
        if not self.search_tool:
            raise RuntimeError("Search tool is unavailable")

        results = await self.search_tool.search(query)
        sources = []
        evidence_blocks = []
        for item in results[:5]:
            title = item.get("title") or item.get("url") or "搜索结果"
            content = item.get("content") or item.get("snippet") or ""
            url = item.get("url") or ""
            sources.append({"title": title, "url": url, "snippet": content})
            evidence_blocks.append(f"标题：{title}\n链接：{url}\n摘要：{content}")

        return ToolExecutionResult(
            tool=self.SEARCH_TOOL,
            success=True,
            summary=f"已获取 {len(sources)} 条联网搜索结果。",
            sources=sources,
            evidence_blocks=evidence_blocks,
            notes=["请优先引用和总结高相关度搜索结果。"],
        )

    async def _run_document_tool(self, query: str, index_id: Optional[str]) -> ToolExecutionResult:
        if not index_id:
            raise RuntimeError("Document index is missing")

        results = await self.embedding_service.search_index(index_id=index_id, query=query, top_k=4)
        sources = []
        evidence_blocks = []
        for item in results:
            source = item.get("source") or item.get("filename") or "文档片段"
            page = item.get("page") or item.get("chunk_id") or "unknown"
            content = item.get("content") or ""
            score = item.get("score")
            sources.append(
                {
                    "source": source,
                    "page": page,
                    "score": score,
                    "content": content,
                }
            )
            evidence_blocks.append(f"来源：{source}\n页码/片段：{page}\n内容：{content}")

        return ToolExecutionResult(
            tool=self.DOCUMENT_TOOL,
            success=True,
            summary=f"已命中 {len(sources)} 条文档检索结果。",
            sources=sources,
            evidence_blocks=evidence_blocks,
            notes=["回答时尽量围绕命中的文档片段来组织。"],
        )

    async def _run_workspace_tool(self, query: str, index_id: Optional[str]) -> ToolExecutionResult:
        if not index_id:
            raise RuntimeError("Workspace index is missing")

        results = await self.embedding_service.search_index(index_id=index_id, query=query, top_k=6)
        sources = []
        evidence_blocks = []
        for item in results:
            source = item.get("source") or item.get("filename") or "工作区文件"
            page = item.get("page") or item.get("chunk_id") or "unknown"
            content = item.get("content") or ""
            sources.append(
                {
                    "source": source,
                    "page": page,
                    "content": content,
                }
            )
            evidence_blocks.append(f"文件：{source}\n片段：{page}\n代码/内容：{content}")

        return ToolExecutionResult(
            tool=self.WORKSPACE_TOOL,
            success=True,
            summary=f"已命中 {len(sources)} 条工作区检索结果。",
            sources=sources,
            evidence_blocks=evidence_blocks,
            notes=["如果用户在问代码问题，优先根据工作区内容定位。"],
        )

    async def _run_weather_tool(self, query: str) -> ToolExecutionResult:
        city = self._extract_city_name(query)
        response = requests.get(
            "https://api.weatherapi.com/v1/current.json",
            params={
                "key": settings.WEATHERAPI_KEY,
                "q": city,
                "lang": "zh",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        location = data.get("location", {})
        current = data.get("current", {})
        condition = current.get("condition", {})
        summary = (
            f"{location.get('name') or city}："
            f"{condition.get('text') or '未知天气'}，"
            f"当前 {current.get('temp_c', '--')}°C，"
            f"体感 {current.get('feelslike_c', '--')}°C。"
        )
        return ToolExecutionResult(
            tool=self.WEATHER_TOOL,
            success=True,
            summary=summary,
            sources=[
                {
                    "source": "WeatherAPI",
                    "city": location.get("name") or city,
                    "content": summary,
                }
            ],
            evidence_blocks=[summary],
            notes=["天气信息为实时外部数据。"],
        )

    async def _stream_research_agent(
        self,
        plan: RouterPlan,
        *,
        query: str,
        index_id: Optional[str],
        trace: TraceRecorder,
        result_holder: Dict[str, ResearchResult],
        should_stop: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> AsyncGenerator[str, None]:
        # 这里改成真正的 SSE 过程流：
        # 每个工具开始、完成、整理结果时，都会立刻向前端推一条 trace 事件。
        result = ResearchResult(route=plan.route)
        result_holder["result"] = result

        if not plan.tools:
            result.research_notes.append("本轮问题不需要调用外部工具，Research Agent 跳过工具执行。")
            yield self._emit_trace(
                stage="research",
                title="工具执行",
                detail="本轮无需调用外部工具，直接进入答案整合阶段。",
                status="completed",
            )
            return

        for tool_name in plan.tools:
            if await self._is_cancelled(should_stop):
                result.research_notes.append("用户已中断，本轮工具执行提前结束。")
                yield self._emit_trace(
                    stage="research",
                    title="工具执行中断",
                    detail="用户已手动停止，本轮工具执行提前结束。",
                    status="failed",
                    tool=tool_name,
                )
                return

            title = self._tool_display_name(tool_name)
            yield self._emit_trace(
                stage="research",
                title=title,
                detail=f"{title}已开始，正在获取外部信息。",
                status="running",
                tool=tool_name,
            )

            if tool_name in {self.SEARCH_TOOL, self.WEATHER_TOOL}:
                operation = lambda: self.tool_registry.execute(tool_name, query)
            else:
                operation = lambda: self.tool_registry.execute(tool_name, query, index_id)

            tool_result = await self._execute_with_retry(
                operation,
                title=title,
                tool=tool_name,
                stage="research",
                trace=trace,
            )
            result.tool_results.append(tool_result)
            result.sources.extend(tool_result.sources)
            result.evidence_blocks.extend(tool_result.evidence_blocks)
            result.research_notes.extend(tool_result.notes)

            if tool_result.success:
                detail = self._build_tool_progress_detail(tool_result)
                trace.add_step(
                    title,
                    detail,
                    stage="research",
                    status="completed",
                    tool=tool_name,
                )
                yield self._emit_trace(
                    stage="research",
                    title=title,
                    detail=detail,
                    status="completed",
                    tool=tool_name,
                )
            else:
                detail = tool_result.error or tool_result.summary
                trace.add_step(
                    title,
                    detail,
                    stage="research",
                    status="failed",
                    tool=tool_name,
                )
                yield self._emit_trace(
                    stage="research",
                    title=title,
                    detail=detail,
                    status="failed",
                    tool=tool_name,
                )

    async def _run_code_agent(
        self,
        *,
        query: str,
        messages: List[Dict[str, str]],
        research_result: ResearchResult,
        plan: RouterPlan,
        should_stop: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> CodeReviewResult:
        # Code Agent 只在代码场景下启用。
        # 这样可以避免每轮普通问答都额外多走一次代码检查，浪费时延和 token。
        if await self._is_cancelled(should_stop):
            return CodeReviewResult(enabled=False)

        code_context = self._extract_code_context(messages)
        evidence = "\n\n".join(research_result.evidence_blocks[:6]).strip()
        language = self._infer_code_language(query, messages)

        prompt = (
            "你是 Code Agent，负责检查代码相关回答是否更稳妥，并把示例代码整理为更规范的输出。\n"
            "请完成下面几件事：\n"
            "1. 判断当前问题是否需要给出代码。\n"
            "2. 如果需要代码，先自查代码逻辑、语法和边界条件是否明显有问题。\n"
            "3. 输出必须是 JSON，字段包含：summary, formatted_answer, language, notes。\n"
            "4. formatted_answer 如果包含代码，请使用 Markdown 三引号代码块，代码块要完整且格式整齐。\n"
            "5. 如果信息不足以保证代码完全正确，要在 summary 或 notes 里明确说明假设。\n"
        )
        user_content = (
            f"用户问题：{query}\n"
            f"Router 路由：{plan.route}\n"
            f"推断语言：{language}\n"
            f"会话中的代码上下文：\n{code_context or '无'}\n\n"
            f"Research 证据：\n{evidence or '无'}"
        )

        response = await self.code_client.chat.completions.create(
            model=self.code_model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        raw_formatted_answer = str(data.get("formatted_answer") or "")
        formatted_answer, formatter_notes = self._format_markdown_code_blocks(raw_formatted_answer)
        notes = [str(item) for item in (data.get("notes") or [])]
        notes.extend(formatter_notes)

        formatter_used = ""
        if formatter_notes:
            formatter_used = " / ".join(sorted({note.split(" 使用 ")[-1].replace(" 格式化。", "") for note in formatter_notes if "使用" in note}))
        return CodeReviewResult(
            enabled=True,
            summary=str(data.get("summary") or "Code Agent 已完成代码检查。"),
            formatted_answer=formatted_answer,
            language=str(data.get("language") or language),
            notes=notes,
            formatter_used=formatter_used,
        )

    def _build_response_messages(
        self,
        hydrated_messages: List[Dict[str, str]],
        plan: RouterPlan,
        research_result: ResearchResult,
        *,
        options: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]],
        code_review: Optional[CodeReviewResult],
    ) -> List[Dict[str, str]]:
        # 这一层的作用是“把所有中间产物汇总成最终 system prompt”。
        # Response Agent 不自己去检索，而是消费 Router / Research / Code / Memory 的结果。
        research_context = "\n\n".join(research_result.evidence_blocks).strip()
        notes = "\n".join(f"- {item}" for item in research_result.research_notes).strip()
        profile_preferences = "\n".join(
            f"- {item}" for item in (user_profile or {}).get("preferences", [])
        )
        tool_summary = ", ".join(plan.tools) if plan.tools else "none"
        code_notes = "\n".join(f"- {item}" for item in (code_review.notes if code_review else []))
        code_summary = code_review.summary if code_review and code_review.enabled else "本轮未启用 Code Agent。"
        formatted_answer = code_review.formatted_answer if code_review and code_review.enabled else ""
        formatter_text = code_review.formatter_used if code_review and code_review.formatter_used else "未使用外部格式化器"

        system_content = (
            "你是 Response Agent，负责把 Router 的计划、Research 的证据、Code Agent 的检查结果、"
            "会话上下文和用户偏好整合成对用户可见的最终中文回答。\n"
            f"当前日期：{datetime.now().strftime('%Y-%m-%d')}\n"
            f"任务目标：{plan.objective}\n"
            f"路由结果：{plan.route}\n"
            f"路由原因：{plan.reason}\n"
            f"工具计划：{tool_summary}\n"
            f"回答风格：{plan.answer_style or options.get('response_style', 'balanced')}\n"
            "回答要求：\n"
            "1. 优先结合检索到的证据和工具结果回答。\n"
            "2. 如果外部证据不足，要明确说明信息不足，不要编造。\n"
            "3. 不要暴露内部多 Agent 术语，直接面向用户表达。\n"
            "4. 如果存在来源信息，尽量自然引用关键来源。\n"
            "5. 如果要输出代码，必须使用完整的 Markdown 代码块，代码前后要有清晰说明。\n"
            "6. 如果 Code Agent 给出了格式化后的代码答案，优先吸收它的结构和代码块格式。\n"
            f"Research 备注：\n{notes or '- 本轮没有额外研究备注。'}\n"
            f"用户偏好：\n{profile_preferences or '- 暂无已记录偏好。'}\n"
            f"Research 证据：\n{research_context or '本轮没有额外外部证据。'}\n"
            f"Code Agent 总结：\n{code_summary}\n"
            f"Code Agent 格式化器：{formatter_text}\n"
            f"Code Agent 备注：\n{code_notes or '- 无额外代码备注。'}\n"
            f"Code Agent 格式化参考：\n{formatted_answer or '无'}"
        )
        return [{"role": "system", "content": system_content}, *hydrated_messages]

    async def _stream_answer(
        self,
        prompt_messages: List[Dict[str, str]],
        *,
        temperature: float,
        should_stop: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> AsyncGenerator[str, None]:
        # 正文生成阶段也带中断检查，当前端点击停止时尽快结束输出。
        last_error = ""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self.response_client.chat.completions.create(
                    model=self.answer_model,
                    messages=prompt_messages,
                    temperature=temperature,
                    stream=True,
                )
                async for chunk in response:
                    if await self._is_cancelled(should_stop):
                        logger.info("Client disconnected during answer stream")
                        return
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as exc:
                last_error = str(exc)
                if attempt >= MAX_RETRIES:
                    raise RuntimeError(f"Answer generation failed after retries: {last_error}")
                await asyncio.sleep(0.8)

    async def _run_memory_agent(self, user_id: int, query: str) -> List[str]:
        return await UserProfileService.extract_preferences(user_id, query)

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        user_id: int,
        conversation_id: int,
        index_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        on_complete: Optional[Callable[[int, int, List[Dict], str], None]] = None,
        should_stop: Optional[Callable[[], Awaitable[bool]]] = None,
    ) -> AsyncGenerator[str, None]:
        # 对外只暴露这一条总入口，内部再串 Router / Research / Code / Response / Memory。
        options = options or {}
        query = self._latest_user_message(messages)
        trace = TraceRecorder(user_id, conversation_id, query)

        try:
            plan = await self.route_query(
                query,
                has_index=bool(index_id),
                options=options,
            )
            verbose_trace = self._should_show_verbose_trace(plan, query, options)
            trace.set_route(plan.route)
            trace.add_step(
                "任务规划",
                f"路由为 {plan.route}，计划工具：{', '.join(plan.tools) or 'none'}。",
                stage="planning",
                status="completed",
            )

            if await self._is_cancelled(should_stop):
                await trace.save(status="cancelled")
                return

            yield self._emit_event(
                {
                    "type": "plan",
                    "plan": {
                        "route": plan.route,
                        "reason": plan.reason,
                        "objective": plan.objective,
                        "tools": plan.tools,
                        "answer_style": plan.answer_style,
                        "confidence": plan.confidence,
                        "verbose_trace": verbose_trace,
                    },
                }
            )
            yield self._emit_event(
                {
                    "type": "route",
                    "route": plan.route,
                    "reason": plan.reason,
                }
            )
            if verbose_trace:
                yield self._emit_trace(
                    stage="planning",
                    title="路由决策",
                    detail=f"本轮选择 {plan.route} 路径，原因：{plan.reason}",
                    status="completed",
                )
                yield self._emit_trace(
                    stage="planning",
                    title="执行计划",
                    detail=(
                        f"目标：{plan.objective}\n"
                        f"工具：{', '.join(plan.tools) or '无'}\n"
                        f"风格：{plan.answer_style}\n"
                        f"置信度：{plan.confidence:.2f}"
                    ),
                    status="completed",
                )

            research_holder: Dict[str, ResearchResult] = {}
            async for event in self._stream_research_agent(
                plan,
                query=query,
                index_id=index_id,
                trace=trace,
                result_holder=research_holder,
                should_stop=should_stop,
            ):
                if verbose_trace:
                    yield event
            research_result = research_holder.get("result", ResearchResult(route=plan.route))

            if await self._is_cancelled(should_stop):
                await trace.save(status="cancelled")
                return

            if research_result.sources:
                # 如果拿到了来源信息，前端会把这些内容渲染到 sources 面板里。
                yield self._emit_event(
                    {
                        "type": "sources",
                        "route": plan.route,
                        "sources": research_result.sources,
                    }
                )

            code_review = CodeReviewResult(enabled=False)
            if self._should_enable_code_agent(query, messages, plan, options):
                if verbose_trace:
                    yield self._emit_trace(
                        stage="research",
                        title="代码检查",
                        detail="Code Agent 正在检查代码思路、整理代码块格式并补充风险提示。",
                        status="running",
                        tool="code_agent",
                    )
                code_review = await self._run_code_agent(
                    query=query,
                    messages=messages,
                    research_result=research_result,
                    plan=plan,
                    should_stop=should_stop,
                )
                trace.add_step(
                    "代码检查",
                    f"{code_review.summary} 格式化器：{code_review.formatter_used or '未命中'}。",
                    stage="research",
                    status="completed",
                    tool="code_agent",
                )
                if verbose_trace:
                    yield self._emit_trace(
                        stage="research",
                        title="代码检查",
                        detail=(
                            f"{code_review.summary}\n"
                            f"格式化器：{code_review.formatter_used or '未命中可用格式化器，保留模型整理结果。'}"
                        ),
                        status="completed",
                        tool="code_agent",
                    )

            prompt_messages = self._build_response_messages(
                messages,
                plan,
                research_result,
                options=options,
                user_profile=user_profile,
                code_review=code_review,
            )
            if verbose_trace:
                yield self._emit_trace(
                    stage="response",
                    title="开始生成",
                    detail="已进入正文流式输出阶段。",
                    status="running",
                )

            full_response: List[str] = []
            async for delta in self._stream_answer(
                prompt_messages,
                temperature=float(options.get("temperature", settings.ASSISTANT_TEMPERATURE)),
                should_stop=should_stop,
            ):
                # 每 yield 一段 content，前端就会把这段内容追加到最后一条 assistant 消息里。
                full_response.append(delta)
                yield self._emit_event({"type": "content", "content": delta})

            answer_text = "".join(full_response)
            trace.add_step(
                "答案生成",
                "最终回答生成完成。",
                stage="response",
                status="completed",
            )

            if plan.requires_memory_update:
                memory_updates = await self._run_memory_agent(user_id, query)
                if memory_updates:
                    trace.add_step(
                        "记忆更新",
                        f"本轮提取并更新 {len(memory_updates)} 条长期偏好记忆。",
                        stage="memory",
                        status="completed",
                    )
                    if verbose_trace:
                        yield self._emit_trace(
                            stage="memory",
                            title="记忆更新",
                            detail=f"本轮已提取并更新 {len(memory_updates)} 条用户偏好记忆。",
                            status="completed",
                        )

            if on_complete and answer_text:
                await on_complete(
                    user_id,
                    conversation_id,
                    messages,
                    answer_text,
                )

            await trace.save(status="completed" if answer_text else "empty")
        except Exception as exc:
            logger.error(f"Agent workflow failed: {str(exc)}", exc_info=True)
            trace.add_step(
                "故障恢复",
                f"执行过程中出现异常：{str(exc)}",
                stage="recovery",
                status="failed",
            )
            await trace.save(status="failed")
            yield self._emit_trace(
                stage="recovery",
                title="故障恢复",
                detail=f"执行过程中出现异常，系统已完成 {MAX_RETRIES} 次重试并回退到兜底输出：{str(exc)}",
                status="failed",
            )
            yield self._emit_event(
                {
                    "type": "content",
                    "content": "本轮回答在执行过程中出现异常，系统已完成重试但仍未成功。你可以直接重新发送，或换一种更简短的提问方式继续。",
                }
            )
