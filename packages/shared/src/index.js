export const TASK_TYPES = {
  SCRIPT: 'script',
  VOICE: 'voice',
  AVATAR: 'avatar',
  EXPORT: 'export',
  IMAGE: 'image',
}

export const TASK_STATUSES = {
  DRAFT: 'draft',
  SCRIPT_READY: 'script_ready',
  VOICE_GENERATING: 'voice_generating',
  VOICE_READY: 'voice_ready',
  AVATAR_GENERATING: 'avatar_generating',
  AVATAR_READY: 'avatar_ready',
  EXPORTING: 'exporting',
  DONE: 'done',
  FAILED: 'failed',
}

export const TASK_PROGRESS_STATUS = {
  QUEUED: 'queued',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  FAILED: 'failed',
}

export const ERROR_CODES = {
  INVALID_INPUT: 'INVALID_INPUT',
  CONTENT_BLOCKED: 'CONTENT_BLOCKED',
  RATE_LIMITED: 'RATE_LIMITED',
  TASK_NOT_FOUND: 'TASK_NOT_FOUND',
  UPLOAD_REJECTED: 'UPLOAD_REJECTED',
  PROVIDER_ERROR: 'PROVIDER_ERROR',
  QUALITY_REJECTED: 'QUALITY_REJECTED',
}

export const CREATION_STEPS = [
  { key: 'script', name: '文案脚本', desc: '输入或优化口播内容' },
  { key: 'voice', name: '声音合成', desc: '选择音色并生成配音' },
  { key: 'avatar', name: '视频预览', desc: '生成数字人口播预览' },
  { key: 'export', name: '导出保存', desc: '包装成片并保存' },
]

export const SCRIPT_TEMPLATES = [
  {
    id: 'brand_intro',
    title: '品牌介绍',
    prompt: '生成一段适合数字人口播的品牌介绍文案，突出卖点、可信度和行动引导。',
    scene: '营销口播',
  },
  {
    id: 'product_pitch',
    title: '产品讲解',
    prompt: '生成一段条理清晰的产品功能讲解文案，突出核心价值、适用场景和差异化。',
    scene: '产品宣传',
  },
  {
    id: 'knowledge_share',
    title: '知识分享',
    prompt: '生成一段适合短视频知识分享的脚本，要求节奏快、观点清晰、结尾有总结。',
    scene: '知识讲解',
  },
]

export const DEFAULT_VOICES = [
  '央视腔男声',
  '直播女声',
  '温柔女声',
]

export const DEFAULT_AVATARS = [
  '商务男主播',
  '品牌女主播',
  '科技讲解员',
]
