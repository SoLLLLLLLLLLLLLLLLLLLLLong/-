<template>
  <scroll-view scroll-x class="step-progress">
    <view class="step-track">
      <view
        v-for="(step, index) in steps"
        :key="step.key"
        class="step-item"
        :class="{
          active: index === currentStep,
          done: index < currentStep,
        }"
        @tap="$emit('change', index)"
      >
        <view class="step-index">{{ String(index + 1).padStart(2, '0') }}</view>
        <view class="step-copy">
          <text class="step-name">{{ step.name }}</text>
          <text class="step-desc">{{ step.desc }}</text>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup>
defineProps({
  steps: {
    type: Array,
    default: () => [],
  },
  currentStep: {
    type: Number,
    default: 0,
  },
})

defineEmits(['change'])
</script>

<style scoped>
.step-progress {
  white-space: nowrap;
}

.step-track {
  display: flex;
  gap: 18rpx;
  padding-right: 20rpx;
}

.step-item {
  width: 250rpx;
  height: 150rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.84);
  border: 2rpx solid transparent;
  box-shadow: 0 10rpx 24rpx rgba(114, 127, 191, 0.08);
  box-sizing: border-box;
  overflow: hidden;
}

.step-item.active {
  border-color: rgba(96, 106, 255, 0.28);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(242, 245, 255, 0.98) 100%);
}

.step-item.done {
  background: linear-gradient(145deg, rgba(242, 246, 255, 0.96), rgba(237, 251, 255, 0.96));
}

.step-index {
  width: 54rpx;
  height: 54rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(95, 99, 255, 0.1);
  color: #5d63ff;
  font-size: 24rpx;
  font-weight: 700;
}

.step-copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  margin-top: 14rpx;
}

.step-name {
  color: #212642;
  font-size: 26rpx;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-desc {
  color: #8d93ad;
  font-size: 21rpx;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
