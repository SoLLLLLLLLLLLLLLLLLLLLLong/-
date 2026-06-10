import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Callable, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger
from app.services.embedding_service import EmbeddingService
from app.tools.search import SearchTool


logger = get_logger(service="agent_chat")


@dataclass
class RouteDecision:
    route: str
    reason: str = ""
    needs_search: bool = False
    needs_rag: bool = False


@dataclass
class ResearchResult:
    route: str
    reason: str = ""
    sources: List[Dict[str, str]] = field(default_factory=list)
    evidence_blocks: List[str] = field(default_factory=list)
    research_notes: List[str] = field(default_factory=list)


class AgentChatService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.AGENT_API_KEY or settings.CHAT_API_KEY,
            base_url=settings.AGENT_BASE_URL or settings.CHAT_BASE_URL,
        )
        self.answer_client = AsyncOpenAI(
            api_key=settings.CHAT_API_KEY,
            base_url=settings.CHAT_BASE_URL,
        )
        self.route_model = settings.AGENT_MODEL_NAME or settings.CHAT_MODEL_NAME
        self.answer_model = settings.CHAT_MODEL_NAME
        self.embedding_service = EmbeddingService()
        try:
            self.search_tool = SearchTool()
        except Exception as exc:
            logger.warning(f"Search tool unavailable: {str(exc)}")
            self.search_tool = None

    def _latest_user_message(self, messages: List[Dict[str, str]]) -> str:
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""

    def _heuristic_route(self, query: str, has_index: bool) -> Optional[Tuple[str, str]]:
        lowered = query.lower()
        search_keywords = [
            "今天",
            "最新",
            "实时",
            "最近",
            "新闻",
            "天气",
            "股价",
            "汇率",
            "当前",
            "recent",
            "latest",
            "today",
            "news",
            "weather",
        ]
        if any(keyword in query or keyword in lowered for keyword in search_keywords):
            return "search", "问题明显依赖最新或实时信息。"

        rag_keywords = [
            "这个pdf",
            "这份pdf",
            "这份文档",
            "这个文档",
            "附件",
            "上传的",
            "根据文档",
            "根据资料",
            "总结这份",
            "summarize this pdf",
            "document",
            "pdf",
        ]
        if has_index and any(keyword in query.lower() for keyword in rag_keywords):
            return "rag", "问题直接指向已上传文档。"

        return None

    async def route_query(self, query: str, has_index: bool) -> RouteDecision:
        heuristic = self._heuristic_route(query, has_index)
        if heuristic:
            route, reason = heuristic
            return RouteDecision(
                route=route,
                reason=reason,
                needs_search=route == "search",
                needs_rag=route == "rag" and has_index,
            )

        prompt = (
            "You are the Router Agent for a multi-agent assistant workflow. "
            "Choose one route from chat, search, rag.\n"
            "Rules:\n"
            "- search: current, latest, real-time, news, web-only facts.\n"
            "- rag: answer should rely on an uploaded document and has_document is true.\n"
            "- chat: everything else.\n"
            "Return strict JSON with keys route, reason, needs_search, needs_rag."
        )
        response = await self.client.chat.completions.create(
            model=self.route_model,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"query": query, "has_document": has_index},
                        ensure_ascii=False,
                    ),
                },
            ],
            stream=False,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            payload = json.loads(content)
            route = payload.get("route", "chat")
            if route not in {"chat", "search", "rag"}:
                route = "chat"
            return RouteDecision(
                route=route,
                reason=payload.get("reason", ""),
                needs_search=bool(payload.get("needs_search", route == "search")),
                needs_rag=bool(payload.get("needs_rag", route == "rag" and has_index)),
            )
        except json.JSONDecodeError:
            logger.warning(f"Router returned non-JSON content: {content}")
            return RouteDecision(route="chat", reason="路由解析失败，回退到普通回答。")

    async def _run_search_agent(
        self,
        query: str,
    ) -> ResearchResult:
        if not self.search_tool:
            return ResearchResult(
                route="search",
                reason="当前未配置联网搜索能力，Research Agent 回退为无工具模式。",
                research_notes=["未配置联网搜索能力，无法执行实时检索。"],
            )

        results = await asyncio.to_thread(self.search_tool.search, query)
        sources = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in results
        ]
        evidence_blocks = [
            [
                f"标题: {item['title']}\n链接: {item['url']}\n摘要: {item['snippet']}"
                for item in sources
            ]
        ][0]
        notes = [f"已完成联网搜索，共检索到 {len(sources)} 条候选结果。"]
        if not sources:
            notes.append("没有查到有效搜索结果，后续回答需要谨慎说明。")
        return ResearchResult(
            route="search",
            sources=sources,
            evidence_blocks=evidence_blocks,
            research_notes=notes,
        )

    async def _run_rag_agent(
        self,
        query: str,
        index_id: str,
    ) -> ResearchResult:
        try:
            results = await self.embedding_service.search_index(
                index_id=index_id,
                query=query,
                top_k=4,
            )
        except ValueError as exc:
            return ResearchResult(
                route="rag",
                reason="文档索引与当前 embedding 配置不兼容。",
                sources=[{"source": "system", "page": "-", "content": str(exc)}],
                research_notes=[
                    "当前文档索引与新的 embedding 配置不兼容。",
                    "建议移除旧文档并重新上传后再继续提问。",
                ],
            )
        sources = [
            {
                "source": item["metadata"].get("source", "unknown"),
                "page": item["metadata"].get("page", "unknown"),
                "content": item["content"],
            }
            for item in results
        ]
        evidence_blocks = [
            [
                f"来源: {item['source']}\n页码: {item['page']}\n内容: {item['content']}"
                for item in sources
            ]
        ][0]
        notes = [f"已完成文档检索，共命中 {len(sources)} 个相关片段。"]
        if not sources:
            notes.append("没有检索到有效文档内容，回答时需要明确说明。")
        return ResearchResult(
            route="rag",
            sources=sources,
            evidence_blocks=evidence_blocks,
            research_notes=notes,
        )

    def _build_response_messages(
        self,
        hydrated_messages: List[Dict[str, str]],
        route_decision: RouteDecision,
        research_result: ResearchResult,
    ) -> List[Dict[str, str]]:
        route_label_map = {
            "chat": "普通回答",
            "search": "联网搜索",
            "rag": "文档检索",
        }
        route_label = route_label_map.get(route_decision.route, "普通回答")

        research_context = "\n\n".join(research_result.evidence_blocks).strip()
        notes = "\n".join(f"- {item}" for item in research_result.research_notes).strip()
        system_content = (
            "你是 Response Agent，负责整合 Router Agent 和 Research Agent 的结果，"
            "给出最终面向用户的中文回答。\n"
            f"本轮路由结果：{route_label}\n"
            f"路由原因：{route_decision.reason or '无'}\n"
            f"当前日期：{datetime.now().strftime('%Y-%m-%d')}\n"
            "回答要求：\n"
            "1. 优先结合研究结果回答，不要忽略检索到的证据。\n"
            "2. 如果证据不足，明确说明信息不足，不要编造。\n"
            "3. 回答要自然、清晰、直接，不要暴露内部 Agent 名称。\n"
            "4. 如果是联网搜索或文档检索，尽量自然引用来源关键信息。\n"
            f"Research Agent 备注：\n{notes or '- 无'}\n"
            f"Research Agent 证据：\n{research_context or '无外部证据，本轮按普通回答处理。'}"
        )
        return [{"role": "system", "content": system_content}, *hydrated_messages]

    async def _run_research_agent(
        self,
        route_decision: RouteDecision,
        query: str,
        index_id: Optional[str],
    ) -> ResearchResult:
        if route_decision.route == "rag" and not index_id:
            route_decision.route = "chat"
            route_decision.reason = "当前没有可用文档，已回退到普通回答。"
            return ResearchResult(
                route="chat",
                reason=route_decision.reason,
                research_notes=["未检测到可用文档索引，本轮不执行文档检索。"],
            )
        if route_decision.route == "search":
            return await self._run_search_agent(query)
        if route_decision.route == "rag" and index_id:
            return await self._run_rag_agent(query, index_id)
        return ResearchResult(
            route="chat",
            reason=route_decision.reason,
            research_notes=["本轮无需调用外部工具，直接基于对话上下文回答。"],
        )

    async def _stream_answer(
        self,
        prompt_messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        response = await self.answer_client.chat.completions.create(
            model=self.answer_model,
            messages=prompt_messages,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        user_id: int,
        conversation_id: int,
        index_id: Optional[str] = None,
        on_complete: Optional[Callable[[int, int, List[Dict], str], None]] = None,
    ) -> AsyncGenerator[str, None]:
        latest_user_message = self._latest_user_message(messages)
        yield (
            "data: "
            + json.dumps(
                {"type": "thinking", "label": "状态", "content": "正在分析用户问题..."},
                ensure_ascii=False,
            )
            + "\n\n"
        )
        route_decision = await self.route_query(latest_user_message, bool(index_id))
        yield (
            "data: "
            + json.dumps(
                {
                    "type": "thinking",
                    "label": "Agent Workflow",
                    "content": "Router Agent 已完成问题分流，Research Agent 准备执行工具调用。",
                },
                ensure_ascii=False,
            )
            + "\n\n"
        )

        if route_decision.route == "search":
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "thinking",
                        "label": "Research Agent",
                        "content": "正在联网搜索相关信息...",
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
        elif route_decision.route == "rag" and index_id:
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "thinking",
                        "label": "Research Agent",
                        "content": "正在检索已上传文档中的相关片段...",
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
        research_result = await self._run_research_agent(
            route_decision=route_decision,
            query=latest_user_message,
            index_id=index_id,
        )
        prompt_messages = self._build_response_messages(
            hydrated_messages=messages,
            route_decision=route_decision,
            research_result=research_result,
        )

        yield (
            "data: "
            + json.dumps(
                {
                    "type": "route",
                    "route": route_decision.route,
                    "reason": route_decision.reason,
                },
                ensure_ascii=False,
            )
            + "\n\n"
        )
        yield (
            "data: "
            + json.dumps(
                {
                    "type": "thinking",
                    "label": "Response Agent",
                    "content": "正在整合路由结果、检索证据与会话记忆，生成最终回答...",
                },
                ensure_ascii=False,
            )
            + "\n\n"
        )

        if research_result.research_notes:
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "thinking",
                        "label": "研究摘要",
                        "content": "\n".join(research_result.research_notes),
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        if research_result.sources:
            preview_lines = []
            for index, item in enumerate(research_result.sources[:3], start=1):
                if item.get("url"):
                    preview_lines.append(f"{index}. {item.get('title') or item.get('url')}")
                else:
                    preview_lines.append(
                        f"{index}. {item.get('source', '文档片段')}（页码：{item.get('page', '未知')}）"
                    )
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "thinking",
                        "label": "中间结果",
                        "content": "\n".join(preview_lines),
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "sources",
                        "route": route_decision.route,
                        "sources": research_result.sources,
                    },
                    ensure_ascii=False,
                )
                + "\n\n"
            )

        full_response: List[str] = []
        async for delta in self._stream_answer(prompt_messages):
            full_response.append(delta)
            yield (
                "data: "
                + json.dumps({"type": "content", "content": delta}, ensure_ascii=False)
                + "\n\n"
            )

        if on_complete:
            await on_complete(
                user_id,
                conversation_id,
                [{"role": "user", "content": latest_user_message}],
                "".join(full_response),
            )
