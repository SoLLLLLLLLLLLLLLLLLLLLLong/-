<template>
  <view class="panel">
    <view class="panel-head">
      <text class="panel-title">文案脚本</text>
      <text class="panel-meta">已输入 {{ wordCount }} 字</text>
    </view>

    <view class="mode-tabs">
      <view class="mode-tab active">自定义文案</view>
      <view class="mode-tab" @tap="$emit('extract')">视频提取</view>
    </view>

    <textarea
      class="script-textarea"
      :value="modelValue"
      placeholder="请输入数字人口播文案，可用于产品介绍、知识分享、品牌口播等场景。"
      maxlength="1000"
      @input="handleInput"
    />

    <view class="quick-actions">
      <view class="ghost-btn" @tap="$emit('fill-demo')">填充示例文案</view>
      <view class="primary-btn" @tap="$emit('optimize')">AI 优化改写</view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'optimize', 'fill-demo', 'extract'])

const wordCount = computed(() => props.modelValue.trim().length)

function handleInput(event) {
  emit('update:modelValue', event.detail.value)
}
</script>

<style scoped>
.panel {
  padding: 30rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20rpx 44rpx rgba(98, 113, 179, 0.08);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  color: #202445;
  font-size: 32rpx;
  font-weight: 700;
}

.panel-meta {
  color: #8e94ad;
  font-size: 22rpx;
}

.mode-tabs {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}

.mode-tab {
  padding: 14rpx 22rpx;
  border-radius: 999rpx;
  background: #f4f6ff;
  color: #8d92aa;
  font-size: 24rpx;
}

.mode-tab.active {
  background: linear-gradient(135deg, rgba(94, 101, 255, 0.12), rgba(100, 192, 255, 0.16));
  color: #5660ff;
  font-weight: 600;
}

.script-textarea {
  width: 100%;
  min-height: 320rpx;
  margin-top: 26rpx;
  padding: 24rpx;
  box-sizing: border-box;
  border-radius: 26rpx;
  background: #f8f9ff;
  color: #262b4f;
  font-size: 28rpx;
  line-height: 1.7;
}

.quick-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}

.ghost-btn,
.primary-btn {
  flex: 1;
  height: 84rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 600;
}

.ghost-btn {
  background: #f5f7ff;
  color: #5660ff;
}

.primary-btn {
  background: linear-gradient(135deg, #5f67ff 0%, #46b8ff 100%);
  color: #ffffff;
}
</style>
