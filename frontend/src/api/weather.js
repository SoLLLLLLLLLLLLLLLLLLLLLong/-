import http from "./http.js";

// 天气接口。
//
// 如果前端传入 city，就按指定城市查询；
// 如果不传，后端会根据请求来源 IP 尝试推断当前城市。
export function getWeather(city = "") {
  return http.get("/weather", {
    params: city ? { city } : {},
  });
}
