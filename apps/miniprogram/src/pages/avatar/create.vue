<template>
  <view class="page page-avatar">
    <view class="page-shell">
      <view class="page-head">
        <view class="page-intro">
          <text class="intro-title">数字人口播创作</text>
          <text class="intro-copy">按文案、配音、预览、导出推进。中间内容独立滚动，底部操作始终可见。</text>
          <text class="intro-badge">当前状态：{{ workflowStatusText }}</text>
        </view>

        <StepProgress :steps="steps" :current-step="store.state.currentStep" @change="handleStepChange" />
      </view>

      <scroll-view scroll-y class="content-scroll">
        <view class="panel-stack">
          <view v-if="store.state.currentStep === 0" class="panel-block">
            <SectionTitle title="文案脚本" caption="可以手写，也可以用模板生成或改写" />
            <scroll-view scroll-x class="template-scroll">
              <view class="template-row">
                <view
                  v-for="template in templates"
                  :key="template.id"
                  class="template-pill"
                  :class="{ selected: store.state.selectedTemplateId === template.id }"
                  @tap="selectTemplate(template)"
                >
                  {{ template.title }}
                </view>
              </view>
            </scroll-view>
            <ScriptEditorPanel
              v-model="store.state.scriptText"
              @optimize="handleOptimizeScript"
              @fill-demo="fillDemoScript"
              @extract="handleComingSoon('视频提取')"
            />
            <view class="mode-actions">
              <view class="mode-btn" @tap="handleGenerateByMode('generate')">模板生成</view>
              <view class="mode-btn" @tap="handleGenerateByMode('rewrite')">压缩改写</view>
              <view class="mode-btn" @tap="handleGenerateByMode('marketing')">营销润色</view>
              <view class="mode-btn" @tap="handleGenerateByMode('knowledge')">知识讲解</view>
            </view>
          </view>

          <view v-if="store.state.currentStep === 1" class="panel-block">
            <SectionTitle title="声音合成" caption="选择音色后生成配音，后续视频会使用该声音" />
            <view class="chip-row">
              <text v-for="category in voiceCategories" :key="category" class="chip">{{ category }}</text>
            </view>
            <view class="voice-list">
              <VoiceCard
                v-for="voice in voices"
                :key="voice.id"
                :voice="voice"
                :selected="store.state.selectedVoice && store.state.selectedVoice.id === voice.id"
                @select="selectVoice"
                @preview="previewVoice"
              />
            </view>
          </view>

          <view v-if="store.state.currentStep === 2" class="panel-block">
            <SectionTitle title="生成预览" caption="先生成口播预览，满意后再进入导出" />
            <view class="preview-stage">
              <view class="stage-preview">
                <text class="stage-label">视频预览</text>
                <text class="stage-title">{{ store.state.selectedAvatar ? store.state.selectedAvatar.name : '等待选择数字人' }}</text>
                <text class="stage-copy">{{ assetHint }}</text>
                <video
                  v-if="store.state.previewUrls.video"
                  class="preview-video"
                  :src="store.state.previewUrls.video"
                  controls
                  object-fit="cover"
                />
                <view v-else class="video-empty">生成后会在这里预览口播视频</view>
              </view>
              <view class="stage-timeline">
                <view class="timeline-item active">01 文案</view>
                <view class="timeline-item active">02 配音</view>
                <view class="timeline-item active">03 预览</view>
                <view class="timeline-item">04 导出</view>
              </view>
            </view>
            <view class="upload-card">
              <text class="upload-title">驱动素材图</text>
              <text class="upload-copy">{{ store.state.imageAsset ? store.state.imageAsset.fileName : '未选择素材图，可直接使用模板数字人。' }}</text>
              <view class="upload-btn" @tap="chooseAvatarAsset">选择图片</view>
              <view v-if="store.state.imageAsset?.quality" class="quality-panel">
                <text class="quality-score">质量评分：{{ store.state.imageAsset.quality.qualityScore }}</text>
                <text class="quality-copy">
                  {{
                    store.state.imageAsset.quality.accepted
                      ? '素材通过校验，适合继续生成数字人。'
                      : store.state.imageAsset.quality.failureReason
                  }}
                </text>
              </view>
            </view>
            <view class="avatar-grid">
              <AvatarCard
                v-for="avatar in avatars"
                :key="avatar.id"
                :avatar="avatar"
                :selected="store.state.selectedAvatar && store.state.selectedAvatar.id === avatar.id"
                @select="selectAvatar"
              />
            </view>
          </view>

          <view v-if="store.state.currentStep === 3" class="panel-block">
            <SectionTitle title="预览与导出" caption="预览视频可以直接查看，导出后会尝试保存到本地" />
            <view class="result-video-card">
              <text class="upload-title">{{ store.state.previewUrls.export ? '最终成片' : '预览视频' }}</text>
              <video
                v-if="resultVideoUrl"
                class="preview-video large"
                :src="resultVideoUrl"
                controls
                object-fit="cover"
              />
              <view v-else class="video-empty">请先生成数字人口播预览</view>
              <text class="upload-copy">{{ resultVideoCopy }}</text>
              <text v-if="store.state.previewUrls.saved" class="saved-path">已保存：{{ store.state.previewUrls.saved }}</text>
            </view>

            <view class="export-settings">
              <text class="upload-title">导出设置</text>
              <view class="chip-row">
                <text v-for="category in bgmCategories" :key="category" class="chip">{{ category }}</text>
              </view>
              <view class="bgm-list">
                <view
                  v-for="track in bgmTracks"
                  :key="track.id"
                  class="bgm-card"
                  :class="{ selected: store.state.selectedBgm && store.state.selectedBgm.id === track.id }"
                  @tap="selectBgm(track)"
                >
                  <view class="bgm-main">
                    <text class="bgm-name">{{ track.name }}</text>
                    <text class="bgm-meta">{{ track.category }} · {{ track.mood }} · {{ track.duration }}</text>
                  </view>
                  <text class="bgm-pick">{{ store.state.selectedBgm && store.state.selectedBgm.id === track.id ? '已选择' : '选择' }}</text>
                </view>
              </view>
            </view>
          </view>

          <TaskStatusPanel
            :status="store.state.task.status"
            :progress="store.state.task.progress"
            :message="store.state.task.message"
            :result-text="taskResultText"
            @retry="retryCurrentAction"
          />

          <view class="preview-card">
            <text class="preview-title">当前创作摘要</text>
            <text class="preview-item">模板：{{ store.state.selectedTemplateId || '未选择模板' }}</text>
            <text class="preview-item">文案：{{ scriptSummary }}</text>
            <text class="preview-item">音色：{{ store.state.selectedVoice ? store.state.selectedVoice.name : '未选择' }}</text>
            <text class="preview-item">数字人：{{ store.state.selectedAvatar ? store.state.selectedAvatar.name : '未选择' }}</text>
            <text class="preview-item">素材图：{{ store.state.imageAsset ? store.state.imageAsset.fileName : '未上传' }}</text>
            <text class="preview-item">BGM：{{ store.state.selectedBgm ? store.state.selectedBgm.name : '可不选' }}</text>
          </view>
        </view>
      </scroll-view>

      <PrimaryActionBar
        :secondary-text="store.state.currentStep > 0 ? '上一步' : '重置'"
        :middle-text="middleButtonText"
        :primary-text="primaryButtonText"
        :disabled="primaryDisabled"
        :middle-disabled="middleDisabled"
        @secondary="handleSecondaryAction"
        @middle="handleMiddleAction"
        @primary="handlePrimaryAction"
      />
    </view>
  </view>
</template>

<script setup>
import { onHide, onShow } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { CREATION_STEPS, TASK_PROGRESS_STATUS, TASK_STATUSES } from '@ai-creator-workshop/shared'
import AvatarCard from '../../components/AvatarCard.vue'
import PrimaryActionBar from '../../components/PrimaryActionBar.vue'
import ScriptEditorPanel from '../../components/ScriptEditorPanel.vue'
import SectionTitle from '../../components/SectionTitle.vue'
import StepProgress from '../../components/StepProgress.vue'
import TaskStatusPanel from '../../components/TaskStatusPanel.vue'
import VoiceCard from '../../components/VoiceCard.vue'
import { avatars } from '../../mock/avatars'
import { bgmCategories, bgmTracks } from '../../mock/bgm'
import { voiceCategories, voices } from '../../mock/voices'
import {
  createAvatarVideo,
  exportVideo,
  generateScript,
  getDiscoveryData,
  getTaskStatus,
  signUpload,
  synthesizeVoice,
} from '../../services/ai'
import { useAvatarCreationStore } from '../../stores/avatar'
import { showComingSoon } from '../../utils/navigation'

const store = useAvatarCreationStore()
const steps = CREATION_STEPS
const templates = ref([])
const audioContext = uni.createInnerAudioContext ? uni.createInnerAudioContext() : null
let pollingTimer = null

const resultVideoUrl = computed(() => store.state.previewUrls.export || store.state.previewUrls.video)

const taskResultText = computed(() => {
  const result = store.state.task.result
  if (!result) {
    return ''
  }

  return result.text || result.summary || '任务已完成。'
})

const scriptSummary = computed(() => {
  if (!store.state.scriptText) {
    return '暂无文案'
  }

  return `${store.state.scriptText.slice(0, 36)}${store.state.scriptText.length > 36 ? '...' : ''}`
})

const workflowStatusText = computed(() => {
  const map = {
    [TASK_STATUSES.DRAFT]: '草稿',
    [TASK_STATUSES.SCRIPT_READY]: '文案完成',
    [TASK_STATUSES.VOICE_GENERATING]: '配音生成中',
    [TASK_STATUSES.VOICE_READY]: '配音完成',
    [TASK_STATUSES.AVATAR_GENERATING]: '视频生成中',
    [TASK_STATUSES.AVATAR_READY]: '可预览',
    [TASK_STATUSES.EXPORTING]: '导出中',
    [TASK_STATUSES.DONE]: '已完成',
    [TASK_STATUSES.FAILED]: '失败',
  }
  return map[store.state.task.workflowStatus] || '草稿'
})

const assetHint = computed(() => {
  if (store.state.imageAsset) {
    return '已上传人像素材，可生成更贴近素材形象的口播视频。'
  }
  return '建议上传单人正脸照片；不上传也可以先用模板数字人生成预览。'
})

const resultVideoCopy = computed(() => {
  if (store.state.previewUrls.export) {
    return '最终导出视频已生成，可以预览或保存到本地。'
  }
  if (store.state.previewUrls.video) {
    return '这是预览视频，满意后再导出最终成片。'
  }
  return '生成预览后，这里会展示可播放视频。'
})

const primaryButtonText = computed(() => {
  const step = store.state.currentStep
  if (step === 0) {
    return '下一步'
  }
  if (step === 1) {
    return store.state.previewUrls.voice ? '重新生成配音' : '生成配音'
  }
  if (step === 2) {
    return store.state.previewUrls.video ? '重新生成预览' : '生成预览视频'
  }
  return store.state.previewUrls.export ? '重新导出' : '导出成片'
})

const middleButtonText = computed(() => {
  if (store.state.currentStep === 3) {
    return '保存本地'
  }
  if (store.state.currentStep === 2 && store.state.previewUrls.video) {
    return '去导出'
  }
  return ''
})

const primaryDisabled = computed(() => {
  if (store.isTaskRunning()) {
    return true
  }

  if (store.state.currentStep === 0) {
    return !store.state.scriptText.trim()
  }
  if (store.state.currentStep === 1) {
    return !store.state.selectedVoice
  }
  if (store.state.currentStep === 2) {
    return !store.state.selectedAvatar
  }
  return !store.state.previewUrls.video
})

const middleDisabled = computed(() => {
  if (store.isTaskRunning()) {
    return true
  }
  if (store.state.currentStep === 3) {
    return !resultVideoUrl.value
  }
  return false
})

onShow(async () => {
  store.restoreFromStorage()
  try {
    const discovery = await getDiscoveryData()
    templates.value = discovery.data.templates || []
  } catch (_error) {
    templates.value = []
  }

  if (store.isTaskRunning() && store.state.task.id) {
    startPolling(store.state.task.id, store.state.task.type)
  }
})

onHide(() => {
  stopPolling()
  if (audioContext) {
    audioContext.stop()
  }
})

function handleStepChange(step) {
  if (step > store.state.currentStep && !canEnterStep(step)) {
    return
  }
  store.setCurrentStep(step)
}

function canEnterStep(step) {
  if (step >= 1 && !store.state.scriptText.trim()) {
    uni.showToast({ title: '请先输入文案', icon: 'none' })
    return false
  }
  if (step >= 2 && !store.state.selectedVoice) {
    uni.showToast({ title: '请先选择音色', icon: 'none' })
    return false
  }
  if (step >= 3 && !store.state.previewUrls.video) {
    uni.showToast({ title: '请先生成视频预览', icon: 'none' })
    return false
  }
  return true
}

function selectTemplate(template) {
  store.setSelectedTemplateId(template.id)
}

function fillDemoScript() {
  store.setScriptText(
    '大家好，欢迎来到 AI创作工坊。本期我们用一分钟演示如何从文案、配音到数字人口播视频快速完成一条产品介绍内容。'
  )
}

async function handleGenerateByMode(mode) {
  try {
    const response = await generateScript({
      text: store.state.scriptText || '请根据模板生成一段适合数字人口播的脚本。',
      mode,
      templateId: store.state.selectedTemplateId,
      scene: '数字人口播',
    })
    store.setScriptText(response.data.text)
    store.setTask({
      ...store.state.task,
      workflowStatus: TASK_STATUSES.SCRIPT_READY,
      message: '脚本已生成，可以继续选择音色。',
    })
    uni.showToast({ title: '文案已更新', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error.message || '文案生成失败', icon: 'none' })
  }
}

async function handleOptimizeScript() {
  await handleGenerateByMode('rewrite')
}

function handleComingSoon(featureName) {
  showComingSoon(featureName)
}

function selectVoice(voice) {
  store.setSelectedVoice(voice)
}

function previewVoice(voice) {
  if (!audioContext) {
    uni.showToast({ title: '当前环境不支持音频试听', icon: 'none' })
    return
  }

  audioContext.stop()
  audioContext.src = store.state.previewUrls.voice || 'https://www.w3schools.com/html/horse.mp3'
  audioContext.autoplay = true
  audioContext.play()
  uni.showToast({
    title: `正在试听 ${voice.name}`,
    icon: 'none',
  })
}

function selectAvatar(avatar) {
  store.setSelectedAvatar(avatar)
}

function selectBgm(track) {
  store.setSelectedBgm(track)
}

async function chooseAvatarAsset() {
  try {
    const chooseResult = await new Promise((resolve, reject) => {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: resolve,
        fail: reject,
      })
    })

    const filePath = chooseResult.tempFiles?.[0]?.path || chooseResult.tempFilePaths?.[0]
    const size = chooseResult.tempFiles?.[0]?.size || 0
    const fileName = filePath.split('/').pop()
    const mimeType = fileName.endsWith('.png') ? 'image/png' : 'image/jpeg'
    const imageInfo = await new Promise((resolve, reject) => {
      uni.getImageInfo({
        src: filePath,
        success: resolve,
        fail: reject,
      })
    })

    const signed = await signUpload({
      fileName,
      size,
      mimeType,
      width: imageInfo.width,
      height: imageInfo.height,
    })

    store.setImageAsset({
      assetId: signed.data.assetId,
      fileName,
      filePath,
      uploadId: signed.data.uploadId,
      objectKey: signed.data.objectKey,
      mimeType,
      size,
      width: imageInfo.width,
      height: imageInfo.height,
      previewUrl: filePath,
      quality: signed.data.quality,
    })
    uni.showToast({
      title: signed.data.quality?.accepted ? '素材图已通过校验' : '素材已记录，请按提示调整',
      icon: 'none',
    })
  } catch (error) {
    uni.showToast({ title: error.message || '素材图选择失败', icon: 'none' })
  }
}

async function handlePrimaryAction() {
  if (store.state.currentStep === 0) {
    store.setTask({
      ...store.state.task,
      workflowStatus: TASK_STATUSES.SCRIPT_READY,
      message: '脚本已准备完成，可以进入配音。',
    })
    store.setCurrentStep(1)
    return
  }

  if (store.state.currentStep === 1) {
    await createAndTrackTask('voice', () =>
      synthesizeVoice({
        scriptText: store.state.scriptText,
        voice: store.state.selectedVoice,
      })
    )
    return
  }

  if (store.state.currentStep === 2) {
    await createAndTrackTask('avatar', () =>
      createAvatarVideo({
        scriptText: store.state.scriptText,
        voiceTaskId: store.state.task.id,
        avatar: store.state.selectedAvatar,
        imageAssetId: store.state.imageAsset?.assetId || '',
        imageAsset: store.state.imageAsset,
        aspectRatio: '9:16',
        resolution: '1080P',
      })
    )
    return
  }

  await createAndTrackTask('export', () =>
    exportVideo({
      avatarTaskId: store.state.task.id,
      bgm: store.state.selectedBgm,
      coverTitle: '数字人口播成片',
      resolution: '1080P',
    })
  )
}

async function handleMiddleAction() {
  if (store.state.currentStep === 2) {
    store.setCurrentStep(3)
    return
  }

  if (store.state.currentStep === 3) {
    await saveVideoToLocal(resultVideoUrl.value)
  }
}

function handleSecondaryAction() {
  if (store.state.currentStep === 0) {
    store.resetAll()
    return
  }

  store.setCurrentStep(store.state.currentStep - 1)
}

async function retryCurrentAction() {
  await handlePrimaryAction()
}

async function createAndTrackTask(type, requestFactory) {
  try {
    const response = await requestFactory()
    const taskData = response.data

    store.setTask({
      ...taskData,
      message: '任务已创建，正在排队处理。',
    })
    startPolling(taskData.id, type)
  } catch (error) {
    store.setTask({
      ...store.state.task,
      status: TASK_PROGRESS_STATUS.FAILED,
      workflowStatus: TASK_STATUSES.FAILED,
      errorMessage: error.message || '任务创建失败',
      message: error.message || '任务创建失败',
    })
    uni.showToast({ title: error.message || '任务创建失败', icon: 'none' })
  }
}

function startPolling(taskId, type) {
  stopPolling()
  const poll = async () => {
    try {
      const response = await getTaskStatus(taskId)
      const taskData = response.data
      store.setTask(taskData)

      if ([TASK_PROGRESS_STATUS.QUEUED, TASK_PROGRESS_STATUS.PROCESSING].includes(taskData.status)) {
        pollingTimer = setTimeout(poll, 1500)
        return
      }

      await applyTaskResult(type, taskData)
      stopPolling()
    } catch (error) {
      store.setTask({
        ...store.state.task,
        status: TASK_PROGRESS_STATUS.FAILED,
        workflowStatus: TASK_STATUSES.FAILED,
        errorMessage: error.message || '任务查询失败',
        message: error.message || '任务查询失败',
      })
      stopPolling()
    }
  }

  pollingTimer = setTimeout(poll, 1000)
}

function stopPolling() {
  if (pollingTimer) {
    clearTimeout(pollingTimer)
    pollingTimer = null
  }
}

async function applyTaskResult(type, taskData) {
  const result = taskData.result || {}
  if (type === 'voice') {
    store.setPreviewUrl('voice', result.voiceUrl || '')
    store.setCurrentStep(2)
    uni.showToast({ title: '配音生成完成', icon: 'none' })
    return
  }

  if (type === 'avatar') {
    store.setPreviewUrl('video', result.previewUrl || '')
    store.setCurrentStep(3)
    uni.showToast({ title: '预览视频已生成', icon: 'none' })
    return
  }

  if (type === 'export') {
    const exportedUrl = result.previewUrl || result.fileUrl || result.downloadUrl || ''
    store.setPreviewUrl('export', exportedUrl)
    uni.showToast({ title: '导出完成，正在保存', icon: 'none' })
    if (exportedUrl) {
      await saveVideoToLocal(exportedUrl, true)
    }
    return
  }

  uni.showToast({ title: '任务已完成', icon: 'none' })
}

function downloadVideo(url) {
  return new Promise((resolve, reject) => {
    uni.downloadFile({
      url,
      success(response) {
        if (response.statusCode === 200 && response.tempFilePath) {
          resolve(response.tempFilePath)
          return
        }
        reject(new Error('视频下载失败'))
      },
      fail: reject,
    })
  })
}

function saveFile(tempFilePath) {
  return new Promise((resolve, reject) => {
    uni.saveFile({
      tempFilePath,
      success: resolve,
      fail: reject,
    })
  })
}

function saveToAlbum(tempFilePath) {
  return new Promise((resolve, reject) => {
    if (!uni.saveVideoToPhotosAlbum) {
      reject(new Error('当前环境不支持保存到相册'))
      return
    }
    uni.saveVideoToPhotosAlbum({
      filePath: tempFilePath,
      success: resolve,
      fail: reject,
    })
  })
}

async function saveVideoToLocal(url, silent = false) {
  if (!url) {
    uni.showToast({ title: '暂无可保存视频', icon: 'none' })
    return
  }

  try {
    const tempFilePath = await downloadVideo(url)
    const saved = await saveFile(tempFilePath)
    store.setPreviewUrl('saved', saved.savedFilePath || tempFilePath)

    try {
      await saveToAlbum(tempFilePath)
      uni.showToast({ title: '已保存到相册', icon: 'none' })
    } catch (_albumError) {
      uni.showToast({ title: '已保存到小程序本地', icon: 'none' })
    }
  } catch (error) {
    if (!silent) {
      uni.showToast({ title: error.message || '保存失败', icon: 'none' })
    }
  }
}
</script>

<style scoped>
.page-avatar {
  height: 100vh;
  overflow: hidden;
  padding: 0;
}

.page-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-head {
  flex-shrink: 0;
  padding: 24rpx 24rpx 16rpx;
}

.content-scroll {
  flex: 1;
  min-height: 0;
  padding: 0 24rpx calc(150rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.page-intro {
  margin-bottom: 20rpx;
}

.intro-title,
.intro-copy,
.intro-badge,
.preview-title,
.preview-item,
.upload-title,
.upload-copy,
.saved-path {
  display: block;
}

.intro-title {
  color: #20243f;
  font-size: 40rpx;
  font-weight: 900;
}

.intro-copy,
.preview-item,
.upload-copy,
.saved-path {
  margin-top: 12rpx;
  color: #7d849f;
  font-size: 24rpx;
  line-height: 1.55;
}

.intro-badge {
  margin-top: 14rpx;
  color: #5262ff;
  font-size: 24rpx;
  font-weight: 800;
}

.panel-stack {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
  padding: 10rpx 0 24rpx;
}

.panel-block {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 32rpx rgba(102, 117, 181, 0.08);
}

.preview-stage {
  margin-bottom: 20rpx;
  display: grid;
  grid-template-columns: 1fr;
  gap: 16rpx;
}

.stage-preview,
.stage-timeline,
.upload-card,
.preview-card,
.result-video-card,
.export-settings {
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f7f9ff;
}

.stage-label,
.stage-title,
.stage-copy,
.quality-score,
.quality-copy {
  display: block;
}

.stage-label,
.quality-score {
  color: #5262ff;
  font-size: 22rpx;
  font-weight: 800;
}

.stage-title {
  margin-top: 10rpx;
  color: #20243f;
  font-size: 28rpx;
  font-weight: 800;
}

.stage-copy,
.quality-copy {
  margin-top: 10rpx;
  color: #7d849f;
  font-size: 22rpx;
  line-height: 1.55;
}

.preview-video,
.video-empty {
  width: 100%;
  height: 360rpx;
  margin-top: 16rpx;
  border-radius: 20rpx;
  background: #e6ecfb;
  overflow: hidden;
}

.preview-video.large,
.result-video-card .video-empty {
  height: 460rpx;
}

.video-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8790aa;
  font-size: 24rpx;
}

.stage-timeline {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10rpx;
}

.timeline-item {
  height: 60rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #9097b0;
  font-size: 21rpx;
  font-weight: 700;
}

.timeline-item.active {
  color: #5262ff;
  background: #eef3ff;
}

.template-scroll {
  white-space: nowrap;
}

.template-row,
.chip-row,
.mode-actions {
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.template-pill,
.chip,
.mode-btn {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: #f3f6ff;
  color: #7d849f;
  font-size: 22rpx;
  font-weight: 700;
}

.template-pill.selected,
.mode-btn {
  color: #5262ff;
}

.mode-actions {
  margin-top: 18rpx;
}

.voice-list,
.bgm-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 20rpx;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 20rpx;
}

.upload-card {
  margin-top: 18rpx;
}

.upload-title,
.preview-title {
  color: #20243f;
  font-size: 28rpx;
  font-weight: 800;
}

.upload-btn {
  width: 170rpx;
  height: 66rpx;
  margin-top: 16rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #5262ff;
  font-size: 24rpx;
  font-weight: 800;
}

.quality-panel {
  margin-top: 16rpx;
  padding: 16rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.9);
}

.export-settings {
  margin-top: 18rpx;
}

.bgm-card {
  height: 108rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 0 20rpx;
  border-radius: 20rpx;
  background: #ffffff;
  box-sizing: border-box;
}

.bgm-card.selected {
  outline: 2rpx solid rgba(82, 98, 255, 0.28);
  background: #f1f5ff;
}

.bgm-main {
  min-width: 0;
}

.bgm-name,
.bgm-meta,
.bgm-pick {
  display: block;
}

.bgm-name {
  color: #20243f;
  font-size: 27rpx;
  font-weight: 800;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bgm-meta {
  margin-top: 8rpx;
  color: #8189a4;
  font-size: 22rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bgm-pick {
  flex-shrink: 0;
  color: #5262ff;
  font-size: 24rpx;
  font-weight: 800;
}

.preview-card {
  background: linear-gradient(135deg, #ffffff 0%, #f2f7ff 100%);
}

.preview-title {
  margin-bottom: 12rpx;
}

.saved-path {
  color: #0f9f6e;
  word-break: break-all;
}
</style>
