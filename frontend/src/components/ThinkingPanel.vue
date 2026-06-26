<template>
  <div v-if="visible" class="thinking-panel">
    <div class="thinking-panel-head">
      <div class="thinking-panel-head-main">
        <span class="thinking-panel-title">
          {{ isActive ? "执行轨迹" : "最近一次执行轨迹" }}
        </span>
        <span class="thinking-panel-status">{{ status || "正在思考中..." }}</span>
      </div>

      <div class="thinking-panel-actions">
        <button class="btn btn-ghost thinking-action" type="button" @click="$emit('toggle')">
          {{ collapsed ? "展开" : "折叠" }}
        </button>
        <button
          v-if="!isActive && logs.length"
          class="btn btn-ghost thinking-action"
          type="button"
          @click="$emit('clear')"
        >
          清空
        </button>
      </div>
    </div>

    <div v-show="!collapsed" class="thinking-panel-body">
      <div v-for="(item, idx) in logs" :key="item.key || idx" class="trace-card">
        <div class="trace-card-head">
          <div class="trace-card-head-main">
            <span class="trace-stage">{{ item.stageLabel || item.stage || "执行过程" }}</span>
            <span class="trace-title">{{ item.title }}</span>
          </div>
          <span class="trace-status" :data-status="item.status">
            {{ item.statusLabel || item.status || "执行中" }}
          </span>
        </div>

        <div class="trace-meta">
          <span v-if="item.tool">工具：{{ item.tool }}</span>
          <span v-if="item.attempt">第 {{ item.attempt }} 次</span>
          <span v-if="item.timestamp">{{ formatTime(item.timestamp) }}</span>
        </div>

        <pre class="trace-detail">{{ item.detail || "暂无细节输出" }}</pre>
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
  margin: 0 0 16px;
  border: 1px solid #dbe6f2;
  border-radius: 18px;
  background: linear-gradient(180deg, #f9fbfe 0%, #ffffff 100%);
  overflow: hidden;
}

.thinking-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid #e8eef6;
}

.thinking-panel-head-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.thinking-panel-title {
  font-size: 14px;
  font-weight: 700;
  color: #123b6b;
}

.thinking-panel-status {
  font-size: 12px;
  color: #58708c;
}

.thinking-panel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.thinking-action {
  min-width: 64px;
}

.thinking-panel-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 280px;
  padding: 14px 16px 16px;
  overflow-y: auto;
}

.trace-card {
  padding: 12px 14px;
  border: 1px solid #e3ebf5;
  border-radius: 14px;
  background: #ffffff;
}

.trace-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.trace-card-head-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.trace-stage {
  font-size: 11px;
  color: #6f89a4;
}

.trace-title {
  font-size: 14px;
  font-weight: 600;
  color: #173d68;
}

.trace-status {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1;
  background: #eef4fb;
  color: #3f5e80;
}

.trace-status[data-status="completed"] {
  background: #edf7ef;
  color: #2d7a44;
}

.trace-status[data-status="failed"] {
  background: #fff1f1;
  color: #b54747;
}

.trace-status[data-status="retrying"],
.trace-status[data-status="running"] {
  background: #eef4ff;
  color: #2d64c8;
}

.trace-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
  font-size: 12px;
  color: #70839b;
}

.trace-detail {
  margin: 10px 0 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.65;
  color: #29405d;
  font-family: inherit;
}

@media (max-width: 768px) {
  .thinking-panel-head {
    flex-direction: column;
    align-items: stretch;
  }

  .thinking-panel-actions {
    justify-content: flex-end;
  }

  .thinking-panel-body {
    max-height: 240px;
  }
}
</style>
