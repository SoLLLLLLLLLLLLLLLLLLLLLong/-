import cors from 'cors'
import express from 'express'
import { ERROR_CODES, SCRIPT_TEMPLATES, TASK_PROGRESS_STATUS, TASK_STATUSES, TASK_TYPES } from '@ai-creator-workshop/shared'
import { analyzeImageAsset } from './asset-quality.js'
import { createAvatarWorkerJob, getAvatarWorkerJob } from './avatar-worker-client.js'
import { config } from './config.js'
import { enqueueJob, listActiveJobs, registerProcessor } from './queue.js'
import { applyRateLimit, redactValue, validateScriptInput, validateUploadMeta } from './security.js'
import { embedText, generateImageWithModel, generateScriptWithLLM } from './siliconflow.js'
import {
  createAssetRecord,
  createTask,
  getAsset,
  getDiscoveryData,
  getTask,
  listTasksByUser,
  listWorksByUser,
  seedDemoWorks,
  updateTask,
  upsertWorkFromTask,
} from './store.js'

const app = express()

app.use(cors())
app.use(express.json({ limit: '1mb' }))

app.use((request, _response, next) => {
  request.userId = request.header('x-user-id') || 'guest-demo'
  seedDemoWorks(request.userId)
  next()
})

registerProcessor('voice', async ({ taskId, voice }) => {
  await new Promise((resolve) => setTimeout(resolve, 1200))
  updateTask(taskId, {
    status: TASK_PROGRESS_STATUS.SUCCESS,
    workflowStatus: TASK_STATUSES.VOICE_READY,
    progress: 100,
    result: {
      voiceUrl: 'https://www.w3schools.com/html/horse.mp3',
      summary: `已生成 ${voice?.name || '默认音色'} 的配音预览。`,
      duration: 18,
      retryable: false,
      failureStage: '',
    },
  })
  upsertWorkFromTask(getTask(taskId))
})

registerProcessor('export', async ({ taskId, resolution }) => {
  await new Promise((resolve) => setTimeout(resolve, 1500))
  updateTask(taskId, {
    status: TASK_PROGRESS_STATUS.SUCCESS,
    workflowStatus: TASK_STATUSES.DONE,
    progress: 100,
    result: {
      fileUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
      previewUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
      coverUrl: `${config.publicFileBaseUrl}/previews/${taskId}.jpg`,
      downloadUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
      summary: `已导出 ${resolution} 成片，可用于发布与预览。`,
      expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
      retryable: false,
      failureStage: '',
    },
  })
  upsertWorkFromTask(getTask(taskId))
})

registerProcessor('image', async ({ taskId, prompt, aspectRatio }) => {
  const result = await generateImageWithModel({ prompt, aspectRatio })
  updateTask(taskId, {
    status: TASK_PROGRESS_STATUS.SUCCESS,
    workflowStatus: TASK_STATUSES.DONE,
    progress: 100,
    result: {
      previewUrl: result.previewUrl,
      downloadUrl: result.previewUrl,
      summary: `已使用 ${result.selectedModel} 生成测试图片。`,
      selectedModel: result.selectedModel,
      provider: result.provider,
      retryable: false,
      failureStage: '',
    },
  })
  upsertWorkFromTask(getTask(taskId))
})

app.get('/api/health', (_request, response) => {
  response.json({
    code: 0,
    message: 'ok',
    data: {
      service: 'api',
      modelConfigured: Boolean(config.deepseekApiKey),
      maskedKey: redactValue(config.deepseekApiKey),
      activeJobs: listActiveJobs(),
    },
  })
})

app.get('/api/discovery', (request, response) => {
  response.json({
    code: 0,
    message: 'ok',
    data: {
      ...getDiscoveryData(),
      recentTasks: listTasksByUser(request.userId).slice(0, 3),
    },
  })
})

app.get('/api/works', (request, response) => {
  response.json({
    code: 0,
    message: 'ok',
    data: listWorksByUser(request.userId),
  })
})

app.get('/api/tasks/:taskId', async (request, response, next) => {
  try {
    const task = getTask(request.params.taskId)
    if (!task || task.userId !== request.userId) {
      const error = new Error('任务不存在。')
      error.code = ERROR_CODES.TASK_NOT_FOUND
      throw error
    }

    if (task.type === TASK_TYPES.AVATAR && task.payload.workerJobId && task.status !== TASK_PROGRESS_STATUS.SUCCESS) {
      const workerData = await getAvatarWorkerJob(task.payload.workerJobId)
      updateTask(task.id, {
        status: workerData.data.status,
        workflowStatus:
          workerData.data.status === TASK_PROGRESS_STATUS.SUCCESS ? TASK_STATUSES.AVATAR_READY : TASK_STATUSES.AVATAR_GENERATING,
        progress: workerData.data.progress,
        result: workerData.data.result,
        errorMessage: workerData.data.errorMessage || '',
      })
      upsertWorkFromTask(getTask(task.id))
    }

    response.json({
      code: 0,
      message: 'ok',
      data: getTask(request.params.taskId),
    })
  } catch (error) {
    next(error)
  }
})

app.post('/api/script/generate', async (request, response, next) => {
  try {
    applyRateLimit(request.userId, 'script-generate', 10)
    const { text = '', mode = 'generate', scene = '通用', templateId = '' } = request.body || {}
    validateScriptInput(text || '占位文本')
    const template = SCRIPT_TEMPLATES.find((entry) => entry.id === templateId)
    const llmResult = await generateScriptWithLLM({
      text,
      mode,
      scene: template?.scene || scene,
    })
    const embedding = await embedText(llmResult.text)
    response.json({
      code: 0,
      message: 'ok',
      data: {
        text: llmResult.text,
        provider: llmResult.provider,
        embeddingProvider: embedding.provider,
        templateUsed: template || null,
      },
    })
  } catch (error) {
    next(error)
  }
})

app.post('/api/voice/tasks', (request, response, next) => {
  try {
    applyRateLimit(request.userId, 'voice-task', 8)
    const { scriptText = '', voice = null } = request.body || {}
    validateScriptInput(scriptText)
    const task = createTask({
      type: TASK_TYPES.VOICE,
      userId: request.userId,
      payload: { scriptText, voice },
      workflowStatus: TASK_STATUSES.VOICE_GENERATING,
      title: `${voice?.name || '默认音色'} 配音任务`,
    })

    enqueueJob('voice', {
      taskId: task.id,
      voice,
    })

    response.json({
      code: 0,
      message: 'ok',
      data: task,
    })
  } catch (error) {
    next(error)
  }
})

app.post('/api/image/tasks', (request, response, next) => {
  try {
    applyRateLimit(request.userId, 'image-task', 8)
    const { prompt = '', aspectRatio = '1:1' } = request.body || {}
    validateScriptInput(prompt)
    const task = createTask({
      type: TASK_TYPES.IMAGE,
      userId: request.userId,
      payload: { prompt, aspectRatio },
      workflowStatus: TASK_STATUSES.EXPORTING,
      title: 'AI 图片生成任务',
    })

    enqueueJob('image', {
      taskId: task.id,
      prompt,
      aspectRatio,
    })

    response.json({
      code: 0,
      message: 'ok',
      data: task,
    })
  } catch (error) {
    next(error)
  }
})

app.post('/api/avatar/tasks', async (request, response, next) => {
  try {
    applyRateLimit(request.userId, 'avatar-task', 6)
    const {
      scriptText = '',
      voiceTaskId = '',
      avatar = null,
      imageAssetId = '',
      imageAsset = null,
      aspectRatio = '9:16',
      resolution = '1080P',
    } = request.body || {}
    validateScriptInput(scriptText)
    const storedAsset = imageAssetId ? getAsset(imageAssetId, request.userId) : null
    const quality = analyzeImageAsset(storedAsset || imageAsset || {})

    if (!quality.accepted) {
      const error = new Error(quality.failureReason)
      error.code = ERROR_CODES.QUALITY_REJECTED
      error.details = quality
      throw error
    }

    const task = createTask({
      type: TASK_TYPES.AVATAR,
      userId: request.userId,
      payload: {
        scriptText,
        voiceTaskId,
        avatar,
        imageAssetId,
        imageAsset: storedAsset || imageAsset,
        aspectRatio,
        resolution,
      },
      workflowStatus: TASK_STATUSES.AVATAR_GENERATING,
      title: `${avatar?.name || '数字人'} 视频任务`,
    })

    const workerJob = await createAvatarWorkerJob({
      taskId: task.id,
      userId: request.userId,
      avatar,
      imageAsset: {
        ...(storedAsset || imageAsset),
        quality,
      },
      scriptText,
      voiceTaskId,
      aspectRatio,
      resolution,
    })

    updateTask(task.id, {
      payload: {
        ...task.payload,
        workerJobId: workerJob.data.jobId,
      },
      progress: 15,
      result: {
        qualityScore: quality.qualityScore,
      },
    })

    response.json({
      code: 0,
      message: 'ok',
      data: getTask(task.id),
    })
  } catch (error) {
    next(error)
  }
})

app.post('/api/export/tasks', (request, response, next) => {
  try {
    applyRateLimit(request.userId, 'export-task', 10)
    const { avatarTaskId = '', bgm = null, coverTitle = '', resolution = '1080P' } = request.body || {}
    const sourceTask = getTask(avatarTaskId)
    if (!sourceTask) {
      const error = new Error('请先生成数字人视频。')
      error.code = ERROR_CODES.TASK_NOT_FOUND
      throw error
    }

    const task = createTask({
      type: TASK_TYPES.EXPORT,
      userId: request.userId,
      payload: { avatarTaskId, bgm, coverTitle, resolution },
      workflowStatus: TASK_STATUSES.EXPORTING,
      title: `${coverTitle || '数字人口播成片'} 导出任务`,
    })

    enqueueJob('export', {
      taskId: task.id,
      resolution,
    })

    response.json({
      code: 0,
      message: 'ok',
      data: task,
    })
  } catch (error) {
    next(error)
  }
})

app.post('/api/uploads/sign', (request, response, next) => {
  try {
    applyRateLimit(request.userId, 'uploads-sign', 20)
    const meta = request.body || {}
    validateUploadMeta(meta)
    const quality = analyzeImageAsset(meta)
    const assetRecord = createAssetRecord({
      userId: request.userId,
      objectKey: `user/${request.userId}/avatar-assets/${Date.now()}_${meta.fileName || 'asset'}`,
      uploadId: `upload_${Date.now()}`,
      fileName: meta.fileName,
      mimeType: meta.mimeType,
      size: meta.size,
      width: meta.width,
      height: meta.height,
      quality,
    })
    response.json({
      code: 0,
      message: 'ok',
      data: {
        uploadId: assetRecord.uploadId,
        assetId: assetRecord.id,
        objectKey: assetRecord.objectKey,
        uploadUrl: `${config.publicFileBaseUrl}/signed-upload`,
        expiresAt: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
        quality,
      },
    })
  } catch (error) {
    next(error)
  }
})

app.use((error, _request, response, _next) => {
  response.status(error.code === ERROR_CODES.TASK_NOT_FOUND ? 404 : 400).json({
    code: error.code || ERROR_CODES.INVALID_INPUT,
    message: error.message || '请求失败',
    data: error.details || null,
  })
})

export { app }
