import {
  DEFAULT_AVATARS,
  DEFAULT_VOICES,
  ERROR_CODES,
  SCRIPT_TEMPLATES,
  TASK_PROGRESS_STATUS,
  TASK_STATUSES,
  TASK_TYPES,
} from '@ai-creator-workshop/shared'
import { findCollectionItem, listCollection, upsertCollectionItem, writeCollection } from './db.js'

function now() {
  return new Date().toISOString()
}

function createId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function nextUserSnapshot(userId) {
  return {
    id: userId,
    updatedAt: now(),
  }
}

export function ensureUser(userId) {
  upsertCollectionItem('users', nextUserSnapshot(userId))
}

export function createTask({ type, userId, payload, workflowStatus, title }) {
  ensureUser(userId)
  const id = createId('task')
  const timestamp = now()
  const task = {
    id,
    type,
    status: TASK_PROGRESS_STATUS.QUEUED,
    workflowStatus,
    progress: 5,
    payload,
    result: null,
    errorCode: '',
    errorMessage: '',
    title,
    userId,
    retryable: false,
    failureStage: '',
    createdAt: timestamp,
    updatedAt: timestamp,
  }

  upsertCollectionItem('tasks', task)
  return task
}

export function updateTask(id, updates) {
  const task = getTask(id)
  if (!task) {
    return null
  }

  const nextTask = {
    ...task,
    ...updates,
    updatedAt: now(),
  }

  upsertCollectionItem('tasks', nextTask)
  return nextTask
}

export function getTask(id) {
  return findCollectionItem('tasks', (task) => task.id === id)
}

export function listTasksByUser(userId) {
  return listCollection('tasks')
    .filter((task) => task.userId === userId)
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
}

export function createAssetRecord({ userId, objectKey, uploadId, fileName, mimeType, size, width, height, quality }) {
  const asset = {
    id: `asset_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    userId,
    uploadId,
    objectKey,
    fileName,
    mimeType,
    size,
    width,
    height,
    quality,
    createdAt: now(),
    updatedAt: now(),
  }
  upsertCollectionItem('assets', asset)
  return asset
}

export function getAsset(assetId, userId) {
  return findCollectionItem('assets', (asset) => asset.id === assetId && asset.userId === userId)
}

export function upsertWorkFromTask(task) {
  const workId = task.id.replace(/^task_/, 'work_')
  const payloadAssetId = task.payload?.imageAsset?.assetId || task.payload?.imageAssetId || ''
  const asset = payloadAssetId ? getAsset(payloadAssetId, task.userId) : null
  const work = {
    id: workId,
    taskId: task.id,
    type: task.type,
    title: task.title,
    status: task.status,
    workflowStatus: task.workflowStatus,
    previewUrl: task.result?.previewUrl || task.result?.fileUrl || '',
    coverUrl: task.result?.coverUrl || '',
    downloadUrl: task.result?.downloadUrl || task.result?.fileUrl || '',
    sourceImageUrl: asset ? `/assets/${asset.objectKey}` : '',
    qualityScore: task.result?.qualityScore || asset?.quality?.qualityScore || 0,
    failureStage: task.failureStage || task.result?.failureStage || '',
    retryable: task.retryable ?? false,
    result: task.result,
    errorMessage: task.errorMessage,
    userId: task.userId,
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
  }

  upsertCollectionItem('works', work)
  return work
}

export function listWorksByUser(userId) {
  return listCollection('works')
    .filter((work) => work.userId === userId)
    .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
}

export function seedDemoWorks(userId = 'guest-demo') {
  if (listWorksByUser(userId).length > 0) {
    return
  }

  const entries = [
    {
      type: TASK_TYPES.AVATAR,
      title: '品牌介绍口播视频',
      status: TASK_PROGRESS_STATUS.SUCCESS,
      workflowStatus: TASK_STATUSES.DONE,
      result: {
        previewUrl: 'https://files.example.com/previews/brand-intro.mp4',
        coverUrl: 'https://files.example.com/previews/brand-intro.jpg',
        downloadUrl: 'https://files.example.com/exports/brand-intro.mp4',
        summary: '已完成 1080P 预览视频，可用于简历演示。',
        qualityScore: 91,
      },
    },
    {
      type: TASK_TYPES.VOICE,
      title: '知识分享配音',
      status: TASK_PROGRESS_STATUS.FAILED,
      workflowStatus: TASK_STATUSES.FAILED,
      result: null,
      errorMessage: '音色服务暂时不可用，请稍后重试。',
      failureStage: 'voice_generation',
      retryable: true,
    },
  ]

  entries.forEach((entry) => {
    const task = createTask({
      type: entry.type,
      userId,
      payload: {},
      workflowStatus: entry.workflowStatus,
      title: entry.title,
    })
    updateTask(task.id, {
      status: entry.status,
      workflowStatus: entry.workflowStatus,
      progress: entry.status === TASK_PROGRESS_STATUS.SUCCESS ? 100 : 0,
      result: entry.result,
      errorMessage: entry.errorMessage || '',
      failureStage: entry.failureStage || '',
      retryable: entry.retryable || false,
      errorCode: entry.errorMessage ? ERROR_CODES.PROVIDER_ERROR : '',
    })
    upsertWorkFromTask(getTask(task.id))
  })
}

export function getDiscoveryData() {
  return {
    templates: SCRIPT_TEMPLATES,
    commonVoices: DEFAULT_VOICES,
    hotAvatars: DEFAULT_AVATARS,
  }
}

export function resetRuntimeData() {
  writeCollection('tasks', [])
  writeCollection('works', [])
  writeCollection('assets', [])
  writeCollection('users', [])
}
