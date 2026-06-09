import {
  createConversation,
  deleteConversation,
  getConversationMessages,
  getConversations,
  getCurrentUser,
  getWeather,
  login,
  register,
  renameConversation,
  streamAgentChat,
  uploadKnowledgeFile,
} from "./api.js";

const app = document.getElementById("app");
const CURRENT_USER_CITY_KEY = "CURRENT_USER_CITY";

const state = {
  token: localStorage.getItem("token") || "",
  user: null,
  conversations: [],
  currentConversationId: Number(localStorage.getItem("conversation_id")) || null,
  messagesByConversation: {},
  attachments: loadAttachments(),
  currentIndexId: null,
  routeLabel: "自动路由",
  routeReason: "",
  sources: [],
  weather: null,
  thinkingVisible: false,
  thinkingStatus: "",
  thinkingLogs: [],
  isLoading: false,
};

function loadAttachments() {
  try {
    return JSON.parse(localStorage.getItem("conversation_attachments") || "{}");
  } catch {
    return {};
  }
}

function saveAttachments() {
  localStorage.setItem(
    "conversation_attachments",
    JSON.stringify(state.attachments)
  );
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function loadCachedCity() {
  return localStorage.getItem(CURRENT_USER_CITY_KEY) || "";
}

function saveCachedCity(city) {
  const next = String(city || "").trim();
  if (!next) {
    return;
  }
  localStorage.setItem(CURRENT_USER_CITY_KEY, next);
}

function renderWeatherCard() {
  if (!state.weather) {
    return `
      <div class="weather-cloud weather-cloud-loading">
        <p class="weather-city">📍 正在获取天气</p>
        <p class="weather-text">请稍候，正在同步当前城市天气...</p>
      </div>
    `;
  }

  if (state.weather.error) {
    return `
      <div class="weather-cloud weather-cloud-loading">
        <p class="weather-city">📍 天气暂不可用</p>
        <p class="weather-text">${escapeHtml(state.weather.error)}</p>
      </div>
    `;
  }

  const temp = state.weather.temperature_c;
  const tempText = typeof temp === "number" ? `${temp}°C` : "--";
  const feelslike =
    typeof state.weather.feelslike_c === "number"
      ? `体感 ${state.weather.feelslike_c}°C`
      : "";

  return `
    <div class="weather-cloud">
      <p class="weather-city">📍 当前城市：${escapeHtml(state.weather.city_name || "未知")}</p>
      <p class="weather-text">${escapeHtml(state.weather.weather_text || "天气信息已更新")}</p>
      <p class="weather-meta">${tempText}${feelslike ? ` · ${escapeHtml(feelslike)}` : ""}</p>
    </div>
  `;
}

function render() {
  if (!state.user) {
    app.innerHTML = renderAuth();
    bindAuthEvents();
    return;
  }

  app.innerHTML = renderWorkspace();
  bindWorkspaceEvents();
}

function renderAuth() {
  return `
    <div class="shell auth-layout">
      <div class="auth-card">
        <h1 class="auth-title">🤖 个人智能助手</h1>
        <p class="auth-subtitle">登录后即可使用自动路由 Agent、历史记忆和文档问答。</p>
        <form id="login-form">
          <div class="field">
            <label for="login-email">邮箱</label>
            <input id="login-email" name="email" type="email" required />
          </div>
          <div class="field">
            <label for="login-password">密码</label>
            <input id="login-password" name="password" type="password" required />
          </div>
          <div class="auth-actions">
            <button class="btn btn-primary" type="submit">登录</button>
            <button class="btn btn-ghost" type="button" id="show-register">注册新账号</button>
          </div>
          <p class="error-text hidden" id="login-error"></p>
        </form>
        <form id="register-form" class="hidden">
          <div class="field">
            <label for="register-username">用户名</label>
            <input id="register-username" name="username" required />
          </div>
          <div class="field">
            <label for="register-email">邮箱</label>
            <input id="register-email" name="email" type="email" required />
          </div>
          <div class="field">
            <label for="register-password">密码</label>
            <input id="register-password" name="password" type="password" required />
          </div>
          <div class="auth-actions">
            <button class="btn btn-primary" type="submit">完成注册</button>
            <button class="btn btn-ghost" type="button" id="show-login">返回登录</button>
          </div>
          <p class="error-text hidden" id="register-error"></p>
          <p class="success-text hidden" id="register-success"></p>
        </form>
      </div>
    </div>
  `;
}

function renderWorkspace() {
  const conversations = state.conversations
    .map((item) => {
      const active = item.id === state.currentConversationId ? "active" : "";
      return `
        <div class="history-item ${active}" data-conversation-id="${item.id}">
          <div class="history-item-title">${escapeHtml(item.title || "未命名会话")}</div>
          <div class="history-item-meta">${escapeHtml(formatDate(item.updated_at || item.created_at))}</div>
          <div class="history-item-actions">
            <button class="btn btn-ghost" data-action="rename" data-conversation-id="${item.id}">重命名</button>
            <button class="btn btn-danger" data-action="delete" data-conversation-id="${item.id}">删除</button>
          </div>
        </div>
      `;
    })
    .join("");

  const currentMessages = state.messagesByConversation[state.currentConversationId] || [];
  const messageHtml = currentMessages.length
    ? currentMessages.map(renderMessage).join("")
    : `
      <div class="empty-state">
        <h3>您好，我是个人智能助手</h3>
        <p>欢迎来到新的对话窗口。无论是日常问题、联网搜索，还是围绕文档内容进行整理和问答，我都可以尽量为您提供清晰、连续的解答。</p>
      </div>
    `;

  const attachment = state.currentConversationId
    ? state.attachments[String(state.currentConversationId)]
    : null;
  const attachmentBanner = attachment
    ? `
      <div class="attachment-banner">
        <span class="attachment-banner-label">当前已关联文档</span>
        <span class="attachment-banner-name" title="${escapeHtml(attachment.filename)}">${escapeHtml(attachment.filename)}</span>
        <button class="attachment-banner-remove" id="remove-attachment-btn" type="button" aria-label="移除当前文档">×</button>
      </div>
    `
    : "";

  const sourceHtml = state.sources.length
    ? `
      <div class="message message.system">
        <h4>参考来源</h4>
        <div class="message-links">
          ${state.sources.map(renderSource).join("")}
        </div>
      </div>
    `
    : "";
  const thinkingHtml = state.thinkingVisible
    ? `
      <div class="thinking-panel">
        <div class="thinking-panel-head">
          <span class="thinking-panel-title">思考过程</span>
          <span class="thinking-panel-status">${escapeHtml(state.thinkingStatus || "正在思考中...")}</span>
        </div>
        <div class="thinking-panel-body">
          ${state.thinkingLogs.map(renderThinkingLine).join("")}
        </div>
      </div>
    `
    : "";

  return `
    <div class="shell app-layout">
      <aside class="sidebar">
        <div class="brand">
          <h1>🤖 个人智能助手</h1>
          <p>👤 ${escapeHtml(state.user.username)} · ${escapeHtml(state.user.email)}</p>
        </div>
        <div class="sidebar-actions">
          <button class="btn btn-primary" id="new-conversation-btn">新建会话</button>
          <button class="btn btn-ghost" id="logout-btn">退出登录</button>
        </div>
        <div class="history">
          ${conversations || '<div class="history-empty">还没有历史会话。</div>'}
        </div>
      </aside>
      <main class="main">
        <div class="chat-topbar">
          <div class="chat-title">
            <h2>${escapeHtml(currentConversationTitle())}</h2>
            <span class="muted">支持多轮对话、联网搜索与文档检索增强问答。</span>
          </div>
          <div class="toolbar">
            ${renderWeatherCard()}
          </div>
        </div>
        <div class="chat-body">
          <div class="messages" id="messages">
            ${sourceHtml}
            ${messageHtml}
            ${thinkingHtml}
          </div>
          <div class="composer-wrap">
            <div class="status-strip">
              <span class="status-pill">记忆：最近消息 + summary 长期记忆</span>
              <span class="status-pill">上传 PDF / DOCX / TXT 后可直接围绕文档提问</span>
            </div>
            ${attachmentBanner}
            <form class="composer" id="composer-form">
              <textarea id="composer-input" placeholder="直接提问即可，例如：帮我总结这份 PDF 的重点，或者帮我查询今天的 AI 新闻。" required></textarea>
              <div class="composer-actions">
                <div class="composer-left">
                  <label class="btn btn-ghost" for="upload-input">上传文档</label>
                  <input id="upload-input" type="file" accept=".pdf,.docx,.txt,.md" class="hidden" />
                </div>
                <div class="composer-right">
                  <button class="btn btn-primary" type="submit" ${state.isLoading ? "disabled" : ""}>发送</button>
                </div>
              </div>
              <p class="error-text hidden" id="composer-error"></p>
            </form>
          </div>
        </div>
      </main>
    </div>
  `;
}

function renderMessage(message) {
  const role = message.sender || message.role || "assistant";
  const roleClass =
    role === "user" ? "user" : role === "assistant" ? "assistant" : "system";
  const pendingClass = message.pending ? " pending" : "";
  return `<div class="message ${roleClass}${pendingClass}">${escapeHtml(message.content)}</div>`;
}

function renderSource(item) {
  if (item.url) {
    return `
      <a class="message-link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
        ${escapeHtml(item.title || item.url)}
        <small>${escapeHtml(item.snippet || item.url)}</small>
      </a>
    `;
  }

  return `
    <div class="message-link">
      ${escapeHtml(item.source || "文档片段")}
      <small>页码：${escapeHtml(item.page || "未知")}</small>
    </div>
  `;
}

function renderThinkingLine(item) {
  return `
    <div class="thinking-line">
      <div class="thinking-label">${escapeHtml(item.label)}</div>
      <div>${escapeHtml(item.content)}</div>
    </div>
  `;
}

function currentConversationTitle() {
  const current = state.conversations.find(
    (item) => item.id === state.currentConversationId
  );
  return current?.title || "新对话";
}

function formatDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function bindAuthEvents() {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const showRegisterBtn = document.getElementById("show-register");
  const showLoginBtn = document.getElementById("show-login");

  showRegisterBtn?.addEventListener("click", () => {
    loginForm.classList.add("hidden");
    registerForm.classList.remove("hidden");
  });

  showLoginBtn?.addEventListener("click", () => {
    registerForm.classList.add("hidden");
    loginForm.classList.remove("hidden");
  });

  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorEl = document.getElementById("login-error");
    errorEl.classList.add("hidden");

    try {
      const formData = new FormData(loginForm);
      const payload = {
        email: String(formData.get("email") || "").trim(),
        password: String(formData.get("password") || ""),
      };
      const data = await login(payload);
      state.token = data.access_token;
      localStorage.setItem("token", state.token);
      await bootstrapUser();
      await refreshWeather();
      render();
    } catch (error) {
      errorEl.textContent = error.message || "登录失败";
      errorEl.classList.remove("hidden");
    }
  });

  registerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorEl = document.getElementById("register-error");
    const successEl = document.getElementById("register-success");
    errorEl.classList.add("hidden");
    successEl.classList.add("hidden");

    try {
      const formData = new FormData(registerForm);
      await register({
        username: String(formData.get("username") || "").trim(),
        email: String(formData.get("email") || "").trim(),
        password: String(formData.get("password") || ""),
      });
      successEl.textContent = "注册成功，请直接登录。";
      successEl.classList.remove("hidden");
      registerForm.reset();
    } catch (error) {
      errorEl.textContent = error.message || "注册失败";
      errorEl.classList.remove("hidden");
    }
  });
}

function bindWorkspaceEvents() {
  document.getElementById("logout-btn")?.addEventListener("click", logout);
  document
    .getElementById("new-conversation-btn")
    ?.addEventListener("click", handleCreateConversation);
  document
    .getElementById("composer-form")
    ?.addEventListener("submit", handleSendMessage);
  document.getElementById("composer-input")?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    const target = event.target;
    const value = typeof target?.value === "string" ? target.value.trim() : "";
    if (!value || state.isLoading) {
      return;
    }

    event.preventDefault();
    document.getElementById("composer-form")?.requestSubmit();
  });
  document
    .getElementById("upload-input")
    ?.addEventListener("change", handleUploadFile);
  document
    .getElementById("remove-attachment-btn")
    ?.addEventListener("click", handleRemoveAttachment);

  document.querySelectorAll("[data-conversation-id]").forEach((element) => {
    if (element.dataset.action) {
      return;
    }
    element.addEventListener("click", async () => {
      await switchConversation(Number(element.dataset.conversationId));
    });
  });

  document.querySelectorAll('[data-action="delete"]').forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const conversationId = Number(button.dataset.conversationId);
      if (!conversationId) {
        return;
      }

      await deleteConversation(conversationId);
      delete state.messagesByConversation[conversationId];
      delete state.attachments[String(conversationId)];
      saveAttachments();
      state.conversations = state.conversations.filter((item) => item.id !== conversationId);

      if (state.currentConversationId === conversationId) {
        state.currentConversationId = state.conversations[0]?.id || null;
        localStorage.setItem("conversation_id", String(state.currentConversationId || ""));
        if (state.currentConversationId) {
          await switchConversation(state.currentConversationId);
          return;
        }
      }

      render();
    });
  });

  document.querySelectorAll('[data-action="rename"]').forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const conversationId = Number(button.dataset.conversationId);
      const current = state.conversations.find((item) => item.id === conversationId);
      const nextName = window.prompt("请输入新的会话名称", current?.title || "");
      if (!nextName) {
        return;
      }

      await renameConversation(conversationId, nextName);
      await refreshConversations(false);
      render();
    });
  });
}

async function bootstrapUser() {
  try {
    state.user = await getCurrentUser();
    await refreshConversations(true);
    render();
  } catch (error) {
    logout(false);
    throw error;
  }
}

async function refreshConversations(ensureCurrent) {
  state.conversations = await getConversations(state.user.id);

  if (!state.conversations.length) {
    const data = await createConversation(state.user.id);
    state.currentConversationId = data.conversation_id;
    localStorage.setItem("conversation_id", String(state.currentConversationId));
    state.conversations = await getConversations(state.user.id);
  } else if (
    ensureCurrent &&
    !state.conversations.some((item) => item.id === state.currentConversationId)
  ) {
    state.currentConversationId = state.conversations[0].id;
    localStorage.setItem("conversation_id", String(state.currentConversationId));
  }

  if (state.currentConversationId) {
    await switchConversation(state.currentConversationId, false);
  }
}

async function refreshWeather() {
  try {
    state.weather = await getWeather();
    if (state.weather?.city_name) {
      saveCachedCity(state.weather.city_name);
    }
  } catch (error) {
    state.weather = {
      error: error.message || "天气获取失败",
    };
  }
}

async function switchConversation(conversationId, rerender = true) {
  state.currentConversationId = conversationId;
  localStorage.setItem("conversation_id", String(conversationId));
  state.currentIndexId = state.attachments[String(conversationId)]?.indexId || null;
  state.routeLabel = "自动路由";
  state.routeReason = "";
  state.sources = [];
  state.thinkingVisible = false;
  state.thinkingStatus = "";
  state.thinkingLogs = [];

  if (!state.messagesByConversation[conversationId]) {
    const messages = await getConversationMessages(conversationId, state.user.id);
    state.messagesByConversation[conversationId] = messages;
  }

  if (rerender) {
    render();
    scrollMessagesToBottom();
  }
}

async function handleCreateConversation() {
  const data = await createConversation(state.user.id);
  state.currentConversationId = data.conversation_id;
  localStorage.setItem("conversation_id", String(state.currentConversationId));
  await refreshConversations(false);
  render();
}

async function handleUploadFile(event) {
  const file = event.target.files?.[0];
  if (!file || !state.currentConversationId) {
    return;
  }

  const errorEl = document.getElementById("composer-error");
  errorEl.classList.add("hidden");

  try {
    const result = await uploadKnowledgeFile(file, state.user.id);
  state.currentIndexId = result.index_id;
    state.attachments[String(state.currentConversationId)] = {
      indexId: result.index_id,
      filename: result.original_name || result.filename,
      chunks: result.chunks,
    };
    saveAttachments();
    pushSystemMessage(
      `已完成文档解析：${result.original_name || result.filename}，共生成 ${result.chunks} 个文本片段。现在你可以直接围绕这份文档提问。`
    );
    render();
    scrollMessagesToBottom();
  } catch (error) {
    errorEl.textContent = error.message || "上传失败";
    errorEl.classList.remove("hidden");
  } finally {
    event.target.value = "";
  }
}

function handleRemoveAttachment() {
  if (!state.currentConversationId) {
    return;
  }

  const attachment = state.attachments[String(state.currentConversationId)];
  if (!attachment) {
    return;
  }

  delete state.attachments[String(state.currentConversationId)];
  saveAttachments();
  state.currentIndexId = null;
  state.sources = [];
  state.routeLabel = "自动路由";
  state.routeReason = "当前会话已移除文档上下文，后续提问将不再使用这份文档检索。";
  pushSystemMessage(`已移除文档：${attachment.filename}`);
  render();
  scrollMessagesToBottom();
}

async function handleSendMessage(event) {
  event.preventDefault();
  const input = document.getElementById("composer-input");
  const errorEl = document.getElementById("composer-error");
  const text = input.value.trim();

  if (!text || !state.currentConversationId || state.isLoading) {
    return;
  }

  errorEl.classList.add("hidden");
  state.sources = [];
  state.thinkingVisible = true;
  state.thinkingStatus = "正在思考中...";
  state.thinkingLogs = [
    {
      label: "状态",
      content: "正在思考中...",
    },
  ];
  state.isLoading = true;
  pushMessage({ sender: "user", content: text });
  pushMessage({
    sender: "assistant",
    content: "正在思考中...",
    pending: true,
  });
  render();
  scrollMessagesToBottom();
  input.value = "";

  try {
    const response = await streamAgentChat(
      [{ role: "user", content: text }],
      state.user.id,
      state.currentConversationId,
      state.currentIndexId
    );
    await consumeEventStream(response, handleStreamEvent);
    await refreshConversationMessages();
    await refreshConversations(false);
  } catch (error) {
    updateLastAssistantMessage(`请求失败：${error.message || "未知错误"}`);
    const messages = state.messagesByConversation[state.currentConversationId] || [];
    const last = messages[messages.length - 1];
    if (last) {
      last.pending = false;
    }
    errorEl.textContent = error.message || "发送失败";
    errorEl.classList.remove("hidden");
  } finally {
    state.isLoading = false;
    render();
    scrollMessagesToBottom();
  }
}

function handleStreamEvent(payload) {
  if (typeof payload === "string") {
    appendToLastAssistantMessage(payload);
    return;
  }

  if (payload.type === "route") {
    const labels = {
      chat: "普通回答",
      search: "联网搜索",
      rag: "文档检索",
    };
    state.routeLabel = labels[payload.route] || "自动路由";
    state.routeReason = payload.reason || "";
    state.thinkingVisible = true;
    state.thinkingStatus = "正在思考中...";
    replaceThinkingLine(
      "路由决策",
      `${state.routeLabel}${payload.reason ? `：${payload.reason}` : ""}`
    );
    render();
    scrollMessagesToBottom();
    return;
  }

  if (payload.type === "thinking") {
    state.thinkingVisible = true;
    state.thinkingStatus = "正在思考中...";
    replaceThinkingLine(payload.label || "中间过程", payload.content || "");
    render();
    scrollMessagesToBottom();
    return;
  }

  if (payload.type === "sources") {
    state.sources = payload.sources || [];
    state.thinkingVisible = true;
    state.thinkingStatus = "正在整理检索结果...";
    replaceThinkingLine(
      payload.route === "search" ? "联网搜索结果" : "文档检索结果",
      summarizeSources(payload.sources || [])
    );
    render();
    scrollMessagesToBottom();
    return;
  }

  if (payload.type === "content") {
    state.thinkingVisible = false;
    state.thinkingStatus = "";
    state.thinkingLogs = [];
    appendToLastAssistantMessage(payload.content || "");
  }
}

function replaceThinkingLine(label, content) {
  const next = state.thinkingLogs.filter((item) => item.label !== label && item.label !== "状态");
  state.thinkingLogs = [
    {
      label: "状态",
      content: state.thinkingStatus || "正在思考中...",
    },
    ...next,
    { label, content },
  ];
}

function summarizeSources(items) {
  if (!items.length) {
    return "未检索到可用内容。";
  }
  return items
    .map((item, index) => {
      if (item.url) {
        return `${index + 1}. ${item.title || item.url}`;
      }
      return `${index + 1}. ${item.source || "文档片段"}（页码：${item.page || "未知"}）`;
    })
    .join("\n");
}

async function refreshConversationMessages() {
  if (!state.currentConversationId) {
    return;
  }

  const messages = await getConversationMessages(
    state.currentConversationId,
    state.user.id
  );
  state.messagesByConversation[state.currentConversationId] = messages;
}

function pushMessage(message) {
  if (!state.messagesByConversation[state.currentConversationId]) {
    state.messagesByConversation[state.currentConversationId] = [];
  }
  state.messagesByConversation[state.currentConversationId].push(message);
}

function pushSystemMessage(content) {
  pushMessage({ sender: "system", content });
}

function updateLastAssistantMessage(content) {
  const messages = state.messagesByConversation[state.currentConversationId] || [];
  const last = messages[messages.length - 1];
  if (last && last.sender === "assistant") {
    last.content = content;
    last.pending = false;
  }
}

function appendToLastAssistantMessage(content) {
  const messages = state.messagesByConversation[state.currentConversationId] || [];
  const last = messages[messages.length - 1];
    if (last && last.sender === "assistant") {
      if (last.pending) {
        last.content = "";
        last.pending = false;
      }
      last.content += content;
      const messagesEl = document.getElementById("messages");
      if (messagesEl) {
        const assistantNodes = messagesEl.querySelectorAll(".message.assistant");
        const currentNode = assistantNodes[assistantNodes.length - 1];
        if (currentNode) {
          currentNode.textContent = last.content;
          currentNode.classList.remove("pending");
        }
      }
      scrollMessagesToBottom();
    }
  }

async function consumeEventStream(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";

    for (const part of parts) {
      const lines = part
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim());

      for (const line of lines) {
        if (!line) {
          continue;
        }
        try {
          onEvent(JSON.parse(line));
        } catch {
          onEvent(line);
        }
      }
    }
  }
}

function scrollMessagesToBottom() {
  requestAnimationFrame(() => {
    const container = document.getElementById("messages");
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  });
}

function logout(rerender = true) {
  localStorage.removeItem("token");
  localStorage.removeItem("conversation_id");
  state.token = "";
  state.user = null;
  state.conversations = [];
  state.currentConversationId = null;
  state.messagesByConversation = {};
  state.currentIndexId = null;
  state.routeLabel = "自动路由";
  state.routeReason = "";
  state.sources = [];
  state.weather = null;
  state.thinkingVisible = false;
  state.thinkingStatus = "";
  state.thinkingLogs = [];
  if (rerender) {
    render();
  }
}

async function bootstrap() {
  if (!state.token) {
    render();
    return;
  }

  try {
    await bootstrapUser();
    await refreshWeather();
    render();
  } catch {
    render();
  }
}

bootstrap();
