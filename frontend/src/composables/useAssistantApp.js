import { useAssistantStore } from "../stores/assistant.js";

// 这个 composable 可以理解成“页面层适配器”。
// 页面组件不直接操作 Pinia 的内部结构，而是统一从这里拿状态和方法。
// 这样以后 store 内部实现调整时，页面层受到的影响会更小。
export function useAssistantApp() {
  const store = useAssistantStore();

  return {
    state: store.state,
    currentMessages: store.currentMessages,
    filteredConversations: store.filteredConversations,
    currentAttachment: store.currentAttachment,
    currentConversationTitle: store.currentConversationTitle,
    weatherCard: store.weatherCard,
    activeThinkingLogs: store.activeThinkingLogs,
    activeThinkingStatus: store.activeThinkingStatus,
    hasThinkingRecord: store.hasThinkingRecord,
    formatDate: store.formatDate,
    handleLogin: store.handleLogin,
    handleRegister: store.handleRegister,
    refreshWeather: store.refreshWeather,
    refreshDocuments: store.refreshDocuments,
    refreshSettings: store.refreshSettings,
    saveSettings: store.saveSettings,
    refreshDashboard: store.refreshDashboard,
    refreshUserProfile: store.refreshUserProfile,
    handleClearUserProfile: store.handleClearUserProfile,
    refreshWorkspace: store.refreshWorkspace,
    handleCreateWorkspaceFolder: store.handleCreateWorkspaceFolder,
    handleScanWorkspaceFolder: store.handleScanWorkspaceFolder,
    switchConversation: store.switchConversation,
    handleCreateConversation: store.handleCreateConversation,
    selectConversation: store.selectConversation,
    handleDeleteConversation: store.handleDeleteConversation,
    handleRenameConversation: store.handleRenameConversation,
    handleSendMessage: store.handleSendMessage,
    handleRegenerateMessage: store.handleRegenerateMessage,
    handleEditAndResend: store.handleEditAndResend,
    copyMessageContent: store.copyMessageContent,
    handleComposerKeydown: store.handleComposerKeydown,
    handleUploadFile: store.handleUploadFile,
    handleDeleteDocument: store.handleDeleteDocument,
    handleRemoveAttachment: store.handleRemoveAttachment,
    handleStopGeneration: store.handleStopGeneration,
    toggleThinkingCollapsed: store.toggleThinkingCollapsed,
    clearLastThinking: store.clearLastThinking,
    logout: store.logout,
    bootstrap: store.bootstrap,
    scrollMessagesToBottom: store.scrollMessagesToBottom,
  };
}
