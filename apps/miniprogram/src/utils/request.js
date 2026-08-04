import { API_BASE_URL, DEMO_USER_ID } from '../config/app'

export function request({ url, method = 'GET', data = null }) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data,
      timeout: 20000,
      header: {
        'content-type': 'application/json',
        'x-user-id': DEMO_USER_ID,
      },
      success(response) {
        const payload = response.data
        if (response.statusCode >= 400 || (payload?.code && payload.code !== 0)) {
          reject(new Error(payload?.message || '请求失败'))
          return
        }

        resolve(payload)
      },
      fail(error) {
        reject(error)
      },
    })
  })
}
