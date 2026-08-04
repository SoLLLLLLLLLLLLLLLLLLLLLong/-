import { TASK_PROGRESS_STATUS } from '@ai-creator-workshop/shared'
import { workerConfig } from './config.js'

const jobs = new Map()

function createId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

async function maybeForward(url, payload) {
  if (!url) {
    return null
  }

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`远程推理服务失败: ${response.status} ${text}`)
  }

  return response.json()
}

function simulateJob(jobId, payload) {
  jobs.set(jobId, {
    jobId,
    provider: workerConfig.provider,
    status: TASK_PROGRESS_STATUS.QUEUED,
    progress: 10,
    payload,
    result: null,
    errorMessage: '',
  })

  setTimeout(() => {
    const queuedJob = jobs.get(jobId)
    if (!queuedJob) {
      return
    }
    jobs.set(jobId, {
      ...queuedJob,
      status: TASK_PROGRESS_STATUS.PROCESSING,
      progress: 58,
    })
  }, 1200)

  setTimeout(() => {
    const processingJob = jobs.get(jobId)
    if (!processingJob) {
      return
    }
    jobs.set(jobId, {
      ...processingJob,
      status: TASK_PROGRESS_STATUS.SUCCESS,
      progress: 100,
      result: {
        previewUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
        coverUrl: `${workerConfig.publicFileBaseUrl}/avatar/${jobId}.jpg`,
        downloadUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
        sourceImageUrl: payload.imageAsset?.previewUrl || '',
        qualityScore: payload.imageAsset?.quality?.qualityScore || 82,
        failureStage: '',
        retryable: false,
        summary: `${payload.avatar?.name || '数字人'} 已完成口型驱动预览。`,
        provider: workerConfig.provider,
      },
})
  }, 2800)
}

export async function createAvatarJob(payload) {
  const jobId = createId('avatar_job')
  const endpointMap = {
    musetalk: workerConfig.museTalkEndpoint,
    wav2lip: workerConfig.wav2lipEndpoint,
    sadtalker: workerConfig.sadTalkerEndpoint,
  }

  const endpoint = endpointMap[workerConfig.provider]
  const forwarded = await maybeForward(endpoint, payload)

  if (forwarded) {
    jobs.set(jobId, {
      jobId,
      provider: workerConfig.provider,
      status: forwarded.status || TASK_PROGRESS_STATUS.QUEUED,
      progress: forwarded.progress || 0,
      payload,
      result: forwarded.result || null,
      errorMessage: '',
    })
    return jobs.get(jobId)
  }

  simulateJob(jobId, payload)
  return jobs.get(jobId)
}

export function getAvatarJob(jobId) {
  return jobs.get(jobId) || null
}

export function getProviderManifest() {
  return {
    activeProvider: workerConfig.provider,
    supportedProviders: [
      {
        id: 'musetalk',
        name: 'MuseTalk',
        repo: 'https://github.com/TMElyralab/MuseTalk',
        usage: '主推方案，适合口型驱动与较现代的数字人口播封装。',
      },
      {
        id: 'wav2lip',
        name: 'Wav2Lip',
        repo: 'https://github.com/Rudrabha/Wav2Lip',
        usage: '备选方案，适合作为稳妥的唇形同步链路。',
      },
      {
        id: 'sadtalker',
        name: 'SadTalker',
        repo: 'https://github.com/OpenTalker/SadTalker',
        usage: '备选方案，适合静态头像驱动型数字人场景。',
      },
    ],
  }
}
