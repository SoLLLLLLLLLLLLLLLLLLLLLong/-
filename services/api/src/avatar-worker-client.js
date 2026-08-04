import { config } from './config.js'

export async function createAvatarWorkerJob(payload) {
  const response = await fetch(`${config.avatarWorkerUrl}/worker/avatar/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`数字人服务不可用: ${response.status} ${text}`)
  }

  return response.json()
}

export async function getAvatarWorkerJob(jobId) {
  const response = await fetch(`${config.avatarWorkerUrl}/worker/avatar/jobs/${jobId}`)
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`数字人任务读取失败: ${response.status} ${text}`)
  }

  return response.json()
}
