const processors = new Map()
const activeJobs = new Set()

export function registerProcessor(type, handler) {
  processors.set(type, handler)
}

export function enqueueJob(type, payload) {
  const handler = processors.get(type)
  if (!handler) {
    throw new Error(`未注册任务处理器: ${type}`)
  }

  const jobId = `${type}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  activeJobs.add(jobId)

  Promise.resolve()
    .then(() => handler(payload))
    .finally(() => {
      activeJobs.delete(jobId)
    })

  return jobId
}

export function listActiveJobs() {
  return Array.from(activeJobs)
}
