<template>
  <div class="chat-topbar">
    <div class="chat-title">
      <h2>{{ title }}</h2>
      <span class="muted">支持多轮对话、联网搜索与文档检索增强问答。</span>
    </div>
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
