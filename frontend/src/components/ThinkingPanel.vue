<template>
  <div v-if="visible" class="thinking-panel">
    <div class="thinking-panel-head">
      <span class="thinking-panel-title">思考过程</span>
      <span class="thinking-panel-status">{{ status || "正在思考中..." }}</span>
    </div>
    <div class="thinking-panel-body">
      <div v-for="(item, idx) in logs" :key="idx" class="thinking-line">
        <div class="thinking-label">{{ item.label }}</div>
        <div>{{ item.content }}</div>
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
  status: {
    type: String,
    default: "",
  },
  logs: {
    type: Array,
    default: () => [],
  },
});
</script>
