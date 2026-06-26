<template>
  <!--
    只有当前真的有来源时才显示。
    这里展示的是：
    - 联网搜索命中的网页来源
    - 文档检索命中的文档片段来源
  -->
  <div v-if="sources.length" class="message system">
    <h4>参考来源</h4>
    <div class="message-links">
      <template v-for="(item, idx) in sources" :key="idx">
        <!-- 网页来源 -->
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

        <!-- 文档片段来源 -->
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
