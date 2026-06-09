from app.core.config import ServiceType, settings
from app.services.deepseek_service import DeepseekService
from app.services.ollama_service import OllamaService
from app.services.search_service import SearchService


class LLMFactory:
    @staticmethod
    def create_chat_service():
        if settings.CHAT_SERVICE == ServiceType.OLLAMA:
            return OllamaService()
        return DeepseekService(
            model=settings.CHAT_MODEL_NAME,
            api_key=settings.CHAT_API_KEY,
            base_url=settings.CHAT_BASE_URL,
        )

    @staticmethod
    def create_reasoner_service():
        if settings.REASON_SERVICE == ServiceType.OLLAMA:
            return OllamaService()
        return DeepseekService(
            model=settings.REASON_MODEL_NAME,
            api_key=settings.REASON_API_KEY,
            base_url=settings.REASON_BASE_URL,
        )

    @staticmethod
    def create_search_service():
        return SearchService()
