<template>
  <div class="shell auth-layout">
    <div class="auth-card">
      <h1 class="auth-title">🤖 个人智能助手</h1>
      <p class="auth-subtitle">登录后即可使用自动路由、历史记忆和文档问答。</p>

      <form v-if="!showRegister" @submit.prevent="submitLogin">
        <div class="field">
          <label for="login-email">邮箱</label>
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
const showRegister = ref(false);
const { state, handleLogin, handleRegister, bootstrap } = useAssistantApp();

onMounted(async () => {
  const ok = await bootstrap();
  if (ok && state.user) {
    router.replace("/chat");
  }
});

async function submitLogin() {
  state.loginError = "";
  try {
    await handleLogin();
    router.replace("/chat");
  } catch (error) {
    state.loginError = error.message || "登录失败";
  }
}

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
