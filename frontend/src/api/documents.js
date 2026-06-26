import http from "./http.js";

export function getDocuments(userId) {
  return http.get("/documents", {
    params: { user_id: userId },
  });
}

export function deleteDocument(documentId, userId) {
  return http.delete(`/documents/${documentId}`, {
    params: { user_id: userId },
  });
}
