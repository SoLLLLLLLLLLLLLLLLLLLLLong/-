import { ERROR_CODES } from '@ai-creator-workshop/shared'

const rateCounter = new Map()
const blockedWords = ['暴恐', '诈骗', '洗钱', '政治煽动']
const allowedMimeTypes = ['image/png', 'image/jpeg', 'image/webp']

function windowKey(userId, action) {
  return `${userId}:${action}:${Math.floor(Date.now() / 60000)}`
}

export function applyRateLimit(userId, action, limit = 12) {
  const key = windowKey(userId, action)
  const nextValue = (rateCounter.get(key) || 0) + 1
  rateCounter.set(key, nextValue)

  if (nextValue > limit) {
    const error = new Error('请求过于频繁，请稍后重试。')
    error.code = ERROR_CODES.RATE_LIMITED
    throw error
  }
}

export function validateScriptInput(text) {
  if (!text || !text.trim()) {
    const error = new Error('文案内容不能为空。')
    error.code = ERROR_CODES.INVALID_INPUT
    throw error
  }

  if (text.length > 1000) {
    const error = new Error('文案内容不能超过 1000 字。')
    error.code = ERROR_CODES.INVALID_INPUT
    throw error
  }

  const matched = blockedWords.find((word) => text.includes(word))
  if (matched) {
    const error = new Error(`文案包含受限词：${matched}`)
    error.code = ERROR_CODES.CONTENT_BLOCKED
    throw error
  }
}

export function validateUploadMeta(meta = {}) {
  if (!allowedMimeTypes.includes(meta.mimeType)) {
    const error = new Error('仅支持 PNG、JPEG、WEBP 图片上传。')
    error.code = ERROR_CODES.UPLOAD_REJECTED
    throw error
  }

  if (Number(meta.size || 0) > 5 * 1024 * 1024) {
    const error = new Error('上传文件不能超过 5MB。')
    error.code = ERROR_CODES.UPLOAD_REJECTED
    throw error
  }

  if (Number(meta.width || 0) <= 0 || Number(meta.height || 0) <= 0) {
    const error = new Error('请上传可读取宽高信息的图片。')
    error.code = ERROR_CODES.UPLOAD_REJECTED
    throw error
  }
}

export function redactValue(value) {
  if (!value) {
    return ''
  }

  if (value.length <= 8) {
    return '***'
  }

  return `${value.slice(0, 4)}***${value.slice(-4)}`
}
