from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env", override=False)
load_dotenv(ROOT_DIR.parent.parent / ".env", override=False)


@dataclass(slots=True)
class WorkerSettings:
    port: int = int(os.getenv("AVATAR_WORKER_PORT", "4000"))
    provider: str = os.getenv("AVATAR_PROVIDER", "musetalk")
    muse_talk_endpoint: str = os.getenv("MUSE_TALK_ENDPOINT", "")
    wav2lip_endpoint: str = os.getenv("WAV2LIP_ENDPOINT", "")
    sad_talker_endpoint: str = os.getenv("SAD_TALKER_ENDPOINT", "")
    public_file_base_url: str = os.getenv("PUBLIC_FILE_BASE_URL", "https://files.example.com")


worker_settings = WorkerSettings()
