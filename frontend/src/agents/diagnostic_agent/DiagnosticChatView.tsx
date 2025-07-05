import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState, ReactNode } from "react";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";

// 诊断消息中的事件类型
export interface ProcessedEvent {
  title: string;
  data: string;
}

// 工具调用组件 props
interface ToolCallProps {
  toolCall: any;
  toolResult?: any;
}

// 工具调用组件
const ToolCall: React.FC<ToolCallProps> = ({ toolCall, toolResult }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const toolName = toolCall?.name || "Unknown Tool";
  const toolArgs = toolCall?.args || {};
  const toolResultContent = toolResult?.content || "";
  
  return (
    <div className="border border-gray-300 rounded-lg mb-3 bg-gray-50">
      {/* 工具调用头部 */}
      <div 
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-100"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-blue-500" />
          <span className="font-mono text-sm text-blue-600">{toolName}</span>
          <Badge variant="secondary" className="text-xs">
            {toolCall?.id ? `ID: ${toolCall.id}` : "Tool Call"}
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
        <div className="border-t border-gray-300 p-3 space-y-3">
          {/* 参数 */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">参数:</h4>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto text-gray-800">
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
          
          {/* 输出结果 */}
          {toolResultContent && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">输出:</h4>
              <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto max-h-60 overflow-y-auto text-gray-800">
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
}

// 工具调用列表组件
const ToolCalls: React.FC<ToolCallsProps> = ({ message, allMessages }) => {
  const toolCalls = (message as any).tool_calls || [];
  
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
  
  return (
    <div className="mb-3">
      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
        <Settings className="h-4 w-4" />
        工具调用 ({toolCalls.length})
      </h4>
      <div className="space-y-2">
        {toolCalls.map((toolCall: any, index: number) => {
          const toolResult = findToolResult(toolCall.id);
          return (
            <ToolCall 
              key={toolCall.id || index} 
              toolCall={toolCall}
              toolResult={toolResult}
            />
          );
        })}
      </div>
    </div>
  );
};

// 用户消息组件 props
interface HumanMessageProps {
  message: Message;
}

// 用户消息组件
const HumanMessage: React.FC<HumanMessageProps> = ({ message }) => {
  return (
    <div className="flex flex-col items-end">
      <div className="text-white rounded-3xl break-words min-h-7 bg-blue-500 max-w-[100%] sm:max-w-[90%] px-4 pt-3 rounded-br-lg">
        <MarkdownRenderer content={
          typeof message.content === "string"
            ? message.content
            : JSON.stringify(message.content)
        } />
      </div>
    </div>
  );
};

// AI 消息组件 props
interface AIMessageProps {
  message: Message;
  allMessages: Message[];
  isLastMessage: boolean;
  isLoading: boolean;
  historicalActivity?: ProcessedEvent[];
  liveActivity?: ProcessedEvent[];
}

// AI 消息组件
const AIMessage: React.FC<AIMessageProps> = ({
  message,
  allMessages,
  isLastMessage,
  isLoading,
  historicalActivity,
  liveActivity,
}) => {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 1500);
    } catch {}
  };

  // 确定要显示的活动事件
  const activityForThisBubble =
    isLastMessage && isLoading ? liveActivity : historicalActivity;
  const isLiveActivityForThisBubble = isLastMessage && isLoading;

  // 检查消息内容是否为空
  const messageContent = typeof message.content === "string" ? message.content : JSON.stringify(message.content);
  const hasContent = messageContent && messageContent.trim().length > 0;

  return (
    <div className="flex flex-col items-start">
      <div className="relative break-words flex flex-col">
        {/* 活动事件时间线 */}
        {activityForThisBubble && activityForThisBubble.length > 0 && (
          <div className="mb-3 border-b border-gray-200 pb-3 text-xs">
            <div className="space-y-2">
              {activityForThisBubble.map((event, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className="w-24 text-gray-600">{event.title}</div>
                  <div className="flex-1 text-gray-700">{event.data}</div>
                </div>
              ))}
              {isLiveActivityForThisBubble && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  诊断中...
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* 工具调用 */}
        <ToolCalls message={message} allMessages={allMessages} />
        
        {/* 消息内容 - 只有当内容不为空时才渲染 */}
        {hasContent && (
          <div className="text-gray-800 break-words min-h-7 bg-gray-100 max-w-[100%] sm:max-w-[90%] px-4 pt-3 rounded-lg mb-2">
            <MarkdownRenderer content={messageContent} />
          </div>
        )}

        {/* 复制按钮 - 只有当内容不为空时才显示 */}
        {hasContent && (
          <Button
            variant="default"
            className="cursor-pointer bg-gray-200 border-gray-300 text-gray-700 hover:bg-gray-300 self-end mt-2"
            onClick={() => handleCopy(messageContent, message.id!)}
          >
            {copiedMessageId === message.id ? "已复制" : "复制"}
            {copiedMessageId === message.id ? <CopyCheck className="ml-2" /> : <Copy className="ml-2" />}
          </Button>
        )}
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
}

// 诊断聊天视图组件
export function DiagnosticChatView({
  messages,
  isLoading,
  onSubmit,
  onCancel,
  liveActivityEvents,
  historicalActivities,
}: DiagnosticChatViewProps) {
  const [inputValue, setInputValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    onSubmit(inputValue);
    setInputValue("");
  };

  return (
    <div className="flex flex-col h-full bg-white" style={{ minHeight: 0 }}>
      {/* 消息区 */}
      <div
        className="flex-1 overflow-y-auto px-4 py-6 bg-gray-50"
        style={{ minHeight: 0, maxHeight: 'calc(100vh - 180px)' }}
      >
        <div className="flex flex-col gap-8">
          {messages.map((message, index) => {
            const isLastMessage = index === messages.length - 1;
            return (
              <div key={message.id || index}>
                {message.type === "human" ? (
                  <HumanMessage message={message} />
                ) : (
                  <AIMessage
                    message={message}
                    allMessages={messages}
                    isLastMessage={isLastMessage}
                    isLoading={isLoading}
                    historicalActivity={historicalActivities[message.id!]}
                    liveActivity={isLastMessage ? liveActivityEvents : undefined}
                  />
                )}
              </div>
            );
          })}
          {isLoading && messages[messages.length - 1]?.type === "human" && (
            <div className="flex items-center gap-2 text-gray-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              诊断中...
            </div>
          )}
        </div>
      </div>

      {/* 输入区 */}
      <div
        className="sticky bottom-0 bg-white border-t border-gray-200 p-4"
        style={{ zIndex: 10 }}
      >
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="请描述您遇到的问题..."
            className="flex-1 bg-gray-100 text-gray-800 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            发送
          </Button>
          {messages.length > 0 && (
            <Button
              type="button"
              onClick={onCancel}
              variant="destructive"
              disabled={!isLoading}
            >
              取消
            </Button>
          )}
        </form>
      </div>
    </div>
  );
} 