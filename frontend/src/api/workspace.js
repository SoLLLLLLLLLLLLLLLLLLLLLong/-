import http from "./http.js";

export function getWorkspaceInfo(userId) {
  return http.get("/workspace", {
    params: { user_id: userId },
  });
}

export function createWorkspaceFolder(userId, folderName) {
  return http.post("/workspace/folders", {
    user_id: userId,
    folder_name: folderName,
  });
}

export function scanWorkspaceFolder(userId, folderPath) {
  return http.post("/workspace/scan", {
    user_id: userId,
    folder_path: folderPath,
  });
}
