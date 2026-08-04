from __future__ import annotations

import hashlib

import httpx

from .config import settings


def build_fallback_text(mode: str, text: str, scene: str) -> str:
    source = text or "请介绍本次内容的核心价值与适用场景。"
    if mode == "rewrite":
        return f"大家好，今天带来一段更适合数字人口播的视频文案：{source[:80]}。我会用更清晰的结构介绍亮点、场景和行动建议，让观众更容易理解并产生兴趣。"
    if mode == "marketing":
        return f"如果你正在寻找一套高效的内容制作方案，这段关于{scene or '产品亮点'}的口播脚本可以帮助你快速打动用户：先讲痛点，再讲优势，最后给出明确行动引导。"
    if mode == "knowledge":
        return f"今天我们用一分钟讲清楚{scene or '一个实用主题'}：先说明背景，再拆解关键点，最后用一个简单结论帮助观众快速记住重点。"
    return f"大家好，欢迎来到 AI创作工坊。今天我们围绕{scene or '品牌介绍'}展开，用简洁清晰的方式介绍核心亮点、适用人群与下一步建议。"


async def request_json(url: str, body: dict, api_key: str) -> dict:
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            url,
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
    response.raise_for_status()
    return response.json()


async def generate_script_with_llm(*, text: str, mode: str, scene: str) -> dict:
    if not settings.deepseek_api_key:
        return {"text": build_fallback_text(mode, text, scene), "provider": "fallback"}

    payload = {
        "model": settings.deepseek_model,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": "你是一名数字人口播脚本助手。请输出适合短视频或数字人口播的中文文案，结构清晰，语言自然，避免夸大承诺，默认控制在 120 到 220 字。",
            },
            {
                "role": "user",
                "content": f"模式：{mode}\n场景：{scene or '通用'}\n原始文案：{text or '无'}\n请直接输出最终脚本。",
            },
        ],
    }
    data = await request_json(f"{settings.deepseek_base_url}/chat/completions", payload, settings.deepseek_api_key)
    return {
        "text": ((data.get("choices") or [{}])[0].get("message") or {}).get("content", "").strip() or build_fallback_text(mode, text, scene),
        "provider": "siliconflow",
    }


async def embed_text(text: str) -> dict:
    if not settings.embedding_api_key:
        return {"embedding": [0.12, 0.34, 0.56], "provider": "fallback"}
    payload = {
        "model": settings.embedding_model,
        "input": text,
    }
    data = await request_json(f"{settings.embedding_base_url}/embeddings", payload, settings.embedding_api_key)
    embedding = ((data.get("data") or [{}])[0]).get("embedding", [])
    return {"embedding": embedding, "provider": "siliconflow"}


def _seed_hash(text: str) -> str:
    return hashlib.md5((text or "kolors").encode("utf-8")).hexdigest()[:12]


async def generate_image_with_model(*, prompt: str, aspect_ratio: str = "1:1") -> dict:
    selected_model = "Kwai-Kolors/Kolors"
    if not settings.deepseek_api_key:
        size = "768/1344" if aspect_ratio == "9:16" else "1024/1024"
        return {
            "selectedModel": selected_model,
            "provider": "fallback",
            "previewUrl": f"https://picsum.photos/seed/{_seed_hash(prompt)}/{size}",
            "prompt": prompt,
            "aspectRatio": aspect_ratio,
        }

    payload = {
        "model": selected_model,
        "prompt": prompt,
        "image_size": "768x1344" if aspect_ratio == "9:16" else "1024x1024",
    }
    data = await request_json(f"{settings.deepseek_base_url}/images/generations", payload, settings.deepseek_api_key)
    preview_url = ((data.get("data") or [{}])[0]).get("url") or f"https://picsum.photos/seed/{_seed_hash(prompt)}/1024/1024"
    return {
        "selectedModel": selected_model,
        "provider": "siliconflow",
        "previewUrl": preview_url,
        "prompt": prompt,
        "aspectRatio": aspect_ratio,
    }
