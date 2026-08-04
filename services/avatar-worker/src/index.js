import { app } from './app.js'
import { workerConfig } from './config.js'

app.listen(workerConfig.port, () => {
  console.log(`[avatar-worker] listening on port ${workerConfig.port}, internal base ${process.env.AVATAR_WORKER_URL || `http://127.0.0.1:${workerConfig.port}`}`)
})
