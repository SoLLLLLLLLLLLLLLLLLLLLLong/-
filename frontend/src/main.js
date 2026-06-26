import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router/index.js";
import "./styles.css";

// 前端应用入口。
//
// 这一层只做“装配”工作，不写具体业务逻辑：
// 1. createApp(App)：创建 Vue 应用实例
// 2. use(createPinia())：注入全局状态管理，后续页面和组件都可以拿到 store
// 3. use(router)：注入路由系统，支持 /auth 和 /chat 页面切换
// 4. mount("#app")：把整个前端应用挂到 index.html 里的 #app 节点
//
// 这里体现的知识点：
// - Vue 3 应用启动流程
// - 插件注入机制
// - 状态管理与路由的全局注册
createApp(App).use(createPinia()).use(router).mount("#app");
