import { computed, nextTick, reactive } from "vue";
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
} from "../api/client.js";

const CURRENT_USER_CITY_KEY = "CURRENT_USER_CITY";
const GENERATION_TIMEOUT_MS = 120000;

function loadAttachments() {
  try {
    return JSON.parse(localStorage.getItem("conversation_attachments") || "{}");
  } catch {
    return {};
  }
}

function saveAttachments(attachments) {
  localStorage.setItem("conversation_attachments", JSON.stringify(attachments));
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

const state = reactive({
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
  streamAbortController: null,
  streamAbortReason: "",
  streamTimeoutId: null,
  composerInput: "",
  loginForm: {
    email: "",
    password: "",
  },
  registerForm: {
    username: "",
    email: "",
    password: "",
  },
  loginError: "",
  registerError: "",
  registerSuccess: "",
  composerError: "",
});

const currentMessages = computed(
  () => state.messagesByConversation[state.currentConversationId] || []
);

const currentAttachment = computed(() =>
  state.currentConversationId
    ? state.attachments[String(state.currentConversationId)] || null
    : null
);

const currentConversationTitle = computed(() => {
  const current = state.conversations.find(
    (item) => item.id === state.currentConversationId
  );
  return current?.title || "新对话";
});

const weatherCard = computed(() => {
  if (!state.weather) {
    return {
      city: "正在获取天气",
      text: "请稍候，正在同步当前城市天气...",
      meta: "",
      loading: true,
    };
  }
  if (state.weather.error) {
    return {
      city: "天气暂不可用",
      text: state.weather.error,
      meta: "",
      loading: true,
    };
  }
  const temp =
    typeof state.weather.temperature_c === "number"
      ? `${state.weather.temperature_c}°C`
      : "--";
  const feels =
    typeof state.weather.feelslike_c === "number"
      ? `体感 ${state.weather.feelslike_c}°C`
      : "";
  return {
    city: `当前城市：${state.weather.city_name || "未知"}`,
    text: state.weather.weather_text || "天气信息已更新",
    meta: feels ? `${temp} · ${feels}` : temp,
    loading: false,
  };
});

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

async function scrollMessagesToBottom() {
  await nextTick();
  const container = document.getElementById("messages");
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

async function handleLogin() {
  state.loginError = "";
  const data = await login({
    email: String(state.loginForm.email || "").trim(),
    password: String(state.loginForm.password || ""),
  });
  state.token = data.access_token;
  localStorage.setItem("token", state.token);
  await bootstrapUser();
  await refreshWeather();
}

async function handleRegister() {
  state.registerError = "";
  state.registerSuccess = "";
  await register({
    username: String(state.registerForm.username || "").trim(),
    email: String(state.registerForm.email || "").trim(),
    password: String(state.registerForm.password || ""),
  });
  state.registerSuccess = "注册成功，请直接登录。";
  state.registerForm = { username: "", email: "", password: "" };
}

async function bootstrapUser() {
  state.user = await getCurrentUser();
  await refreshConversations(true);
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
    await scrollMessagesToBottom();
  }
}

async function handleCreateConversation() {
  const data = await createConversation(state.user.id);
  state.currentConversationId = data.conversation_id;
  localStorage.setItem("conversation_id", String(state.currentConversationId));
  await refreshConversations(false);
}

async function ensureActiveConversation() {
  if (state.currentConversationId) {
    return state.currentConversationId;
  }
  const data = await createConversation(state.user.id);
  state.currentConversationId = data.conversation_id;
  localStorage.setItem("conversation_id", String(state.currentConversationId));
  await refreshConversations(false);
  return state.currentConversationId;
}

async function selectConversation(id) {
  await switchConversation(id);
}

async function handleDeleteConversation(conversationId) {
  await deleteConversation(conversationId);
  delete state.messagesByConversation[conversationId];
  delete state.attachments[String(conversationId)];
  saveAttachments(state.attachments);
  state.conversations = state.conversations.filter((item) => item.id !== conversationId);
  if (state.currentConversationId === conversationId) {
    state.currentConversationId = state.conversations[0]?.id || null;
    localStorage.setItem("conversation_id", String(state.currentConversationId || ""));
  }
  if (state.currentConversationId) {
    await switchConversation(state.currentConversationId, false);
  }
}

async function handleRenameConversation(conversationId) {
  const current = state.conversations.find((item) => item.id === conversationId);
  const nextName = window.prompt("请输入新的会话名", current?.title || "");
  if (!nextName) {
    return;
  }
  await renameConversation(conversationId, nextName);
  await refreshConversations(false);
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
  const last = currentMessages.value[currentMessages.value.length - 1];
  if (last && last.sender === "assistant") {
    last.content = content;
    last.pending = false;
  }
}

function appendToLastAssistantMessage(content) {
  const last = currentMessages.value[currentMessages.value.length - 1];
  if (last && last.sender === "assistant") {
    if (last.pending) {
      last.content = "";
      last.pending = false;
    }
    last.content += content;
  }
}

function finalizeInterruptedResponse(note) {
  const last = currentMessages.value[currentMessages.value.length - 1];
  if (!last || last.sender !== "assistant") {
    pushSystemMessage(note);
    return;
  }
  if (last.pending || !last.content || last.content === "正在思考中...") {
    last.content = note;
    last.pending = false;
    return;
  }
  last.pending = false;
  pushSystemMessage(note);
}

function replaceThinkingLine(label, content) {
  const next = state.thinkingLogs.filter(
    (item) => item.label !== label && item.label !== "状态"
  );
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

function handleStreamEvent(payload) {
  if (typeof payload === "string") {
    appendToLastAssistantMessage(payload);
    scrollMessagesToBottom();
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
    scrollMessagesToBottom();
    return;
  }
  if (payload.type === "thinking") {
    state.thinkingVisible = true;
    state.thinkingStatus = "正在思考中...";
    replaceThinkingLine(payload.label || "中间过程", payload.content || "");
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
    scrollMessagesToBottom();
    return;
  }
  if (payload.type === "content") {
    state.thinkingVisible = false;
    state.thinkingStatus = "";
    state.thinkingLogs = [];
    appendToLastAssistantMessage(payload.content || "");
    scrollMessagesToBottom();
  }
}

function handleStopGeneration(reason = "manual") {
  if (!state.streamAbortController) {
    return;
  }
  state.streamAbortReason = reason;
  state.streamAbortController.abort();
}

async function handleSendMessage() {
  const text = state.composerInput.trim();
  if (!text || state.isLoading) {
    return;
  }
  state.composerError = "";
  try {
    await ensureActiveConversation();
    state.sources = [];
    state.thinkingVisible = true;
    state.thinkingStatus = "正在思考中...";
    state.thinkingLogs = [{ label: "状态", content: "正在思考中..." }];
    state.isLoading = true;
    pushMessage({ sender: "user", content: text });
    pushMessage({
      sender: "assistant",
      content: "正在思考中...",
      pending: true,
    });
    state.composerInput = "";
    await scrollMessagesToBottom();

    state.streamAbortReason = "";
    state.streamAbortController = new AbortController();
    state.streamTimeoutId = window.setTimeout(() => {
      handleStopGeneration("timeout");
    }, GENERATION_TIMEOUT_MS);

    const response = await streamAgentChat(
      [{ role: "user", content: text }],
      state.user.id,
      state.currentConversationId,
      state.currentIndexId,
      state.streamAbortController.signal
    );
    await consumeEventStream(response, (payload) => handleStreamEvent(payload));
    await refreshConversationMessages();
    await refreshConversations(false);
  } catch (error) {
    const reason = state.streamAbortReason;
    if (reason === "manual") {
      finalizeInterruptedResponse("本轮回答已手动停止。");
    } else if (reason === "timeout") {
      finalizeInterruptedResponse("本轮回答因超时已停止，你可以继续追问或重新发送。");
      state.composerError = "生成超时，已停止本轮回答";
    } else if (error?.name === "AbortError") {
      finalizeInterruptedResponse("本轮回答已中断。");
    } else {
      updateLastAssistantMessage(`请求失败：${error.message || "未知错误"}`);
      const last = currentMessages.value[currentMessages.value.length - 1];
      if (last) {
        last.pending = false;
      }
      state.composerError =
        error.message?.includes("Failed to fetch") || error.message?.includes("Network")
          ? "网络连接中断，请检查网络后重试"
          : error.message || "发送失败";
    }
  } finally {
    if (state.streamTimeoutId) {
      clearTimeout(state.streamTimeoutId);
      state.streamTimeoutId = null;
    }
    state.streamAbortController = null;
    state.streamAbortReason = "";
    state.isLoading = false;
    await scrollMessagesToBottom();
  }
}

async function handleComposerKeydown(event) {
  if (event.key !== "Enter" || event.shiftKey) {
    return;
  }
  const value = typeof event.target?.value === "string" ? event.target.value.trim() : "";
  if (!value || state.isLoading) {
    return;
  }
  event.preventDefault();
  await handleSendMessage();
}

async function handleUploadFile(file) {
  if (!file) {
    return;
  }
  state.composerError = "";
  await ensureActiveConversation();
  const result = await uploadKnowledgeFile(file, state.user.id);
  state.currentIndexId = result.index_id;
  state.attachments[String(state.currentConversationId)] = {
    indexId: result.index_id,
    filename: result.original_name || result.filename,
    chunks: result.chunks,
  };
  saveAttachments(state.attachments);
  pushSystemMessage(
    `已完成文档解析：${result.original_name || result.filename}，共生成 ${result.chunks} 个文本片段。现在你可以直接围绕这份文档提问。`
  );
  await scrollMessagesToBottom();
}

async function handleRemoveAttachment() {
  if (!state.currentConversationId) {
    return;
  }
  const attachment = state.attachments[String(state.currentConversationId)];
  if (!attachment) {
    return;
  }
  delete state.attachments[String(state.currentConversationId)];
  saveAttachments(state.attachments);
  state.currentIndexId = null;
  state.sources = [];
  state.routeLabel = "自动路由";
  state.routeReason = "当前会话已移除文档上下文，后续提问将不再使用这份文档检索。";
  pushSystemMessage(`已移除文档：${attachment.filename}`);
  await scrollMessagesToBottom();
}

function logout() {
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
  state.isLoading = false;
  state.composerInput = "";
  state.composerError = "";
  state.streamAbortController = null;
  state.streamAbortReason = "";
  state.loginError = "";
  state.registerError = "";
  state.registerSuccess = "";
}

async function bootstrap() {
  loadCachedCity();
  if (!state.token) {
    return false;
  }
  try {
    await bootstrapUser();
    await refreshWeather();
    return true;
  } catch {
    logout();
    return false;
  }
}

export function useAssistantApp() {
  return {
    state,
    currentMessages,
    currentAttachment,
    currentConversationTitle,
    weatherCard,
    formatDate,
    handleLogin,
    handleRegister,
    refreshWeather,
    switchConversation,
    handleCreateConversation,
    selectConversation,
    handleDeleteConversation,
    handleRenameConversation,
    handleSendMessage,
    handleComposerKeydown,
    handleUploadFile,
    handleRemoveAttachment,
    handleStopGeneration,
    logout,
    bootstrap,
    scrollMessagesToBottom,
  };
}
