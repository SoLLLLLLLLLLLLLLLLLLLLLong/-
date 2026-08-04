from __future__ import annotations

import asyncio
import random
import time

from .config import worker_settings


TASK_PROGRESS_STATUS = {
    "QUEUED": "queued",
    "PROCESSING": "processing",
    "SUCCESS": "success",
}

jobs: dict[str, dict] = {}


def create_id(prefix: str) -> str:
    suffix = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
    return f"{prefix}_{int(time.time() * 1000)}_{suffix}"


async def simulate_job(job_id: str, payload: dict) -> None:
    jobs[job_id] = {
        "jobId": job_id,
        "provider": worker_settings.provider,
        "status": TASK_PROGRESS_STATUS["QUEUED"],
        "progress": 10,
        "payload": payload,
        "result": None,
        "errorMessage": "",
    }
    await asyncio.sleep(1.2)
    if job_id not in jobs:
        return
    jobs[job_id]["status"] = TASK_PROGRESS_STATUS["PROCESSING"]
    jobs[job_id]["progress"] = 58
    await asyncio.sleep(1.6)
    if job_id not in jobs:
        return
    jobs[job_id]["status"] = TASK_PROGRESS_STATUS["SUCCESS"]
    jobs[job_id]["progress"] = 100
    jobs[job_id]["result"] = {
        "previewUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
        "coverUrl": f"{worker_settings.public_file_base_url}/avatar/{job_id}.jpg",
        "downloadUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
        "sourceImageUrl": ((payload.get("imageAsset") or {}).get("previewUrl")) or "",
        "qualityScore": ((payload.get("imageAsset") or {}).get("quality") or {}).get("qualityScore", 82),
        "failureStage": "",
        "retryable": False,
        "summary": f"{((payload.get('avatar') or {}).get('name') or '数字人')} 已完成口型驱动预览。",
        "provider": worker_settings.provider,
    }


async def create_avatar_job(payload: dict) -> dict:
    job_id = create_id("avatar_job")
    asyncio.create_task(simulate_job(job_id, payload))
    await asyncio.sleep(0)
    return jobs[job_id]


def get_avatar_job(job_id: str) -> dict | None:
    return jobs.get(job_id)


def get_provider_manifest() -> dict:
    return {
        "activeProvider": worker_settings.provider,
        "supportedProviders": [
            {
                "id": "musetalk",
                "name": "MuseTalk",
                "repo": "https://github.com/TMElyralab/MuseTalk",
                "usage": "主推方案，适合口型驱动与较现代的数字人口播封装。",
            },
            {
                "id": "wav2lip",
                "name": "Wav2Lip",
                "repo": "https://github.com/Rudrabha/Wav2Lip",
                "usage": "备选方案，适合作为更稳的唇形同步链路。",
            },
            {
                "id": "sadtalker",
                "name": "SadTalker",
                "repo": "https://github.com/OpenTalker/SadTalker",
                "usage": "备选方案，适合静态头像驱动型数字人场景。",
            },
        ],
    }
