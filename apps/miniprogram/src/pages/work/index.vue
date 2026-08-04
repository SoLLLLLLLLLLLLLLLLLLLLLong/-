<template>
  <view class="page works-page">
    <view class="page-head">
      <text class="page-title">作品与任务中心</text>
      <text class="page-copy">查看配音、数字人视频和导出成片，支持失败追踪与质量评分。</text>
    </view>

    <view v-if="works.length" class="work-grid">
      <view v-for="work in works" :key="work.id" class="work-card">
        <view class="card-cover">
          <view class="cover-badge">{{ formatType(work.type) }}</view>
          <text class="cover-score">质量 {{ work.qualityScore || 0 }}</text>
        </view>
        <view class="card-body">
          <view class="work-top">
            <view class="work-main">
              <text class="work-title">{{ work.title }}</text>
              <text class="work-meta">{{ formatWorkflow(work.workflowStatus) }} · {{ formatStatus(work.status) }}</text>
            </view>
            <text class="work-status" :class="work.status">{{ formatStatus(work.status) }}</text>
          </view>
          <text class="work-detail">{{ work.result?.summary || work.errorMessage || '任务处理中，请稍后刷新。' }}</text>
          <text v-if="work.failureStage" class="work-failure">失败阶段：{{ work.failureStage }}</text>
          <text v-if="work.previewUrl" class="work-link">预览：{{ work.previewUrl }}</text>
          <text v-if="work.downloadUrl" class="work-link">导出：{{ work.downloadUrl }}</text>
        </view>
      </view>
    </view>

    <view v-else class="empty-card">
      <text class="empty-title">当前还没有作品记录</text>
      <text class="empty-copy">进入首页后选择“数字人口播”，完成一条链路后这里会自动出现记录。</text>
    </view>
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import { listWorks } from '../../services/ai'

const works = ref([])

onShow(async () => {
  try {
    const response = await listWorks()
    works.value = response.data || []
  } catch (_error) {
    works.value = []
  }
})

function formatType(type) {
  const map = {
    script: '文案',
    voice: '配音',
    avatar: '数字人',
    export: '导出',
    image: '图片',
  }
  return map[type] || type
}

function formatWorkflow(status) {
  const map = {
    draft: '草稿',
    script_ready: '文案完成',
    voice_generating: '配音中',
    voice_ready: '配音完成',
    avatar_generating: '视频生成中',
    avatar_ready: '可预览',
    exporting: '导出中',
    done: '已完成',
    failed: '失败',
  }
  return map[status] || '未开始'
}

function formatStatus(status) {
  const map = {
    queued: '排队中',
    processing: '处理中',
    success: '已完成',
    failed: '失败',
  }
  return map[status] || '未开始'
}
</script>

<style scoped>
.page-head {
  margin-bottom: 28rpx;
}

.page-title,
.page-copy,
.work-title,
.work-meta,
.work-detail,
.work-link,
.empty-title,
.empty-copy,
.work-failure,
.cover-score,
.cover-badge {
  display: block;
}

.page-title,
.empty-title {
  color: #20243f;
  font-size: 40rpx;
  font-weight: 900;
}

.page-copy,
.empty-copy {
  margin-top: 12rpx;
  color: #7d849f;
  font-size: 24rpx;
  line-height: 1.55;
}

.work-grid {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.work-card,
.empty-card {
  overflow: hidden;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
}

.card-cover {
  position: relative;
  height: 170rpx;
  padding: 22rpx;
  background: linear-gradient(135deg, #5262ff 0%, #35a9e8 100%);
  box-sizing: border-box;
}

.cover-badge,
.cover-score {
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 800;
}

.cover-score {
  position: absolute;
  right: 22rpx;
  bottom: 22rpx;
}

.card-body,
.empty-card {
  padding: 24rpx;
}

.work-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.work-main {
  min-width: 0;
}

.work-title {
  color: #20243f;
  font-size: 30rpx;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.work-meta {
  margin-top: 8rpx;
  color: #858ca6;
  font-size: 22rpx;
}

.work-status {
  flex-shrink: 0;
  font-size: 24rpx;
  font-weight: 800;
}

.work-status.queued,
.work-status.processing {
  color: #5262ff;
}

.work-status.success {
  color: #0f9f6e;
}

.work-status.failed {
  color: #e75656;
}

.work-detail,
.work-failure {
  margin-top: 16rpx;
  color: #5d657e;
  font-size: 24rpx;
  line-height: 1.55;
}

.work-failure {
  color: #e75656;
}

.work-link {
  margin-top: 12rpx;
  color: #5262ff;
  font-size: 22rpx;
  word-break: break-all;
}
</style>
