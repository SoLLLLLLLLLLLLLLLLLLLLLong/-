const MIN_WIDTH = 480
const MIN_HEIGHT = 640
const IDEAL_RATIO = 0.75

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

export function analyzeImageAsset(imageAsset = {}) {
  const width = Number(imageAsset.width || 0)
  const height = Number(imageAsset.height || 0)
  const size = Number(imageAsset.size || 0)
  const mimeType = imageAsset.mimeType || ''

  const checks = {
    hasSingleFace: imageAsset.faceCountHint ? Number(imageAsset.faceCountHint) === 1 : true,
    frontFacing: imageAsset.poseHint ? imageAsset.poseHint === 'front' : true,
    notOccluded: imageAsset.occlusionHint ? imageAsset.occlusionHint === 'clear' : true,
    minResolution: width >= MIN_WIDTH && height >= MIN_HEIGHT,
    mimeAllowed: ['image/png', 'image/jpeg', 'image/webp'].includes(mimeType),
    sizeAllowed: size > 0 && size <= 5 * 1024 * 1024,
  }

  const ratio = height ? width / height : 0
  const ratioScore = 1 - Math.min(Math.abs(ratio - IDEAL_RATIO), 0.5) / 0.5
  const resolutionScore = clamp(((width * height) / (960 * 1280)) * 100, 0, 100)
  const baseScore = Math.round((ratioScore * 0.25 + resolutionScore / 100 * 0.35 + (checks.notOccluded ? 0.2 : 0) + (checks.hasSingleFace ? 0.2 : 0)) * 100)

  let failureStage = ''
  let failureReason = ''

  if (!checks.mimeAllowed || !checks.sizeAllowed) {
    failureStage = 'upload'
    failureReason = '素材图格式或大小不符合要求。'
  } else if (!checks.hasSingleFace) {
    failureStage = 'face_detection'
    failureReason = '检测到多人脸，请上传单人正脸照片。'
  } else if (!checks.frontFacing) {
    failureStage = 'face_pose'
    failureReason = '照片不是正脸，建议上传正面清晰照片。'
  } else if (!checks.notOccluded) {
    failureStage = 'occlusion'
    failureReason = '人脸存在遮挡，请更换无遮挡素材。'
  } else if (!checks.minResolution) {
    failureStage = 'quality'
    failureReason = '照片清晰度不足，请上传更高清图片。'
  }

  return {
    qualityScore: clamp(baseScore, 0, 100),
    checks,
    failureStage,
    failureReason,
    retryable: Boolean(failureStage),
    accepted: !failureStage,
  }
}
