<template>
  <view class="feature-card" :class="[variant]" @tap="handleTap">
    <view class="feature-icon">{{ icon }}</view>
    <view class="feature-content">
      <text class="feature-title">{{ title }}</text>
      <text class="feature-subtitle">{{ displaySubtitle }}</text>
    </view>
    <text v-if="badge" class="feature-badge">{{ badge }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: String,
    default: 'AI',
  },
  badge: {
    type: String,
    default: '',
  },
  variant: {
    type: String,
    default: 'default',
  },
})

const emit = defineEmits(['click'])

const displaySubtitle = computed(() => {
  const text = props.subtitle || ''
  return text.length > 12 ? `${text.slice(0, 12)}...` : text
})

function handleTap() {
  emit('click', props.title)
}
</script>

<style scoped>
.feature-card {
  position: relative;
  height: 176rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 0 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 32rpx rgba(102, 120, 194, 0.08);
  box-sizing: border-box;
  overflow: hidden;
}

.feature-card.hero {
  height: 370rpx;
  align-items: flex-end;
  padding-bottom: 34rpx;
  background:
    radial-gradient(circle at 20% 20%, rgba(92, 114, 255, 0.14), transparent 32%),
    linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%);
}

.feature-card.primary {
  background: linear-gradient(180deg, #ffffff 0%, #f5f9ff 100%);
}

.feature-card.accent {
  background: linear-gradient(145deg, #ffffff 0%, #f2fbff 100%);
}

.feature-icon {
  width: 76rpx;
  height: 76rpx;
  flex-shrink: 0;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4e63ff;
  font-size: 32rpx;
  font-weight: 800;
  background: linear-gradient(145deg, rgba(88, 110, 255, 0.12), rgba(53, 178, 255, 0.16));
}

.feature-card.hero .feature-icon {
  width: 110rpx;
  height: 110rpx;
  border-radius: 28rpx;
  font-size: 42rpx;
}

.feature-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.feature-title {
  display: block;
  color: #20243f;
  font-size: 32rpx;
  font-weight: 800;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feature-subtitle {
  display: block;
  height: 56rpx;
  color: #7d849f;
  font-size: 23rpx;
  line-height: 28rpx;
  overflow: hidden;
}

.feature-badge {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(74, 97, 255, 0.12);
  color: #5263ff;
  font-size: 20rpx;
  font-weight: 700;
}
</style>
