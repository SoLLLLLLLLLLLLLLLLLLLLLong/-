<template>
  <div class="shell app-layout">
    <SidebarPanel
      :user="state.user"
      :conversations="filteredConversations"
      v-model:conversation-search="state.conversationSearch"
      :current-conversation-id="state.currentConversationId"
      :format-date="formatDate"
      @create="handleCreateConversation"
      @logout="performLogout"
      @select="selectConversation"
      @rename="handleRenameConversation"
      @delete="handleDeleteConversation"
    />

    <main class="main page-main">
      <section class="page-card">
        <div class="page-head">
          <div>
            <h2>助手设置</h2>
            <p>模型名称从后端环境变量读取，这里主要调整本轮请求参数。</p>
          </div>
          <button class="btn btn-primary" type="button" :disabled="state.settingsSaving" @click="save">
            保存设置
          </button>
        </div>

        <div class="settings-grid">
          <label class="field">
            <span>模型</span>
            <select v-model="draft.model">
              <option value="env:CHAT_MODEL_NAME">使用 .env 中的聊天模型</option>
              <option value="env:AGENT_MODEL_NAME">使用 .env 中的 Agent 模型</option>
              <option value="custom-placeholder">自定义模型占位</option>
            </select>
          </label>

          <label class="field">
            <span>温度 temperature</span>
            <input v-model.number="draft.temperature" type="number" min="0" max="2" step="0.1" />
          </label>

          <label class="field toggle-field">
            <span>是否允许联网搜索</span>
            <input v-model="draft.enable_search" type="checkbox" />
          </label>

          <label class="field">
            <span>回答风格</span>
            <select v-model="draft.response_style">
              <option value="balanced">平衡清晰</option>
              <option value="concise">简洁直接</option>
              <option value="detailed">详细讲解</option>
              <option value="interview">面试表达</option>
            </select>
          </label>
        </div>

        <p v-if="state.settingsError" class="error-text">{{ state.settingsError }}</p>
        <p v-if="state.settingsSavedAt" class="success-text">
          已保存：{{ formatDate(state.settingsSavedAt) }}
        </p>
      </section>

      <section class="page-card">
        <div class="page-head">
          <div>
            <h2>用户画像记忆</h2>
            <p>系统会从包含“请记住、我喜欢、我的偏好”等表达的对话中抽取偏好。</p>
          </div>
          <button class="btn btn-danger" type="button" @click="handleClearUserProfile">
            清空记忆
          </button>
        </div>

        <p v-if="state.profileError" class="error-text">{{ state.profileError }}</p>
        <div v-if="!state.userProfile.preferences?.length" class="empty-inline">
          暂无用户画像记忆。
        </div>
        <ul v-else class="profile-list">
          <li v-for="item in state.userProfile.preferences" :key="item">{{ item }}</li>
        </ul>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, reactive, watch } from "vue";
import { useRouter } from "vue-router";
import SidebarPanel from "../components/SidebarPanel.vue";
import { useAssistantApp } from "../composables/useAssistantApp.js";

const router = useRouter();
const {
  state,
  filteredConversations,
  formatDate,
  bootstrap,
  saveSettings,
  handleClearUserProfile,
  handleCreateConversation,
  selectConversation,
  handleDeleteConversation,
  handleRenameConversation,
  logout,
} = useAssistantApp();

const draft = reactive({ ...state.settings });

watch(
  () => state.settings,
  (value) => Object.assign(draft, value),
  { deep: true }
);

onMounted(async () => {
  const ok = await bootstrap();
  if (!ok || !state.user) {
    router.replace("/auth");
  }
});

async function save() {
  await saveSettings(draft);
}

function performLogout() {
  logout();
  router.replace("/auth");
}
</script>
