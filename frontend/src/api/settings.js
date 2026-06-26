import http from "./http.js";

export function getAssistantSettings(userId) {
  return http.get("/assistant/settings", {
    params: { user_id: userId },
  });
}

export function updateAssistantSettings(userId, settings) {
  return http.put("/assistant/settings", {
    user_id: userId,
    ...settings,
  });
}
