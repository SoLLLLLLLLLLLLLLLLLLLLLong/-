<template>
  <view class="section-title">
    <view class="section-line"></view>
    <text class="section-text">{{ title }}</text>
    <text v-if="caption" class="section-caption">{{ caption }}</text>
  </view>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  caption: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.section-title {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.section-line {
  width: 8rpx;
  height: 30rpx;
  border-radius: 999rpx;
  background: linear-gradient(180deg, #6f6dff 0%, #55b8ff 100%);
}

.section-text {
  color: #242847;
  font-size: 32rpx;
  font-weight: 700;
}

.section-caption {
  color: #9ea3b9;
  font-size: 22rpx;
}
</style>
