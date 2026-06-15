const JSON_HEADERS = {
  "Content-Type": "application/json",
};

function getToken() {
  return localStorage.getItem("token") || "";
}

function buildHeaders(extra = {}) {
  const headers = { ...extra };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function parseError(response) {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") {
      return data.detail;
    }
    return JSON.stringify(data);
  } catch {
    return `请求失败 (${response.status})`;
  }
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response;
}

export async function register(payload) {
  const response = await request("/api/register", {
    method: "POST",
    headers: buildHeaders(JSON_HEADERS),
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function login(payload) {
  const response = await request("/api/token", {
    method: "POST",
    headers: buildHeaders(JSON_HEADERS),
    body: JSON.stringify(payload),
  });
  return response.json();
}

export async function getCurrentUser() {
  const response = await request("/api/users/me", {
    headers: buildHeaders(),
  });
  return response.json();
}

export async function createConversation(userId) {
  const response = await request("/api/conversations", {
    method: "POST",
    headers: buildHeaders(JSON_HEADERS),
    body: JSON.stringify({ user_id: userId }),
  });
  return response.json();
}

export async function getConversations(userId) {
  const response = await request(`/api/conversations/user/${userId}`, {
    headers: buildHeaders(),
  });
  return response.json();
}

export async function getConversationMessages(conversationId, userId) {
  const response = await request(
    `/api/conversations/${conversationId}/messages?user_id=${userId}`,
    {
      headers: buildHeaders(),
    }
  );
  return response.json();
}

export async function deleteConversation(conversationId) {
  await request(`/api/conversations/${conversationId}`, {
    method: "DELETE",
    headers: buildHeaders(),
  });
}

export async function renameConversation(conversationId, name) {
  await request(`/api/conversations/${conversationId}/name`, {
    method: "PUT",
    headers: buildHeaders(JSON_HEADERS),
    body: JSON.stringify({ name }),
  });
}

export async function uploadKnowledgeFile(file, userId) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", String(userId));

  const response = await request("/api/upload", {
    method: "POST",
    headers: buildHeaders(),
    body: formData,
  });
  return response.json();
}

export async function getWeather(city = "") {
  const query = city ? `?city=${encodeURIComponent(city)}` : "";
  const response = await request(`/api/weather${query}`, {
    headers: buildHeaders(),
  });
  return response.json();
}

export async function streamAgentChat(messages, userId, conversationId, indexId, signal) {
  return request("/api/agent/chat", {
    method: "POST",
    headers: buildHeaders(JSON_HEADERS),
    signal,
    body: JSON.stringify({
      messages,
      user_id: userId,
      conversation_id: conversationId,
      index_id: indexId || null,
    }),
  });
}
