<template>
  <view class="avatar-card" :class="{ selected }" @tap="$emit('select', avatar)">
    <view class="avatar-preview" :style="{ background: avatar.background }">
      <text class="avatar-preview-label">{{ avatar.previewLabel }}</text>
    </view>
    <view class="avatar-content">
      <text class="avatar-name">{{ avatar.name }}</text>
      <text class="avatar-desc">{{ avatar.description }}</text>
      <view class="avatar-tags">
        <text v-for="tag in avatar.tags" :key="tag" class="avatar-tag">{{ tag }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  avatar: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['select'])
</script>

<style scoped>
.avatar-card {
  height: 430rpx;
  overflow: hidden;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid transparent;
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
}

.avatar-card.selected {
  border-color: rgba(76, 97, 255, 0.3);
}

.avatar-preview {
  height: 190rpx;
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  padding: 20rpx;
  box-sizing: border-box;
}

.avatar-preview-label {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.88);
  color: #26304d;
  font-size: 21rpx;
  font-weight: 700;
}

.avatar-content {
  padding: 20rpx;
}

.avatar-name,
.avatar-desc {
  display: block;
}

.avatar-name {
  color: #20243f;
  font-size: 28rpx;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.avatar-desc {
  height: 72rpx;
  margin-top: 12rpx;
  color: #626982;
  font-size: 22rpx;
  line-height: 36rpx;
  overflow: hidden;
}

.avatar-tags {
  height: 42rpx;
  display: flex;
  gap: 10rpx;
  margin-top: 16rpx;
  overflow: hidden;
}

.avatar-tag {
  flex-shrink: 0;
  padding: 7rpx 12rpx;
  border-radius: 999rpx;
  background: #f4f6fd;
  color: #7e849e;
  font-size: 20rpx;
}
</style>
