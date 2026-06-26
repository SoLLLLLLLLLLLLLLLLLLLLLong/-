<template>
  <div v-if="visible" class="thinking-panel">
    <div class="thinking-panel-status-row">
      <span class="thinking-panel-status">{{ status || "正在思考中..." }}</span>
      <div class="thinking-panel-actions">
        <button class="thinking-action" type="button" @click="$emit('toggle')">
          {{ collapsed ? "展开" : "收起" }}
        </button>
        <button
          v-if="!isActive && logs.length"
          class="thinking-action"
          type="button"
          @click="$emit('clear')"
        >
          清空
        </button>
      </div>
    </div>

    <div v-show="!collapsed" class="thinking-panel-body">
      <div v-for="(item, idx) in logs" :key="item.key || idx" class="trace-row">
        <div class="trace-row-inline">
          <span class="trace-title">{{ item.title || "执行步骤" }}</span>
          <span class="trace-status" :data-status="item.status">
            {{ item.statusLabel || item.status || "执行中" }}
          </span>
          <span>{{ item.stageLabel || item.stage || "执行过程" }}</span>
          <span v-if="item.tool">工具：{{ item.tool }}</span>
          <span v-if="item.attempt">第 {{ item.attempt }} 次</span>
          <span v-if="item.timestamp">{{ formatTime(item.timestamp) }}</span>
        </div>

        <pre v-if="item.detail" class="trace-detail">{{ item.detail }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
  isActive: {
    type: Boolean,
    default: false,
  },
  status: {
    type: String,
    default: "",
  },
  logs: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["toggle", "clear"]);

function formatTime(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
</script>

<style scoped>
.thinking-panel {
  margin: 0 0 10px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.thinking-panel-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.thinking-panel-status {
  font-size: 13px;
  color: #60758f;
}

.thinking-panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-action {
  border: 0;
  background: transparent;
  color: #47627f;
  font-size: 12px;
  cursor: pointer;
  padding: 0;
}

.thinking-panel-body {
  margin-top: 6px;
  display: grid;
  gap: 6px;
  max-height: 32vh;
  overflow-y: auto;
}

.trace-row {
  display: grid;
  gap: 3px;
  padding: 5px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.75);
}

.trace-row-inline {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 10px;
}

.trace-title {
  font-size: 12px;
  font-weight: 600;
  color: #173d68;
}

.trace-status {
  font-size: 11px;
  color: #5a7390;
}

.trace-status[data-status="completed"] {
  color: #2d7a44;
}

.trace-status[data-status="failed"] {
  color: #b54747;
}

.trace-status[data-status="retrying"],
.trace-status[data-status="running"] {
  color: #2d64c8;
}

.trace-detail {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.6;
  color: #334b67;
  font-family: inherit;
}

@media (max-width: 768px) {
  .thinking-panel-status-row,
  .trace-row-inline {
    align-items: flex-start;
    flex-direction: column;
  }

  .thinking-panel-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
