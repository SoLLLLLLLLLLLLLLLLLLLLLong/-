export function navigateToAvatarCreate() {
  uni.navigateTo({
    url: '/pages/avatar/create',
  })
}

export function navigateToImageCreate() {
  uni.navigateTo({
    url: '/pages/image/index',
  })
}

export function showComingSoon(featureName) {
  uni.showToast({
    title: `${featureName}建设中`,
    icon: 'none',
    duration: 1800,
  })
}
