from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings


ROOT_DIR = Path(__file__).parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class ServiceType(str, Enum):
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    SILICONFLOW = "siliconflow"


class Settings(BaseSettings):
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_CHAT_MODEL: str = "deepseek-ai/DeepSeek-V3"
    SILICONFLOW_REASON_MODEL: str = "Qwen/QwQ-32B"
    SILICONFLOW_AGENT_MODEL: str = "deepseek-ai/DeepSeek-V3"
    SILICONFLOW_VISION_MODEL: str = "Qwen/Qwen2.5-VL-72B-Instruct"

    VISION_API_KEY: str = ""
    VISION_BASE_URL: str = ""
    VISION_MODEL: str = ""

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "qwen2.5:7b"
    OLLAMA_REASON_MODEL: str = "qwen2.5:7b"
    OLLAMA_EMBEDDING_MODEL: str = "bge-m3"
    OLLAMA_AGENT_MODEL: str = "qwen2.5:7b"

    CHAT_SERVICE: ServiceType = ServiceType.SILICONFLOW
    REASON_SERVICE: ServiceType = ServiceType.SILICONFLOW
    AGENT_SERVICE: ServiceType = ServiceType.SILICONFLOW

    SERPAPI_KEY: str = ""
    TAVILY_API_KEY: str = ""
    WEATHERAPI_KEY: str = ""
    WEATHER_DEFAULT_CITY: str = "Beijing"
    SEARCH_RESULT_COUNT: int = 3

    DB_TYPE: str = "sqlite"
    SQLITE_DB_PATH: str = "resources/app.db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "assist_gen"

    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_CACHE_EXPIRE: int = 3600
    REDIS_CACHE_THRESHOLD: float = 0.8
    ENABLE_REDIS_CACHE: bool = False

    EMBEDDING_TYPE: str = "sentence_transformer"
    EMBEDDING_MODEL: str = "bge-m3"
    EMBEDDING_MODEL_PATH: str = ""
    EMBEDDING_PROVIDER: str = "siliconflow"
    EMBEDDING_THRESHOLD: float = 0.90
    MEMORY_SUMMARY_TRIGGER_MESSAGES: int = 12
    MEMORY_KEEP_RECENT_MESSAGES: int = 8
    MEMORY_SUMMARY_MIN_MESSAGES: int = 4
    ASSISTANT_MODEL_PLACEHOLDER: str = "env:CHAT_MODEL_NAME"
    ASSISTANT_TEMPERATURE: float = 0.7
    ASSISTANT_ENABLE_WEB_SEARCH: bool = True
    ASSISTANT_RESPONSE_STYLE: str = "balanced"

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_TYPE.lower() == "sqlite":
            sqlite_path = Path(self.SQLITE_DB_PATH)
            if not sqlite_path.is_absolute():
                sqlite_path = ROOT_DIR / sqlite_path
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{sqlite_path.as_posix()}"
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def _service_api_key(self, service: ServiceType) -> str:
        if service == ServiceType.SILICONFLOW:
            return self.SILICONFLOW_API_KEY
        if service == ServiceType.DEEPSEEK:
            return self.DEEPSEEK_API_KEY
        return ""

    def _service_base_url(self, service: ServiceType) -> str:
        if service == ServiceType.SILICONFLOW:
            return self.SILICONFLOW_BASE_URL
        if service == ServiceType.DEEPSEEK:
            return self.DEEPSEEK_BASE_URL
        return self.OLLAMA_BASE_URL

    def _service_model(self, service: ServiceType, purpose: str) -> str:
        if service == ServiceType.SILICONFLOW:
            mapping = {
                "chat": self.SILICONFLOW_CHAT_MODEL,
                "reason": self.SILICONFLOW_REASON_MODEL,
                "agent": self.SILICONFLOW_AGENT_MODEL,
                "vision": self.SILICONFLOW_VISION_MODEL,
            }
            return mapping[purpose]
        if service == ServiceType.DEEPSEEK:
            return self.DEEPSEEK_MODEL
        mapping = {
            "chat": self.OLLAMA_CHAT_MODEL,
            "reason": self.OLLAMA_REASON_MODEL,
            "agent": self.OLLAMA_AGENT_MODEL,
        }
        return mapping.get(purpose, self.OLLAMA_CHAT_MODEL)

    @property
    def CHAT_API_KEY(self) -> str:
        return self._service_api_key(self.CHAT_SERVICE)

    @property
    def CHAT_BASE_URL(self) -> str:
        return self._service_base_url(self.CHAT_SERVICE)

    @property
    def CHAT_MODEL_NAME(self) -> str:
        return self._service_model(self.CHAT_SERVICE, "chat")

    @property
    def REASON_API_KEY(self) -> str:
        return self._service_api_key(self.REASON_SERVICE)

    @property
    def REASON_BASE_URL(self) -> str:
        return self._service_base_url(self.REASON_SERVICE)

    @property
    def REASON_MODEL_NAME(self) -> str:
        return self._service_model(self.REASON_SERVICE, "reason")

    @property
    def AGENT_API_KEY(self) -> str:
        return self._service_api_key(self.AGENT_SERVICE)

    @property
    def AGENT_BASE_URL(self) -> str:
        return self._service_base_url(self.AGENT_SERVICE)

    @property
    def AGENT_MODEL_NAME(self) -> str:
        return self._service_model(self.AGENT_SERVICE, "agent")

    @property
    def EFFECTIVE_VISION_API_KEY(self) -> str:
        return self.VISION_API_KEY or self.SILICONFLOW_API_KEY or self.DEEPSEEK_API_KEY

    @property
    def EFFECTIVE_VISION_BASE_URL(self) -> str:
        return self.VISION_BASE_URL or self.SILICONFLOW_BASE_URL or self.DEEPSEEK_BASE_URL

    @property
    def EFFECTIVE_VISION_MODEL(self) -> str:
        return self.VISION_MODEL or self.SILICONFLOW_VISION_MODEL or self.DEEPSEEK_MODEL

    @property
    def EMBEDDING_API_KEY(self) -> str:
        if self.EMBEDDING_PROVIDER.lower() == "siliconflow":
            return self.SILICONFLOW_API_KEY or self.DEEPSEEK_API_KEY
        if self.EMBEDDING_PROVIDER.lower() == "deepseek":
            return self.DEEPSEEK_API_KEY
        return self.SILICONFLOW_API_KEY or self.DEEPSEEK_API_KEY

    @property
    def EMBEDDING_BASE_URL(self) -> str:
        if self.EMBEDDING_PROVIDER.lower() == "siliconflow":
            return self.SILICONFLOW_BASE_URL or self.DEEPSEEK_BASE_URL
        if self.EMBEDDING_PROVIDER.lower() == "deepseek":
            return self.DEEPSEEK_BASE_URL
        return self.SILICONFLOW_BASE_URL or self.DEEPSEEK_BASE_URL

    @property
    def EMBEDDING_MODEL_NAME(self) -> str:
        return self.EMBEDDING_MODEL or "Qwen/Qwen3-Embedding-0.6B"

    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
