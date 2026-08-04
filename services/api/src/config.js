import dotenv from 'dotenv'

dotenv.config()

export const config = {
  port: Number(process.env.API_PORT || 3000),
  deepseekApiKey: process.env.DEEPSEEK_API_KEY || '',
  deepseekBaseUrl: process.env.DEEPSEEK_BASE_URL || 'https://api.siliconflow.cn/v1',
  deepseekModel: process.env.DEEPSEEK_MODEL || 'deepseek-ai/DeepSeek-V4-Flash',
  embeddingApiKey: process.env.EMBEDDING_API_KEY || '',
  embeddingBaseUrl: process.env.EMBEDDING_BASE_URL || 'https://api.siliconflow.cn/v1',
  embeddingModel: process.env.EMBEDDING_MODEL || 'Qwen/Qwen3-Embedding-0.6B',
  avatarWorkerUrl: process.env.AVATAR_WORKER_URL || 'http://127.0.0.1:4000',
  publicFileBaseUrl: process.env.PUBLIC_FILE_BASE_URL || 'https://files.example.com',
}
