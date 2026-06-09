import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Callable, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger
from app.services.embedding_service import EmbeddingService
from app.tools.search import SearchTool


logger = get_logger(service="agent_chat")


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

    async def route_query(self, query: str, has_index: bool) -> Tuple[str, str]:
        heuristic = self._heuristic_route(query, has_index)
        if heuristic:
            return heuristic

        prompt = (
            "You are a router for a chat assistant. "
            "Choose one route from chat, search, rag.\n"
            "Rules:\n"
            "- search: current, latest, real-time, news, web-only facts.\n"
            "- rag: answer should rely on an uploaded document and has_document is true.\n"
            "- chat: everything else.\n"
            "Return strict JSON with keys route and reason."
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
            return route, payload.get("reason", "")
        except json.JSONDecodeError:
            logger.warning(f"Router returned non-JSON content: {content}")
            return "chat", "路由解析失败，回退到普通回答。"

    async def _build_search_messages(
        self,
        query: str,
        hydrated_messages: List[Dict[str, str]],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        if not self.search_tool:
            fallback_system = {
                "role": "system",
                "content": "当前未配置联网搜索能力，请直接基于已有知识作答，并说明未进行联网检索。",
            }
            return [fallback_system, *hydrated_messages], []

        results = await asyncio.to_thread(self.search_tool.search, query)
        sources = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in results
        ]
        context = "\n\n".join(
            [
                f"标题: {item['title']}\n链接: {item['url']}\n摘要: {item['snippet']}"
                for item in sources
            ]
        )
        system_message = {
            "role": "system",
            "content": (
                "你是一个联网搜索问答助手。请优先依据下面的搜索结果回答，"
                "并在回答中自然提及关键信息来源。"
                f"\n当前日期: {datetime.now().strftime('%Y-%m-%d')}"
                f"\n搜索结果:\n{context or '没有查到相关结果。'}"
            ),
        }
        return [system_message, *hydrated_messages], sources

    async def _build_rag_messages(
        self,
        query: str,
        index_id: str,
        hydrated_messages: List[Dict[str, str]],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        try:
            results = await self.embedding_service.search_index(
                index_id=index_id,
                query=query,
                top_k=4,
            )
        except ValueError as exc:
            system_message = {
                "role": "system",
                "content": (
                    "当前文档索引与新的 embedding 配置不兼容。"
                    "请移除旧文档后重新上传，再继续进行文档问答。"
                ),
            }
            fallback_messages = [system_message, *hydrated_messages]
            return fallback_messages, [{"source": "system", "page": "-", "content": str(exc)}]
        sources = [
            {
                "source": item["metadata"].get("source", "unknown"),
                "page": item["metadata"].get("page", "unknown"),
                "content": item["content"],
            }
            for item in results
        ]
        context = "\n\n".join(
            [
                f"来源: {item['source']}\n页码: {item['page']}\n内容: {item['content']}"
                for item in sources
            ]
        )
        system_message = {
            "role": "system",
            "content": (
                "你是一个文档问答助手。请优先依据提供的文档片段回答。"
                "如果文档信息不足，请明确说明，不要编造。"
                f"\n文档片段:\n{context or '没有检索到相关文档内容。'}"
            ),
        }
        return [system_message, *hydrated_messages], sources

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
        route, reason = await self.route_query(latest_user_message, bool(index_id))
        prompt_messages = messages
        sources: List[Dict[str, str]] = []

        if route == "search":
            yield (
                "data: "
                + json.dumps(
                    {"type": "thinking", "label": "执行步骤", "content": "正在联网搜索相关信息..."},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            prompt_messages, sources = await self._build_search_messages(
                latest_user_message,
                messages,
            )
        elif route == "rag" and index_id:
            yield (
                "data: "
                + json.dumps(
                    {"type": "thinking", "label": "执行步骤", "content": "正在检索已上传文档中的相关片段..."},
                    ensure_ascii=False,
                )
                + "\n\n"
            )
            prompt_messages, sources = await self._build_rag_messages(
                latest_user_message,
                index_id,
                messages,
            )
        else:
            route = "chat"

        yield (
            "data: "
            + json.dumps(
                {"type": "route", "route": route, "reason": reason},
                ensure_ascii=False,
            )
            + "\n\n"
        )
        if sources:
            preview_lines = []
            for index, item in enumerate(sources[:3], start=1):
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
                    {"type": "sources", "route": route, "sources": sources},
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
