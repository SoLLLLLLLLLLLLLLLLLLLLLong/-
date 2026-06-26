import http from "./http.js";

export function getUserProfile(userId) {
  return http.get("/profile", {
    params: { user_id: userId },
  });
}

export function clearUserProfile(userId) {
  return http.delete("/profile", {
    params: { user_id: userId },
  });
}
