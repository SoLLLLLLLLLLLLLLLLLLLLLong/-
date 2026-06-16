<template>
  <div
    class="history-item"
    :class="{ active: active }"
    @click="$emit('select', item.id)"
  >
    <div class="history-item-title">{{ item.title || "未命名会话" }}</div>
    <div class="history-item-meta">{{ formatDate(item.updated_at || item.created_at) }}</div>
    <div class="history-item-actions">
      <button class="btn btn-ghost" @click.stop="$emit('rename', item.id)">重命名</button>
      <button class="btn btn-danger" @click.stop="$emit('delete', item.id)">删除</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  item: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
  formatDate: {
    type: Function,
    required: true,
  },
});

defineEmits(["select", "rename", "delete"]);
</script>
