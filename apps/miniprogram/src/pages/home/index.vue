<template>
  <view class="page page-home">
    <scroll-view scroll-y class="page-scroll">
      <BrandHeader subtitle="图片、音频、视频与数字人口播工具台" />

      <view class="hero-grid">
        <FeatureCard
          v-for="card in heroCards"
          :key="card.key"
          :title="card.title"
          :subtitle="card.subtitle"
          :icon="card.icon"
          :badge="card.badge"
          :variant="card.variant"
          @click="handleHeroClick(card)"
        />
      </view>

      <view class="section-block">
        <SectionTitle title="核心功能" />
        <view class="feature-grid">
          <FeatureCard
            v-for="feature in coreFeatures"
            :key="feature.key"
            :title="feature.title"
            :subtitle="feature.subtitle"
            :icon="feature.icon"
            @click="handleFeatureClick(feature)"
          />
        </view>
      </view>

      <view class="section-block">
        <SectionTitle title="最近任务" caption="生成进度和失败状态会自动回到这里" />
        <view v-if="recentTasks.length" class="recent-list">
          <view v-for="task in recentTasks" :key="task.id" class="recent-item">
            <view class="recent-main">
              <text class="recent-title">{{ task.title }}</text>
              <text class="recent-meta">{{ formatType(task.type) }} · {{ formatWorkflow(task.workflowStatus) }}</text>
            </view>
            <text class="recent-status" :class="task.status">{{ formatStatus(task.status) }}</text>
          </view>
        </view>
        <view v-else class="empty-copy">暂无近期任务，进入数字人口播开始创建。</view>
      </view>

      <view class="section-block">
        <SectionTitle title="创作素材" caption="常用模板、音色和数字人快速取用" />
        <scroll-view scroll-x class="chip-scroll">
          <view class="chip-row">
            <view v-for="template in templates" :key="template.id" class="template-chip">
              {{ template.title }}
            </view>
          </view>
        </scroll-view>
        <view class="quick-card-row">
          <view class="quick-card">
            <text class="quick-title">常用音色</text>
            <text class="quick-copy">{{ commonVoices.join(' / ') || '暂无数据' }}</text>
          </view>
          <view class="quick-card">
            <text class="quick-title">热门数字人</text>
            <text class="quick-copy">{{ hotAvatars.join(' / ') || '暂无数据' }}</text>
          </view>
        </view>
      </view>

      <view class="avatar-banner" @tap="goAvatarCreate">
        <view class="banner-copy">
          <text class="banner-title">{{ bannerInfo.title }}</text>
          <text class="banner-subtitle">{{ bannerInfo.subtitle }}</text>
          <view class="banner-btn">{{ bannerInfo.actionText }}</view>
        </view>
        <view class="banner-art">
          <view class="banner-screen">
            <text class="banner-ai">AI</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import { ref } from 'vue'
import BrandHeader from '../../components/BrandHeader.vue'
import FeatureCard from '../../components/FeatureCard.vue'
import SectionTitle from '../../components/SectionTitle.vue'
import { bannerInfo, coreFeatures, heroCards } from '../../mock/home'
import { getDiscoveryData } from '../../services/ai'
import { navigateToAvatarCreate, navigateToImageCreate, showComingSoon } from '../../utils/navigation'

const recentTasks = ref([])
const templates = ref([])
const commonVoices = ref([])
const hotAvatars = ref([])

onShow(async () => {
  try {
    const response = await getDiscoveryData()
    recentTasks.value = response.data.recentTasks || []
    templates.value = response.data.templates || []
    commonVoices.value = response.data.commonVoices || []
    hotAvatars.value = response.data.hotAvatars || []
  } catch (_error) {
    recentTasks.value = []
    templates.value = []
    commonVoices.value = []
    hotAvatars.value = []
  }
})

function handleHeroClick(card) {
  if (card.key === 'image') {
    navigateToImageCreate()
    return
  }
  showComingSoon(card.title)
}

function handleFeatureClick(feature) {
  if (feature.key === 'image-create') {
    navigateToImageCreate()
    return
  }
  if (feature.available && feature.key === 'avatar') {
    goAvatarCreate()
    return
  }
  showComingSoon(feature.title)
}

function goAvatarCreate() {
  navigateToAvatarCreate()
}

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
.page-home {
  height: 100vh;
  overflow: hidden;
  padding-bottom: 0;
}

.page-scroll {
  height: calc(100vh - 100rpx);
  padding: 28rpx 24rpx calc(40rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.08fr 1fr;
  grid-template-rows: repeat(2, 176rpx);
  gap: 18rpx;
  margin-top: 26rpx;
}

.hero-grid :deep(.feature-card:first-child) {
  grid-row: span 2;
}

.section-block {
  margin-top: 28rpx;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.recent-item {
  height: 118rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 0 22rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12rpx 28rpx rgba(102, 117, 181, 0.06);
  box-sizing: border-box;
}

.recent-main {
  min-width: 0;
}

.recent-title,
.recent-meta,
.recent-status,
.quick-title,
.quick-copy,
.empty-copy {
  display: block;
}

.recent-title,
.quick-title {
  color: #20243f;
  font-size: 28rpx;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-meta,
.quick-copy,
.empty-copy {
  margin-top: 8rpx;
  color: #7d849f;
  font-size: 23rpx;
  line-height: 1.5;
}

.recent-status {
  flex-shrink: 0;
  color: #5262ff;
  font-size: 24rpx;
  font-weight: 800;
}

.recent-status.success {
  color: #0f9f6e;
}

.recent-status.failed {
  color: #e75656;
}

.chip-scroll {
  white-space: nowrap;
}

.chip-row {
  display: flex;
  gap: 14rpx;
}

.template-chip {
  padding: 14rpx 20rpx;
  border-radius: 999rpx;
  background: #f3f6ff;
  color: #5262ff;
  font-size: 24rpx;
  font-weight: 700;
}

.quick-card-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
  margin-top: 20rpx;
}

.quick-card {
  height: 150rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12rpx 28rpx rgba(102, 117, 181, 0.06);
  box-sizing: border-box;
  overflow: hidden;
}

.quick-copy {
  height: 68rpx;
  overflow: hidden;
}

.avatar-banner {
  height: 250rpx;
  display: flex;
  gap: 18rpx;
  margin-top: 28rpx;
  margin-bottom: 24rpx;
  padding: 28rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #ffffff 0%, #eef6ff 54%, #f7f3ff 100%);
  box-shadow: 0 16rpx 34rpx rgba(102, 116, 177, 0.08);
  box-sizing: border-box;
  overflow: hidden;
}

.banner-copy {
  flex: 1;
  min-width: 0;
}

.banner-title {
  display: block;
  color: #20243f;
  font-size: 40rpx;
  font-weight: 900;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.banner-subtitle {
  display: block;
  height: 68rpx;
  margin-top: 14rpx;
  color: #737b98;
  font-size: 24rpx;
  line-height: 34rpx;
  overflow: hidden;
}

.banner-btn {
  width: 160rpx;
  height: 66rpx;
  margin-top: 20rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #5262ff;
  font-size: 24rpx;
  font-weight: 800;
  box-shadow: 0 10rpx 24rpx rgba(97, 111, 175, 0.12);
}

.banner-art {
  width: 190rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-screen {
  width: 160rpx;
  height: 160rpx;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #5262ff 0%, #35aae8 100%);
  box-shadow: 0 18rpx 32rpx rgba(80, 98, 255, 0.22);
}

.banner-ai {
  color: #ffffff;
  font-size: 42rpx;
  font-weight: 900;
}
</style>
