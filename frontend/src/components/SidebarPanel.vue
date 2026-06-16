<template>
  <aside class="sidebar">
    <div class="brand">
      <h1>🤖 个人智能助手</h1>
      <p v-if="user">👤 {{ user.username }} · {{ user.email }}</p>
    </div>

    <div class="sidebar-actions">
      <button class="btn btn-primary" @click="$emit('create')">新建会话</button>
      <button class="btn btn-ghost" @click="$emit('logout')">退出登录</button>
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
  currentConversationId: {
    type: Number,
    default: null,
  },
  formatDate: {
    type: Function,
    required: true,
  },
});

defineEmits(["create", "logout", "select", "rename", "delete"]);
</script>
