import http from "./http.js";

// 文件上传接口。
//
// 这里和普通 JSON 接口不同，必须使用 FormData：
// - file 是二进制文件对象
// - user_id 作为额外字段一并上传
//
// 数据传输流程：
// 前端 File -> FormData -> /api/upload -> 后端保存文件并构建索引 -> 返回 index_id
export function uploadKnowledgeFile(file, userId) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("user_id", String(userId));
  return http.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}
