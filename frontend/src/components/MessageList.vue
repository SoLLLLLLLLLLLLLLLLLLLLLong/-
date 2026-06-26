<template>
  <section class="messages-shell">
    <div id="messages" class="messages-scroll">
      <!-- 顶部区域放“来源信息 + thinking / trace”，属于消息区内部的一部分。 -->
      <div
        v-if="sources.length || hasThinkingRecord"
        class="messages-top-panels"
        :class="{ active: thinkingVisible }"
      >
        <SourcesPanel :sources="sources" />

        <ThinkingPanel
          :visible="hasThinkingRecord"
          :collapsed="thinkingCollapsed"
          :is-active="thinkingVisible"
          :status="activeThinkingStatus"
          :logs="activeThinkingLogs"
          @toggle="$emit('toggle-thinking')"
          @clear="$emit('clear-thinking')"
        />
      </div>

      <!-- 这里才是真正的聊天消息流。 -->
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
    </div>
  </section>
</template>

<script setup>
import EmptyState from "./EmptyState.vue";
import MessageBubble from "./MessageBubble.vue";
import SourcesPanel from "./SourcesPanel.vue";
import ThinkingPanel from "./ThinkingPanel.vue";

// MessageList 负责组织“消息区的整体结构”，
// 它本身不决定业务逻辑，只负责把不同状态渲染成不同区域。
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

.messages-top-panels {
  position: sticky;
  top: 0;
  z-index: 2;
  display: grid;
  gap: 12px;
  padding-bottom: 10px;
  background: linear-gradient(180deg, rgba(247, 251, 255, 0.98) 0%, rgba(247, 251, 255, 0.92) 72%, rgba(247, 251, 255, 0) 100%);
  backdrop-filter: blur(6px);
}

.messages-top-panels.active {
  padding-bottom: 14px;
}

.message-stream {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
