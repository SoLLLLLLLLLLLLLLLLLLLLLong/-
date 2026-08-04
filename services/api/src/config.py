from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=False)
load_dotenv(ROOT_DIR.parent.parent / ".env", override=False)


@dataclass(slots=True)
class Settings:
    port: int = int(os.getenv("API_PORT", "3000"))
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.siliconflow.cn/v1")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    avatar_worker_url: str = os.getenv("AVATAR_WORKER_URL", "http://127.0.0.1:4000")
    public_file_base_url: str = os.getenv("PUBLIC_FILE_BASE_URL", "https://files.example.com")


settings = Settings()
