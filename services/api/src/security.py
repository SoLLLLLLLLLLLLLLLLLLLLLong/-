from __future__ import annotations

import time

from fastapi import HTTPException

from .constants import ERROR_CODES


_rate_counter: dict[str, int] = {}
_blocked_words = ["暴恐", "诈骗", "洗钱", "政治煽动"]
_allowed_mime_types = {"image/png", "image/jpeg", "image/webp"}


def _window_key(user_id: str, action: str) -> str:
    return f"{user_id}:{action}:{int(time.time() // 60)}"


def fail(code: str, message: str, status_code: int = 400, details=None) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message, "data": details})


def apply_rate_limit(user_id: str, action: str, limit: int = 12) -> None:
    key = _window_key(user_id, action)
    next_value = _rate_counter.get(key, 0) + 1
    _rate_counter[key] = next_value
    if next_value > limit:
        fail(ERROR_CODES["RATE_LIMITED"], "请求过于频繁，请稍后重试。", 429)


def validate_script_input(text: str) -> None:
    if not text or not text.strip():
        fail(ERROR_CODES["INVALID_INPUT"], "文案内容不能为空。")
    if len(text) > 1000:
        fail(ERROR_CODES["INVALID_INPUT"], "文案内容不能超过 1000 字。")
    matched = next((word for word in _blocked_words if word in text), None)
    if matched:
        fail(ERROR_CODES["CONTENT_BLOCKED"], f"文案包含受限词：{matched}")


def validate_upload_meta(meta: dict | None = None) -> None:
    meta = meta or {}
    if meta.get("mimeType") not in _allowed_mime_types:
        fail(ERROR_CODES["UPLOAD_REJECTED"], "仅支持 PNG、JPEG、WEBP 图片上传。")
    if int(meta.get("size") or 0) > 5 * 1024 * 1024:
        fail(ERROR_CODES["UPLOAD_REJECTED"], "上传文件不能超过 5MB。")
    if int(meta.get("width") or 0) <= 0 or int(meta.get("height") or 0) <= 0:
        fail(ERROR_CODES["UPLOAD_REJECTED"], "请上传可读取宽高信息的图片。")


def redact_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"
