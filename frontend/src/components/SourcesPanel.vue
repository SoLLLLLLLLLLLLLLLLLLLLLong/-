<template>
  <div v-if="sources.length" class="message system">
    <h4>参考来源</h4>
    <div class="message-links">
      <template v-for="(item, idx) in sources" :key="idx">
        <a
          v-if="item.url"
          class="message-link"
          :href="item.url"
          target="_blank"
          rel="noreferrer"
        >
          {{ item.title || item.url }}
          <small>{{ item.snippet || item.url }}</small>
        </a>
        <div v-else class="message-link">
          {{ item.source || "文档片段" }}
          <small>页码：{{ item.page || "未知" }}</small>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sources: {
    type: Array,
    default: () => [],
  },
});
</script>
