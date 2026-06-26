import json
from pathlib import Path
from typing import Dict

from app.core.config import ROOT_DIR, settings


SETTINGS_FILE = ROOT_DIR / "resources" / "assistant_settings.json"


class SettingsService:
    @staticmethod
    def _defaults() -> Dict:
        return {
            "model": settings.ASSISTANT_MODEL_PLACEHOLDER,
            "temperature": settings.ASSISTANT_TEMPERATURE,
            "enable_search": settings.ASSISTANT_ENABLE_WEB_SEARCH,
            "response_style": settings.ASSISTANT_RESPONSE_STYLE,
        }

    @staticmethod
    def _load_all() -> Dict:
        if not SETTINGS_FILE.exists():
            return {}
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def get_settings(user_id: int) -> Dict:
        all_settings = SettingsService._load_all()
        return {
            **SettingsService._defaults(),
            **all_settings.get(str(user_id), {}),
        }

    @staticmethod
    def update_settings(user_id: int, payload: Dict) -> Dict:
        current = SettingsService.get_settings(user_id)
        enable_search = payload.get("enable_search")
        next_settings = {
            **current,
            "model": payload.get("model") or settings.ASSISTANT_MODEL_PLACEHOLDER,
            "temperature": float(payload.get("temperature", current["temperature"])),
            "enable_search": current["enable_search"] if enable_search is None else bool(enable_search),
            "response_style": payload.get("response_style") or settings.ASSISTANT_RESPONSE_STYLE,
        }
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        all_settings = SettingsService._load_all()
        all_settings[str(user_id)] = next_settings
        SETTINGS_FILE.write_text(
            json.dumps(all_settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return next_settings
