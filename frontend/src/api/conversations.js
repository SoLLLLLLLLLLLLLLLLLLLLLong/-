import http from "./http.js";

// 会话相关接口。
// 职责是把“会话列表 / 历史消息 / 会话操作”统一封装起来。

// 创建新会话。
// 两种常见触发场景：
// 1. 用户主动点击“新建会话”
// 2. 用户第一次直接发送消息，但当前还没有会话，需要前端兜底自动创建
export function createConversation(userId) {
  return http.post("/conversations", { user_id: userId });
}

// 获取当前用户的会话列表。
// 左侧边栏显示的数据就来自这个接口。
export function getConversations(userId) {
  return http.get(`/conversations/user/${userId}`);
}

// 获取某个会话的历史消息。
// 聊天区里展示的历史内容，最终都要从这里拉回来。
export function getConversationMessages(conversationId, userId) {
  return http.get(`/conversations/${conversationId}/messages`, {
    params: { user_id: userId },
  });
}

// 截断消息。
// 主要用于“重新生成”或“编辑后重发”场景：
// 需要先把旧回答之后的消息从当前会话里截掉，再重新发送。
export function truncateConversationMessages(conversationId, messageId, userId) {
  return http.delete(`/conversations/${conversationId}/messages/from/${messageId}`, {
    params: { user_id: userId },
  });
}

// 删除会话。
// 删除成功后，前端还需要同步清理本地的消息缓存和附件映射。
export function deleteConversation(conversationId) {
  return http.delete(`/conversations/${conversationId}`);
}

// 重命名会话。
// 前端只负责把新标题传给后端，
// 真正的数据库更新由后端完成。
export function renameConversation(conversationId, name) {
  return http.put(`/conversations/${conversationId}/name`, { name });
}
