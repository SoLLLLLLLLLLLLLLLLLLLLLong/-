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
            <h2>文档管理</h2>
            <p>上传、查看和删除知识库文档。文档上传后会自动解析并建立向量索引。</p>
          </div>
          <label class="btn btn-primary">
            上传文档
            <input class="hidden" type="file" accept=".pdf,.docx,.txt,.md" @change="onUpload" />
          </label>
        </div>

        <p v-if="state.documentsError" class="error-text">{{ state.documentsError }}</p>

        <div v-if="state.documentsLoading" class="empty-inline">正在加载文档列表...</div>
        <div v-else-if="!state.documents.length" class="empty-inline">
          暂无文档，可以先上传 PDF、DOCX、TXT 或 Markdown 文件。
        </div>

        <div v-else class="data-list">
          <article v-for="doc in state.documents" :key="doc.id" class="data-item">
            <div>
              <h3>{{ doc.original_name || doc.filename }}</h3>
              <p>
                {{ doc.chunks || 0 }} 个片段 · {{ formatDate(doc.created_at || doc.upload_time) }}
              </p>
              <small>{{ doc.path }}</small>
            </div>
            <button class="btn btn-danger" type="button" @click="handleDeleteDocument(doc.id)">
              删除
            </button>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import SidebarPanel from "../components/SidebarPanel.vue";
import { useAssistantApp } from "../composables/useAssistantApp.js";

const router = useRouter();
const {
  state,
  filteredConversations,
  formatDate,
  bootstrap,
  handleCreateConversation,
  selectConversation,
  handleDeleteConversation,
  handleRenameConversation,
  handleUploadFile,
  handleDeleteDocument,
  logout,
} = useAssistantApp();

onMounted(async () => {
  const ok = await bootstrap();
  if (!ok || !state.user) {
    router.replace("/auth");
  }
});

async function onUpload(event) {
  const file = event.target.files?.[0];
  if (file) {
    await handleUploadFile(file);
  }
  event.target.value = "";
}

function performLogout() {
  logout();
  router.replace("/auth");
}
</script>
