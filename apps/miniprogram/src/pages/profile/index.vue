<template>
  <view class="page profile-page">
    <view class="hero-card">
      <text class="hero-title">AI 创作工坊账户</text>
      <text class="hero-copy">当前为演示用户视角。这里展示任务统计、最近使用和后续可扩展的会员信息。</text>
    </view>

    <view class="stats-grid">
      <view class="stat-card">
        <text class="stat-value">{{ stats.total }}</text>
        <text class="stat-label">总任务数</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ stats.success }}</text>
        <text class="stat-label">完成任务</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ stats.failed }}</text>
        <text class="stat-label">失败任务</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ stats.avatar }}</text>
        <text class="stat-label">数字人任务</text>
      </view>
    </view>

    <view class="panel-card">
      <text class="panel-title">最近使用模板</text>
      <text class="panel-copy">{{ recentTemplateTitle }}</text>
    </view>

    <view class="panel-card">
      <text class="panel-title">系统说明</text>
      <text class="panel-copy">模型密钥只保存在服务端环境变量中，前端不直连上游模型服务。长任务会在服务端持续执行，返回页面时可恢复状态。</text>
    </view>
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import { computed, reactive, ref } from 'vue'
import { listWorks } from '../../services/ai'
import { useAvatarCreationStore } from '../../stores/avatar'

const stats = reactive({
  total: 0,
  success: 0,
  failed: 0,
  avatar: 0,
})

const store = useAvatarCreationStore()
const works = ref([])

const recentTemplateTitle = computed(() => {
  if (!store.state.selectedTemplateId) {
    return '暂无记录'
  }

  return store.state.selectedTemplateId
})

onShow(async () => {
  try {
    const response = await listWorks()
    works.value = response.data || []
    stats.total = works.value.length
    stats.success = works.value.filter((item) => item.status === 'success').length
    stats.failed = works.value.filter((item) => item.status === 'failed').length
    stats.avatar = works.value.filter((item) => item.type === 'avatar').length
  } catch (_error) {
    stats.total = 0
    stats.success = 0
    stats.failed = 0
    stats.avatar = 0
  }
})
</script>

<style scoped>
.hero-card,
.panel-card,
.stat-card {
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
}

.hero-card,
.panel-card {
  padding: 24rpx;
  border-radius: 24rpx;
}

.hero-title,
.hero-copy,
.panel-title,
.panel-copy,
.stat-value,
.stat-label {
  display: block;
}

.hero-title,
.panel-title {
  color: #20243f;
  font-size: 34rpx;
  font-weight: 900;
}

.hero-copy,
.panel-copy,
.stat-label {
  margin-top: 12rpx;
  color: #7d849f;
  font-size: 24rpx;
  line-height: 1.55;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 24rpx;
}

.stat-card {
  height: 150rpx;
  padding: 24rpx;
  border-radius: 22rpx;
  box-sizing: border-box;
}

.stat-value {
  color: #5262ff;
  font-size: 38rpx;
  font-weight: 900;
}

.panel-card {
  margin-top: 24rpx;
}
</style>
