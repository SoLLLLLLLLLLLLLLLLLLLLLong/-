import asyncio
import json
import time
from typing import AsyncGenerator, Callable, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logger import get_logger


logger = get_logger(service="deepseek")


class DeepseekService:
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        logger.info("Initializing OpenAI-compatible chat service")
        self.client = AsyncOpenAI(
            api_key=api_key or settings.CHAT_API_KEY,
            base_url=base_url or settings.CHAT_BASE_URL,
        )
        self.model = model or settings.CHAT_MODEL_NAME
        self.enable_cache = settings.ENABLE_REDIS_CACHE

    async def _stream_cached_response(
        self, response: str, delay: float = 0.05
    ) -> AsyncGenerator[str, None]:
        chunks = [response[i : i + 4] for i in range(0, len(response), 4)]
        for chunk in chunks:
            await asyncio.sleep(delay)
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    async def generate_stream(
        self,
        messages: List[Dict],
        user_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        on_complete: Optional[Callable[[int, int, List[Dict], str], None]] = None,
    ) -> AsyncGenerator[str, None]:
        cache = None
        try:
            if self.enable_cache:
                from app.services.redis_semantic_cache import RedisSemanticCache

                cache = RedisSemanticCache(prefix="deepseek", user_id=user_id)

            start_time = time.time()
            if cache:
                cached_response = await cache.lookup(messages)
                if cached_response:
                    logger.info(
                        f"Cache hit! Response time: {time.time() - start_time:.4f} seconds"
                    )
                    async for chunk in self._stream_cached_response(cached_response):
                        yield chunk
                    if on_complete and user_id is not None and conversation_id is not None:
                        await on_complete(user_id, conversation_id, messages, cached_response)
                    return

            full_response = []
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_response.append(delta)
                    yield f"data: {json.dumps(delta, ensure_ascii=False)}\n\n"

            complete_response = "".join(full_response)
            if cache:
                await cache.update(messages, complete_response)

            logger.info(
                f"Cache miss. Response time: {time.time() - start_time:.4f} seconds"
            )
            if on_complete and user_id is not None and conversation_id is not None:
                await on_complete(user_id, conversation_id, messages, complete_response)

        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}", exc_info=True)
            error_msg = json.dumps(f"生成回复时出错: {str(e)}", ensure_ascii=False)
            yield f"data: {error_msg}\n\n"

    async def generate(self, messages: List[Dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False,
        )
        return response.choices[0].message.content
