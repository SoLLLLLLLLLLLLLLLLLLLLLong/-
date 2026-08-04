<script>
export default {
  onLaunch() {
    console.log('AI创作工坊启动')
  },
}
</script>

<style>
page {
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(120, 104, 255, 0.12), transparent 28%),
    linear-gradient(180deg, #f7f9ff 0%, #eef3ff 100%);
  color: #1f2547;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

view,
text,
textarea,
scroll-view {
  box-sizing: border-box;
}

.page {
  min-height: 100vh;
  padding: 28rpx 24rpx calc(40rpx + env(safe-area-inset-bottom));
}
</style>
