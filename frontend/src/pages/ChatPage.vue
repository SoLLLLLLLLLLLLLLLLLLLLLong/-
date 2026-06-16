<template>
  <div class="shell app-layout">
    <SidebarPanel
      :user="state.user"
      :conversations="state.conversations"
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
          :thinking-status="state.thinkingStatus"
          :thinking-logs="state.thinkingLogs"
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

const router = useRouter();
const {
  state,
  currentMessages,
  currentAttachment,
  currentConversationTitle,
  weatherCard,
  formatDate,
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
} = useAssistantApp();

onMounted(async () => {
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
