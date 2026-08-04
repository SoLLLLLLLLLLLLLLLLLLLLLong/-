from __future__ import annotations

import httpx

from .config import settings
from .security import fail
from .constants import ERROR_CODES


async def create_avatar_worker_job(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{settings.avatar_worker_url}/worker/avatar/jobs", json=payload)
    if response.status_code >= 400:
        fail(ERROR_CODES["PROVIDER_ERROR"], f"数字人服务不可用: {response.status_code} {response.text}")
    return response.json()


async def get_avatar_worker_job(job_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(f"{settings.avatar_worker_url}/worker/avatar/jobs/{job_id}")
    if response.status_code >= 400:
        fail(ERROR_CODES["PROVIDER_ERROR"], f"数字人任务读取失败: {response.status_code} {response.text}")
    return response.json()
