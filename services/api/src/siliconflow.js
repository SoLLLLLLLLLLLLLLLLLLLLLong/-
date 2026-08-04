import { config } from './config.js'

function buildFallbackText({ mode, text, scene }) {
  const source = text || '请介绍本次内容的核心价值与适用场景。'
  if (mode === 'rewrite') {
    return `大家好，今天带来一段更适合数字人口播的视频文案：${source.slice(0, 80)}。我们会用更清楚的结构介绍亮点、场景和行动建议，让观众更容易理解并产生兴趣。`
  }

  if (mode === 'marketing') {
    return `如果你正在寻找一套高效的内容制作方案，这段关于${scene || '产品亮点'}的口播脚本可以帮助你快速打动用户：先讲痛点，再讲优势，最后给出明确行动引导。`
  }

  if (mode === 'knowledge') {
    return `今天我们用一分钟讲清楚${scene || '一个实用主题'}：先说明背景，再拆解关键点，最后用一个简单结论帮助观众快速记住重点。`
  }

  return `大家好，欢迎来到 AI创作工坊。今天我们围绕${scene || '品牌介绍'}展开，用简洁清楚的方式介绍核心亮点、适用人群与下一步建议。`
}

async function requestJson(url, body, apiKey) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`上游模型请求失败: ${response.status} ${text}`)
  }

  return response.json()
}

export async function generateScriptWithLLM({ text, mode, scene }) {
  if (!config.deepseekApiKey) {
    return {
      text: buildFallbackText({ mode, text, scene }),
      provider: 'fallback',
    }
  }

  const messages = [
    {
      role: 'system',
      content:
        '你是一名数字人口播脚本助手。请输出适合短视频或数字人口播的中文文案，结构清晰，语言自然，避免夸张承诺，默认控制在 120 到 220 字。',
    },
    {
      role: 'user',
      content: `模式：${mode}\n场景：${scene || '通用'}\n原始文案：${text || '无'}\n请直接输出最终脚本。`,
    },
  ]

  const payload = {
    model: config.deepseekModel,
    temperature: 0.7,
    messages,
  }

  const data = await requestJson(`${config.deepseekBaseUrl}/chat/completions`, payload, config.deepseekApiKey)
  return {
    text: data.choices?.[0]?.message?.content?.trim() || buildFallbackText({ mode, text, scene }),
    provider: 'siliconflow',
  }
}

export async function embedText(text) {
  if (!config.embeddingApiKey) {
    return {
      embedding: [0.12, 0.34, 0.56],
      provider: 'fallback',
    }
  }

  const payload = {
    model: config.embeddingModel,
    input: text,
  }

  const data = await requestJson(`${config.embeddingBaseUrl}/embeddings`, payload, config.embeddingApiKey)
  return {
    embedding: data.data?.[0]?.embedding || [],
    provider: 'siliconflow',
  }
}

function stringHash(input) {
  return Array.from(input || 'kolors').reduce((accumulator, character) => accumulator + character.charCodeAt(0), 0)
}

export async function generateImageWithModel({ prompt, aspectRatio = '1:1' }) {
  const selectedModel = 'Kwai-Kolors/Kolors'

  if (!config.deepseekApiKey) {
    return {
      selectedModel,
      provider: 'fallback',
      previewUrl: `https://picsum.photos/seed/${stringHash(prompt)}/1024/1024`,
      prompt,
      aspectRatio,
    }
  }

  const payload = {
    model: selectedModel,
    prompt,
    image_size: aspectRatio === '9:16' ? '768x1344' : '1024x1024',
  }

  const data = await requestJson(`${config.deepseekBaseUrl}/images/generations`, payload, config.deepseekApiKey)
  return {
    selectedModel,
    provider: 'siliconflow',
    previewUrl: data.data?.[0]?.url || `https://picsum.photos/seed/${stringHash(prompt)}/1024/1024`,
    prompt,
    aspectRatio,
  }
}
