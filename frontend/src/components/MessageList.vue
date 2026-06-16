<template>
  <div id="messages" class="messages">
    <SourcesPanel :sources="sources" />

    <template v-if="messages.length">
      <div
        v-for="(message, idx) in messages"
        :key="message.id || idx"
        class="message"
        :class="[(message.sender || message.role || 'assistant'), { pending: message.pending }]"
      >
        {{ message.content }}
      </div>
    </template>

    <EmptyState v-else />

    <ThinkingPanel
      :visible="thinkingVisible"
      :status="thinkingStatus"
      :logs="thinkingLogs"
    />
  </div>
</template>

<script setup>
import EmptyState from "./EmptyState.vue";
import SourcesPanel from "./SourcesPanel.vue";
import ThinkingPanel from "./ThinkingPanel.vue";

defineProps({
  sources: {
    type: Array,
    default: () => [],
  },
  messages: {
    type: Array,
    default: () => [],
  },
  thinkingVisible: {
    type: Boolean,
    default: false,
  },
  thinkingStatus: {
    type: String,
    default: "",
  },
  thinkingLogs: {
    type: Array,
    default: () => [],
  },
});
</script>
