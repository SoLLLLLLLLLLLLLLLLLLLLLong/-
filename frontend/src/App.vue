<template>
  <!--
    App.vue 是最顶层壳组件。

    它本身不关心“当前显示登录页还是聊天页”，
    也不关心用户、会话、消息这些业务状态。
    它只负责提供一个路由出口，让 Vue Router 决定当前该渲染哪个页面。

    这也是正式前端工程里比较常见的写法：
    - App.vue 负责最外层容器
    - router 负责页面切换
    - page/store 负责具体业务逻辑
  -->
  <RouterView />
</template>
