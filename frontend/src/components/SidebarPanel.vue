<template>
  <aside class="sidebar">
    <div class="brand">
      <h1>个人智能助手</h1>
      <div v-if="user" class="brand-user-row">
        <p>{{ user.username }} · {{ user.email }}</p>
        <button class="brand-logout" type="button" @click="emit('logout')">退出登录</button>
      </div>
    </div>

    <nav class="side-nav" aria-label="主导航">
      <RouterLink class="side-nav-link" to="/workspace">工作区</RouterLink>
      <RouterLink class="side-nav-link" to="/settings">设置</RouterLink>
      <RouterLink class="side-nav-link" to="/documents">文档</RouterLink>
      <RouterLink class="side-nav-link" to="/dashboard">统计</RouterLink>

      <div class="side-nav-group">
        <button
          class="side-nav-link side-nav-trigger"
          :class="{ active: route.path === '/chat'}"
          type="button"
          @click="toggleChatGroup"
        >
          <span>聊天</span>
          <span class="side-nav-arrow">{{ chatExpanded ? "▾" : "▸" }}</span>
        </button>

        <div v-show="chatExpanded" class="chat-group-panel">
          <div class="chat-group-actions">
            <button class="btn btn-primary chat-create-btn" type="button" @click="handleCreateClick">
              新建会话
            </button>
            <input
              :value="conversationSearch"
              class="chat-search-input"
              type="search"
              placeholder="搜索会话标题..."
              @input="emit('update:conversationSearch', $event.target.value)"
            />
          </div>

          <ConversationList
            :conversations="conversations"
            :current-conversation-id="currentConversationId"
            :format-date="formatDate"
            @select="emit('select', $event)"
            @rename="emit('rename', $event)"
            @delete="emit('delete', $event)"
          />
        </div>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import ConversationList from "./ConversationList.vue";

const CHAT_PANEL_EXPANDED_KEY = "sidebar_chat_panel_expanded";

defineProps({
  user: {
    type: Object,
    default: null,
  },
  conversations: {
    type: Array,
    default: () => [],
  },
  conversationSearch: {
    type: String,
    default: "",
  },
  currentConversationId: {
    type: Number,
    default: null,
  },
  formatDate: {
    type: Function,
    required: true,
  },
});

const emit = defineEmits([
  "create",
  "logout",
  "select",
  "rename",
  "delete",
  "update:conversationSearch",
]);

const router = useRouter();
const route = useRoute();
const chatExpanded = ref(loadInitialExpanded());

function loadInitialExpanded() {
  const saved = localStorage.getItem(CHAT_PANEL_EXPANDED_KEY);
  if (saved === "true") {
    return true;
  }
  if (saved === "false") {
    return false;
  }
  return route.path === "/chat";
}

function persistExpanded(value) {
  localStorage.setItem(CHAT_PANEL_EXPANDED_KEY, value ? "true" : "false");
}

function toggleChatGroup() {
  chatExpanded.value = !chatExpanded.value;
  persistExpanded(chatExpanded.value);
  if (route.path !== "/chat") {
    router.push("/chat");
  }
}

async function handleCreateClick() {
  emit("create");
  chatExpanded.value = true;
  persistExpanded(true);
  if (route.path !== "/chat") {
    await router.push("/chat");
  }
}
</script>
