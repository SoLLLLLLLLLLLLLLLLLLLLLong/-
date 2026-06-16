<template>
  <div class="history">
    <template v-if="conversations.length">
      <ConversationListItem
        v-for="item in conversations"
        :key="item.id"
        :item="item"
        :active="item.id === currentConversationId"
        :format-date="formatDate"
        @select="$emit('select', $event)"
        @rename="$emit('rename', $event)"
        @delete="$emit('delete', $event)"
      />
    </template>
    <div v-else class="history-empty">还没有历史会话。</div>
  </div>
</template>

<script setup>
import ConversationListItem from "./ConversationListItem.vue";

defineProps({
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

defineEmits(["select", "rename", "delete"]);
</script>
