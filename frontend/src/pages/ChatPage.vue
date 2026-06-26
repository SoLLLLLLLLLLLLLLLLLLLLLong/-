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

    <main class="main">
      <ChatHeader
        :title="currentConversationTitle"
        :weather-card="weatherCard"
      />

      <div class="chat-body">
        <MessageList
          :sources="state.sources"
          :messages="currentMessages"
          :thinking-visible="state.thinkingVisible"
          :thinking-collapsed="state.thinkingCollapsed"
          :active-thinking-status="activeThinkingStatus"
          :active-thinking-logs="activeThinkingLogs"
          :has-thinking-record="hasThinkingRecord"
          @toggle-thinking="toggleThinkingCollapsed"
          @clear-thinking="clearLastThinking"
          @copy-message="copyMessageContent"
          @regenerate-message="handleRegenerateMessage"
          @edit-resend-message="handleEditAndResend"
        />

        <ComposerPanel
          v-model:composer-input="state.composerInput"
          :current-attachment="currentAttachment"
          :is-loading="state.isLoading"
          :composer-error="state.composerError"
          @remove-attachment="handleRemoveAttachment"
          @send="handleSendMessage"
          @keydown="handleComposerKeydown"
          @upload="onUploadFile"
          @stop="handleStopGeneration('manual')"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import ChatHeader from "../components/ChatHeader.vue";
import ComposerPanel from "../components/ComposerPanel.vue";
import MessageList from "../components/MessageList.vue";
import SidebarPanel from "../components/SidebarPanel.vue";
import { useAssistantApp } from "../composables/useAssistantApp.js";

// 聊天页是整个前端最核心的页面。
// 它本身不直接写复杂业务逻辑，而是像“页面装配层”：
// 1. 从 composable 里拿状态和方法
// 2. 把状态分发给各个子组件
// 3. 把子组件事件再转回 store 逻辑

const router = useRouter();

const {
  state,
  currentMessages,
  filteredConversations,
  currentAttachment,
  currentConversationTitle,
  weatherCard,
  activeThinkingStatus,
  activeThinkingLogs,
  hasThinkingRecord,
  formatDate,
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
  handleRemoveAttachment,
  handleStopGeneration,
  toggleThinkingCollapsed,
  clearLastThinking,
  logout,
  bootstrap,
} = useAssistantApp();

onMounted(async () => {
  // 页面挂载后先尝试恢复登录态和初始化聊天数据。
  // 如果 token 无效或当前用户不存在，就回到登录页。
  const ok = await bootstrap();
  if (!ok || !state.user) {
    router.replace("/auth");
  }
});

async function onUploadFile(file) {
  try {
    await handleUploadFile(file);
  } catch (error) {
    state.composerError = error.message || "上传失败";
  }
}

function performLogout() {
  logout();
  router.replace("/auth");
}
</script>
