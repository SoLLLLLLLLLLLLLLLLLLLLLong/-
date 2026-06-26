import axios from "axios";

// 从 localStorage 里读取 token。
// 普通需要鉴权的请求都会复用这里的结果。
function getToken() {
  return localStorage.getItem("token") || "";
}

// 普通 JSON 接口统一走这个 axios 实例。
// 这一层属于“请求基础设施层”：
// - baseURL：统一接口前缀
// - timeout：统一超时控制
// - request interceptor：统一加 token
// - response interceptor：统一取 data / 统一整理错误
const http = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

// 请求拦截器：
// 在请求真正发出去之前，如果本地存在 token，就自动带上。
http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：
// 成功时直接返回 response.data，调用方就不用每次写 response.data 了。
// 失败时尽量把后端 detail/message 提炼成可直接展示的 Error。
http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail =
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      "请求失败";
    return Promise.reject(new Error(detail));
  }
);

export { getToken };
export default http;
