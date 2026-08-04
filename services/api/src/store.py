from __future__ import annotations

import random
import time
from datetime import datetime, timezone

from .constants import (
    DEFAULT_AVATARS,
    DEFAULT_VOICES,
    ERROR_CODES,
    SCRIPT_TEMPLATES,
    TASK_PROGRESS_STATUS,
    TASK_STATUSES,
    TASK_TYPES,
)
from .database import find_collection_item, list_collection, upsert_collection_item, write_collection


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_id(prefix: str) -> str:
    suffix = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
    return f"{prefix}_{int(time.time() * 1000)}_{suffix}"


def ensure_user(user_id: str) -> None:
    upsert_collection_item("users", {"id": user_id, "updatedAt": now()})


def create_task(*, type: str, user_id: str, payload: dict, workflow_status: str, title: str) -> dict:
    ensure_user(user_id)
    task = {
        "id": create_id("task"),
        "type": type,
        "status": TASK_PROGRESS_STATUS["QUEUED"],
        "workflowStatus": workflow_status,
        "progress": 5,
        "payload": payload,
        "result": None,
        "errorCode": "",
        "errorMessage": "",
        "title": title,
        "userId": user_id,
        "retryable": False,
        "failureStage": "",
        "createdAt": now(),
        "updatedAt": now(),
    }
    upsert_collection_item("tasks", task)
    return task


def get_task(task_id: str) -> dict | None:
    return find_collection_item("tasks", lambda task: task.get("id") == task_id)


def update_task(task_id: str, updates: dict) -> dict | None:
    task = get_task(task_id)
    if not task:
        return None
    next_task = {**task, **updates, "updatedAt": now()}
    upsert_collection_item("tasks", next_task)
    return next_task


def list_tasks_by_user(user_id: str) -> list[dict]:
    return sorted(
        [task for task in list_collection("tasks") if task.get("userId") == user_id],
        key=lambda item: item.get("updatedAt", ""),
        reverse=True,
    )


def create_asset_record(*, user_id: str, object_key: str, upload_id: str, file_name: str, mime_type: str, size: int, width: int, height: int, quality: dict) -> dict:
    asset = {
        "id": create_id("asset"),
        "userId": user_id,
        "uploadId": upload_id,
        "objectKey": object_key,
        "fileName": file_name,
        "mimeType": mime_type,
        "size": size,
        "width": width,
        "height": height,
        "quality": quality,
        "createdAt": now(),
        "updatedAt": now(),
    }
    upsert_collection_item("assets", asset)
    return asset


def get_asset(asset_id: str, user_id: str) -> dict | None:
    return find_collection_item("assets", lambda asset: asset.get("id") == asset_id and asset.get("userId") == user_id)


def upsert_work_from_task(task: dict | None) -> dict | None:
    if not task:
        return None
    work_id = task["id"].replace("task_", "work_", 1)
    payload_asset_id = (
        task.get("payload", {}).get("imageAsset", {}).get("assetId")
        or task.get("payload", {}).get("imageAssetId")
        or ""
    )
    asset = get_asset(payload_asset_id, task["userId"]) if payload_asset_id else None
    result = task.get("result") or {}
    work = {
        "id": work_id,
        "taskId": task["id"],
        "type": task["type"],
        "title": task["title"],
        "status": task["status"],
        "workflowStatus": task["workflowStatus"],
        "previewUrl": result.get("previewUrl") or result.get("fileUrl") or "",
        "coverUrl": result.get("coverUrl") or "",
        "downloadUrl": result.get("downloadUrl") or result.get("fileUrl") or "",
        "sourceImageUrl": f"/assets/{asset['objectKey']}" if asset else "",
        "qualityScore": result.get("qualityScore") or (asset or {}).get("quality", {}).get("qualityScore", 0),
        "failureStage": task.get("failureStage") or result.get("failureStage") or "",
        "retryable": task.get("retryable", False),
        "result": result,
        "errorMessage": task.get("errorMessage", ""),
        "userId": task["userId"],
        "createdAt": task["createdAt"],
        "updatedAt": task["updatedAt"],
    }
    upsert_collection_item("works", work)
    return work


def list_works_by_user(user_id: str) -> list[dict]:
    return sorted(
        [work for work in list_collection("works") if work.get("userId") == user_id],
        key=lambda item: item.get("updatedAt", ""),
        reverse=True,
    )


def get_discovery_data() -> dict:
    return {
        "templates": SCRIPT_TEMPLATES,
        "commonVoices": DEFAULT_VOICES,
        "hotAvatars": DEFAULT_AVATARS,
    }


def seed_demo_works(user_id: str = "guest-demo") -> None:
    if list_works_by_user(user_id):
        return
    entries = [
        {
            "type": TASK_TYPES["AVATAR"],
            "title": "品牌介绍口播视频",
            "status": TASK_PROGRESS_STATUS["SUCCESS"],
            "workflowStatus": TASK_STATUSES["DONE"],
            "result": {
                "previewUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
                "coverUrl": "https://files.example.com/previews/brand-intro.jpg",
                "downloadUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
                "summary": "已完成 1080P 预览视频，可用于简历演示。",
                "qualityScore": 91,
            },
        },
        {
            "type": TASK_TYPES["VOICE"],
            "title": "知识分享配音",
            "status": TASK_PROGRESS_STATUS["FAILED"],
            "workflowStatus": TASK_STATUSES["FAILED"],
            "result": None,
            "errorMessage": "音色服务暂时不可用，请稍后重试。",
            "failureStage": "voice_generation",
            "retryable": True,
        },
    ]
    for entry in entries:
        task = create_task(
            type=entry["type"],
            user_id=user_id,
            payload={},
            workflow_status=entry["workflowStatus"],
            title=entry["title"],
        )
        update_task(
            task["id"],
            {
                "status": entry["status"],
                "workflowStatus": entry["workflowStatus"],
                "progress": 100 if entry["status"] == TASK_PROGRESS_STATUS["SUCCESS"] else 0,
                "result": entry.get("result"),
                "errorMessage": entry.get("errorMessage", ""),
                "failureStage": entry.get("failureStage", ""),
                "retryable": entry.get("retryable", False),
                "errorCode": ERROR_CODES["PROVIDER_ERROR"] if entry.get("errorMessage") else "",
            },
        )
        upsert_work_from_task(get_task(task["id"]))


def reset_runtime_data() -> None:
    write_collection("tasks", [])
    write_collection("works", [])
    write_collection("assets", [])
    write_collection("users", [])
