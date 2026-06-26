<template>
  <div class="shell auth-layout">
    <div class="auth-card">
      <h1 class="auth-title">个人智能助手</h1>
      <p class="auth-subtitle">登录后即可使用自动路由、历史记忆和文档问答。</p>

      <!--
        登录表单和注册表单通过 showRegister 切换。
        这属于最基础的“条件渲染”场景：v-if / v-else。
      -->
      <form v-if="!showRegister" @submit.prevent="submitLogin">
        <div class="field">
          <label for="login-email">邮箱</label>
          <!--
            v-model 直接把输入值绑定到 store.state.loginForm.email。
            也就是说，输入框变化 -> Vue 响应式状态变化。
          -->
          <input id="login-email" v-model="state.loginForm.email" type="email" required />
        </div>
        <div class="field">
          <label for="login-password">密码</label>
          <input
            id="login-password"
            v-model="state.loginForm.password"
            type="password"
            required
          />
        </div>
        <div class="auth-actions">
          <button class="btn btn-primary" type="submit">登录</button>
          <button class="btn btn-ghost" type="button" @click="showRegister = true">
            注册新账号
          </button>
        </div>
        <p v-if="state.loginError" class="error-text">{{ state.loginError }}</p>
      </form>

      <form v-else @submit.prevent="submitRegister">
        <div class="field">
          <label for="register-username">用户名</label>
          <input id="register-username" v-model="state.registerForm.username" required />
        </div>
        <div class="field">
          <label for="register-email">邮箱</label>
          <input id="register-email" v-model="state.registerForm.email" type="email" required />
        </div>
        <div class="field">
          <label for="register-password">密码</label>
          <input
            id="register-password"
            v-model="state.registerForm.password"
            type="password"
            required
          />
        </div>
        <div class="auth-actions">
          <button class="btn btn-primary" type="submit">完成注册</button>
          <button class="btn btn-ghost" type="button" @click="showRegister = false">
            返回登录
          </button>
        </div>
        <p v-if="state.registerError" class="error-text">{{ state.registerError }}</p>
        <p v-if="state.registerSuccess" class="success-text">{{ state.registerSuccess }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAssistantApp } from "../composables/useAssistantApp.js";

const router = useRouter();

// false 表示显示登录表单，true 表示显示注册表单。
const showRegister = ref(false);

// 页面层通过 useAssistantApp 拿到统一的状态和方法。
// 这样页面不用自己管理登录请求细节，只负责触发动作和展示结果。
const { state, handleLogin, handleRegister, bootstrap } = useAssistantApp();

// 页面一挂载就尝试恢复登录态：
// - 如果本地 token 仍然有效，就直接跳去聊天页
// - 如果无效，就留在当前登录页
onMounted(async () => {
  const ok = await bootstrap();
  if (ok && state.user) {
    router.replace("/chat");
  }
});

// 登录表单提交：
// 1. 清空上次错误
// 2. 调 store 里的 handleLogin
// 3. 登录成功后 replace 到 /chat
async function submitLogin() {
  state.loginError = "";
  try {
    await handleLogin();
    router.replace("/chat");
  } catch (error) {
    state.loginError = error.message || "登录失败";
  }
}

// 注册表单提交：
// 1. 调注册接口
// 2. 成功后切回登录表单
// 3. 错误则显示在页面上
async function submitRegister() {
  state.registerError = "";
  try {
    await handleRegister();
    showRegister.value = false;
  } catch (error) {
    state.registerError = error.message || "注册失败";
  }
}
</script>
