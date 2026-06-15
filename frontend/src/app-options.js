import { nextTick } from "vue";
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
} from "./api/client.js";

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

export default {
  data() {
    return {
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
      showRegister: false,
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
    };
  },
  computed: {
    currentMessages() {
      return this.messagesByConversation[this.currentConversationId] || [];
    },
    currentAttachment() {
      return this.currentConversationId
        ? this.attachments[String(this.currentConversationId)] || null
        : null;
    },
    currentConversationTitle() {
      const current = this.conversations.find(
        (item) => item.id === this.currentConversationId
      );
      return current?.title || "新对话";
    },
    weatherCard() {
      if (!this.weather) {
        return {
          city: "正在获取天气",
          text: "请稍候，正在同步当前城市天气...",
          meta: "",
          loading: true,
        };
      }
      if (this.weather.error) {
        return {
          city: "天气暂不可用",
          text: this.weather.error,
          meta: "",
          loading: true,
        };
      }
      const temp = typeof this.weather.temperature_c === "number"
        ? `${this.weather.temperature_c}°C`
        : "--";
      const feels =
        typeof this.weather.feelslike_c === "number"
          ? `体感 ${this.weather.feelslike_c}°C`
          : "";
      return {
        city: `当前城市：${this.weather.city_name || "未知"}`,
        text: this.weather.weather_text || "天气信息已更新",
        meta: feels ? `${temp} · ${feels}` : temp,
        loading: false,
      };
    },
  },
  methods: {
    formatDate(value) {
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
    },
    async scrollMessagesToBottom() {
      await nextTick();
      const container = this.$refs.messages;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },
    async showAuth(loginMode = true) {
      this.showRegister = !loginMode;
      await nextTick();
    },
    async handleLogin() {
      this.loginError = "";
      try {
        const data = await login({
          email: String(this.loginForm.email || "").trim(),
          password: String(this.loginForm.password || ""),
        });
        this.token = data.access_token;
        localStorage.setItem("token", this.token);
        await this.bootstrapUser();
        await this.refreshWeather();
      } catch (error) {
        this.loginError = error.message || "登录失败";
      }
    },
    async handleRegister() {
      this.registerError = "";
      this.registerSuccess = "";
      try {
        await register({
          username: String(this.registerForm.username || "").trim(),
          email: String(this.registerForm.email || "").trim(),
          password: String(this.registerForm.password || ""),
        });
        this.registerSuccess = "注册成功，请直接登录。";
        this.registerForm = { username: "", email: "", password: "" };
      } catch (error) {
        this.registerError = error.message || "注册失败";
      }
    },
    async bootstrapUser() {
      try {
        this.user = await getCurrentUser();
        await this.refreshConversations(true);
      } catch (error) {
        this.logout(false);
        throw error;
      }
    },
    async refreshConversations(ensureCurrent) {
      this.conversations = await getConversations(this.user.id);
      if (!this.conversations.length) {
        const data = await createConversation(this.user.id);
        this.currentConversationId = data.conversation_id;
        localStorage.setItem("conversation_id", String(this.currentConversationId));
        this.conversations = await getConversations(this.user.id);
      } else if (
        ensureCurrent &&
        !this.conversations.some((item) => item.id === this.currentConversationId)
      ) {
        this.currentConversationId = this.conversations[0].id;
        localStorage.setItem("conversation_id", String(this.currentConversationId));
      }
      if (this.currentConversationId) {
        await this.switchConversation(this.currentConversationId, false);
      }
    },
    async refreshWeather() {
      try {
        this.weather = await getWeather();
        if (this.weather?.city_name) {
          saveCachedCity(this.weather.city_name);
        }
      } catch (error) {
        this.weather = {
          error: error.message || "天气获取失败",
        };
      }
    },
    async switchConversation(conversationId, rerender = true) {
      this.currentConversationId = conversationId;
      localStorage.setItem("conversation_id", String(conversationId));
      this.currentIndexId = this.attachments[String(conversationId)]?.indexId || null;
      this.routeLabel = "自动路由";
      this.routeReason = "";
      this.sources = [];
      this.thinkingVisible = false;
      this.thinkingStatus = "";
      this.thinkingLogs = [];

      if (!this.messagesByConversation[conversationId]) {
        const messages = await getConversationMessages(conversationId, this.user.id);
        this.messagesByConversation[conversationId] = messages;
      }
      if (rerender) {
        await this.scrollMessagesToBottom();
      }
    },
    async handleCreateConversation() {
      const data = await createConversation(this.user.id);
      this.currentConversationId = data.conversation_id;
      localStorage.setItem("conversation_id", String(this.currentConversationId));
      await this.refreshConversations(false);
    },
    async ensureActiveConversation() {
      if (this.currentConversationId) {
        return this.currentConversationId;
      }
      const data = await createConversation(this.user.id);
      this.currentConversationId = data.conversation_id;
      localStorage.setItem("conversation_id", String(this.currentConversationId));
      await this.refreshConversations(false);
      return this.currentConversationId;
    },
    async selectConversation(id) {
      await this.switchConversation(id);
    },
    async handleDeleteConversation(conversationId) {
      await deleteConversation(conversationId);
      delete this.messagesByConversation[conversationId];
      delete this.attachments[String(conversationId)];
      saveAttachments(this.attachments);
      this.conversations = this.conversations.filter((item) => item.id !== conversationId);
      if (this.currentConversationId === conversationId) {
        this.currentConversationId = this.conversations[0]?.id || null;
        localStorage.setItem("conversation_id", String(this.currentConversationId || ""));
      }
      if (this.currentConversationId) {
        await this.switchConversation(this.currentConversationId, false);
      }
    },
    async handleRenameConversation(conversationId) {
      const current = this.conversations.find((item) => item.id === conversationId);
      const nextName = window.prompt("请输入新的会话名", current?.title || "");
      if (!nextName) {
        return;
      }
      await renameConversation(conversationId, nextName);
      await this.refreshConversations(false);
    },
    pushMessage(message) {
      if (!this.messagesByConversation[this.currentConversationId]) {
        this.messagesByConversation[this.currentConversationId] = [];
      }
      this.messagesByConversation[this.currentConversationId].push(message);
    },
    pushSystemMessage(content) {
      this.pushMessage({ sender: "system", content });
    },
    updateLastAssistantMessage(content) {
      const last = this.currentMessages[this.currentMessages.length - 1];
      if (last && last.sender === "assistant") {
        last.content = content;
        last.pending = false;
      }
    },
    appendToLastAssistantMessage(content) {
      const last = this.currentMessages[this.currentMessages.length - 1];
      if (last && last.sender === "assistant") {
        if (last.pending) {
          last.content = "";
          last.pending = false;
        }
        last.content += content;
      }
    },
    finalizeInterruptedResponse(note) {
      const last = this.currentMessages[this.currentMessages.length - 1];
      if (!last || last.sender !== "assistant") {
        this.pushSystemMessage(note);
        return;
      }
      if (last.pending || !last.content || last.content === "正在思考中...") {
        last.content = note;
        last.pending = false;
        return;
      }
      last.pending = false;
      this.pushSystemMessage(note);
    },
    replaceThinkingLine(label, content) {
      const next = this.thinkingLogs.filter(
        (item) => item.label !== label && item.label !== "状态"
      );
      this.thinkingLogs = [
        {
          label: "状态",
          content: this.thinkingStatus || "正在思考中...",
        },
        ...next,
        { label, content },
      ];
    },
    summarizeSources(items) {
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
    },
    async refreshConversationMessages() {
      if (!this.currentConversationId) {
        return;
      }
      const messages = await getConversationMessages(
        this.currentConversationId,
        this.user.id
      );
      this.messagesByConversation[this.currentConversationId] = messages;
    },
    async consumeEventStream(response, onEvent) {
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
    },
    handleStreamEvent(payload) {
      if (typeof payload === "string") {
        this.appendToLastAssistantMessage(payload);
        this.scrollMessagesToBottom();
        return;
      }
      if (payload.type === "route") {
        const labels = {
          chat: "普通回答",
          search: "联网搜索",
          rag: "文档检索",
        };
        this.routeLabel = labels[payload.route] || "自动路由";
        this.routeReason = payload.reason || "";
        this.thinkingVisible = true;
        this.thinkingStatus = "正在思考中...";
        this.replaceThinkingLine(
          "路由决策",
          `${this.routeLabel}${payload.reason ? `：${payload.reason}` : ""}`
        );
        this.scrollMessagesToBottom();
        return;
      }
      if (payload.type === "thinking") {
        this.thinkingVisible = true;
        this.thinkingStatus = "正在思考中...";
        this.replaceThinkingLine(payload.label || "中间过程", payload.content || "");
        this.scrollMessagesToBottom();
        return;
      }
      if (payload.type === "sources") {
        this.sources = payload.sources || [];
        this.thinkingVisible = true;
        this.thinkingStatus = "正在整理检索结果...";
        this.replaceThinkingLine(
          payload.route === "search" ? "联网搜索结果" : "文档检索结果",
          this.summarizeSources(payload.sources || [])
        );
        this.scrollMessagesToBottom();
        return;
      }
      if (payload.type === "content") {
        this.thinkingVisible = false;
        this.thinkingStatus = "";
        this.thinkingLogs = [];
        this.appendToLastAssistantMessage(payload.content || "");
        this.scrollMessagesToBottom();
      }
    },
    handleStopGeneration(reason = "manual") {
      if (!this.streamAbortController) {
        return;
      }
      this.streamAbortReason = reason;
      this.streamAbortController.abort();
    },
    async handleSendMessage() {
      const text = this.composerInput.trim();
      if (!text || this.isLoading) {
        return;
      }
      this.composerError = "";
      try {
        await this.ensureActiveConversation();
        this.sources = [];
        this.thinkingVisible = true;
        this.thinkingStatus = "正在思考中...";
        this.thinkingLogs = [{ label: "状态", content: "正在思考中..." }];
        this.isLoading = true;
        this.pushMessage({ sender: "user", content: text });
        this.pushMessage({
          sender: "assistant",
          content: "正在思考中...",
          pending: true,
        });
        this.composerInput = "";
        await this.scrollMessagesToBottom();

        this.streamAbortReason = "";
        this.streamAbortController = new AbortController();
        this.streamTimeoutId = window.setTimeout(() => {
          this.handleStopGeneration("timeout");
        }, GENERATION_TIMEOUT_MS);

        const response = await streamAgentChat(
          [{ role: "user", content: text }],
          this.user.id,
          this.currentConversationId,
          this.currentIndexId,
          this.streamAbortController.signal
        );
        await this.consumeEventStream(response, (payload) => this.handleStreamEvent(payload));
        await this.refreshConversationMessages();
        await this.refreshConversations(false);
      } catch (error) {
        const reason = this.streamAbortReason;
        if (reason === "manual") {
          this.finalizeInterruptedResponse("本轮回答已手动停止。");
        } else if (reason === "timeout") {
          this.finalizeInterruptedResponse("本轮回答因超时已停止，你可以继续追问或重新发送。");
          this.composerError = "生成超时，已停止本轮回答";
        } else if (error?.name === "AbortError") {
          this.finalizeInterruptedResponse("本轮回答已中断。");
        } else {
          this.updateLastAssistantMessage(`请求失败：${error.message || "未知错误"}`);
          const last = this.currentMessages[this.currentMessages.length - 1];
          if (last) {
            last.pending = false;
          }
          this.composerError =
            error.message?.includes("Failed to fetch") || error.message?.includes("Network")
              ? "网络连接中断，请检查网络后重试"
              : error.message || "发送失败";
        }
      } finally {
        if (this.streamTimeoutId) {
          clearTimeout(this.streamTimeoutId);
          this.streamTimeoutId = null;
        }
        this.streamAbortController = null;
        this.streamAbortReason = "";
        this.isLoading = false;
        await this.scrollMessagesToBottom();
      }
    },
    async handleComposerKeydown(event) {
      if (event.key !== "Enter" || event.shiftKey) {
        return;
      }
      const value = typeof event.target?.value === "string" ? event.target.value.trim() : "";
      if (!value || this.isLoading) {
        return;
      }
      event.preventDefault();
      await this.handleSendMessage();
    },
    async handleUploadFile(event) {
      const file = event.target.files?.[0];
      if (!file) {
        return;
      }
      this.composerError = "";
      try {
        await this.ensureActiveConversation();
        const result = await uploadKnowledgeFile(file, this.user.id);
        this.currentIndexId = result.index_id;
        this.attachments[String(this.currentConversationId)] = {
          indexId: result.index_id,
          filename: result.original_name || result.filename,
          chunks: result.chunks,
        };
        saveAttachments(this.attachments);
        this.pushSystemMessage(
          `已完成文档解析：${result.original_name || result.filename}，共生成 ${result.chunks} 个文本片段。现在你可以直接围绕这份文档提问。`
        );
        await this.scrollMessagesToBottom();
      } catch (error) {
        this.composerError = error.message || "上传失败";
      } finally {
        event.target.value = "";
      }
    },
    async handleRemoveAttachment() {
      if (!this.currentConversationId) {
        return;
      }
      const attachment = this.attachments[String(this.currentConversationId)];
      if (!attachment) {
        return;
      }
      delete this.attachments[String(this.currentConversationId)];
      saveAttachments(this.attachments);
      this.currentIndexId = null;
      this.sources = [];
      this.routeLabel = "自动路由";
      this.routeReason = "当前会话已移除文档上下文，后续提问将不再使用这份文档检索。";
      this.pushSystemMessage(`已移除文档：${attachment.filename}`);
      await this.scrollMessagesToBottom();
    },
    logout(rerender = true) {
      localStorage.removeItem("token");
      localStorage.removeItem("conversation_id");
      this.token = "";
      this.user = null;
      this.conversations = [];
      this.currentConversationId = null;
      this.messagesByConversation = {};
      this.currentIndexId = null;
      this.routeLabel = "自动路由";
      this.routeReason = "";
      this.sources = [];
      this.weather = null;
      this.thinkingVisible = false;
      this.thinkingStatus = "";
      this.thinkingLogs = [];
      this.isLoading = false;
      this.composerInput = "";
      this.composerError = "";
      this.streamAbortController = null;
      this.streamAbortReason = "";
      if (rerender) {
        this.showRegister = false;
      }
    },
    async bootstrap() {
      if (!this.token) {
        return;
      }
      try {
        await this.bootstrapUser();
        await this.refreshWeather();
      } catch {
        this.showRegister = false;
      }
    },
  },
  async mounted() {
    loadCachedCity();
    await this.bootstrap();
  },
  template: `
    <div v-if="!user" class="shell auth-layout">
      <div class="auth-card">
        <h1 class="auth-title">🤖 个人智能助手</h1>
        <p class="auth-subtitle">登录后即可使用自动路由、历史记忆和文档问答。</p>

        <form v-if="!showRegister" @submit.prevent="handleLogin">
          <div class="field">
            <label for="login-email">邮箱</label>
            <input id="login-email" v-model="loginForm.email" type="email" required />
          </div>
          <div class="field">
            <label for="login-password">密码</label>
            <input id="login-password" v-model="loginForm.password" type="password" required />
          </div>
          <div class="auth-actions">
            <button class="btn btn-primary" type="submit">登录</button>
            <button class="btn btn-ghost" type="button" @click="showAuth(false)">注册新账号</button>
          </div>
          <p v-if="loginError" class="error-text">{{ loginError }}</p>
        </form>

        <form v-else @submit.prevent="handleRegister">
          <div class="field">
            <label for="register-username">用户名</label>
            <input id="register-username" v-model="registerForm.username" required />
          </div>
          <div class="field">
            <label for="register-email">邮箱</label>
            <input id="register-email" v-model="registerForm.email" type="email" required />
          </div>
          <div class="field">
            <label for="register-password">密码</label>
            <input id="register-password" v-model="registerForm.password" type="password" required />
          </div>
          <div class="auth-actions">
            <button class="btn btn-primary" type="submit">完成注册</button>
            <button class="btn btn-ghost" type="button" @click="showAuth(true)">返回登录</button>
          </div>
          <p v-if="registerError" class="error-text">{{ registerError }}</p>
          <p v-if="registerSuccess" class="success-text">{{ registerSuccess }}</p>
        </form>
      </div>
    </div>

    <div v-else class="shell app-layout">
      <aside class="sidebar">
        <div class="brand">
          <h1>🤖 个人智能助手</h1>
          <p>👤 {{ user.username }} · {{ user.email }}</p>
        </div>
        <div class="sidebar-actions">
          <button class="btn btn-primary" @click="handleCreateConversation">新建会话</button>
          <button class="btn btn-ghost" @click="logout()">退出登录</button>
        </div>
        <div class="history">
          <template v-if="conversations.length">
            <div
              v-for="item in conversations"
              :key="item.id"
              class="history-item"
              :class="{ active: item.id === currentConversationId }"
              @click="selectConversation(item.id)"
            >
              <div class="history-item-title">{{ item.title || "未命名会话" }}</div>
              <div class="history-item-meta">{{ formatDate(item.updated_at || item.created_at) }}</div>
              <div class="history-item-actions">
                <button class="btn btn-ghost" @click.stop="handleRenameConversation(item.id)">重命名</button>
                <button class="btn btn-danger" @click.stop="handleDeleteConversation(item.id)">删除</button>
              </div>
            </div>
          </template>
          <div v-else class="history-empty">还没有历史会话。</div>
        </div>
      </aside>

      <main class="main">
        <div class="chat-topbar">
          <div class="chat-title">
            <h2>{{ currentConversationTitle }}</h2>
            <span class="muted">支持多轮对话、联网搜索与文档检索增强问答。</span>
          </div>
          <div class="toolbar">
            <div class="weather-cloud" :class="{ 'weather-cloud-loading': weatherCard.loading }">
              <p class="weather-city">📍 {{ weatherCard.city }}</p>
              <p class="weather-text">{{ weatherCard.text }}</p>
              <p v-if="weatherCard.meta" class="weather-meta">{{ weatherCard.meta }}</p>
            </div>
          </div>
        </div>

        <div class="chat-body">
          <div ref="messages" class="messages" id="messages">
            <div v-if="sources.length" class="message system">
              <h4>参考来源</h4>
              <div class="message-links">
                <template v-for="(item, idx) in sources" :key="idx">
                  <a
                    v-if="item.url"
                    class="message-link"
                    :href="item.url"
                    target="_blank"
                    rel="noreferrer"
                  >
                    {{ item.title || item.url }}
                    <small>{{ item.snippet || item.url }}</small>
                  </a>
                  <div v-else class="message-link">
                    {{ item.source || "文档片段" }}
                    <small>页码：{{ item.page || "未知" }}</small>
                  </div>
                </template>
              </div>
            </div>

            <template v-if="currentMessages.length">
              <div
                v-for="(message, idx) in currentMessages"
                :key="message.id || idx"
                class="message"
                :class="[(message.sender || message.role || 'assistant'), { pending: message.pending }]"
              >
                {{ message.content }}
              </div>
            </template>
            <div v-else class="empty-state">
              <h3>您好，我是个人智能助手</h3>
              <p>欢迎来到新的对话窗口。无论是日常问题、联网搜索，还是围绕文档内容进行整理和问答，我都可以尽量为您提供清晰、连续的解答。</p>
            </div>

            <div v-if="thinkingVisible" class="thinking-panel">
              <div class="thinking-panel-head">
                <span class="thinking-panel-title">思考过程</span>
                <span class="thinking-panel-status">{{ thinkingStatus || "正在思考中..." }}</span>
              </div>
              <div class="thinking-panel-body">
                <div v-for="(item, idx) in thinkingLogs" :key="idx" class="thinking-line">
                  <div class="thinking-label">{{ item.label }}</div>
                  <div>{{ item.content }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="composer-wrap">
            <div class="status-strip">
              <span class="status-pill">记忆：最近消息 + summary 长期记忆</span>
              <span class="status-pill">上传 PDF / DOCX / TXT 后可直接围绕文档提问</span>
            </div>

            <div v-if="currentAttachment" class="attachment-banner">
              <span class="attachment-banner-label">当前已关联文档</span>
              <span class="attachment-banner-name" :title="currentAttachment.filename">{{ currentAttachment.filename }}</span>
              <button class="attachment-banner-remove" type="button" aria-label="移除当前文档" @click="handleRemoveAttachment">×</button>
            </div>

            <form class="composer" @submit.prevent="handleSendMessage">
              <textarea
                v-model="composerInput"
                id="composer-input"
                placeholder="直接提问即可，例如：帮我总结这份 PDF 的重点，或者帮我查询今天的 AI 新闻。"
                required
                @keydown="handleComposerKeydown"
              ></textarea>
              <div class="composer-actions">
                <div class="composer-left">
                  <label class="btn btn-ghost" for="upload-input">上传文档</label>
                  <input id="upload-input" type="file" accept=".pdf,.docx,.txt,.md" class="hidden" @change="handleUploadFile" />
                </div>
                <div class="composer-right">
                  <button
                    v-if="isLoading"
                    class="btn btn-danger"
                    type="button"
                    @click="handleStopGeneration('manual')"
                  >
                    停止生成
                  </button>
                  <button v-else class="btn btn-primary" type="submit">发送</button>
                </div>
              </div>
              <p v-if="composerError" class="error-text">{{ composerError }}</p>
            </form>
          </div>
        </div>
      </main>
    </div>
  `,
};

