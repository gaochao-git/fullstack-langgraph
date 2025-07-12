import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Settings, User, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState, ReactNode, useEffect } from "react";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { FaultWelcomeSimple } from "./FaultWelcomeSimple";

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
      <Loader2 className="h-4 w-4 animate-spin" />
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
}

// 工具调用组件
const ToolCall: React.FC<ToolCallProps> = ({ toolCall, toolResult, isPending, onApprove, onReject }) => {
  const [isExpanded, setIsExpanded] = useState(isPending || false); // 待确认状态默认展开
  
  const toolName = toolCall?.name || "Unknown Tool";
  const toolArgs = toolCall?.args || {};
  const toolResultContent = toolResult?.content || "";
  
  
  return (
    <div className={`border rounded-lg mb-3 ${isPending ? 'border-orange-300 bg-orange-50' : 'border-gray-300 bg-gray-50'}`}>
      {/* 工具调用头部 */}
      <div 
        className={`flex items-center justify-between p-3 cursor-pointer ${isPending ? 'hover:bg-orange-100' : 'hover:bg-gray-100'}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Settings className={`h-4 w-4 ${isPending ? 'text-orange-500' : 'text-blue-500'}`} />
          <span className={`font-mono text-sm ${isPending ? 'text-orange-700' : 'text-blue-600'}`}>{toolName}</span>
          <Badge variant={isPending ? "destructive" : "secondary"} className="text-xs">
            {isPending ? "待确认" : (toolCall?.id ? `ID: ${toolCall.id}` : "Tool Call")}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-500" />
          )}
        </div>
      </div>
      
      {/* 展开的内容 */}
      {isExpanded && (
        <div className={`border-t p-3 space-y-3 overflow-x-auto ${isPending ? 'border-orange-300' : 'border-gray-300'}`}>
          {/* 参数 */}
          <div className="min-w-fit max-w-full">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">参数:</h4>
            <pre className={`p-2 rounded text-xs overflow-x-auto text-gray-800 whitespace-pre max-w-full ${isPending ? 'bg-orange-100' : 'bg-gray-100'}`}>
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
          
          {/* 待确认状态的操作按钮 */}
          {isPending && (
            <div className="flex gap-2 pt-2 border-t border-orange-200 mt-3 pt-3">
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
                variant="destructive"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onReject?.();
                }}
              >
                取消
              </Button>
            </div>
          )}
          
          
          {/* 输出结果 */}
          {toolResultContent && (
            <div className="min-w-fit max-w-full">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">输出:</h4>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto max-h-60 overflow-y-auto text-gray-800 whitespace-pre max-w-full">
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
  
  // 过滤掉 QuestionInfoExtraction 和没有工具名的调用
  const toolCalls = allToolCalls.filter((call: any) => {
    const toolName = call.name || call.function?.name;
    return toolName && toolName !== 'QuestionInfoExtraction' && toolName !== 'DiagnosisReflectionOutput';
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
    <div className="mb-3">
      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
        <Settings className="h-4 w-4" />
        工具调用 ({toolCalls.length})
      </h4>
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
    <div className="flex flex-col h-full bg-white" style={{ minHeight: 0 }}>
      {/* 消息区 */}
      <div
        className="flex-1 overflow-y-auto px-4 py-6 bg-gray-50"
        style={{ minHeight: 0, maxHeight: 'calc(100vh - 180px)' }}
      >
        <div className="flex flex-col">
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
                <div className="flex items-center gap-2 justify-end max-w-[85%] sm:max-w-[80%]">
                  <div className="text-gray-800 rounded-2xl break-words min-h-7 bg-blue-50 overflow-x-auto min-w-fit px-4 pt-3 pb-2">
                    <span className="whitespace-pre-wrap">
                      {typeof round.user.content === "string" ? round.user.content : JSON.stringify(round.user.content)}
                    </span>
                  </div>
                  <div className="rounded-full bg-blue-100 p-2 flex-shrink-0 flex items-center justify-center">
                    <User className="h-5 w-5 text-blue-600" />
                  </div>
                </div>
              </div>
              {/* 助手合并输出区域 */}
              {round.assistant.length > 0 && (
                <div className="flex flex-col items-start mb-6">
                  <div className="flex items-start gap-2 max-w-[85%] sm:max-w-[80%] min-w-0">
                    <div className="rounded-full bg-gray-200 p-2 flex-shrink-0 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-gray-600" />
                    </div>
                    <div className="relative flex flex-col bg-gray-100 rounded-lg p-4 shadow min-w-0 flex-1 overflow-x-auto">
                      {round.assistant.map((msg, i) => {
                        // 活动事件和 AI 内容
                        if (msg.type === 'ai') {
                          const activityForThisMessage = historicalActivities[msg.id!] || [];
                          return (
                            <div key={msg.id || i} className="min-w-0 w-full">
                              {activityForThisMessage.length > 0 && (
                                <div className="mb-3 border-b border-gray-200 pb-3 text-xs overflow-x-auto">
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
                              {/* 工具调用（只渲染本条消息的 tool_calls） */}
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
                        }
                        // 工具调用结果
                        if (msg.type === 'tool') {
                          // 不单独渲染，由 ToolCalls 负责
                          return null;
                        }
                        return null;
                      })}
                      {/* 合并区域只显示最后一条 AI 消息的复制按钮 */}
                      {(() => {
                        // 找到最后一条有内容的 AI 消息
                        const lastAiMsg = [...round.assistant].reverse().find(m => m.type === 'ai' && m.content && String(m.content).trim().length > 0);
                        if (!lastAiMsg) return null;
                        const aiContent = typeof lastAiMsg.content === 'string' ? lastAiMsg.content : JSON.stringify(lastAiMsg.content);
                        return (
                          <Button
                            variant="default"
                            className="cursor-pointer bg-gray-200 border-gray-300 text-gray-700 hover:bg-gray-300 self-end mt-2"
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
            <div className="flex items-center gap-2 text-gray-600 mb-6">
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
          background: '#ffffff',
          zIndex: 10,
          borderTop: '1px solid #e5e7eb',
        }}
      >
        <form onSubmit={handleSubmit} className="flex gap-2 p-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={interrupt ? "请先确认或取消工具执行..." : "请描述您遇到的问题..."}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading || !!interrupt}
          />
          <Button
            type="submit"
            disabled={isLoading || !inputValue.trim() || !!interrupt}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            {interrupt ? <DiagnosisButtonText text="工具确认" /> : isLoading ? <DiagnosisButtonText /> : "发送"}
          </Button>
          {(isLoading || interrupt) && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              className="px-4 py-2 text-red-500 border-red-500 hover:bg-red-50"
            >
              取消
            </Button>
          )}
        </form>
      </div>
    </div>
  );
} 