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
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ChatHeader from "../components/ChatHeader.vue";
import ComposerPanel from "../components/ComposerPanel.vue";
import MessageList from "../components/MessageList.vue";
import SidebarPanel from "../components/SidebarPanel.vue";
import { useAssistantApp } from "../composables/useAssistantApp.js";

// 聊天页主要负责装配消息区、输入区和侧边栏。
// 真正的会话同步逻辑放在 store 中，页面层只负责在合适的时机触发它。

const router = useRouter();
const route = useRoute();

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
  ensureChatPageReady,
} = useAssistantApp();

async function syncChatPage() {
  // 每次进入聊天页时都主动补一次当前页数据，
  // 避免从其他导航页切回聊天页时仍然停留在旧状态。
  const ok = await ensureChatPageReady();
  if (!ok || !state.user) {
    router.replace("/auth");
  }
}

onMounted(syncChatPage);

watch(
  () => route.fullPath,
  async (path) => {
    if (path === "/chat") {
      await syncChatPage();
    }
  }
);

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
