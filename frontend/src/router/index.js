import { createRouter, createWebHistory } from "vue-router";
import AuthPage from "../pages/AuthPage.vue";
import ChatPage from "../pages/ChatPage.vue";
import DashboardPage from "../pages/DashboardPage.vue";
import DocumentsPage from "../pages/DocumentsPage.vue";
import SettingsPage from "../pages/SettingsPage.vue";
import WorkspacePage from "../pages/WorkspacePage.vue";

// 根据本地是否存在 token，决定首页应该去聊天页还是登录页。
// 这里只做“粗判断”，真正校验 token 是否有效仍然要靠后端接口。
function resolveHome() {
  return localStorage.getItem("token") ? "/chat" : "/auth";
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: () => resolveHome(),
    },
    {
      path: "/auth",
      name: "auth",
      component: AuthPage,
    },
    {
      path: "/chat",
      name: "chat",
      component: ChatPage,
    },
    {
      path: "/documents",
      name: "documents",
      component: DocumentsPage,
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: DashboardPage,
    },
    {
      path: "/workspace",
      name: "workspace",
      component: WorkspacePage,
    },
    {
      path: "/settings",
      name: "settings",
      component: SettingsPage,
    },
    // 未匹配路径统一回到首页判断逻辑，避免落到空白页。
    {
      path: "/:pathMatch(.*)*",
      redirect: () => resolveHome(),
    },
  ],
});

export default router;
