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
            <h2>数据面板</h2>
            <p>用于展示这个问答系统的基础使用情况。</p>
          </div>
          <button class="btn btn-ghost" type="button" @click="refreshDashboard">刷新</button>
        </div>

        <p v-if="state.dashboardError" class="error-text">{{ state.dashboardError }}</p>

        <div class="metric-grid">
          <article class="metric-card">
            <span>问答次数</span>
            <strong>{{ state.dashboard.qa_count || 0 }}</strong>
          </article>
          <article class="metric-card">
            <span>搜索次数</span>
            <strong>{{ state.dashboard.search_count || 0 }}</strong>
          </article>
          <article class="metric-card">
            <span>文档数量</span>
            <strong>{{ state.dashboard.document_count || 0 }}</strong>
          </article>
          <article class="metric-card">
            <span>平均响应时间</span>
            <strong>{{ avgResponseTime }}</strong>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import SidebarPanel from "../components/SidebarPanel.vue";
import { useAssistantApp } from "../composables/useAssistantApp.js";

const router = useRouter();
const {
  state,
  filteredConversations,
  formatDate,
  bootstrap,
  refreshDashboard,
  handleCreateConversation,
  selectConversation,
  handleDeleteConversation,
  handleRenameConversation,
  logout,
} = useAssistantApp();

const avgResponseTime = computed(() => {
  const value = Number(state.dashboard.avg_response_time_ms || 0);
  if (!value) {
    return "--";
  }
  return `${(value / 1000).toFixed(2)}s`;
});

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
