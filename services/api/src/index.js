import { app } from './app.js'
import { config } from './config.js'

app.listen(config.port, () => {
  console.log(`[api] listening on port ${config.port}, LAN/Public base should be ${process.env.API_BASE_URL || `http://172.22.121.135:${config.port}`}`)
})
