<template>
  <div class="weather-cloud" :class="{ 'weather-cloud-loading': weatherCard.loading }">
    <p class="weather-city">📍 {{ weatherCard.city }}</p>
    <p class="weather-text">{{ weatherCard.text }}</p>
    <p v-if="weatherCard.meta" class="weather-meta">{{ weatherCard.meta }}</p>
  </div>
</template>

<script setup>
defineProps({
  weatherCard: {
    type: Object,
    required: true,
  },
});
</script>
