<template>
  <aside class="sidebar">
    <div class="brand">
      <h1>个人智能助手</h1>
      <p v-if="user">{{ user.username }} · {{ user.email }}</p>
    </div>

    <nav class="side-nav" aria-label="主导航">
      <RouterLink class="side-nav-link" to="/chat">聊天</RouterLink>
      <RouterLink class="side-nav-link" to="/documents">文档</RouterLink>
      <RouterLink class="side-nav-link" to="/dashboard">统计</RouterLink>
      <RouterLink class="side-nav-link" to="/workspace">工作区</RouterLink>
      <RouterLink class="side-nav-link" to="/settings">设置</RouterLink>
    </nav>

    <div class="sidebar-actions">
      <button class="btn btn-primary" @click="$emit('create')">新建会话</button>
      <button class="btn btn-ghost" @click="$emit('logout')">退出登录</button>
    </div>

    <div class="sidebar-search">
      <input
        :value="conversationSearch"
        type="search"
        placeholder="搜索会话标题..."
        @input="$emit('update:conversationSearch', $event.target.value)"
      />
    </div>

    <ConversationList
      :conversations="conversations"
      :current-conversation-id="currentConversationId"
      :format-date="formatDate"
      @select="$emit('select', $event)"
      @rename="$emit('rename', $event)"
      @delete="$emit('delete', $event)"
    />
  </aside>
</template>

<script setup>
import ConversationList from "./ConversationList.vue";

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

defineEmits([
  "create",
  "logout",
  "select",
  "rename",
  "delete",
  "update:conversationSearch",
]);
</script>
