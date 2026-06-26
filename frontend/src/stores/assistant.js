import { computed, nextTick, reactive } from "vue";
import { defineStore } from "pinia";
import {
  clearUserProfile,
  createConversation,
  createWorkspaceFolder,
  deleteConversation,
  deleteDocument,
  getAssistantSettings,
  getConversationMessages,
  getConversations,
  getCurrentUser,
  getDashboardStats,
  getDocuments,
  getUserProfile,
  getWeather,
  getWorkspaceInfo,
  login,
  register,
  renameConversation,
  scanWorkspaceFolder,
  streamAgentChat,
  truncateConversationMessages,
  updateAssistantSettings,
  uploadKnowledgeFile,
} from "../api/client.js";

const CURRENT_USER_CITY_KEY = "CURRENT_USER_CITY";
const ATTACHMENTS_KEY = "conversation_attachments";
const LOCAL_SETTINGS_KEY = "assistant_runtime_settings";
const GENERATION_TIMEOUT_MS = 120000;

function loadJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key) || "") || fallback;
  } catch {
    return fallback;
  }
}

function saveJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function saveCachedCity(city) {
  const next = String(city || "").trim();
  if (next) {
    localStorage.setItem(CURRENT_USER_CITY_KEY, next);
  }
}

function normalizeMessage(message) {
  return {
    ...message,
    sender: message.sender || message.role || "assistant",
  };
}

function createDefaultSettings() {
  return {
    model: "env:CHAT_MODEL_NAME",
    temperature: 0.7,
    enable_search: true,
    response_style: "balanced",
  };
}

function formatRouteLabel(route) {
  const routeMap = {
    chat: "普通回答",
    search: "联网搜索",
    rag: "文档检索",
    weather: "天气工具",
    workspace: "工作区检索",
    hybrid: "混合检索",
  };
  return routeMap[route] || "自动路由";
}

function formatStageLabel(stage) {
  const stageMap = {
    routing: "路由规划",
    planning: "路由规划",
    research: "工具执行",
    response: "答案生成",
    memory: "记忆更新",
    recovery: "恢复处理",
  };
  return stageMap[stage] || "执行过程";
}

function formatTraceStatus(status) {
  const statusMap = {
    pending: "等待中",
    running: "执行中",
    completed: "已完成",
    failed: "失败",
    skipped: "已跳过",
    retrying: "重试中",
  };
  return statusMap[status] || "执行中";
}

function createTraceEntry(payload = {}) {
  const stage = payload.stage || "research";
  const title = payload.title || formatStageLabel(stage);
  const detail = payload.detail || payload.content || "";
  const attempt = Number(payload.attempt || 1);
  const tool = payload.tool || "";
  const status = payload.status || "completed";
  const timestamp = payload.timestamp || new Date().toISOString();

  return {
    key: `${stage}:${tool}:${title}:${attempt}`,
    stage,
    stageLabel: formatStageLabel(stage),
    title,
    detail,
    tool,
    attempt,
    status,
    statusLabel: formatTraceStatus(status),
    timestamp,
  };
}

function summarizeSources(items) {
  if (!items.length) {
    return "本轮没有拿到可用的外部证据。";
  }

  return items
    .map((item, index) => {
      if (item.url) {
        return `${index + 1}. ${item.title || item.url}`;
      }
      const page = item.page || "未知页码";
      return `${index + 1}. ${item.source || "文档片段"}（页码：${page}）`;
    })
    .join("\n");
}

export const useAssistantStore = defineStore("assistant", () => {
  const state = reactive({
    token: localStorage.getItem("token") || "",
    user: null,

    conversations: [],
    conversationSearch: "",
    currentConversationId: Number(localStorage.getItem("conversation_id")) || null,
    messagesByConversation: {},

    attachments: loadJson(ATTACHMENTS_KEY, {}),
    currentIndexId: null,
    documents: [],
    documentsLoading: false,
    documentsError: "",

    settings: {
      ...createDefaultSettings(),
      ...loadJson(LOCAL_SETTINGS_KEY, {}),
    },
    settingsSaving: false,
    settingsError: "",
    settingsSavedAt: "",

    dashboard: {
      qa_count: 0,
      search_count: 0,
      document_count: 0,
      avg_response_time_ms: 0,
    },
    dashboardLoading: false,
    dashboardError: "",

    userProfile: {
      preferences: [],
    },
    profileLoading: false,
    profileError: "",

    workspace: {
      root: "",
      folders: [],
      indexed_files: [],
      active_folder: "",
      index_id: null,
    },
    workspaceLoading: false,
    workspaceError: "",
    workspaceFolderName: "assistant_workspace",

    sources: [],
    routeLabel: "自动路由",
    routeReason: "",
    weather: null,

    thinkingVisible: false,
    thinkingCollapsed: false,
    thinkingStatus: "",
    thinkingLogs: [],
    lastThinkingStatus: "",
    lastThinkingLogs: [],
    lastThinkingUpdatedAt: "",

    isLoading: false,
    composerInput: "",
    composerError: "",
    streamAbortController: null,
    streamAbortReason: "",
    streamTimeoutId: null,

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
  });

  const currentMessages = computed(
    () => state.messagesByConversation[state.currentConversationId] || []
  );

  const filteredConversations = computed(() => {
    const keyword = state.conversationSearch.trim().toLowerCase();
    if (!keyword) {
      return state.conversations;
    }
    return state.conversations.filter((item) =>
      `${item.title || ""} ${item.created_at || ""} ${item.updated_at || ""}`
        .toLowerCase()
        .includes(keyword)
    );
  });

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
        loading: false,
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

  const activeThinkingLogs = computed(() =>
    state.thinkingVisible ? state.thinkingLogs : state.lastThinkingLogs
  );

  const activeThinkingStatus = computed(() =>
    state.thinkingVisible ? state.thinkingStatus : state.lastThinkingStatus
  );

  const hasThinkingRecord = computed(
    () => state.thinkingVisible || state.lastThinkingLogs.length > 0
  );

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

  function resetThinkingPanel() {
    state.thinkingVisible = false;
    state.thinkingStatus = "";
    state.thinkingLogs = [];
  }

  function snapshotThinkingPanel() {
    if (!state.thinkingLogs.length) {
      return;
    }
    state.lastThinkingLogs = state.thinkingLogs.map((item) => ({ ...item }));
    state.lastThinkingStatus = state.thinkingStatus;
    state.lastThinkingUpdatedAt = new Date().toISOString();
  }

  function openThinkingPanel(status = "正在思考中...") {
    state.thinkingVisible = true;
    state.thinkingCollapsed = false;
    state.thinkingStatus = status;
  }

  function upsertThinkingEntry(payload) {
    const entry = createTraceEntry(payload);
    const existingIndex = state.thinkingLogs.findIndex(
      (item) => item.key === entry.key
    );

    if (existingIndex >= 0) {
      state.thinkingLogs.splice(existingIndex, 1, entry);
    } else {
      state.thinkingLogs.push(entry);
    }
  }

  function setThinkingStatusByStage(stage, status) {
    if (status === "failed") {
      state.thinkingStatus = "本轮有步骤执行失败，正在尝试恢复...";
      return;
    }

    const stageStatusMap = {
      routing: "Router 正在规划执行步骤...",
      planning: "Router 正在规划执行步骤...",
      research: "Research Agent 正在调用工具并整理证据...",
      response: "Response Agent 正在组织最终回答...",
      memory: "Memory Agent 正在更新长期记忆...",
      recovery: "正在执行兜底恢复逻辑...",
    };

    state.thinkingStatus =
      stageStatusMap[stage] || (status === "completed" ? "步骤已完成" : "正在思考中...");
  }

  function buildRuntimeOptions() {
    return {
      ...state.settings,
      knowledge_source_type: currentAttachment.value?.type || "document",
      attachment_name: currentAttachment.value?.filename || "",
    };
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
    await Promise.allSettled([
      refreshConversations(true),
      refreshDocuments(),
      refreshSettings(),
      refreshDashboard(),
      refreshUserProfile(),
      refreshWorkspace(),
    ]);
  }

  async function refreshConversations(ensureCurrent) {
    if (!state.user?.id) {
      return;
    }

    state.conversations = await getConversations(state.user.id);

    if (!state.conversations.length) {
      state.currentConversationId = null;
      localStorage.removeItem("conversation_id");
      return;
    }

    if (
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

  async function refreshDocuments() {
    if (!state.user?.id) {
      return;
    }
    state.documentsLoading = true;
    state.documentsError = "";
    try {
      state.documents = await getDocuments(state.user.id);
    } catch (error) {
      state.documentsError = error.message || "文档列表获取失败";
    } finally {
      state.documentsLoading = false;
    }
  }

  async function refreshSettings() {
    if (!state.user?.id) {
      return;
    }
    state.settingsError = "";
    try {
      const remote = await getAssistantSettings(state.user.id);
      state.settings = {
        ...createDefaultSettings(),
        ...remote,
        ...loadJson(LOCAL_SETTINGS_KEY, {}),
      };
    } catch {
      state.settings = {
        ...createDefaultSettings(),
        ...loadJson(LOCAL_SETTINGS_KEY, {}),
      };
    }
  }

  async function saveSettings(nextSettings) {
    state.settingsSaving = true;
    state.settingsError = "";
    state.settings = {
      ...state.settings,
      ...nextSettings,
    };
    saveJson(LOCAL_SETTINGS_KEY, state.settings);
    try {
      if (state.user?.id) {
        state.settings = await updateAssistantSettings(state.user.id, state.settings);
      }
      state.settingsSavedAt = new Date().toISOString();
    } catch (error) {
      state.settingsError = error.message || "设置保存失败，已先保存在本地。";
    } finally {
      state.settingsSaving = false;
    }
  }

  async function refreshDashboard() {
    if (!state.user?.id) {
      return;
    }
    state.dashboardLoading = true;
    state.dashboardError = "";
    try {
      state.dashboard = await getDashboardStats(state.user.id);
    } catch (error) {
      state.dashboardError = error.message || "统计数据获取失败";
    } finally {
      state.dashboardLoading = false;
    }
  }

  async function refreshUserProfile() {
    if (!state.user?.id) {
      return;
    }
    state.profileLoading = true;
    state.profileError = "";
    try {
      state.userProfile = await getUserProfile(state.user.id);
    } catch (error) {
      state.profileError = error.message || "用户记忆获取失败";
    } finally {
      state.profileLoading = false;
    }
  }

  async function handleClearUserProfile() {
    if (!state.user?.id) {
      return;
    }
    const confirmed = window.confirm("确认清空用户画像记忆吗？");
    if (!confirmed) {
      return;
    }
    state.userProfile = await clearUserProfile(state.user.id);
  }

  async function refreshWorkspace() {
    if (!state.user?.id) {
      return;
    }
    state.workspaceLoading = true;
    state.workspaceError = "";
    try {
      state.workspace = await getWorkspaceInfo(state.user.id);
    } catch (error) {
      state.workspaceError = error.message || "工作区信息获取失败";
    } finally {
      state.workspaceLoading = false;
    }
  }

  async function handleCreateWorkspaceFolder() {
    if (!state.user?.id) {
      return;
    }
    state.workspaceLoading = true;
    state.workspaceError = "";
    try {
      state.workspace = await createWorkspaceFolder(
        state.user.id,
        state.workspaceFolderName
      );
    } catch (error) {
      state.workspaceError = error.message || "创建工作区失败";
    } finally {
      state.workspaceLoading = false;
    }
  }

  async function handleScanWorkspaceFolder(folderPath) {
    if (!state.user?.id) {
      return;
    }
    state.workspaceLoading = true;
    state.workspaceError = "";
    try {
      const result = await scanWorkspaceFolder(state.user.id, folderPath);
      state.workspace = result.workspace;
      state.currentIndexId = result.index_id || state.currentIndexId;
      if (state.currentConversationId && result.index_id) {
        state.attachments[String(state.currentConversationId)] = {
          indexId: result.index_id,
          filename: result.folder_name || "本地工作区",
          chunks: result.chunks || 0,
          type: "workspace",
        };
        saveJson(ATTACHMENTS_KEY, state.attachments);
      }
    } catch (error) {
      state.workspaceError = error.message || "工作区索引失败";
    } finally {
      state.workspaceLoading = false;
    }
  }

  async function switchConversation(conversationId, rerender = true) {
    state.currentConversationId = conversationId;
    localStorage.setItem("conversation_id", String(conversationId));
    state.currentIndexId = state.attachments[String(conversationId)]?.indexId || null;
    state.routeLabel = "自动路由";
    state.routeReason = "";
    state.sources = [];
    resetThinkingPanel();

    if (!state.messagesByConversation[conversationId]) {
      const messages = await getConversationMessages(conversationId, state.user.id);
      state.messagesByConversation[conversationId] = messages.map(normalizeMessage);
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
    await switchConversation(state.currentConversationId, false);
  }

  async function ensureActiveConversation() {
    if (state.currentConversationId) {
      return state.currentConversationId;
    }
    const data = await createConversation(state.user.id);
    state.currentConversationId = data.conversation_id;
    localStorage.setItem("conversation_id", String(state.currentConversationId));
    state.messagesByConversation[state.currentConversationId] = [];
    await refreshConversations(false);
    return state.currentConversationId;
  }

  async function selectConversation(id) {
    await switchConversation(id);
  }

  async function handleDeleteConversation(conversationId) {
    const current = state.conversations.find((item) => item.id === conversationId);
    const confirmed = window.confirm(
      `确认删除会话“${current?.title || "未命名会话"}”吗？删除后历史消息也会一起移除。`
    );
    if (!confirmed) {
      return;
    }

    await deleteConversation(conversationId);
    delete state.messagesByConversation[conversationId];
    delete state.attachments[String(conversationId)];
    saveJson(ATTACHMENTS_KEY, state.attachments);
    state.conversations = state.conversations.filter((item) => item.id !== conversationId);

    if (state.currentConversationId === conversationId) {
      state.currentConversationId = state.conversations[0]?.id || null;
      if (state.currentConversationId) {
        localStorage.setItem("conversation_id", String(state.currentConversationId));
      } else {
        localStorage.removeItem("conversation_id");
      }
    }

    if (state.currentConversationId) {
      await switchConversation(state.currentConversationId, false);
    }

    await refreshDashboard();
  }

  async function handleRenameConversation(payload) {
    const target =
      typeof payload === "object" && payload !== null
        ? payload
        : { id: payload, name: "" };
    const nextName = String(target.name || "").trim();
    if (!target.id || !nextName) {
      return;
    }
    await renameConversation(target.id, nextName);
    const current = state.conversations.find((item) => item.id === target.id);
    if (current) {
      current.title = nextName;
    }
    await refreshConversations(false);
  }

  function pushMessage(message) {
    if (!state.messagesByConversation[state.currentConversationId]) {
      state.messagesByConversation[state.currentConversationId] = [];
    }
    state.messagesByConversation[state.currentConversationId].push(normalizeMessage(message));
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

  async function refreshConversationMessages() {
    if (!state.currentConversationId || !state.user?.id) {
      return;
    }
    const messages = await getConversationMessages(
      state.currentConversationId,
      state.user.id
    );
    state.messagesByConversation[state.currentConversationId] =
      messages.map(normalizeMessage);
  }

  // 读取后端 SSE 响应。
  // 后端不是一次返回完整 JSON，而是持续写出 data: {...}\n\n。
  // 这里通过 ReadableStream 的 reader 持续取 chunk，再按 SSE 边界拆开。
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

  function handlePlanEvent(payload) {
    const plan = payload.plan || payload;
    state.routeLabel = formatRouteLabel(plan.route);
    state.routeReason = plan.reason || "";
    openThinkingPanel("Router 正在规划执行步骤...");
    upsertThinkingEntry({
      stage: "routing",
      title: "Router 输出执行计划",
      detail: [
        `目标：${plan.objective || "完成本轮问题处理"}`,
        `路由：${state.routeLabel}`,
        `工具：${Array.isArray(plan.tools) && plan.tools.length ? plan.tools.join("、") : "无"}`,
        plan.reason ? `原因：${plan.reason}` : "",
      ]
        .filter(Boolean)
        .join("\n"),
      status: "completed",
    });
  }

  function handleTraceEvent(payload) {
    openThinkingPanel();
    setThinkingStatusByStage(payload.stage, payload.status);
    upsertThinkingEntry(payload);
  }

  function handleSourcesEvent(payload) {
    state.sources = payload.sources || [];
    openThinkingPanel("Research Agent 正在整理证据...");
    upsertThinkingEntry({
      stage: "research",
      title: "证据整理完成",
      detail: summarizeSources(state.sources),
      status: "completed",
      tool: payload.route || "",
    });
  }

  function handleContentEvent(payload) {
    if (state.thinkingVisible && state.thinkingLogs.length) {
      snapshotThinkingPanel();
    }
    state.thinkingVisible = false;
    state.thinkingStatus = "";
    state.thinkingLogs = [];
    appendToLastAssistantMessage(payload.content || "");
    scrollMessagesToBottom();
  }

  function handleStreamEvent(payload) {
    if (typeof payload === "string") {
      appendToLastAssistantMessage(payload);
      scrollMessagesToBottom();
      return;
    }

    if (payload.type === "plan") {
      handlePlanEvent(payload);
      scrollMessagesToBottom();
      return;
    }

    if (payload.type === "route") {
      state.routeLabel = formatRouteLabel(payload.route);
      state.routeReason = payload.reason || "";
      return;
    }

    if (payload.type === "thinking" || payload.type === "trace") {
      handleTraceEvent(payload);
      scrollMessagesToBottom();
      return;
    }

    if (payload.type === "sources") {
      handleSourcesEvent(payload);
      scrollMessagesToBottom();
      return;
    }

    if (payload.type === "content") {
      handleContentEvent(payload);
    }
  }

  function handleStopGeneration(reason = "manual") {
    if (!state.streamAbortController) {
      return;
    }
    state.streamAbortReason = reason;
    state.streamAbortController.abort();
  }

  async function truncateBeforeResend(messageIndex) {
    if (messageIndex == null || messageIndex < 0) {
      return;
    }
    const message = currentMessages.value[messageIndex];
    if (message?.id) {
      await truncateConversationMessages(
        state.currentConversationId,
        message.id,
        state.user.id
      );
    }
    state.messagesByConversation[state.currentConversationId] =
      currentMessages.value.slice(0, messageIndex);
  }

  async function sendTextMessage(text, options = {}) {
    const content = String(text || "").trim();
    if (!content || state.isLoading) {
      return;
    }

    state.composerError = "";

    try {
      await ensureActiveConversation();
      await truncateBeforeResend(options.trimFromIndex);

      state.sources = [];
      openThinkingPanel("Router 正在规划执行步骤...");
      state.thinkingLogs = [];
      state.isLoading = true;

      // 先写本地用户消息，让页面立刻有反馈。
      pushMessage({ sender: "user", content });

      // 再放一条 assistant 占位消息，后续流式正文会持续追加到这条消息里。
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
        [{ role: "user", content }],
        state.user.id,
        state.currentConversationId,
        state.currentIndexId,
        buildRuntimeOptions(),
        state.streamAbortController.signal
      );

      await consumeEventStream(response, (payload) => handleStreamEvent(payload));

      await refreshConversationMessages();
      await refreshConversations(false);
      await Promise.allSettled([
        refreshDashboard(),
        refreshDocuments(),
        refreshUserProfile(),
      ]);
    } catch (error) {
      const reason = state.streamAbortReason;

      if (reason === "manual") {
        snapshotThinkingPanel();
        resetThinkingPanel();
        finalizeInterruptedResponse("本轮回答已手动停止。");
      } else if (reason === "timeout") {
        snapshotThinkingPanel();
        resetThinkingPanel();
        finalizeInterruptedResponse("本轮回答因超时已停止，你可以继续追问或重新发送。");
        state.composerError = "生成超时，已停止本轮回答";
      } else if (error?.name === "AbortError") {
        snapshotThinkingPanel();
        resetThinkingPanel();
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

  async function handleSendMessage() {
    await sendTextMessage(state.composerInput);
  }

  async function handleRegenerateMessage(messageIndex) {
    if (state.isLoading) {
      return;
    }

    let userIndex = messageIndex;
    while (userIndex >= 0 && currentMessages.value[userIndex]?.sender !== "user") {
      userIndex -= 1;
    }

    const userMessage = currentMessages.value[userIndex];
    if (!userMessage?.content) {
      return;
    }

    await sendTextMessage(userMessage.content, { trimFromIndex: userIndex });
  }

  async function handleEditAndResend({ index, content }) {
    if (state.isLoading) {
      return;
    }
    const nextContent = String(content || "").trim();
    if (!nextContent) {
      return;
    }
    await sendTextMessage(nextContent, { trimFromIndex: index });
  }

  async function copyMessageContent(message) {
    const content = String(message?.content || "");
    if (!content) {
      return;
    }
    await navigator.clipboard.writeText(content);
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
      type: "document",
    };
    saveJson(ATTACHMENTS_KEY, state.attachments);
    pushSystemMessage(
      `已完成文档解析：${result.original_name || result.filename}，共生成 ${result.chunks} 个文本片段。现在你可以直接围绕这份文档提问。`
    );
    await Promise.allSettled([refreshDocuments(), refreshDashboard()]);
    await scrollMessagesToBottom();
  }

  async function handleDeleteDocument(documentId) {
    const confirmed = window.confirm("确认删除这份文档吗？删除后将不再用于后续检索。");
    if (!confirmed) {
      return;
    }
    await deleteDocument(documentId, state.user.id);
    state.documents = state.documents.filter((item) => item.id !== documentId);
    await refreshDashboard();
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
    saveJson(ATTACHMENTS_KEY, state.attachments);
    state.currentIndexId = null;
    state.sources = [];
    state.routeLabel = "自动路由";
    state.routeReason = "当前会话已移除文档上下文，后续提问将不再使用这份文档检索。";
    pushSystemMessage(`已移除文档：${attachment.filename}`);
    await scrollMessagesToBottom();
  }

  function toggleThinkingCollapsed() {
    state.thinkingCollapsed = !state.thinkingCollapsed;
  }

  function clearLastThinking() {
    state.lastThinkingLogs = [];
    state.lastThinkingStatus = "";
    state.lastThinkingUpdatedAt = "";
    if (!state.thinkingVisible) {
      state.thinkingCollapsed = false;
    }
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
    resetThinkingPanel();
    state.lastThinkingStatus = "";
    state.lastThinkingLogs = [];
    state.lastThinkingUpdatedAt = "";
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
    localStorage.getItem(CURRENT_USER_CITY_KEY);
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

  return {
    state,
    currentMessages,
    filteredConversations,
    currentAttachment,
    currentConversationTitle,
    weatherCard,
    activeThinkingLogs,
    activeThinkingStatus,
    hasThinkingRecord,
    formatDate,
    handleLogin,
    handleRegister,
    refreshWeather,
    refreshDocuments,
    refreshSettings,
    saveSettings,
    refreshDashboard,
    refreshUserProfile,
    handleClearUserProfile,
    refreshWorkspace,
    handleCreateWorkspaceFolder,
    handleScanWorkspaceFolder,
    switchConversation,
    handleCreateConversation,
    selectConversation,
    handleDeleteConversation,
    handleRenameConversation,
    handleSendMessage,
    handleRegenerateMessage,
    handleEditAndResend,
    copyMessageContent,
    handleComposerKeydown,
    handleUploadFile,
    handleDeleteDocument,
    handleRemoveAttachment,
    handleStopGeneration,
    toggleThinkingCollapsed,
    clearLastThinking,
    logout,
    bootstrap,
    scrollMessagesToBottom,
  };
});
