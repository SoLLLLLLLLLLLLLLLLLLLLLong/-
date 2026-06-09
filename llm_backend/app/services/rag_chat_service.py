import json
from typing import AsyncGenerator, Dict, List

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.embedding_service import EmbeddingService


class RAGChatService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.client = AsyncOpenAI(
            api_key=settings.CHAT_API_KEY,
            base_url=settings.CHAT_BASE_URL,
        )
        self.model = settings.CHAT_MODEL_NAME

    async def generate_stream(
        self, messages: List[Dict[str, str]], index_id: str
    ) -> AsyncGenerator[str, None]:
        query = next(
            (msg["content"] for msg in reversed(messages) if msg["role"] == "user"),
            "",
        )
        results = await self.embedding_service.search_index(
            index_id=index_id,
            query=query,
            top_k=3,
        )

        context = "\n\n".join(
            [
                f"来源: {item['metadata'].get('source', 'unknown')}\n"
                f"页码: {item['metadata'].get('page', 'unknown')}\n"
                f"内容: {item['content']}"
                for item in results
            ]
        )

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识库问答助手。请优先基于提供的知识库片段回答。"
                    "如果知识库中没有足够信息，请明确说明，不要编造。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"知识库片段:\n{context or '没有检索到相关内容'}\n\n"
                    f"用户问题:\n{query}"
                ),
            },
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=prompt_messages,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = json.dumps(chunk.choices[0].delta.content, ensure_ascii=False)
                yield f"data: {content}\n\n"
