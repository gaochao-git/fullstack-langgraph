import { useState } from "react";
import type { Message } from "@langchain/langgraph-sdk";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Copy, CopyCheck, ChevronDown, ChevronRight, Settings, Loader2 } from "lucide-react";
import { ActivityTimeline } from "./ActivityTimeline";
import { InputForm } from "./InputForm";

// 处理过的事件类型
export interface ProcessedEvent {
  title: string;
  data: any;
}

// 消息组合类型
interface MessageGroup {
  id: string;
  start: number; // allMessages 的起始 index（包含）
  end: number;   // allMessages 的结束 index（不包含）
  humanMessage: Message;
  isLastGroup: boolean;
  isLoading: boolean;
}

// 将消息按对话组合
const groupMessages = (messages: Message[]): MessageGroup[] => {
  const groups: MessageGroup[] = [];
  let start = 0;
  for (let i = 0; i < messages.length; i++) {
    if (messages[i].type === 'human') {
      if (i > start) {
        // 上一组结束
        groups[groups.length - 1].end = i;
      }
      groups.push({
        id: messages[i].id || `group-${i}`,
        start: i,
        end: messages.length, // 先设为结尾，后面遇到下一个 human 会修正
        humanMessage: messages[i],
        isLastGroup: false,
        isLoading: false,
      });
      start = i;
    }
  }
  // 修正最后一组
  if (groups.length > 0) {
    groups[groups.length - 1].end = messages.length;
    groups[groups.length - 1].isLastGroup = true;
  }
  return groups;
};

// 工具调用组件
const ToolCall: React.FC<{
  toolCall: any;
  toolResult?: any;
}> = ({ toolCall, toolResult }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const toolName = toolCall?.name || toolCall?.function?.name || "Unknown Tool";
  const toolArgs = toolCall?.args || toolCall?.function?.arguments || {};
  const toolResultContent = toolResult?.content || "";
  return (
    <div className="border border-gray-300 rounded-lg mb-1 bg-gray-50">
      <div 
        className="flex items-center justify-between p-2 cursor-pointer hover:bg-gray-100"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 flex-1">
          <Settings className="h-4 w-4 text-blue-500" />
          <span className="text-xs text-gray-600">工具调用</span>
          <span className="font-mono text-sm text-blue-600">{toolName}</span>
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-gray-500 ml-auto" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-500 ml-auto" />
          )}
        </div>
      </div>
      {isExpanded && (
        <div className="border-t border-gray-300 p-3 space-y-3">
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">参数:</h4>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto text-gray-800">
              {typeof toolArgs === 'string' ? toolArgs : JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
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

// 简化的 markdown 组件
const mdComponents = {
  // 基础组件即可
};

// 用户消息组件
const HumanMessageGroup: React.FC<{ 
  group: MessageGroup;
}> = ({ group }) => {
  if (!group.humanMessage) return null;

  return (
    <div className="flex flex-col items-end mb-6">
      <div className="text-white rounded-3xl break-words min-h-7 bg-blue-500 max-w-[100%] sm:max-w-[90%] px-4 pt-3 rounded-br-lg">
        <ReactMarkdown components={mdComponents}>
          {typeof group.humanMessage.content === "string"
            ? group.humanMessage.content
            : JSON.stringify(group.humanMessage.content)}
        </ReactMarkdown>
      </div>
    </div>
  );
};

// 助手消息组件
const AssistantMessageGroup: React.FC<{
  group: MessageGroup;
  allMessages: Message[];
  historicalActivities: Record<string, ProcessedEvent[]>;
  liveActivityEvents: ProcessedEvent[];
}> = ({ group, allMessages, historicalActivities, liveActivityEvents }) => {
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 1500);
    } catch {}
  };

  // 活动事件
  const activityForThisGroup =
    group.isLastGroup && group.isLoading
      ? liveActivityEvents
      : (() => {
          // 找到本组第一个 ai 消息的 id
          const aiMsg = allMessages.slice(group.start + 1, group.end).find(m => m.type === 'ai');
          return aiMsg ? historicalActivities[aiMsg.id!] : undefined;
        })();
  const isLiveActivityForThisGroup = group.isLastGroup && group.isLoading;

  // 收集所有可复制内容
  const allAiContent = allMessages
    .slice(group.start + 1, group.end)
    .filter(msg => msg.type === 'ai')
    .map(msg => (typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)))
    .filter(content => content && content.trim().length > 0)
    .join('\n\n');

  // 只要有内容就渲染
  const hasContent = allMessages.slice(group.start + 1, group.end).some(
    msg =>
      (msg.type === 'ai' && msg.content && String(msg.content).trim()) ||
      msg.type === 'tool'
  );

  if (!hasContent && (!activityForThisGroup || activityForThisGroup.length === 0)) {
    return null;
  }

  return (
    <div className="flex flex-col items-start mb-6">
      <div className="relative break-words flex flex-col max-w-[100%] sm:max-w-[90%]">
        {/* 活动事件时间线 */}
        {activityForThisGroup && activityForThisGroup.length > 0 && (
          <div className="mb-3 border-b border-gray-200 pb-3 text-xs">
            <ActivityTimeline
              processedEvents={activityForThisGroup}
              isLoading={isLiveActivityForThisGroup}
            />
          </div>
        )}
        {/* 交错渲染 */}
        {allMessages.slice(group.start + 1, group.end).map((msg, idx) => {
          if (msg.type === 'ai') {
            const content =
              typeof msg.content === 'string'
                ? msg.content
                : JSON.stringify(msg.content);
            if (!content || !content.trim()) return null;
            return (
              <div key={msg.id || idx} className="text-gray-800 bg-gray-100 rounded-lg p-4 mb-2 w-full">
                <ReactMarkdown components={mdComponents}>{content}</ReactMarkdown>
              </div>
            );
          } else if (msg.type === 'tool') {
            // 查找 tool_call 信息
            const toolCallId = (msg as any).tool_call_id;
            // 反查本组 aiMessage 里 tool_calls 的结构
            const aiMsg = allMessages
              .slice(group.start + 1, group.end)
              .find(ai => ai.type === 'ai' && (ai as any).tool_calls && (ai as any).tool_calls.some((tc: any) => tc.id === toolCallId));
            const toolCall = aiMsg ? (aiMsg as any).tool_calls.find((tc: any) => tc.id === toolCallId) : undefined;
            return (
              <ToolCall key={msg.id || idx} toolCall={toolCall} toolResult={msg} />
            );
          }
          return null;
        })}
        {/* 复制按钮 */}
        {hasContent && (
          <Button
            variant="default"
            className="cursor-pointer bg-gray-200 border-gray-300 text-gray-700 hover:bg-gray-300 self-end mt-2"
            onClick={() => {
              const contentToCopy = allAiContent || "工具调用结果";
              handleCopy(contentToCopy, group.id);
            }}
          >
            {copiedMessageId === group.id ? "已复制" : "复制"}
            {copiedMessageId === group.id ? <CopyCheck /> : <Copy />}
          </Button>
        )}
      </div>
    </div>
  );
};

// 聊天消息视图属性
interface ChatMessagesViewProps {
  messages: Message[];
  isLoading: boolean;
  scrollAreaRef: React.RefObject<HTMLDivElement>;
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
      <div
        className="flex-1 overflow-y-auto px-4 py-6 bg-gray-50"
        style={{ minHeight: 0, maxHeight: 'calc(100vh - 180px)' }}
        ref={scrollAreaRef as any}
      >
        <div className="flex flex-col">
          {messages.map((msg, idx) => {
            // 用户消息
            if (msg.type === 'human') {
              return (
                <div key={msg.id || idx} className="flex flex-col items-end mb-6">
                  <div className="text-white rounded-3xl break-words min-h-7 bg-blue-500 max-w-[100%] sm:max-w-[90%] px-4 pt-3 rounded-br-lg">
                    <ReactMarkdown components={mdComponents}>
                      {typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)}
                    </ReactMarkdown>
                  </div>
                </div>
              );
            }
            // AI消息内容
            if ((msg.type === 'ai' || msg.type === 'AIMessageChunk') && msg.content && String(msg.content).trim()) {
              return (
                <div key={msg.id || idx} className="flex flex-col items-start mb-6">
                  <div className="text-gray-800 bg-gray-100 rounded-lg p-4 mb-2 w-full">
                    <ReactMarkdown components={mdComponents}>
                      {typeof msg.content === "string" ? msg.content : JSON.stringify(msg.content)}
                    </ReactMarkdown>
                  </div>
                  <Button
                    variant="default"
                    className="cursor-pointer bg-gray-200 border-gray-300 text-gray-700 hover:bg-gray-300 self-end mt-2"
                    onClick={() => handleCopy(msg.content, msg.id || String(idx))}
                  >
                    {copiedMessageId === (msg.id || String(idx)) ? "已复制" : "复制"}
                    {copiedMessageId === (msg.id || String(idx)) ? <CopyCheck /> : <Copy />}
                  </Button>
                </div>
              );
            }
            // AI消息的 tool_calls
            if ((msg.type === 'ai' || msg.type === 'AIMessageChunk') && msg.additional_kwargs && msg.additional_kwargs.tool_calls && msg.additional_kwargs.tool_calls.length > 0) {
              return msg.additional_kwargs.tool_calls.map((toolCall, tIdx) => (
                <div key={(msg.id || idx) + '-tool-' + tIdx} className="flex flex-col items-start mb-6">
                  <ToolCall toolCall={toolCall} />
                </div>
              ));
            }
            // tool消息
            if (msg.type === 'tool') {
              return (
                <div key={msg.id || idx} className="flex flex-col items-start mb-6">
                  <ToolCall toolCall={msg} toolResult={msg} />
                </div>
              );
            }
            return null;
          })}
          {isLoading && messages.length > 0 && messages[messages.length - 1]?.type === "human" && (
            <div className="flex items-center gap-2 text-gray-600 mb-6">
              <Loader2 className="h-4 w-4 animate-spin" />
              {isDiagnosticMode ? "诊断中..." : "研究中..."}
            </div>
          )}
          <div id="chat-messages-end" />
        </div>
      </div>
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

