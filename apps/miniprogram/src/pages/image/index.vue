<template>
  <view class="page page-image">
    <view class="page-shell">
      <view class="page-head">
        <text class="page-title">AI 图片生成</text>
        <text class="page-copy">当前优先使用 Kwai-Kolors/Kolors 做测试出图，适合先验证图片生成链路。</text>
      </view>

      <view class="prompt-card">
        <textarea
          class="prompt-input"
          :value="prompt"
          maxlength="300"
          placeholder="请输入出图提示词，例如：蓝白科技感、极简高级感的 AI 创作海报。"
          @input="prompt = $event.detail.value"
        />
        <view class="aspect-row">
          <view class="aspect-chip" :class="{ selected: aspectRatio === '1:1' }" @tap="aspectRatio = '1:1'">1:1</view>
          <view class="aspect-chip" :class="{ selected: aspectRatio === '9:16' }" @tap="aspectRatio = '9:16'">9:16</view>
        </view>
        <view class="generate-btn" :class="{ disabled: generating }" @tap="generateImage">
          {{ generating ? '生成中...' : '立即生成' }}
        </view>
      </view>

      <view class="result-card">
        <text class="result-title">生成结果</text>
        <image v-if="previewUrl" class="result-image" :src="previewUrl" mode="aspectFill" />
        <view v-else class="result-empty">生成完成后会在这里显示预览图</view>
        <text class="result-meta">模型：{{ selectedModel }}</text>
        <text class="result-meta">{{ statusMessage }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { createImageTask, getTaskStatus } from '../../services/ai'

const prompt = ref('')
const aspectRatio = ref('1:1')
const previewUrl = ref('')
const selectedModel = ref('Kwai-Kolors/Kolors')
const statusMessage = ref('等待生成')
const generating = ref(false)

async function generateImage() {
  if (generating.value) {
    return
  }

  try {
    generating.value = true
    statusMessage.value = '正在创建任务...'
    const created = await createImageTask({
      prompt: prompt.value || '一张科技感的 AI 创作海报',
      aspectRatio: aspectRatio.value,
    })

    let done = false
    while (!done) {
      await new Promise((resolve) => setTimeout(resolve, 1200))
      const task = await getTaskStatus(created.data.id)
      if (task.data.status === 'success') {
        previewUrl.value = task.data.result?.previewUrl || ''
        selectedModel.value = task.data.result?.selectedModel || selectedModel.value
        statusMessage.value = task.data.result?.summary || '图片生成完成'
        done = true
      } else if (task.data.status === 'failed') {
        statusMessage.value = task.data.errorMessage || '图片生成失败'
        done = true
      } else {
        statusMessage.value = `生成中 ${task.data.progress || 0}%`
      }
    }
  } catch (error) {
    statusMessage.value = error.message || '图片生成失败'
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.page-image {
  min-height: 100vh;
}

.page-shell {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.page-title,
.page-copy,
.result-title,
.result-meta {
  display: block;
}

.page-title {
  color: #20243f;
  font-size: 40rpx;
  font-weight: 900;
}

.page-copy,
.result-meta {
  margin-top: 12rpx;
  color: #7d849f;
  font-size: 24rpx;
  line-height: 1.55;
}

.prompt-card,
.result-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
}

.prompt-input {
  width: 100%;
  height: 230rpx;
  padding: 22rpx;
  border-radius: 20rpx;
  background: #f7f9ff;
  font-size: 28rpx;
  color: #20243f;
  box-sizing: border-box;
}

.aspect-row {
  display: flex;
  gap: 14rpx;
  margin-top: 18rpx;
}

.aspect-chip {
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: #f3f6ff;
  color: #7d849f;
  font-size: 24rpx;
  font-weight: 700;
}

.aspect-chip.selected {
  color: #5262ff;
}

.generate-btn {
  height: 84rpx;
  margin-top: 18rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #5262ff 0%, #35a9e8 100%);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 800;
}

.generate-btn.disabled {
  opacity: 0.5;
}

.result-title {
  color: #20243f;
  font-size: 30rpx;
  font-weight: 800;
}

.result-image,
.result-empty {
  width: 100%;
  height: 560rpx;
  margin-top: 20rpx;
  border-radius: 22rpx;
  background: #f7f9ff;
}

.result-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8790aa;
  font-size: 24rpx;
}
</style>
