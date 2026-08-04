from __future__ import annotations

import sys

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .config import worker_settings
from .provider import create_avatar_job, get_avatar_job, get_provider_manifest


app = FastAPI(title="AI Creator Workshop Avatar Worker", version="0.2.0")


def response_ok(data, message: str = "ok", code: int = 0):
    return {"code": code, "message": message, "data": data}


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": "PROVIDER_ERROR", "message": str(exc.detail), "data": None}
        return JSONResponse(status_code=exc.status_code, content=response_ok(detail.get("data"), detail.get("message", "worker 请求失败"), detail.get("code", "PROVIDER_ERROR")))
    return JSONResponse(status_code=500, content=response_ok(None, str(exc) or "worker 请求失败", "PROVIDER_ERROR"))


@app.get("/worker/health")
async def health():
    return response_ok(get_provider_manifest())


@app.post("/worker/avatar/assets")
async def avatar_assets(request: Request):
    body = await request.json()
    return response_ok(
        {
            "assetId": f"asset_{body.get('uploadId') or 'temp'}",
            "objectKey": body.get("objectKey", ""),
            "uploadId": body.get("uploadId", ""),
            "verified": True,
        }
    )


@app.post("/worker/avatar/jobs")
async def avatar_jobs(request: Request):
    job = await create_avatar_job(await request.json())
    return response_ok(job)


@app.get("/worker/avatar/jobs/{job_id}")
async def avatar_job_detail(job_id: str):
    job = get_avatar_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "TASK_NOT_FOUND", "message": "数字人任务不存在。", "data": None})
    return response_ok(job)


def main() -> None:
    reload_enabled = "--reload" in sys.argv
    print(f"[avatar-worker] listening on http://0.0.0.0:{worker_settings.port}")
    uvicorn.run("src.main:app", host="0.0.0.0", port=worker_settings.port, reload=reload_enabled)


if __name__ == "__main__":
    main()
