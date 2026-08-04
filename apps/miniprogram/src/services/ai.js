import { request } from '../utils/request'

export function getDiscoveryData() {
  return request({
    url: '/api/discovery',
  })
}

export function generateScript(payload = {}) {
  return request({
    url: '/api/script/generate',
    method: 'POST',
    data: payload,
  })
}

export function synthesizeVoice(payload = {}) {
  return request({
    url: '/api/voice/tasks',
    method: 'POST',
    data: payload,
  })
}

export function createAvatarVideo(payload = {}) {
  return request({
    url: '/api/avatar/tasks',
    method: 'POST',
    data: payload,
  })
}

export function exportVideo(payload = {}) {
  return request({
    url: '/api/export/tasks',
    method: 'POST',
    data: payload,
  })
}

export function createImageTask(payload = {}) {
  return request({
    url: '/api/image/tasks',
    method: 'POST',
    data: payload,
  })
}

export function getTaskStatus(taskId) {
  return request({
    url: `/api/tasks/${taskId}`,
  })
}

export function listWorks() {
  return request({
    url: '/api/works',
  })
}

export function signUpload(payload = {}) {
  return request({
    url: '/api/uploads/sign',
    method: 'POST',
    data: payload,
  })
}
