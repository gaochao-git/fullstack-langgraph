// Agent module exports
// Remove agentApi export to avoid circular dependencies
import AgentManagement from './AgentManagement';
import AgentMarketplace from './AgentMarketplace';
import AgentChat from './AgentChat';
import ChatEngine from './components/ChatEngine';
import GenericAgentWelcome from './components/GenericAgentWelcome';

export {AgentManagement,AgentMarketplace,AgentChat,ChatEngine,GenericAgentWelcome};
// Chat component exports
export { ChatMessages } from './components/ChatMessage';
export { DiagnosticAgentWelcome } from './components/DiagnosticAgentWelcome';
export type { ProcessedEvent } from './components/ChatMessage';
// 默认导出以保持兼容性
export default AgentManagement;