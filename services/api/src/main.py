from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone

import uvicorn
from fastapi import BackgroundTasks, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .constants import ERROR_CODES, SCRIPT_TEMPLATES, TASK_PROGRESS_STATUS, TASK_STATUSES, TASK_TYPES
from .quality import analyze_image_asset
from .security import apply_rate_limit, fail, redact_value, validate_script_input, validate_upload_meta
from .siliconflow import embed_text, generate_image_with_model, generate_script_with_llm
from .store import (
    create_asset_record,
    create_task,
    get_asset,
    get_discovery_data,
    get_task,
    list_tasks_by_user,
    list_works_by_user,
    seed_demo_works,
    update_task,
    upsert_work_from_task,
)
from .worker_client import create_avatar_worker_job, get_avatar_worker_job


app = FastAPI(title="AI Creator Workshop API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
active_jobs: set[str] = set()


def response_ok(data, message: str = "ok", code: int = 0):
    return {"code": code, "message": message, "data": data}


@app.middleware("http")
async def attach_user(request: Request, call_next):
    request.state.user_id = request.headers.get("x-user-id", "guest-demo")
    seed_demo_works(request.state.user_id)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception):
    if hasattr(exc, "status_code") and hasattr(exc, "detail"):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": ERROR_CODES["INVALID_INPUT"], "message": str(exc.detail), "data": None}
        return JSONResponse(status_code=exc.status_code, content=response_ok(detail.get("data"), detail.get("message", "请求失败"), detail.get("code", ERROR_CODES["INVALID_INPUT"])))
    return JSONResponse(status_code=500, content=response_ok(None, str(exc) or "服务异常", ERROR_CODES["PROVIDER_ERROR"]))


async def run_voice_job(task_id: str, voice: dict | None):
    job_key = f"voice:{task_id}"
    active_jobs.add(job_key)
    try:
        update_task(task_id, {"status": TASK_PROGRESS_STATUS["PROCESSING"], "progress": 45})
        await asyncio.sleep(1.2)
        update_task(
            task_id,
            {
                "status": TASK_PROGRESS_STATUS["SUCCESS"],
                "workflowStatus": TASK_STATUSES["VOICE_READY"],
                "progress": 100,
                "result": {
                    "voiceUrl": "https://www.w3schools.com/html/horse.mp3",
                    "summary": f"已生成 {((voice or {}).get('name') or '默认音色')} 的配音预览。",
                    "duration": 18,
                    "retryable": False,
                    "failureStage": "",
                },
            },
        )
        upsert_work_from_task(get_task(task_id))
    finally:
        active_jobs.discard(job_key)


async def run_export_job(task_id: str, resolution: str):
    job_key = f"export:{task_id}"
    active_jobs.add(job_key)
    try:
        update_task(task_id, {"status": TASK_PROGRESS_STATUS["PROCESSING"], "progress": 60})
        await asyncio.sleep(1.5)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        update_task(
            task_id,
            {
                "status": TASK_PROGRESS_STATUS["SUCCESS"],
                "workflowStatus": TASK_STATUSES["DONE"],
                "progress": 100,
                "result": {
                    "fileUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
                    "previewUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
                    "coverUrl": f"{settings.public_file_base_url}/previews/{task_id}.jpg",
                    "downloadUrl": "https://www.w3schools.com/html/mov_bbb.mp4",
                    "summary": f"已导出 {resolution} 成片，可用于发布与预览。",
                    "expiresAt": expires_at,
                    "retryable": False,
                    "failureStage": "",
                },
            },
        )
        upsert_work_from_task(get_task(task_id))
    finally:
        active_jobs.discard(job_key)


async def run_image_job(task_id: str, prompt: str, aspect_ratio: str):
    job_key = f"image:{task_id}"
    active_jobs.add(job_key)
    try:
        update_task(task_id, {"status": TASK_PROGRESS_STATUS["PROCESSING"], "progress": 35})
        result = await generate_image_with_model(prompt=prompt, aspect_ratio=aspect_ratio)
        update_task(
            task_id,
            {
                "status": TASK_PROGRESS_STATUS["SUCCESS"],
                "workflowStatus": TASK_STATUSES["DONE"],
                "progress": 100,
                "result": {
                    "previewUrl": result["previewUrl"],
                    "downloadUrl": result["previewUrl"],
                    "summary": f"已使用 {result['selectedModel']} 生成测试图片。",
                    "selectedModel": result["selectedModel"],
                    "provider": result["provider"],
                    "retryable": False,
                    "failureStage": "",
                },
            },
        )
        upsert_work_from_task(get_task(task_id))
    finally:
        active_jobs.discard(job_key)


@app.get("/api/health")
async def health():
    return response_ok(
        {
            "service": "api",
            "modelConfigured": bool(settings.deepseek_api_key),
            "maskedKey": redact_value(settings.deepseek_api_key),
            "activeJobs": sorted(active_jobs),
        }
    )


@app.get("/api/discovery")
async def discovery(request: Request):
    return response_ok({**get_discovery_data(), "recentTasks": list_tasks_by_user(request.state.user_id)[:3]})


@app.get("/api/works")
async def works(request: Request):
    return response_ok(list_works_by_user(request.state.user_id))


@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str, request: Request):
    task = get_task(task_id)
    if not task or task.get("userId") != request.state.user_id:
        fail(ERROR_CODES["TASK_NOT_FOUND"], "任务不存在。", 404)

    if (
        task["type"] == TASK_TYPES["AVATAR"]
        and task.get("payload", {}).get("workerJobId")
        and task["status"] != TASK_PROGRESS_STATUS["SUCCESS"]
    ):
        worker_data = await get_avatar_worker_job(task["payload"]["workerJobId"])
        worker_result = worker_data.get("data", {})
        update_task(
            task["id"],
            {
                "status": worker_result.get("status", TASK_PROGRESS_STATUS["PROCESSING"]),
                "workflowStatus": TASK_STATUSES["AVATAR_READY"]
                if worker_result.get("status") == TASK_PROGRESS_STATUS["SUCCESS"]
                else TASK_STATUSES["AVATAR_GENERATING"],
                "progress": worker_result.get("progress", 0),
                "result": worker_result.get("result"),
                "errorMessage": worker_result.get("errorMessage", ""),
            },
        )
        upsert_work_from_task(get_task(task["id"]))

    return response_ok(get_task(task_id))


@app.post("/api/script/generate")
async def generate_script(request: Request):
    apply_rate_limit(request.state.user_id, "script-generate", 10)
    body = await request.json()
    text = body.get("text", "")
    mode = body.get("mode", "generate")
    scene = body.get("scene", "通用")
    template_id = body.get("templateId", "")
    validate_script_input(text or "占位文本")
    template = next((entry for entry in SCRIPT_TEMPLATES if entry["id"] == template_id), None)
    llm_result = await generate_script_with_llm(text=text, mode=mode, scene=(template or {}).get("scene", scene))
    embedding = await embed_text(llm_result["text"])
    return response_ok(
        {
            "text": llm_result["text"],
            "provider": llm_result["provider"],
            "embeddingProvider": embedding["provider"],
            "templateUsed": template,
        }
    )


@app.post("/api/voice/tasks")
async def create_voice_task(request: Request, background_tasks: BackgroundTasks):
    apply_rate_limit(request.state.user_id, "voice-task", 8)
    body = await request.json()
    script_text = body.get("scriptText", "")
    voice = body.get("voice")
    validate_script_input(script_text)
    task = create_task(
        type=TASK_TYPES["VOICE"],
        user_id=request.state.user_id,
        payload={"scriptText": script_text, "voice": voice},
        workflow_status=TASK_STATUSES["VOICE_GENERATING"],
        title=f"{(voice or {}).get('name', '默认音色')} 配音任务",
    )
    background_tasks.add_task(run_voice_job, task["id"], voice)
    return response_ok(task)


@app.post("/api/image/tasks")
async def create_image_task(request: Request, background_tasks: BackgroundTasks):
    apply_rate_limit(request.state.user_id, "image-task", 8)
    body = await request.json()
    prompt = body.get("prompt", "")
    aspect_ratio = body.get("aspectRatio", "1:1")
    validate_script_input(prompt)
    task = create_task(
        type=TASK_TYPES["IMAGE"],
        user_id=request.state.user_id,
        payload={"prompt": prompt, "aspectRatio": aspect_ratio},
        workflow_status=TASK_STATUSES["EXPORTING"],
        title="AI 图片生成任务",
    )
    background_tasks.add_task(run_image_job, task["id"], prompt, aspect_ratio)
    return response_ok(task)


@app.post("/api/avatar/tasks")
async def create_avatar_task(request: Request):
    apply_rate_limit(request.state.user_id, "avatar-task", 6)
    body = await request.json()
    script_text = body.get("scriptText", "")
    voice_task_id = body.get("voiceTaskId", "")
    avatar = body.get("avatar")
    image_asset_id = body.get("imageAssetId", "")
    image_asset = body.get("imageAsset")
    aspect_ratio = body.get("aspectRatio", "9:16")
    resolution = body.get("resolution", "1080P")
    validate_script_input(script_text)
    stored_asset = get_asset(image_asset_id, request.state.user_id) if image_asset_id else None
    quality = analyze_image_asset(stored_asset or image_asset or {})
    if not quality["accepted"]:
        fail(ERROR_CODES["QUALITY_REJECTED"], quality["failureReason"], 400, quality)

    task = create_task(
        type=TASK_TYPES["AVATAR"],
        user_id=request.state.user_id,
        payload={
            "scriptText": script_text,
            "voiceTaskId": voice_task_id,
            "avatar": avatar,
            "imageAssetId": image_asset_id,
            "imageAsset": stored_asset or image_asset,
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
        },
        workflow_status=TASK_STATUSES["AVATAR_GENERATING"],
        title=f"{(avatar or {}).get('name', '数字人')} 视频任务",
    )

    worker_job = await create_avatar_worker_job(
        {
            "taskId": task["id"],
            "userId": request.state.user_id,
            "avatar": avatar,
            "imageAsset": {**(stored_asset or image_asset or {}), "quality": quality},
            "scriptText": script_text,
            "voiceTaskId": voice_task_id,
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
        }
    )
    update_task(
        task["id"],
        {
            "payload": {**task["payload"], "workerJobId": worker_job["data"]["jobId"]},
            "progress": 15,
            "result": {"qualityScore": quality["qualityScore"]},
        },
    )
    return response_ok(get_task(task["id"]))


@app.post("/api/export/tasks")
async def create_export_task(request: Request, background_tasks: BackgroundTasks):
    apply_rate_limit(request.state.user_id, "export-task", 10)
    body = await request.json()
    avatar_task_id = body.get("avatarTaskId", "")
    bgm = body.get("bgm")
    cover_title = body.get("coverTitle", "")
    resolution = body.get("resolution", "1080P")
    source_task = get_task(avatar_task_id)
    if not source_task:
        fail(ERROR_CODES["TASK_NOT_FOUND"], "请先生成数字人视频。", 404)
    task = create_task(
        type=TASK_TYPES["EXPORT"],
        user_id=request.state.user_id,
        payload={"avatarTaskId": avatar_task_id, "bgm": bgm, "coverTitle": cover_title, "resolution": resolution},
        workflow_status=TASK_STATUSES["EXPORTING"],
        title=f"{cover_title or '数字人口播成片'} 导出任务",
    )
    background_tasks.add_task(run_export_job, task["id"], resolution)
    return response_ok(task)


@app.post("/api/uploads/sign")
async def sign_upload(request: Request):
    apply_rate_limit(request.state.user_id, "uploads-sign", 20)
    meta = await request.json()
    validate_upload_meta(meta)
    quality = analyze_image_asset(meta)
    asset_record = create_asset_record(
        user_id=request.state.user_id,
        object_key=f"user/{request.state.user_id}/avatar-assets/{int(datetime.now().timestamp() * 1000)}_{meta.get('fileName', 'asset')}",
        upload_id=f"upload_{int(datetime.now().timestamp() * 1000)}",
        file_name=meta.get("fileName", ""),
        mime_type=meta.get("mimeType", ""),
        size=int(meta.get("size", 0)),
        width=int(meta.get("width", 0)),
        height=int(meta.get("height", 0)),
        quality=quality,
    )
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    return response_ok(
        {
            "uploadId": asset_record["uploadId"],
            "assetId": asset_record["id"],
            "objectKey": asset_record["objectKey"],
            "uploadUrl": f"{settings.public_file_base_url}/signed-upload",
            "expiresAt": expires_at,
            "quality": quality,
        }
    )


def main() -> None:
    reload_enabled = "--reload" in sys.argv
    print(f"[api] listening on port {settings.port}, LAN/Public base should be {settings.avatar_worker_url.replace(':4000', ':3000') if settings.avatar_worker_url.endswith(':4000') else f'http://172.22.121.135:{settings.port}'}")
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port, reload=reload_enabled)


if __name__ == "__main__":
    main()
