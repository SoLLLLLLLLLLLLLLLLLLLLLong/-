import { reactive } from 'vue'
import { defineStore } from 'pinia'
import { TASK_PROGRESS_STATUS, TASK_STATUSES } from '@ai-creator-workshop/shared'

const STORAGE_KEY = 'ai_creator_avatar_store'

const createPreviewUrls = () => ({
  voice: '',
  video: '',
  export: '',
  saved: '',
})

const createDefaultTask = () => ({
  id: '',
  type: '',
  status: '',
  workflowStatus: TASK_STATUSES.DRAFT,
  progress: 0,
  message: '当前暂无进行中的任务。',
  result: null,
  errorMessage: '',
  retryable: false,
  failureStage: '',
})

const createDefaultState = () => ({
  scriptText: '',
  selectedVoice: null,
  selectedAvatar: null,
  selectedBgm: null,
  selectedTemplateId: '',
  imageAsset: null,
  currentStep: 0,
  task: createDefaultTask(),
  previewUrls: createPreviewUrls(),
})

export const useAvatarCreationStore = defineStore('avatarCreation', () => {
  const state = reactive(createDefaultState())

  function persist() {
    uni.setStorageSync(
      STORAGE_KEY,
      JSON.stringify({
        scriptText: state.scriptText,
        selectedVoice: state.selectedVoice,
        selectedAvatar: state.selectedAvatar,
        selectedBgm: state.selectedBgm,
        selectedTemplateId: state.selectedTemplateId,
        imageAsset: state.imageAsset,
        currentStep: state.currentStep,
        task: state.task,
        previewUrls: state.previewUrls,
      })
    )
  }

  function restoreFromStorage() {
    const raw = uni.getStorageSync(STORAGE_KEY)
    if (!raw) {
      return
    }

    try {
      const parsed = JSON.parse(raw)
      state.scriptText = parsed.scriptText || ''
      state.selectedVoice = parsed.selectedVoice || null
      state.selectedAvatar = parsed.selectedAvatar || null
      state.selectedBgm = parsed.selectedBgm || null
      state.selectedTemplateId = parsed.selectedTemplateId || ''
      state.imageAsset = parsed.imageAsset || null
      state.currentStep = parsed.currentStep || 0
      state.task = {
        ...createDefaultTask(),
        ...(parsed.task || {}),
      }
      state.previewUrls = {
        ...createPreviewUrls(),
        ...(parsed.previewUrls || {}),
      }
    } catch (_error) {
      uni.removeStorageSync(STORAGE_KEY)
    }
  }

  function setScriptText(value) {
    state.scriptText = value
    persist()
  }

  function setSelectedVoice(voice) {
    state.selectedVoice = voice
    persist()
  }

  function setSelectedAvatar(avatar) {
    state.selectedAvatar = avatar
    persist()
  }

  function setSelectedBgm(bgm) {
    state.selectedBgm = bgm
    persist()
  }

  function setSelectedTemplateId(templateId) {
    state.selectedTemplateId = templateId
    persist()
  }

  function setImageAsset(asset) {
    state.imageAsset = asset
    persist()
  }

  function setCurrentStep(step) {
    state.currentStep = step
    persist()
  }

  function setTask(task) {
    state.task = {
      ...createDefaultTask(),
      ...task,
    }
    persist()
  }

  function setTaskMessage(message) {
    state.task = {
      ...state.task,
      message,
    }
    persist()
  }

  function setPreviewUrl(key, value) {
    state.previewUrls = {
      ...state.previewUrls,
      [key]: value,
    }
    persist()
  }

  function isTaskRunning() {
    return [TASK_PROGRESS_STATUS.QUEUED, TASK_PROGRESS_STATUS.PROCESSING].includes(state.task.status)
  }

  function resetAll() {
    Object.assign(state, createDefaultState())
    persist()
  }

  return {
    state,
    setScriptText,
    setSelectedVoice,
    setSelectedAvatar,
    setSelectedBgm,
    setSelectedTemplateId,
    setImageAsset,
    setCurrentStep,
    setTask,
    setTaskMessage,
    setPreviewUrl,
    isTaskRunning,
    restoreFromStorage,
    resetAll,
  }
})
