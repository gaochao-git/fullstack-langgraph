import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Settings } from "lucide-react";
import { InputForm } from "@/components/InputForm";
import { Button } from "@/components/ui/button";
import { useState, ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  ActivityTimeline,
  ProcessedEvent,
} from "@/components/ActivityTimeline"; // Assuming ActivityTimeline is in the same dir or adjust path

// Markdown component props type from former ReportView
type MdComponentProps = {
  className?: string;
  children?: ReactNode;
  [key: string]: any;
};

// Markdown components (from former ReportView.tsx)
const mdComponents = {
  h1: ({ className, children, ...props }: MdComponentProps) => (
    <h1 className={cn("text-2xl font-bold mt-4 mb-2", className)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ className, children, ...props }: MdComponentProps) => (
    <h2 className={cn("text-xl font-bold mt-3 mb-2", className)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ className, children, ...props }: MdComponentProps) => (
    <h3 className={cn("text-lg font-bold mt-3 mb-1", className)} {...props}>
      {children}
    </h3>
  ),
  p: ({ className, children, ...props }: MdComponentProps) => (
    <p className={cn("mb-3 leading-7", className)} {...props}>
      {children}
    </p>
  ),
  a: ({ className, children, href, ...props }: MdComponentProps) => (
    <Badge className="text-xs mx-0.5">
      <a
        className={cn("text-blue-400 hover:text-blue-300 text-xs", className)}
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    </Badge>
  ),
  ul: ({ className, children, ...props }: MdComponentProps) => (
    <ul className={cn("list-disc pl-6 mb-3", className)} {...props}>
      {children}
    </ul>
  ),
  ol: ({ className, children, ...props }: MdComponentProps) => (
    <ol className={cn("list-decimal pl-6 mb-3", className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ className, children, ...props }: MdComponentProps) => (
    <li className={cn("mb-1", className)} {...props}>
      {children}
    </li>
  ),
  blockquote: ({ className, children, ...props }: MdComponentProps) => (
    <blockquote
      className={cn(
        "border-l-4 border-neutral-600 pl-4 italic my-3 text-sm",
        className
      )}
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }: MdComponentProps) => (
    <code
      className={cn(
        "bg-neutral-900 rounded px-1 py-0.5 font-mono text-xs",
        className
      )}
      {...props}
    >
      {children}
    </code>
  ),
  pre: ({ className, children, ...props }: MdComponentProps) => (
    <pre
      className={cn(
        "bg-neutral-900 p-3 rounded-lg overflow-x-auto font-mono text-xs my-3",
        className
      )}
      {...props}
    >
      {children}
    </pre>
  ),
  hr: ({ className, ...props }: MdComponentProps) => (
    <hr className={cn("border-neutral-600 my-4", className)} {...props} />
  ),
  table: ({ className, children, ...props }: MdComponentProps) => (
    <div className="my-3 overflow-x-auto">
      <table className={cn("border-collapse w-full", className)} {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ className, children, ...props }: MdComponentProps) => (
    <th
      className={cn(
        "border border-neutral-600 px-3 py-2 text-left font-bold",
        className
      )}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ className, children, ...props }: MdComponentProps) => (
    <td
      className={cn("border border-neutral-600 px-3 py-2", className)}
      {...props}
    >
      {children}
    </td>
  ),
};

// Props for HumanMessageBubble
interface HumanMessageBubbleProps {
  message: Message;
  mdComponents: typeof mdComponents;
}

// HumanMessageBubble Component
const HumanMessageBubble: React.FC<HumanMessageBubbleProps> = ({
  message,
  mdComponents,
}) => {
  return (
    <div
      className={`text-white rounded-3xl break-words min-h-7 bg-blue-500 max-w-[100%] sm:max-w-[90%] px-4 pt-3 rounded-br-lg`}
    >
      <ReactMarkdown components={mdComponents}>
        {typeof message.content === "string"
          ? message.content
          : JSON.stringify(message.content)}
      </ReactMarkdown>
    </div>
  );
};

// 工具调用组件
interface ToolCallProps {
  toolCall: any;
  toolResult?: any;
}

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

// 工具调用列表组件
interface ToolCallsProps {
  message: Message;
  allMessages: Message[];
}

const ToolCalls: React.FC<ToolCallsProps> = ({ message, allMessages }) => {
  // 检查是否有工具调用
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
      <h4 className="text-sm font-semibold text-neutral-300 mb-2 flex items-center gap-2">
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

// Props for AiMessageBubble
interface AiMessageBubbleProps {
  message: Message;
  historicalActivity: ProcessedEvent[] | undefined;
  liveActivity: ProcessedEvent[] | undefined;
  isLastMessage: boolean;
  isOverallLoading: boolean;
  mdComponents: typeof mdComponents;
  handleCopy: (text: string, messageId: string) => void;
  copiedMessageId: string | null;
  allMessages: Message[];
}

// AiMessageBubble Component
const AiMessageBubble: React.FC<AiMessageBubbleProps> = ({
  message,
  historicalActivity,
  liveActivity,
  isLastMessage,
  isOverallLoading,
  mdComponents,
  handleCopy,
  copiedMessageId,
  allMessages,
}) => {
  // Determine which activity events to show and if it's for a live loading message
  const activityForThisBubble =
    isLastMessage && isOverallLoading ? liveActivity : historicalActivity;
  const isLiveActivityForThisBubble = isLastMessage && isOverallLoading;

  // 检查消息内容是否为空
  const messageContent = typeof message.content === "string" ? message.content : JSON.stringify(message.content);
  const hasContent = messageContent && messageContent.trim().length > 0;

  return (
    <div className={`relative break-words flex flex-col`}>
      {activityForThisBubble && activityForThisBubble.length > 0 && (
        <div className="mb-3 border-b border-gray-200 pb-3 text-xs">
          <ActivityTimeline
            processedEvents={activityForThisBubble}
            isLoading={isLiveActivityForThisBubble}
          />
        </div>
      )}
      
      {/* 工具调用 */}
      <ToolCalls message={message} allMessages={allMessages} />
      
      {/* 消息内容 - 只有当内容不为空时才渲染 */}
      {hasContent && (
        <div className="text-gray-800 bg-gray-100 rounded-lg p-4 mb-2">
          <ReactMarkdown components={mdComponents}>
            {messageContent}
          </ReactMarkdown>
        </div>
      )}
      
      {/* 复制按钮 - 只有当内容不为空时才显示 */}
      {hasContent && (
        <Button
          variant="default"
          className="cursor-pointer bg-gray-200 border-gray-300 text-gray-700 hover:bg-gray-300 self-end"
          onClick={() => handleCopy(messageContent, message.id!)}
        >
          {copiedMessageId === message.id ? "Copied" : "Copy"}
          {copiedMessageId === message.id ? <CopyCheck /> : <Copy />}
        </Button>
      )}
    </div>
  );
};

interface ChatMessagesViewProps {
  messages: Message[];
  isLoading: boolean;
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;
  onSubmit: (inputValue: string, effort?: string, model?: string) => void;
  onCancel: () => void;
  liveActivityEvents: ProcessedEvent[];
  historicalActivities: Record<string, ProcessedEvent[]>;
  isDiagnosticMode?: boolean;
}

export function ChatMessagesView({
  messages,
  isLoading,
  scrollAreaRef,
  onSubmit,
  onCancel,
  liveActivityEvents,
  historicalActivities,
  isDiagnosticMode = false,
}: ChatMessagesViewProps) {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 1500);
    } catch {}
  };

  return (
    <div className="flex flex-col h-full bg-white" style={{ minHeight: 0 }}>
      {/* 消息区 */}
      <div
        className="flex-1 overflow-y-auto px-4 py-6 bg-gray-50"
        style={{ minHeight: 0, maxHeight: 'calc(100vh - 180px)' }}
        ref={scrollAreaRef as any}
      >
        <div className="flex flex-col gap-8">
          {messages.map((message, index) => {
            const isLastMessage = index === messages.length - 1;
            return (
                <div
                key={message.id || index}
                className={`flex flex-col ${
                  message.type === "human" ? "items-end" : "items-start"
                  }`}
                >
                  {message.type === "human" ? (
                    <HumanMessageBubble
                      message={message}
                      mdComponents={mdComponents}
                    />
                  ) : (
                    <AiMessageBubble
                      message={message}
                      historicalActivity={historicalActivities[message.id!]}
                    liveActivity={isLastMessage ? liveActivityEvents : undefined}
                    isLastMessage={isLastMessage}
                    isOverallLoading={isLoading}
                      mdComponents={mdComponents}
                      handleCopy={handleCopy}
                      copiedMessageId={copiedMessageId}
                      allMessages={messages}
                    />
                  )}
              </div>
            );
          })}
          {isLoading && messages[messages.length - 1]?.type === "human" && (
            <div className="flex items-center gap-2 text-gray-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              {isDiagnosticMode ? "Diagnosing..." : "Researching..."}
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
        <InputForm
          onSubmit={onSubmit}
          onCancel={onCancel}
          isLoading={isLoading}
          hasHistory={messages.length > 0}
          isDiagnosticMode={isDiagnosticMode}
        />
      </div>
    </div>
  );
}
