import os
import uuid
from datetime import datetime
from ipaddress import ip_address
from pathlib import Path
from typing import Dict, List, Optional

import requests
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.api import api_router
from app.core.config import settings
from app.core.database import init_database
from app.core.logger import get_logger, log_structured
from app.core.middleware import LoggingMiddleware
from app.services.agent_chat_service import AgentChatService
from app.services.conversation_service import ConversationService
from app.services.embedding_service import EmbeddingService
from app.services.llm_factory import LLMFactory
from app.services.rag_chat_service import RAGChatService

CURRENT_DIR = Path(__file__).parent


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

logger = get_logger(service="main")
app = FastAPI(title="AssistGen REST API")


@app.on_event("startup")
async def startup_event():
    await init_database()


app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")


class ReasonRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int


class ChatMessage(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int
    conversation_id: int


class AgentChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    user_id: int
    conversation_id: int
    index_id: Optional[str] = None


class RAGChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    index_id: str
    user_id: int


class CreateConversationRequest(BaseModel):
    user_id: int


class UpdateConversationNameRequest(BaseModel):
    name: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def _extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()
    return (request.client.host if request.client else "") or ""


def _is_public_ip(ip_value: str) -> bool:
    try:
        parsed = ip_address(ip_value)
        return not (
            parsed.is_private
            or parsed.is_loopback
            or parsed.is_reserved
            or parsed.is_multicast
            or parsed.is_unspecified
        )
    except ValueError:
        return False


def _resolve_city_from_ip(request: Request) -> str:
    ip_value = _extract_client_ip(request)
    lookup_target = ip_value if _is_public_ip(ip_value) else ""
    lookup_url = f"http://ip-api.com/json/{lookup_target}"

    try:
        response = requests.get(
            lookup_url,
            params={"lang": "zh-CN"},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.warning(f"IP city resolve failed: {str(exc)}")
        return settings.WEATHER_DEFAULT_CITY or "Beijing"

    if data.get("status") != "success":
        return settings.WEATHER_DEFAULT_CITY or "Beijing"

    return (
        data.get("city")
        or data.get("regionName")
        or settings.WEATHER_DEFAULT_CITY
        or "Beijing"
    )


@app.get("/api/weather")
async def weather_endpoint(request: Request, city: Optional[str] = Query(default=None)):
    if not settings.WEATHERAPI_KEY:
        raise HTTPException(status_code=503, detail="WEATHERAPI_KEY 未配置")

    target_city = (city or _resolve_city_from_ip(request) or settings.WEATHER_DEFAULT_CITY or "Beijing").strip()
    url = "https://api.weatherapi.com/v1/current.json"

    try:
        response = requests.get(
            url,
            params={
                "key": settings.WEATHERAPI_KEY,
                "q": target_city,
                "lang": "zh",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        logger.error(f"Weather request failed: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=502, detail="天气服务请求失败")

    location = data.get("location", {})
    current = data.get("current", {})
    condition = current.get("condition", {})

    return {
        "city_name": location.get("name") or target_city,
        "region": location.get("region") or "",
        "country": location.get("country") or "",
        "weather_text": condition.get("text") or "天气信息获取成功",
        "temperature_c": current.get("temp_c"),
        "feelslike_c": current.get("feelslike_c"),
        "humidity": current.get("humidity"),
        "wind_kph": current.get("wind_kph"),
        "icon": condition.get("icon") or "",
        "updated_at": current.get("last_updated") or "",
    }


@app.post("/api/chat")
async def chat_endpoint(request: ChatMessage):
    try:
        logger.info(
            f"Processing chat request for user {request.user_id} "
            f"in conversation {request.conversation_id}"
        )
        chat_service = LLMFactory.create_chat_service()
        hydrated_messages = await ConversationService.build_chat_messages(
            request.conversation_id,
            request.messages,
        )
        return StreamingResponse(
            chat_service.generate_stream(
                messages=hydrated_messages,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                on_complete=ConversationService.save_message,
            ),
            media_type="text/event-stream",
        )
    except Exception as exc:
        logger.error(f"Chat error: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/agent/chat")
async def agent_chat_endpoint(request: AgentChatRequest):
    try:
        logger.info(
            f"Processing agent chat for user {request.user_id} "
            f"in conversation {request.conversation_id}"
        )
        hydrated_messages = await ConversationService.build_chat_messages(
            request.conversation_id,
            request.messages,
        )
        service = AgentChatService()
        return StreamingResponse(
            service.generate_stream(
                messages=hydrated_messages,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                index_id=request.index_id,
                on_complete=ConversationService.save_message,
            ),
            media_type="text/event-stream",
        )
    except Exception as exc:
        logger.error(f"Agent chat error: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/reason")
async def reason_endpoint(request: ReasonRequest):
    try:
        logger.info(f"Processing reasoning request for user {request.user_id}")
        reasoner = LLMFactory.create_reasoner_service()
        log_structured(
            "reason_request",
            {
                "user_id": request.user_id,
                "message_count": len(request.messages),
                "last_message": request.messages[-1]["content"][:100] + "...",
            },
        )
        return StreamingResponse(
            reasoner.generate_stream(request.messages),
            media_type="text/event-stream",
        )
    except Exception as exc:
        logger.error(f"Reasoning error: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/search")
async def search_endpoint(request: ChatMessage):
    try:
        logger.info(
            f"Processing search request for user {request.user_id} "
            f"in conversation {request.conversation_id}"
        )
        search_service = LLMFactory.create_search_service()
        latest_query = next(
            (item["content"] for item in reversed(request.messages) if item["role"] == "user"),
            "",
        )
        return StreamingResponse(
            search_service.generate_stream(
                query=latest_query,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                on_complete=ConversationService.save_message,
            ),
            media_type="text/event-stream",
        )
    except Exception as exc:
        logger.error(f"Search error: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = Form(...),
):
    try:
        logger.info(f"Uploading file for user {user_id}: {file.filename}")

        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}"))
        first_level_dir = UPLOAD_DIR / user_uuid

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        second_level_dir = first_level_dir / timestamp
        second_level_dir.mkdir(parents=True, exist_ok=True)

        original_name, ext = os.path.splitext(file.filename or "upload")
        new_filename = f"{original_name}_{timestamp}{ext}"
        file_path = second_level_dir / new_filename

        content = await file.read()
        with open(file_path, "wb") as file_obj:
            file_obj.write(content)

        file_info = {
            "filename": new_filename,
            "original_name": file.filename,
            "size": len(content),
            "type": file.content_type,
            "path": str(file_path).replace("\\", "/"),
            "user_id": user_id,
            "user_uuid": user_uuid,
            "upload_time": timestamp,
            "directory": str(second_level_dir),
        }

        embedding_service = EmbeddingService()
        embedding_result = await embedding_service.create_embeddings(str(file_path))

        return {
            **file_info,
            "status": embedding_result["status"],
            "index_id": embedding_result["index_id"],
            "chunks": embedding_result["chunks"],
        }
    except Exception as exc:
        logger.error(f"Upload failed for user {user_id}: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat-rag")
async def rag_chat_endpoint(request: RAGChatRequest):
    try:
        logger.info(f"Processing RAG chat request for user {request.user_id}")
        rag_chat_service = RAGChatService()
        return StreamingResponse(
            rag_chat_service.generate_stream(request.messages, request.index_id),
            media_type="text/event-stream",
        )
    except Exception as exc:
        logger.error(f"RAG chat error for user {request.user_id}: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/conversations")
async def create_conversation(request: CreateConversationRequest):
    try:
        conversation_id = await ConversationService.create_conversation(request.user_id)
        return {"conversation_id": conversation_id}
    except Exception as exc:
        logger.error(f"Error creating conversation: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/conversations/user/{user_id}")
async def get_user_conversations(user_id: int):
    try:
        return await ConversationService.get_user_conversations(user_id)
    except Exception as exc:
        logger.error(f"Error getting conversations: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int, user_id: int = Query(...)):
    try:
        return await ConversationService.get_conversation_messages(conversation_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error getting messages: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    try:
        await ConversationService.delete_conversation(conversation_id)
        return {"message": "会话已删除"}
    except Exception as exc:
        logger.error(f"Delete conversation failed: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.put("/api/conversations/{conversation_id}/name")
async def update_conversation_name(
    conversation_id: int,
    request: UpdateConversationNameRequest,
):
    try:
        await ConversationService.update_conversation_name(conversation_id, request.name)
        return {"message": "会话名称已更新"}
    except Exception as exc:
        logger.error(f"Update conversation name failed: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


STATIC_DIR = CURRENT_DIR / "static" / "dist"
ASSETS_DIR = STATIC_DIR / "assets"

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


@app.get("/")
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")
