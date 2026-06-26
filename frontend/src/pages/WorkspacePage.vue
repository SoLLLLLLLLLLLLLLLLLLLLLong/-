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
            <h2>本地代码工作区</h2>
            <p>在后端工作目录下创建一个用户文件夹，并把该文件夹内容作为问答上下文。</p>
          </div>
          <button class="btn btn-ghost" type="button" @click="refreshWorkspace">刷新</button>
        </div>

        <div class="workspace-create">
          <input v-model.trim="state.workspaceFolderName" placeholder="文件夹名称" />
          <button class="btn btn-primary" type="button" @click="handleCreateWorkspaceFolder">
            创建文件夹
          </button>
        </div>

        <p v-if="state.workspaceError" class="error-text">{{ state.workspaceError }}</p>
        <p class="muted">工作区根目录：{{ state.workspace.root || "暂未创建" }}</p>

        <div class="data-list">
          <article v-for="folder in state.workspace.folders" :key="folder.path" class="data-item">
            <div>
              <h3>{{ folder.name }}</h3>
              <p>{{ folder.path }}</p>
            </div>
            <button class="btn btn-primary" type="button" @click="handleScanWorkspaceFolder(folder.path)">
              扫描并用于问答
            </button>
          </article>
        </div>

        <div v-if="state.workspace.indexed_files?.length" class="workspace-files">
          <h3>最近索引的文件</h3>
          <ul>
            <li v-for="file in state.workspace.indexed_files" :key="file">{{ file }}</li>
          </ul>
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
  refreshWorkspace,
  handleCreateWorkspaceFolder,
  handleScanWorkspaceFolder,
  handleCreateConversation,
  selectConversation,
  handleDeleteConversation,
  handleRenameConversation,
  logout,
} = useAssistantApp();

onMounted(async () => {
  const ok = await bootstrap();
  if (!ok || !state.user) {
    router.replace("/auth");
  }
});

function performLogout() {
  logout();
  router.replace("/auth");
}
</script>
