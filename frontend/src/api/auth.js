import http from "./http.js";

// 认证相关接口。
// 这一层只负责“请求哪个后端地址”，不负责页面跳转和状态修改。

// 注册接口：
// 前端把用户名、邮箱、密码作为 JSON 交给后端。
// 后端会负责查重、密码哈希和用户入库。
export function register(payload) {
  return http.post("/register", payload);
}

// 登录接口：
// 当前后端 /api/token 走的是 OAuth2PasswordRequestForm，
// 所以这里不能直接发 JSON，而要发 application/x-www-form-urlencoded。
// 另外后端把 username 字段当成“邮箱/账号”来校验，这里前端传 email 即可。
export function login(payload) {
  const form = new URLSearchParams();
  form.set("username", payload.email || "");
  form.set("password", payload.password || "");

  return http.post("/token", form, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });
}

// 获取当前登录用户：
// 常用于刷新页面后的登录态恢复。
// 如果 token 失效，这一步通常会报错，前端再回到登录页。
export function getCurrentUser() {
  return http.get("/users/me");
}
