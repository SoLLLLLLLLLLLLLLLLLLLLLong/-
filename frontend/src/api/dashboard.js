import http from "./http.js";

export function getDashboardStats(userId) {
  return http.get("/dashboard/stats", {
    params: { user_id: userId },
  });
}
