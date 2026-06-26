<template>
  <div class="chat-topbar">
    <div class="chat-title">
      <!-- 当前会话标题来自 store 的 currentConversationTitle -->
      <h2>{{ title }}</h2>
      <span class="muted">支持多轮对话、联网搜索与文档检索增强问答。</span>
    </div>

    <!-- 天气卡片本身只负责展示，天气数据的整理发生在 store 的 weatherCard computed -->
    <div class="toolbar">
      <WeatherCard :weather-card="weatherCard" />
    </div>
  </div>
</template>

<script setup>
import WeatherCard from "./WeatherCard.vue";

defineProps({
  title: {
    type: String,
    required: true,
  },
  weatherCard: {
    type: Object,
    required: true,
  },
});
</script>
