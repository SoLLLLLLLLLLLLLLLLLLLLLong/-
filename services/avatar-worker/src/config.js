import dotenv from 'dotenv'

dotenv.config()

export const workerConfig = {
  port: Number(process.env.AVATAR_WORKER_PORT || 4000),
  provider: process.env.AVATAR_PROVIDER || 'musetalk',
  museTalkEndpoint: process.env.MUSE_TALK_ENDPOINT || '',
  wav2lipEndpoint: process.env.WAV2LIP_ENDPOINT || '',
  sadTalkerEndpoint: process.env.SADTALKER_ENDPOINT || '',
  publicFileBaseUrl: process.env.PUBLIC_FILE_BASE_URL || 'https://files.example.com',
}
