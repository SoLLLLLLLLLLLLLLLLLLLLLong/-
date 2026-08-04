<template>
  <view class="task-panel">
    <view class="task-head">
      <text class="task-title">任务状态</text>
      <text class="task-status" :class="statusClass">{{ statusText }}</text>
    </view>
    <text class="task-message">{{ message }}</text>
    <view class="progress-track">
      <view class="progress-bar" :style="{ width: `${safeProgress}%` }"></view>
    </view>
    <view v-if="resultText" class="task-result">
      <text class="task-result-label">结果摘要</text>
      <text class="task-result-copy">{{ resultText }}</text>
    </view>
    <view v-if="showRetry" class="task-retry" @tap="$emit('retry')">重新尝试</view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'idle',
  },
  progress: {
    type: Number,
    default: 0,
  },
  message: {
    type: String,
    default: '当前暂无进行中的任务。',
  },
  resultText: {
    type: String,
    default: '',
  },
})

defineEmits(['retry'])

const safeProgress = computed(() => Math.max(0, Math.min(100, props.progress)))

const statusText = computed(() => {
  const map = {
    idle: '未开始',
    queued: '排队中',
    processing: '生成中',
    success: '已完成',
    failed: '失败',
  }
  return map[props.status] || '未开始'
})

const statusClass = computed(() => props.status)
const showRetry = computed(() => props.status === 'failed')
</script>

<style scoped>
.task-panel {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
}

.task-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.task-title {
  color: #20243f;
  font-size: 30rpx;
  font-weight: 800;
}

.task-status {
  font-size: 24rpx;
  font-weight: 700;
}

.task-status.idle {
  color: #8f96b2;
}

.task-status.queued,
.task-status.processing {
  color: #5262ff;
}

.task-status.success {
  color: #0f9f6e;
}

.task-status.failed {
  color: #e75656;
}

.task-message {
  display: block;
  margin-top: 16rpx;
  color: #646b85;
  font-size: 24rpx;
  line-height: 1.55;
}

.progress-track {
  height: 12rpx;
  margin-top: 20rpx;
  border-radius: 999rpx;
  background: #edf1ff;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #5262ff 0%, #36a9e8 100%);
}

.task-result {
  margin-top: 20rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  background: #f7f9ff;
}

.task-result-label,
.task-result-copy {
  display: block;
}

.task-result-label {
  color: #5262ff;
  font-size: 22rpx;
  font-weight: 700;
}

.task-result-copy {
  margin-top: 10rpx;
  color: #273050;
  font-size: 24rpx;
  line-height: 1.55;
}

.task-retry {
  margin-top: 20rpx;
  height: 70rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(231, 86, 86, 0.08);
  color: #e75656;
  font-size: 24rpx;
  font-weight: 700;
}
</style>
