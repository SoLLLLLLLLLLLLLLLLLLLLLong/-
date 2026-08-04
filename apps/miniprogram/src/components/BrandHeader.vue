<template>
  <view class="brand-header">
    <view class="brand-copy">
      <view class="brand-logo">
        <text class="logo-mark">AI</text>
      </view>
      <view class="brand-text">
        <text class="brand-name">{{ title }}</text>
        <text class="brand-tagline">{{ tagline }}</text>
      </view>
    </view>
    <view class="brand-tip">
      <text class="tip-title">{{ tipTitle }}</text>
      <text class="tip-copy">{{ tipCopy }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'AI创作工坊',
  },
  tagline: {
    type: String,
    default: '图片、音频、视频与数字人口播工具台',
  },
  tipTitle: {
    type: String,
    default: '添加到我的小程序',
  },
  tipCopy: {
    type: String,
    default: '下次打开更方便',
  },
})
</script>

<style scoped>
.brand-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.brand-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.brand-logo {
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #5262ff 0%, #35a9e8 100%);
  box-shadow: 0 16rpx 32rpx rgba(80, 98, 255, 0.22);
}

.logo-mark {
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
}

.brand-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.brand-name {
  color: #20243f;
  font-size: 40rpx;
  font-weight: 900;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-tagline {
  color: #7d849f;
  font-size: 24rpx;
  line-height: 1.45;
}

.brand-tip {
  width: 220rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, #3d85ef 0%, #5262ff 100%);
  box-shadow: 0 14rpx 30rpx rgba(80, 98, 255, 0.2);
  box-sizing: border-box;
}

.tip-title,
.tip-copy {
  display: block;
  color: #ffffff;
}

.tip-title {
  font-size: 24rpx;
  font-weight: 800;
}

.tip-copy {
  margin-top: 8rpx;
  font-size: 20rpx;
  opacity: 0.9;
  line-height: 1.45;
}
</style>
