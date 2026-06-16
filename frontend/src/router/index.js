import { createRouter, createWebHistory } from "vue-router";
import AuthPage from "../pages/AuthPage.vue";
import ChatPage from "../pages/ChatPage.vue";

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
      path: "/:pathMatch(.*)*",
      redirect: () => resolveHome(),
    },
  ],
});

export default router;
