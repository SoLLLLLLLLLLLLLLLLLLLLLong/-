import express from 'express'
import { ERROR_CODES } from '@ai-creator-workshop/shared'
import { createAvatarJob, getAvatarJob, getProviderManifest } from './provider.js'

const app = express()

app.use(express.json({ limit: '2mb' }))

app.get('/worker/health', (_request, response) => {
  response.json({
    code: 0,
    message: 'ok',
    data: getProviderManifest(),
  })
})

app.post('/worker/avatar/assets', (request, response) => {
  const { objectKey = '', uploadId = '' } = request.body || {}
  response.json({
    code: 0,
    message: 'ok',
    data: {
      assetId: `asset_${Date.now()}`,
      objectKey,
      uploadId,
      verified: true,
    },
  })
})

app.post('/worker/avatar/jobs', async (request, response, next) => {
  try {
    const job = await createAvatarJob(request.body || {})
    response.json({
      code: 0,
      message: 'ok',
      data: job,
    })
  } catch (error) {
    next(error)
  }
})

app.get('/worker/avatar/jobs/:jobId', (request, response, next) => {
  try {
    const job = getAvatarJob(request.params.jobId)
    if (!job) {
      const error = new Error('数字人任务不存在。')
      error.code = ERROR_CODES.TASK_NOT_FOUND
      throw error
    }

    response.json({
      code: 0,
      message: 'ok',
      data: job,
    })
  } catch (error) {
    next(error)
  }
})

app.use((error, _request, response, _next) => {
  response.status(400).json({
    code: error.code || ERROR_CODES.PROVIDER_ERROR,
    message: error.message || 'worker 请求失败',
    data: null,
  })
})

export { app }
