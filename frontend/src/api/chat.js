import { getToken } from "./http.js";

async function parseError(response) {
  try {
    const data = await response.json();
    return data?.detail || JSON.stringify(data);
  } catch {
    return `请求失败 (${response.status})`;
  }
}

// 这里保留 fetch，而不是直接换成 axios。
// 原因是当前聊天接口返回的是流式响应，前端需要直接访问 response.body，
// 再通过 getReader() 持续读取后端一段一段推回来的内容。
export async function streamAgentChat(
  messages,
  userId,
  conversationId,
  indexId,
  options,
  signal
) {
  const headers = {
    "Content-Type": "application/json",
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch("/api/agent/chat", {
    method: "POST",
    headers,
    signal,
    body: JSON.stringify({
      messages,
      user_id: userId,
      conversation_id: conversationId,
      index_id: indexId || null,
      options: options || {},
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response;
}
