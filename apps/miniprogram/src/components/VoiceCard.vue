<template>
  <view class="voice-card" :class="{ selected }" @tap="$emit('select', voice)">
    <view class="voice-head">
      <view class="voice-title-wrap">
        <text class="voice-name">{{ voice.name }}</text>
        <text class="voice-region">{{ voice.region }}</text>
      </view>
      <text class="voice-tag">{{ voice.gender }}</text>
    </view>
    <text class="voice-desc">{{ voice.description }}</text>
    <view class="voice-tags">
      <text v-for="tag in voice.tags" :key="tag" class="voice-chip">{{ tag }}</text>
    </view>
    <view class="voice-actions">
      <view class="preview-btn" @tap.stop="$emit('preview', voice)">试听</view>
      <view class="use-btn">{{ selected ? '已选择' : '使用音色' }}</view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  voice: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['select', 'preview'])
</script>

<style scoped>
.voice-card {
  height: 330rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid transparent;
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
  box-sizing: border-box;
}

.voice-card.selected {
  border-color: rgba(76, 97, 255, 0.3);
  background: linear-gradient(180deg, #ffffff, #f4f8ff);
}

.voice-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12rpx;
}

.voice-title-wrap {
  min-width: 0;
}

.voice-name,
.voice-region,
.voice-desc {
  display: block;
}

.voice-name {
  color: #20243f;
  font-size: 30rpx;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.voice-region {
  margin-top: 8rpx;
  color: #8a91aa;
  font-size: 22rpx;
}

.voice-tag {
  flex-shrink: 0;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(80, 98, 255, 0.1);
  color: #5362ff;
  font-size: 22rpx;
}

.voice-desc {
  height: 76rpx;
  margin-top: 18rpx;
  color: #60677f;
  font-size: 24rpx;
  line-height: 38rpx;
  overflow: hidden;
}

.voice-tags {
  height: 44rpx;
  display: flex;
  gap: 10rpx;
  margin-top: 16rpx;
  overflow: hidden;
}

.voice-chip {
  flex-shrink: 0;
  padding: 7rpx 12rpx;
  border-radius: 999rpx;
  background: #f4f6fd;
  color: #7e849e;
  font-size: 21rpx;
}

.voice-actions {
  display: flex;
  gap: 14rpx;
  margin-top: 18rpx;
}

.preview-btn,
.use-btn {
  flex: 1;
  height: 68rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 700;
}

.preview-btn {
  background: #f2f5ff;
  color: #5162ff;
}

.use-btn {
  background: #20243f;
  color: #ffffff;
}
</style>
