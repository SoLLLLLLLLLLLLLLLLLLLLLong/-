from __future__ import annotations


MIN_WIDTH = 480
MIN_HEIGHT = 640
IDEAL_RATIO = 0.75


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def analyze_image_asset(image_asset: dict | None = None) -> dict:
    image_asset = image_asset or {}
    width = int(image_asset.get("width") or 0)
    height = int(image_asset.get("height") or 0)
    size = int(image_asset.get("size") or 0)
    mime_type = image_asset.get("mimeType") or ""

    checks = {
        "hasSingleFace": int(image_asset.get("faceCountHint", 1) or 1) == 1,
        "frontFacing": (image_asset.get("poseHint") or "front") == "front",
        "notOccluded": (image_asset.get("occlusionHint") or "clear") == "clear",
        "minResolution": width >= MIN_WIDTH and height >= MIN_HEIGHT,
        "mimeAllowed": mime_type in {"image/png", "image/jpeg", "image/webp"},
        "sizeAllowed": 0 < size <= 5 * 1024 * 1024,
    }

    ratio = width / height if height else 0
    ratio_score = 1 - min(abs(ratio - IDEAL_RATIO), 0.5) / 0.5
    resolution_score = clamp(((width * height) / (960 * 1280)) * 100, 0, 100)
    base_score = round(
        (
            ratio_score * 0.25
            + resolution_score / 100 * 0.35
            + (0.2 if checks["notOccluded"] else 0)
            + (0.2 if checks["hasSingleFace"] else 0)
        )
        * 100
    )

    failure_stage = ""
    failure_reason = ""

    if not checks["mimeAllowed"] or not checks["sizeAllowed"]:
        failure_stage = "upload"
        failure_reason = "素材图片格式或大小不符合要求。"
    elif not checks["hasSingleFace"]:
        failure_stage = "face_detection"
        failure_reason = "检测到多人脸，请上传单人正脸照片。"
    elif not checks["frontFacing"]:
        failure_stage = "face_pose"
        failure_reason = "照片不是正脸，建议上传正面清晰照片。"
    elif not checks["notOccluded"]:
        failure_stage = "occlusion"
        failure_reason = "人脸存在遮挡，请更换无遮挡素材。"
    elif not checks["minResolution"]:
        failure_stage = "quality"
        failure_reason = "照片清晰度不足，请上传更高清图片。"

    return {
        "qualityScore": clamp(base_score, 0, 100),
        "checks": checks,
        "failureStage": failure_stage,
        "failureReason": failure_reason,
        "retryable": bool(failure_stage),
        "accepted": not failure_stage,
    }
