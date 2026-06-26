<template>
  <section class="messages-shell">
    <div id="messages" class="messages-scroll">
      <div v-if="messages.length" class="message-stream">
        <MessageBubble
          v-for="(message, idx) in messages"
          :key="message.id || idx"
          :message="message"
          :index="idx"
          @copy="$emit('copy-message', $event)"
          @regenerate="$emit('regenerate-message', $event)"
          @edit-resend="$emit('edit-resend-message', $event)"
        />
      </div>

      <EmptyState v-else />

      <div
        v-if="sources.length || thinkingVisible"
        class="messages-bottom-panels"
        :class="{ active: thinkingVisible }"
      >
        <ThinkingPanel
          :visible="thinkingVisible"
          :collapsed="thinkingCollapsed"
          :is-active="thinkingVisible"
          :status="activeThinkingStatus"
          :logs="activeThinkingLogs"
          @toggle="$emit('toggle-thinking')"
          @clear="$emit('clear-thinking')"
        />

        <SourcesPanel :sources="sources" />
      </div>
    </div>
  </section>
</template>

<script setup>
import EmptyState from "./EmptyState.vue";
import MessageBubble from "./MessageBubble.vue";
import SourcesPanel from "./SourcesPanel.vue";
import ThinkingPanel from "./ThinkingPanel.vue";

// MessageList 负责组织消息流和消息区下方的辅助面板。
// 这里把 thinking 面板放在消息流后面，这样会跟在 assistant 的“正在思考中...”下面显示。
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
  thinkingCollapsed: {
    type: Boolean,
    default: false,
  },
  activeThinkingStatus: {
    type: String,
    default: "",
  },
  activeThinkingLogs: {
    type: Array,
    default: () => [],
  },
  hasThinkingRecord: {
    type: Boolean,
    default: false,
  },
});

defineEmits([
  "toggle-thinking",
  "clear-thinking",
  "copy-message",
  "regenerate-message",
  "edit-resend-message",
]);
</script>

<style scoped>
.messages-shell {
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.messages-scroll {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.messages-bottom-panels {
  display: grid;
  gap: 12px;
  margin-top: 10px;
}

.messages-bottom-panels.active {
  margin-top: 12px;
}

.message-stream {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
