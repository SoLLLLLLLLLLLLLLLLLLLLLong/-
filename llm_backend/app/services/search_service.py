import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Callable, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger
from app.prompts.search_prompts import SEARCH_SUMMARY_PROMPT, SEARCH_SYSTEM_PROMPT
from app.services.function_tools import FunctionTool, ToolRegistry
from app.tools.definitions import SEARCH_TOOL
from app.tools.search import SearchTool


logger = get_logger(service="search")


class SearchService:
    def __init__(self):
        logger.info("Initializing SearchService...")
        self.client = AsyncOpenAI(
            api_key=settings.CHAT_API_KEY,
            base_url=settings.CHAT_BASE_URL,
        )
        self.model = settings.CHAT_MODEL_NAME
        self.search_tool = SearchTool()
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(
            FunctionTool(
                **SEARCH_TOOL,
                handler=self._handle_search,
            )
        )
        self.tools_description = self._generate_tools_description()

    def _generate_tools_description(self) -> str:
        tool_descriptions = []
        for tool_def in self.tool_registry.get_tools_definition():
            func = tool_def["function"]
            params = [
                f"{param_name}: {param_info['description']}"
                for param_name, param_info in func["parameters"]["properties"].items()
                if param_name in func["parameters"].get("required", [])
            ]
            tool_descriptions.append(
                f"{func['name']}: {func['description']}"
                + (f"。必填参数: {', '.join(params)}" if params else "")
            )
        return "你现在可用的工具有：\n\n" + "\n".join(tool_descriptions)

    async def _handle_search(self, query: str) -> List[Dict]:
        return await asyncio.to_thread(self.search_tool.search, query)

    async def _call_with_tool(self, messages: List[Dict]) -> Dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tool_registry.get_tools_definition(),
            tool_choice="auto",
        )
        return response.choices[0]

    async def generate_stream(
        self,
        query: str,
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        on_complete: Optional[Callable] = None,
    ) -> AsyncGenerator[str, None]:
        messages = [
            {
                "role": "system",
                "content": SEARCH_SYSTEM_PROMPT.format(
                    tools_description=self.tools_description
                ),
            },
            {"role": "user", "content": query},
        ]

        choice = await self._call_with_tool(messages)

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            search_results = await self.tool_registry.execute_tool(
                tool_call.function.name,
                tool_call.function.arguments,
            )

            context = "\n---\n".join(
                [
                    f"来源: {result['title']}\n链接: {result['url']}\n内容: {result['snippet']}\n"
                    for result in search_results
                ]
            )
            context_prompt = SEARCH_SUMMARY_PROMPT.format(
                context=context,
                query=query,
                cur_date=datetime.now().strftime("%Y-%m-%d"),
            )

            yield f"data: {json.dumps({'type': 'search_start'}, ensure_ascii=False)}\n\n"
            yield (
                f"data: {json.dumps({'type': 'search_results', 'total': len(search_results), 'query': query, 'results': search_results}, ensure_ascii=False)}\n\n"
            )

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": context_prompt}],
                stream=True,
            )
            full_response = []
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response.append(content)
                    yield f"data: {json.dumps(content, ensure_ascii=False)}\n\n"

            if on_complete and user_id is not None and conversation_id is not None:
                await on_complete(
                    user_id,
                    conversation_id,
                    [{"role": "user", "content": query}],
                    "".join(full_response),
                )
            return

        yield f"data: {json.dumps({'type': 'direct_answer'}, ensure_ascii=False)}\n\n"
        stream_response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        full_response = []
        async for chunk in stream_response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response.append(content)
                yield f"data: {json.dumps({'type': 'direct_content', 'content': content}, ensure_ascii=False)}\n\n"

        if on_complete and user_id is not None and conversation_id is not None:
            await on_complete(
                user_id,
                conversation_id,
                [{"role": "user", "content": query}],
                "".join(full_response),
            )
