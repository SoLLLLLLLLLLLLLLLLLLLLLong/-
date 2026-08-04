TASK_TYPES = {
    "SCRIPT": "script",
    "VOICE": "voice",
    "AVATAR": "avatar",
    "EXPORT": "export",
    "IMAGE": "image",
}

TASK_STATUSES = {
    "DRAFT": "draft",
    "SCRIPT_READY": "script_ready",
    "VOICE_GENERATING": "voice_generating",
    "VOICE_READY": "voice_ready",
    "AVATAR_GENERATING": "avatar_generating",
    "AVATAR_READY": "avatar_ready",
    "EXPORTING": "exporting",
    "DONE": "done",
    "FAILED": "failed",
}

TASK_PROGRESS_STATUS = {
    "QUEUED": "queued",
    "PROCESSING": "processing",
    "SUCCESS": "success",
    "FAILED": "failed",
}

ERROR_CODES = {
    "INVALID_INPUT": "INVALID_INPUT",
    "CONTENT_BLOCKED": "CONTENT_BLOCKED",
    "RATE_LIMITED": "RATE_LIMITED",
    "TASK_NOT_FOUND": "TASK_NOT_FOUND",
    "UPLOAD_REJECTED": "UPLOAD_REJECTED",
    "PROVIDER_ERROR": "PROVIDER_ERROR",
    "QUALITY_REJECTED": "QUALITY_REJECTED",
}

SCRIPT_TEMPLATES = [
    {
        "id": "brand_intro",
        "title": "品牌介绍",
        "prompt": "生成一段适合数字人口播的品牌介绍文案，突出卖点、可信度和行动引导。",
        "scene": "营销口播",
    },
    {
        "id": "product_pitch",
        "title": "产品讲解",
        "prompt": "生成一段条理清晰的产品功能讲解文案，突出核心价值、适用场景和差异化。",
        "scene": "产品宣传",
    },
    {
        "id": "knowledge_share",
        "title": "知识分享",
        "prompt": "生成一段适合短视频知识分享的脚本，要求节奏快、观点清晰、结尾有总结。",
        "scene": "知识讲解",
    },
]

DEFAULT_VOICES = [
    "CN 央视腔男声",
    "CN 带货直播女声",
    "CN 台湾腔女声",
]

DEFAULT_AVATARS = [
    "商业知识男主播",
    "品牌分享女主播",
    "科技讲解男主播",
]
