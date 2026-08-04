<template>
  <view class="action-bar">
    <view v-if="secondaryText" class="secondary-btn" @tap="$emit('secondary')">{{ secondaryText }}</view>
    <view v-if="middleText" class="middle-btn" :class="{ disabled: middleDisabled }" @tap="handleMiddle">
      {{ middleText }}
    </view>
    <view class="primary-btn" :class="{ disabled }" @tap="handlePrimary">{{ primaryText }}</view>
  </view>
</template>

<script setup>
const props = defineProps({
  primaryText: {
    type: String,
    default: '下一步',
  },
  secondaryText: {
    type: String,
    default: '',
  },
  middleText: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  middleDisabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['primary', 'secondary', 'middle'])

function handlePrimary() {
  if (props.disabled) {
    return
  }

  emit('primary')
}

function handleMiddle() {
  if (props.middleDisabled) {
    return
  }

  emit('middle')
}
</script>

<style scoped>
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 10;
  display: flex;
  gap: 14rpx;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(246, 248, 252, 0.96);
  backdrop-filter: blur(18rpx);
  box-shadow: 0 -10rpx 28rpx rgba(100, 117, 180, 0.08);
  box-sizing: border-box;
}

.secondary-btn,
.middle-btn,
.primary-btn {
  height: 86rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
  white-space: nowrap;
}

.secondary-btn {
  width: 150rpx;
  background: #ffffff;
  color: #5262ff;
  box-shadow: 0 10rpx 24rpx rgba(100, 117, 180, 0.08);
}

.middle-btn {
  flex: 1;
  background: #ffffff;
  color: #20243f;
  box-shadow: 0 10rpx 24rpx rgba(100, 117, 180, 0.08);
}

.primary-btn {
  flex: 1.35;
  color: #ffffff;
  background: linear-gradient(135deg, #4f63ff 0%, #32a8e8 100%);
  box-shadow: 0 14rpx 30rpx rgba(70, 105, 235, 0.2);
}

.primary-btn.disabled,
.middle-btn.disabled {
  opacity: 0.45;
}
</style>
