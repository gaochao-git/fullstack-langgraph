import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Wrench, User, Bot, ArrowDown, Plus, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState, ReactNode, useEffect, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { FaultWelcomeSimple } from "./FaultWelcomeSimple";
import ZabbixDataRenderer, { canRenderChart } from "./ZabbixDataRenderer";

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


// 动态按钮文字组件
const DiagnosisButtonText: React.FC<{ text?: string }> = ({ text = "诊断中" }) => {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => {
        if (prev.length >= 3) return "";
        return prev + ".";
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <span className="flex items-center gap-2">
      <Loader2 className="h-4 w-4 animate-spin text-cyan-100" />
      {text}
      <span className="inline-block w-6 text-left">{dots}</span>
    </span>
  );
};

// 工具调用组件 props
interface ToolCallProps {
  toolCall: any;
  toolResult?: any;
  isPending?: boolean; // 是否为待确认状态
  onApprove?: () => void; // 确认回调
  onReject?: () => void; // 拒绝回调
  toolCount?: number; // 新增：工具调用总数
}

// 工具调用组件
const ToolCall: React.FC<ToolCallProps> = ({ toolCall, toolResult, isPending, onApprove, onReject, toolCount }) => {
  const [isExpanded, setIsExpanded] = useState(isPending || false); // 待确认状态默认展开
  
  const toolName = toolCall?.name || "Unknown Tool";
  const toolArgs = toolCall?.args || {};
  const toolResultContent = toolResult?.content || "";
  
  
  return (
    <div className={`border rounded-xl mb-1 shadow-sm transition-all duration-300 overflow-hidden ${isPending ? 'border-orange-400 bg-gradient-to-r from-orange-100 to-yellow-100' : 'border-cyan-400 bg-gradient-to-r from-blue-800 to-blue-900'}`}>
      {/* 工具调用头部（合并描述和折叠按钮） */}
      <div 
        className={`flex items-center justify-between px-3 py-1.5 cursor-pointer transition-all duration-200 ${isPending ? 'hover:bg-gradient-to-r hover:from-orange-200 hover:to-yellow-200' : 'hover:bg-gradient-to-r hover:from-blue-700 hover:to-blue-800'}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Wrench className={`h-5 w-5 ${isPending ? 'text-orange-600' : 'text-cyan-300'}`} />
          <span className={`font-mono text-sm font-semibold truncate ${isPending ? 'text-orange-800' : 'text-yellow-400'}`}>{toolName}</span>
          <span className={`ml-2 text-xs font-bold flex-shrink-0 ${isPending ? 'text-orange-700' : 'text-yellow-400'}`}>工具调用（{toolCount || 1}）</span>
          {isPending && (
            <Badge className="text-xs ml-2 bg-orange-500 hover:bg-orange-600 text-white border-orange-500">
              待确认
            </Badge>
          )}
        </div>
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
          
          {/* 待确认状态的操作按钮 */}
          {isPending && (
            <div className="flex gap-2 pt-1.5 border-t border-orange-200 mt-2 pt-2">
              <Button
                variant="default"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onApprove?.();
                }}
                className="bg-green-500 hover:bg-green-600 text-white"
              >
                确认执行
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onReject?.();
                }}
                className="border-gray-400 text-gray-600 hover:bg-gray-100 rounded-md"
              >
                取消
              </Button>
            </div>
          )}
          
          
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
  onInterruptResume?: (approved: boolean) => void; // 添加interrupt处理函数
}

// 工具调用列表组件
const ToolCalls: React.FC<ToolCallsProps> = ({ message, allMessages, interrupt, onInterruptResume }) => {
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
    if (!interrupt) {
      return false;
    }
    
    // 检查是否为最新的消息且有interrupt
    const isLatestMessage = allMessages.length > 0 && allMessages[allMessages.length - 1].id === message.id;
    
    if (!isLatestMessage) {
      return false;
    }
    
    // 如果是最新消息且有interrupt，则标记为待确认
    return true;
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
              isPending={isPending}
              onApprove={() => onInterruptResume?.(true)}
              onReject={() => onInterruptResume?.(false)}
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
  onInterruptResume?: (approved: boolean) => void; // 添加interrupt处理函数
}

// 新增：对话轮分组（每轮：用户消息+本轮所有助手消息）
interface DialogRound {
  user: Message;
  assistant: Message[];
}

// 诊断聊天视图组件
export function DiagnosticChatView({
  messages,
  isLoading,
  onSubmit,
  onCancel,
  liveActivityEvents,
  historicalActivities,
  interrupt,
  onInterruptResume,
}: DiagnosticChatViewProps) {
  const [inputValue, setInputValue] = useState<string>("");
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState<boolean>(true);
  const [showScrollButton, setShowScrollButton] = useState<boolean>(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isScrollingRef = useRef<boolean>(false);
  
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
    setShowScrollButton(!atBottom);
  }, [isAtBottom]);

  // 点击滚动按钮
  const handleScrollButtonClick = useCallback(() => {
    setIsAutoScrollEnabled(true);
    setShowScrollButton(false);
    scrollToBottom();
  }, [scrollToBottom]);

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
    <div className="flex flex-col h-full relative w-full overflow-x-hidden" style={{ minHeight: 0, background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 50%, #1E3A8A 100%)' }}>
      {/* 消息区 */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto overflow-x-hidden px-4 py-6 relative"
        style={{ background: 'linear-gradient(180deg, #0F172A 0%, #1E293B 100%)', minHeight: 0, maxHeight: 'calc(100vh - 140px)' }}
        onScroll={handleScroll}
      >
        <div className="flex flex-col overflow-x-hidden">
          {messages.length === 0 && (
            <div className="w-full">
              <FaultWelcomeSimple 
                onDiagnose={() => {}} 
                onContinueChat={() => {}}
                onStartDiagnosis={handleStartDiagnosis}
              />
            </div>
          )}
          {dialogRounds.map((round, idx) => (
            <div key={round.user.id || idx}>
              {/* 用户消息 */}
              <div className="flex flex-col items-end mb-6">
                <div className="flex items-center gap-2 justify-end max-w-[90%]">
                  <div className="text-white rounded-2xl break-words min-h-7 overflow-x-auto min-w-fit px-4 pt-3 pb-2 border border-cyan-400" style={{ backgroundColor: '#1D4ED8' }}>
                    <span className="whitespace-pre-wrap">
                      {typeof round.user.content === "string" ? round.user.content : JSON.stringify(round.user.content)}
                    </span>
                  </div>
                  <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: '#1E3A8A' }}>
                    <User className="h-5 w-5 text-blue-200" />
                  </div>
                </div>
              </div>
              {/* 助手合并输出区域 */}
              {round.assistant.length > 0 && (
                <div className="flex flex-col items-start mb-6">
                  <div className="flex items-start gap-2 max-w-[90%] min-w-0 w-full">
                    <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: '#374151' }}>
                      <Bot className="h-5 w-5 text-blue-200" />
                    </div>
                    <div className="relative flex flex-col rounded-xl p-4 shadow-lg min-w-0 flex-1 overflow-hidden border border-cyan-400" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 100%)' }}>
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
                                {/* AI 内容 */}
                                {msg.content && (
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
          {/* 加载状态 */}
          {isLoading && messages.length > 0 && messages[messages.length - 1]?.type === "human" && (
            <div className="flex items-center gap-2 text-gray-300 mb-6">
              <Loader2 className="h-4 w-4 animate-spin" />
              诊断中...
            </div>
          )}
          
          {/* 保证自动滚动到底部 */}
          <div id="chat-messages-end" />
        </div>
        
      </div>
      
      {/* 输入区固定底部 */}
      <div
        style={{
          position: 'sticky',
          bottom: 0,
          background: 'linear-gradient(90deg, #1E40AF 0%, #3B82F6 100%)',
          zIndex: 10,
          borderTop: '2px solid #60A5FA',
        }}
      >
        <form onSubmit={handleSubmit} className="flex gap-2 p-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={interrupt ? "请先确认或取消工具执行..." : "请描述您遇到的问题..."}
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400"
            style={{ backgroundColor: '#1E293B', borderColor: '#60A5FA', borderWidth: '2px', color: '#F1F5F9' }}
            disabled={isLoading || !!interrupt}
          />
          <Button
            type="submit"
            disabled={isLoading || !inputValue.trim() || !!interrupt}
            className="bg-cyan-500 text-white px-6 py-2 rounded-lg hover:bg-cyan-600 disabled:opacity-50 shadow-lg border border-cyan-400"
          >
            {interrupt ? <DiagnosisButtonText text="工具确认" /> : isLoading ? <DiagnosisButtonText /> : "发送"}
          </Button>
          {(isLoading || interrupt) && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="px-4 py-2 text-orange-300 border-orange-400 hover:bg-orange-900/30"
            >
              取消
            </Button>
          )}
        </form>
      </div>
    </div>
  );
} 