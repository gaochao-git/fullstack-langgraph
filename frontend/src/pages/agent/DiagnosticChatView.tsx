import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Wrench, User, Bot, Plus, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState, useEffect, useRef, useCallback } from "react";
import { cn } from "@/utils/lib-utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import DiagnosticAgentWelcome from "./components/DiagnosticAgentWelcome";
import ZabbixDataRenderer, { canRenderChart } from "./components/ZabbixDataRenderer";
import { useTheme } from "@/hooks/ThemeContext";
import { theme, message } from 'antd';
import type { GlobalToken } from 'antd/es/theme/interface';

// 黑名单：不显示这些工具调用，便于用户发现和维护
const HIDDEN_TOOLS = [
  'QuestionInfoExtraction',      // 问题信息提取
  'DiagnosisReflectionOutput',   // 诊断反思输出
  'IntentAnalysisOutput'         // 意图分析输出
];

// 诊断消息中的事件类型
export interface ProcessedEvent {
  title: string;
  data: any;
}

// 工具调用组件 props
interface ToolCallProps {
  toolCall: any;
  toolResult?: any;
  isPending?: boolean; // 是否为待确认状态
  onApprove?: () => void; // 确认回调
  onReject?: () => void; // 拒绝回调
  toolCount?: number; // 新增：工具调用总数
  token?: GlobalToken; // 主题token
}

// 工具调用组件
const ToolCall: React.FC<ToolCallProps> = ({ toolCall, toolResult, isPending, onApprove, onReject, toolCount, token }) => {
  const [isExpanded, setIsExpanded] = useState(isPending || false); // 待确认状态默认展开
  
  // 如果没有传入token，使用默认的
  const themeToken = token || theme.useToken().token;
  
  // 当工具变为待审批状态时，自动展开
  useEffect(() => {
    if (isPending) {
      setIsExpanded(true);
    }
  }, [isPending]);
  
  const toolName = toolCall?.name || "Unknown Tool";
  const toolArgs = toolCall?.args || {};
  const toolResultContent = toolResult?.content || "";
  
  
  return (
    <div 
      className="border rounded-xl mb-1 shadow-sm transition-all duration-300 overflow-hidden"
      style={{ 
        borderColor: isPending ? themeToken.colorWarning : themeToken.colorPrimary,
        background: isPending ? themeToken.colorWarningBg : themeToken.colorPrimaryBg
      }}>
      {/* 工具调用头部（合并描述和折叠按钮） */}
      <div 
        className="flex items-center justify-between px-3 py-1.5 cursor-pointer transition-all duration-200 hover:opacity-90"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Wrench className="h-5 w-5" style={{ color: isPending ? themeToken.colorWarning : themeToken.colorPrimary }} />
          <span className="font-mono text-sm font-semibold truncate" style={{ color: isPending ? themeToken.colorWarning : themeToken.colorWarningText }}>{toolName}</span>
          <span className="ml-2 text-xs font-bold flex-shrink-0" style={{ color: isPending ? themeToken.colorWarning : themeToken.colorWarningText }}>工具调用（{toolCount || 1}）</span>
        </div>
        
        {/* 待确认状态的操作按钮 - 放在头部 */}
        {isPending && (
          <div className="flex gap-2 mr-2" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="default"
              size="sm"
              onClick={() => {
                console.log(`🔧 确认工具: ${toolCall.name}`, toolCall.args);
                // 传递详细的审批信息给后端
                onApprove?.();
              }}
              className="bg-green-500 hover:bg-green-600 text-white font-medium text-xs px-2 py-1 h-6"
            >
              ✅ 确认
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                console.log(`❌ 拒绝工具: ${toolCall.name}`);
                onReject?.();
              }}
              className="border-red-400 text-red-600 hover:bg-red-50 font-medium text-xs px-2 py-1 h-6"
            >
              ❌ 拒绝
            </Button>
          </div>
        )}
        
        {isExpanded ? (
          <ChevronDown className={`h-4 w-4 ${isPending ? 'text-orange-600' : 'text-cyan-300'}`} />
        ) : (
          <ChevronRight className={`h-4 w-4 ${isPending ? 'text-orange-600' : 'text-cyan-300'}`} />
        )}
      </div>
      
      {/* 展开的内容 */}
      {isExpanded && (
        <div className={`border-t-2 p-3 space-y-3 overflow-x-auto ${isPending ? 'border-orange-400' : 'border-cyan-400'}`}>
          {/* 参数 */}
          <div className="min-w-fit max-w-full">
            <h4 className={`text-sm font-bold mb-2 ${isPending ? 'text-cyan-300' : 'text-cyan-300'}`}>参数:</h4>
            <pre className={`p-3 rounded-lg text-xs overflow-x-auto whitespace-pre max-w-full border ${isPending ? 'bg-gray-900 text-cyan-300 border-cyan-500' : 'bg-gray-900 text-cyan-300 border-cyan-500'}`}>
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
          
          
          
          {/* 输出结果 */}
          {toolResultContent && (
            <div className="min-w-fit max-w-full">
              <h4 className={`text-sm font-bold mb-2 ${isPending ? 'text-cyan-300' : 'text-cyan-300'}`}>输出:</h4>
              
              {/* 工具展开后只显示原始JSON数据 */}
              <pre className={`p-3 rounded-lg text-xs overflow-x-auto max-h-48 overflow-y-auto whitespace-pre max-w-full border ${isPending ? 'bg-gray-900 text-cyan-300 border-cyan-500' : 'bg-gray-900 text-cyan-300 border-cyan-500'}`}>
                {typeof toolResultContent === 'string' 
                  ? toolResultContent 
                  : JSON.stringify(toolResultContent, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 工具调用列表组件 props
interface ToolCallsProps {
  message: Message;
  allMessages: Message[];
  interrupt?: any; // 添加interrupt数据
  onInterruptResume?: (approved: boolean | string[]) => void; // 添加interrupt处理函数
  token?: GlobalToken; // 主题token
}

// 工具调用列表组件
const ToolCalls: React.FC<ToolCallsProps> = ({ message, allMessages, interrupt, onInterruptResume, token }) => {
  const allToolCalls = (message as any).tool_calls || [];
  
  // 使用全局定义的黑名单过滤工具调用
  const toolCalls = allToolCalls.filter((call: any) => {
    const toolName = call.name || call.function?.name;
    return toolName && !HIDDEN_TOOLS.includes(toolName);
  });
  
  if (!toolCalls.length) return null;
  
  // 查找对应的工具结果
  const findToolResult = (toolCallId: string) => {
    const messageIndex = allMessages.findIndex(msg => msg.id === message.id);
    if (messageIndex === -1) return null;
    
    // 查找下一个 ToolMessage
    for (let i = messageIndex + 1; i < allMessages.length; i++) {
      const nextMessage = allMessages[i];
      if (nextMessage.type === 'tool' && (nextMessage as any).tool_call_id === toolCallId) {
        return nextMessage;
      }
    }
    return null;
  };
  
  // 检查工具调用是否为待确认状态
  const isPendingToolCall = (toolCall: any) => {
    if (!interrupt || !interrupt.value) {
      return false;
    }
    
    const interruptValue = interrupt.value;
    
    // 工具审批：使用工具名+参数精确匹配
    if (interruptValue.suggestion_type === "tool_approval") {
      return interruptValue.tool_name === toolCall.name && 
             JSON.stringify(interruptValue.tool_args) === JSON.stringify(toolCall.args || {});
    }
    
    // SOP执行：检查工具调用列表中是否包含当前工具
    if (interruptValue.suggestion_type === "sop_execution" && interruptValue.tool_calls) {
      return interruptValue.tool_calls.some((sopToolCall: any) => 
        sopToolCall.name === toolCall.name && 
        JSON.stringify(sopToolCall.args || {}) === JSON.stringify(toolCall.args || {})
      );
    }
    
    return false;
  };
  
  return (
    <div className="mb-1">
      <div className="space-y-2">
        {toolCalls.map((toolCall: any, index: number) => {
          const toolResult = findToolResult(toolCall.id);
          const isPending = isPendingToolCall(toolCall);
          return (
            <ToolCall 
              key={toolCall.id || index} 
              toolCall={toolCall}
              toolResult={toolResult}
              token={token}
              isPending={isPending}
              onApprove={() => {
                console.log(`🔧 确认工具: ${toolCall.name}`, toolCall.args);
                // 传递详细的审批信息给后端
                onInterruptResume?.(true);
              }}
              onReject={() => {
                console.log(`🔧 拒绝工具: ${toolCall.name}`, toolCall.args);
                // 传递详细的审批信息给后端
                onInterruptResume?.(false);
              }}
              toolCount={toolCalls.length}
            />
          );
        })}
      </div>
    </div>
  );
};


// 诊断聊天视图 props
interface DiagnosticChatViewProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (inputValue: string) => void;
  onCancel: () => void;
  liveActivityEvents: ProcessedEvent[];
  historicalActivities: Record<string, ProcessedEvent[]>;
  interrupt?: any; // 添加interrupt属性
  onInterruptResume?: (approved: boolean | string[]) => void; // 添加interrupt处理函数
}

// 新增：对话轮分组（每轮：用户消息+本轮所有助手消息）
interface DialogRound {
  user: Message;
  assistant: Message[];
}

// 智能体信息类型
interface Agent {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_description: string;
  agent_capabilities: string[];
  agent_status: string;
  agent_enabled: string;
  is_builtin: string;
}

// 自定义欢迎组件接口
interface WelcomeComponentProps {
  agent: Agent | null;
  onSubmit: (message: string) => void;
}

// 诊断聊天视图组件 Props 扩展
interface DiagnosticChatViewProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (input: string) => void;
  onCancel: () => void;
  liveActivityEvents: ProcessedEvent[];
  historicalActivities: Record<string, ProcessedEvent[]>;
  interrupt?: any;
  onInterruptResume?: (approved: boolean | string[]) => void;
  onNewSession?: () => void; // 新增：新建会话回调
  onHistoryToggle?: () => void; // 新增：历史会话抽屉切换回调
  availableModels?: Array<{id: string, name: string, provider: string, type: string}>; // 新增：可用模型列表
  currentModel?: string; // 新增：当前选中的模型
  onModelChange?: (modelType: string) => void; // 新增：模型切换回调
  WelcomeComponent?: React.ComponentType<WelcomeComponentProps>; // 新增：自定义欢迎组件
  agent?: Agent | null; // 新增：智能体信息
  onFileUploaded?: (fileInfo: any) => void; // 新增：文件上传回调
}

// 诊断聊天视图组件
export function DiagnosticChatView({
  messages,
  isLoading,
  onSubmit,
  onCancel,
  liveActivityEvents: _liveActivityEvents,
  historicalActivities,
  interrupt,
  onInterruptResume,
  onNewSession,
  onHistoryToggle,
  availableModels = [],
  currentModel,
  onModelChange,
  WelcomeComponent,
  agent,
  onFileUploaded,
}: DiagnosticChatViewProps) {
  const { isDark } = useTheme();
  const { token } = theme.useToken();
  const [inputValue, setInputValue] = useState<string>("");
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState<boolean>(true);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isScrollingRef = useRef<boolean>(false);
  const [uploadingImage, setUploadingImage] = useState<boolean>(false);
  
  // 处理故障诊断开始 - 将诊断消息设置到输入框
  const handleStartDiagnosis = (message: string) => {
    setInputValue(message);
  };
  
  
  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 1500);
    } catch {}
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSubmit(inputValue.trim());
      setInputValue("");
    }
  };

  // 处理粘贴事件，支持图片粘贴
  const handlePaste = async (e: React.ClipboardEvent<HTMLInputElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.indexOf('image') !== -1) {
        e.preventDefault(); // 阻止默认粘贴行为
        
        const blob = item.getAsFile();
        if (!blob) continue;

        setUploadingImage(true);
        
        try {
          // 创建 FormData
          const formData = new FormData();
          formData.append('file', blob, `paste-image-${Date.now()}.png`);

          // 调用文件上传 API
          const response = await fetch('/api/chat/files/upload', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
            },
            body: formData,
          });

          const result = await response.json();
          
          if (result.status === 'ok' && result.data) {
            // 上传成功，将文件信息添加到消息中
            const fileInfo = `[文件已上传: ${result.data.file_name}]`;
            setInputValue(prev => prev + (prev ? ' ' : '') + fileInfo);
            
            // 如果有文件管理器，更新文件列表
            if (onFileUploaded) {
              onFileUploaded(result.data);
            }
            
            message.success('图片上传成功');
          } else {
            message.error(result.msg || '图片上传失败');
          }
        } catch (error) {
          console.error('图片上传失败:', error);
          message.error('图片上传失败，请重试');
        } finally {
          setUploadingImage(false);
        }
        
        break; // 只处理第一个图片
      }
    }
  };

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (messagesContainerRef.current) {
      isScrollingRef.current = true;
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      setTimeout(() => {
        isScrollingRef.current = false;
      }, 100);
    }
  }, []);

  // 检查是否已滚动到底部
  const isAtBottom = useCallback(() => {
    if (!messagesContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    return scrollHeight - scrollTop - clientHeight < 10; // 10px 容差
  }, []);

  // 处理手动滚动
  const handleScroll = useCallback(() => {
    if (isScrollingRef.current) return; // 忽略程序化滚动
    
    const atBottom = isAtBottom();
    setIsAutoScrollEnabled(atBottom);
  }, [isAtBottom]);

  // 监听消息变化，自动滚动
  useEffect(() => {
    if (isAutoScrollEnabled && messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, isAutoScrollEnabled, scrollToBottom]);

  // 监听加载状态变化，自动滚动
  useEffect(() => {
    if (isAutoScrollEnabled && isLoading) {
      scrollToBottom();
    }
  }, [isLoading, isAutoScrollEnabled, scrollToBottom]);

  // 分组：每个人类消息+其后的所有助手消息为一轮
  const dialogRounds: DialogRound[] = [];
  let currentRound: DialogRound | null = null;
  messages.forEach((msg) => {
    if (msg.type === 'human') {
      if (currentRound) dialogRounds.push(currentRound);
      currentRound = { user: msg, assistant: [] };
    } else if (currentRound) {
      currentRound.assistant.push(msg);
    }
  });
  if (currentRound) dialogRounds.push(currentRound);

  return (
    <div className="flex flex-col h-full relative w-full overflow-x-hidden" style={{ minHeight: 0 }}>
      <style>
        {`
          @keyframes buttonSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes buttonPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.02); }
          }
        `}
      </style>
      
      {/* 头部工具栏 */}
      <div className={cn(
        "flex items-center justify-between px-4 py-3 border-b transition-colors duration-200",
        isDark 
          ? "bg-gray-800 border-gray-700" 
          : "bg-white border-gray-200"
      )}>
        <div className="flex items-center gap-2">
          <Bot className={cn("h-5 w-5", isDark ? "text-cyan-400" : "text-blue-600")} />
          <span className={cn("font-semibold", isDark ? "text-white" : "text-gray-900")}>
            {agent?.agent_name || null}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            onClick={onNewSession}
            variant="outline"
            size="sm"
            className={cn(
              "text-xs px-3 py-1.5 h-7 transition-colors duration-200",
              isDark 
                ? "bg-blue-600/20 hover:bg-blue-600/40 border-blue-500 text-blue-200 hover:text-white" 
                : "bg-blue-50 hover:bg-blue-100 border-blue-300 text-blue-700 hover:text-blue-800"
            )}
          >
            <Plus className="h-3 w-3 mr-1" />
            新建会话
          </Button>
          <Button
            onClick={onHistoryToggle}
            variant="outline"
            size="sm"
            className={cn(
              "text-xs px-3 py-1.5 h-7 transition-colors duration-200",
              isDark 
                ? "bg-purple-600/20 hover:bg-purple-600/40 border-purple-500 text-purple-200 hover:text-white" 
                : "bg-purple-50 hover:bg-purple-100 border-purple-300 text-purple-700 hover:text-purple-800"
            )}
          >
            <History className="h-3 w-3 mr-1" />
            历史会话
          </Button>
        </div>
      </div>
      
      {/* 消息区 */}
      <div
        ref={messagesContainerRef}
        className={cn(
          "flex-1 overflow-y-auto overflow-x-hidden px-4 py-6 relative transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-b from-gray-900 to-gray-800" 
            : "bg-gradient-to-b from-white to-gray-50"
        )}
        style={{ minHeight: 0, maxHeight: 'calc(100vh - 190px)' }}
        onScroll={handleScroll}
      >
        <div className="flex flex-col overflow-x-hidden">
          {messages.length === 0 && (
            <div className="w-full">
              {WelcomeComponent ? (
                <WelcomeComponent 
                  agent={agent || null}
                  onSubmit={onSubmit}
                />
              ) : (
                <DiagnosticAgentWelcome 
                  onDiagnose={() => {}} 
                  onContinueChat={() => {}}
                  onStartDiagnosis={handleStartDiagnosis}
                />
              )}
            </div>
          )}
          {dialogRounds.map((round, idx) => (
            <div key={round.user.id || idx}>
              {/* 用户消息 */}
              <div className="flex flex-col items-end mb-6 pl-4">
                <div className="flex items-center gap-2 justify-end max-w-[90%] w-full">
                  <div className="text-white rounded-2xl break-words min-h-7 overflow-x-auto min-w-fit px-4 pt-3 pb-2" style={{ 
                    backgroundColor: token.colorPrimary,
                    borderColor: token.colorPrimary,
                    border: '1px solid'
                  }}>
                    <span className="whitespace-pre-wrap">
                      {typeof round.user.content === "string" ? round.user.content : JSON.stringify(round.user.content)}
                    </span>
                  </div>
                  <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: token.colorPrimary }}>
                    <User className="h-5 w-5 text-blue-200" />
                  </div>
                </div>
              </div>
              {/* 助手合并输出区域 - 只有当有实际可显示内容时才显示 */}
              {(() => {
                // 检查是否有任何实际要渲染的内容
                let hasRenderableContent = false;
                
                round.assistant.forEach((msg) => {
                  if (msg.type === 'ai') {
                    // 检查AI内容
                    if (msg.content && String(msg.content).trim()) {
                      hasRenderableContent = true;
                    }
                    
                    // 检查工具调用（排除黑名单中的工具）
                    const toolCalls = (msg as any).tool_calls || [];
                    const visibleToolCalls = toolCalls.filter((call: any) => {
                      const toolName = call.name || call.function?.name;
                      return toolName && !HIDDEN_TOOLS.includes(toolName);
                    });
                    if (visibleToolCalls.length > 0) {
                      hasRenderableContent = true;
                    }
                  }
                });
                
                return hasRenderableContent;
              })() && (
                <div className="flex flex-col items-start mb-6 mr-2">
                  <div className="flex items-start gap-2 w-full">
                    <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: token.colorTextQuaternary }}>
                      <Bot className="h-5 w-5 text-blue-200" />
                    </div>
                    <div className="relative flex flex-col rounded-xl p-4 shadow-lg min-w-0 flex-1 overflow-hidden" style={{ 
                      border: `1px solid ${token.colorPrimary}`,
                      background: token.colorBgContainer
                    }}>
                      {(() => {
                        // 按时间顺序渲染所有消息和图表
                        const renderItems: React.ReactNode[] = [];
                        
                        round.assistant.forEach((msg, i) => {
                          if (msg.type === 'ai') {
                            const activityForThisMessage = historicalActivities[msg.id!] || [];
                            
                            // AI 消息内容
                            renderItems.push(
                              <div key={msg.id || `ai-${i}`} className="min-w-0 w-full mb-3">
                                {activityForThisMessage.length > 0 && (
                                  <div className="mb-3 border-b border-blue-300 pb-3 text-xs overflow-x-auto">
                                    <ActivityTimeline
                                      processedEvents={activityForThisMessage}
                                      isLoading={false}
                                    />
                                  </div>
                                )}
                                {/* AI 内容 - 过滤空内容 */}
                                {msg.content && String(msg.content).trim() && (
                                  <div className="mb-2 overflow-x-auto min-w-0">
                                    <div className="min-w-fit max-w-none">
                                      <MarkdownRenderer content={typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)} />
                                    </div>
                                  </div>
                                )}
                                
                                {/* 工具调用 */}
                                {(msg as any).tool_calls && (msg as any).tool_calls.length > 0 && (
                                  <div className="overflow-x-auto">
                                    <div className="min-w-fit">
                                      <ToolCalls 
                                        key={msg.id || i} 
                                        message={msg} 
                                        allMessages={messages}
                                        token={token} 
                                        interrupt={interrupt}
                                        onInterruptResume={onInterruptResume}
                                      />
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                            
                            // 为每个工具调用添加对应的图表
                            const toolCalls = (msg as any).tool_calls || [];
                            toolCalls.forEach((toolCall: any) => {
                              if (toolCall.name === 'get_zabbix_metric_data') {
                                // 查找工具调用的结果
                                const messageIndex = messages.findIndex(m => m.id === msg.id);
                                if (messageIndex !== -1) {
                                  for (let j = messageIndex + 1; j < messages.length; j++) {
                                    const nextMessage = messages[j];
                                    if (nextMessage.type === 'tool' && (nextMessage as any).tool_call_id === toolCall.id) {
                                      const toolResult = nextMessage.content;
                                      if (canRenderChart(toolResult, toolCall.name)) {
                                        renderItems.push(
                                          <div key={`chart-${toolCall.id}`} className="min-w-0 w-full mb-3">
                                            <ZabbixDataRenderer data={toolResult} toolName={toolCall.name} />
                                          </div>
                                        );
                                      }
                                      break;
                                    }
                                  }
                                }
                              }
                            });
                          }
                        });
                        
                        return renderItems;
                      })()}
                      {/* 合并区域只显示最后一条 AI 消息的复制按钮 */}
                      {(() => {
                        // 找到最后一条有内容的 AI 消息
                        const lastAiMsg = [...round.assistant].reverse().find(m => m.type === 'ai' && m.content && String(m.content).trim().length > 0);
                        if (!lastAiMsg) return null;
                        const aiContent = typeof lastAiMsg.content === 'string' ? lastAiMsg.content : JSON.stringify(lastAiMsg.content);
                        return (
                          <Button
                            variant="default"
                            className="cursor-pointer bg-blue-200 border-blue-300 text-blue-800 hover:bg-blue-300 self-end mt-2"
                            onClick={() => handleCopy(aiContent, lastAiMsg.id!)}
                          >
                            {copiedMessageId === lastAiMsg.id ? "已复制" : "复制"}
                            {copiedMessageId === lastAiMsg.id ? <CopyCheck /> : <Copy />}
                          </Button>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          
          {/* 加载状态 - 当正在加载且最后一轮没有助手气泡时显示 */}
          {isLoading && (() => {
            const lastRound = dialogRounds[dialogRounds.length - 1];
            if (!lastRound || lastRound.assistant.length === 0) return true;
            
            // 检查最后一轮是否会显示助手气泡（使用与上面气泡相同的逻辑）
            let hasRenderableContent = false;
            lastRound.assistant.forEach((msg) => {
              if (msg.type === 'ai') {
                // 检查AI内容
                if (msg.content && String(msg.content).trim()) {
                  hasRenderableContent = true;
                }
                
                // 检查工具调用（排除黑名单中的工具）
                const toolCalls = (msg as any).tool_calls || [];
                const visibleToolCalls = toolCalls.filter((call: any) => {
                  const toolName = call.name || call.function?.name;
                  return toolName && !HIDDEN_TOOLS.includes(toolName);
                });
                if (visibleToolCalls.length > 0) {
                  hasRenderableContent = true;
                }
              }
            });
            
            return !hasRenderableContent;
          })() && (
            <div className="flex flex-col items-start mb-6 mr-2">
              <div className="flex items-start gap-2 w-full">
                <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: '#374151' }}>
                  <Bot className="h-5 w-5 text-blue-200" />
                </div>
                <div className="flex items-center gap-2 text-gray-300">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  思考中...
                </div>
              </div>
            </div>
          )}
          

          {/* 保证自动滚动到底部 */}
          <div id="chat-messages-end" />
        </div>
        
      </div>
      
      {/* 输入区固定底部 */}
      <div
        className={cn(
          "sticky bottom-0 z-10 border-t-2 transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-r from-gray-800 to-gray-700 border-gray-600" 
            : "bg-gradient-to-r from-white to-gray-50 border-gray-300"
        )}
      >
        <form onSubmit={handleSubmit} className="p-2 sm:p-4">
          {/* 地址栏样式的输入容器 */}
          <div className={cn(
            "flex items-center border-2 rounded-lg overflow-hidden shadow-sm transition-all duration-200 focus-within:ring-2 focus-within:ring-cyan-400",
            isDark 
              ? "bg-gray-800 border-gray-600" 
              : "bg-white border-gray-300"
          )}>
            {/* 模型选择器 - 作为地址栏的协议部分 */}
            <div className={cn(
              "flex items-center border-r px-3 py-2.5",
              isDark 
                ? "border-gray-600" 
                : "border-gray-300"
            )}>
              <select
                value={currentModel || ''}
                onChange={(e) => onModelChange?.(e.target.value)}
                className={cn(
                  "bg-transparent text-sm font-medium cursor-pointer focus:outline-none",
                  isDark ? "text-gray-200" : "text-gray-700"
                )}
                disabled={isLoading || !!interrupt || availableModels.length === 0}
                title={availableModels.length > 0 ? `当前模型: ${availableModels.find(m => m.type === currentModel)?.name || '未选择'}` : '正在加载模型...'}
              >
                {availableModels.length > 0 ? (
                  availableModels.map((model) => {
                    return (
                      <option 
                        key={model.id} 
                        value={model.type}
                      >
                        {model.name}
                      </option>
                    );
                  })
                ) : (
                  <option value="" disabled>
                    加载中...
                  </option>
                )}
              </select>
            </div>
            
            {/* 输入框 - 作为地址栏的主体部分 */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onPaste={handlePaste}
              placeholder={interrupt ? "请先确认或取消工具执行..." : (window.innerWidth < 640 ? "请描述问题..." : "请描述您遇到的问题...")}
              className={cn(
                "flex-1 px-3 py-2.5 bg-transparent focus:outline-none text-sm sm:text-base",
                isDark 
                  ? "text-gray-100 placeholder-gray-400" 
                  : "text-gray-900 placeholder-gray-500"
              )}
              disabled={isLoading || !!interrupt || uploadingImage}
            />
            
            {/* 上传状态指示器 */}
            {uploadingImage && (
              <div className="flex items-center px-2 text-sm text-blue-500">
                <Loader2 className="w-4 h-4 animate-spin mr-1" />
                <span>上传中...</span>
              </div>
            )}
            
            {/* 发送/取消按钮 - 作为地址栏的操作部分 */}
            <div className={cn(
              "flex items-center border-l px-2",
              isDark 
                ? "border-gray-600" 
                : "border-gray-300"
            )}>
              {(isLoading || interrupt) ? (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onCancel();
                  }}
                  className={cn(
                    "p-2 rounded hover:bg-opacity-80 transition-colors duration-200 flex items-center gap-1",
                    "text-orange-500 hover:bg-orange-100"
                  )}
                  style={{
                    animation: 'buttonPulse 1.5s ease-in-out infinite'
                  }}
                >
                  <span 
                    style={{
                      display: 'inline-block',
                      width: '12px',
                      height: '12px',
                      border: '2px solid currentColor',
                      borderTop: '2px solid transparent',
                      borderRadius: '50%',
                      animation: 'buttonSpin 1s linear infinite'
                    }}
                  />
                  <span className="hidden sm:inline text-sm">取消</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!inputValue.trim()}
                  className={cn(
                    "p-2 rounded transition-colors duration-200 flex items-center gap-1",
                    !inputValue.trim()
                      ? "text-gray-400 cursor-not-allowed"
                      : "text-cyan-500 hover:bg-cyan-50 hover:text-cyan-600"
                  )}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                  </svg>
                  <span className="hidden sm:inline text-sm">发送</span>
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
} 