<template>
  <!--
    天气卡片是纯展示组件：
    - 不直接请求后端
    - 不自己计算温度文案
    - 只负责把父层传进来的结构展示出来
  -->
  <div class="weather-cloud" :class="{ 'weather-cloud-loading': weatherCard.loading }">
    <p class="weather-city">📍 {{ weatherCard.city }}</p>
    <p class="weather-text">{{ weatherCard.text }}</p>
    <p v-if="weatherCard.meta" class="weather-meta">{{ weatherCard.meta }}</p>
  </div>
</template>

<script setup>
// weatherCard 至少包含这些字段：
// - city：城市文案
// - text：天气描述
// - meta：温度 / 体感等补充信息
// - loading：是否还在获取中
defineProps({
  weatherCard: {
    type: Object,
    required: true,
  },
});
</script>
