// 统一出口文件。
//
// 这样其他文件只需要从 client.js 导入，不需要关心每个接口具体放在哪个模块里。
// 这属于“接口聚合层”，方便后期继续拆分和维护。
export { register, login, getCurrentUser } from "./auth.js";
export {
  createConversation,
  getConversations,
  getConversationMessages,
  truncateConversationMessages,
  deleteConversation,
  renameConversation,
} from "./conversations.js";
export { uploadKnowledgeFile } from "./upload.js";
export { getWeather } from "./weather.js";
export { streamAgentChat } from "./chat.js";
export { getDocuments, deleteDocument } from "./documents.js";
export { getAssistantSettings, updateAssistantSettings } from "./settings.js";
export { getDashboardStats } from "./dashboard.js";
export {
  getWorkspaceInfo,
  createWorkspaceFolder,
  scanWorkspaceFolder,
} from "./workspace.js";
export { getUserProfile, clearUserProfile } from "./profile.js";
