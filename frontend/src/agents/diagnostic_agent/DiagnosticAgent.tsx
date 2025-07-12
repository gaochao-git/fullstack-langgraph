import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { DiagnosticChatView } from "./DiagnosticChatView";
import type { ProcessedEvent } from "./DiagnosticChatView";

export default function DiagnosticAgent() {
  const [sessionKey, setSessionKey] = useState<number>(0); // 用于强制重新挂载组件
  
  // 新开会话功能 - 通过重新挂载组件完全重置所有状态
  const handleNewSession = useCallback(() => {
    setSessionKey(prev => prev + 1);
    console.log('创建新会话 - 重新挂载组件');
  }, []);

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
        <DiagnosticSession key={sessionKey} onNewSession={handleNewSession} />
      </main>
    </div>
  );
}

// 内部组件，管理单个会话的所有状态
function DiagnosticSession({ onNewSession }: { onNewSession: () => void }) {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<ProcessedEvent[]>([]);
  const [historicalActivities, setHistoricalActivities] = useState<Record<string, ProcessedEvent[]>>({});
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);

  const thread = useStream<{
    messages: Message[];
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:8000"
      : "http://localhost:8123",
    assistantId: "diagnostic_agent",
    messagesKey: "messages",
    onUpdateEvent: (event: any) => {
      console.log("event", event);
      let processedEvent: ProcessedEvent | null = null;
      if (event.diagnostic_step) {
        processedEvent = {
          title: "Diagnostic Step",
          data: event.diagnostic_step || "",
        };
      } else if (event.analysis) {
        processedEvent = {
          title: "Analysis",
          data: event.analysis || "",
        };
      } else if (event.finalize_diagnosis) {
        processedEvent = {
          title: "Finalizing Diagnosis",
          data: "Composing final diagnostic report.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    onError: (error: any) => {
      setError(error.message);
    },
  });

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      thread.submit({
        messages: newMessages,
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  const handleInterruptResume = useCallback((approved: boolean) => {
    thread.submit(undefined, { command: { resume: approved } });
  }, [thread]);


  // 查看历史功能
  const handleViewHistory = useCallback(() => {
    const historyInfo = {
      threadId: thread.threadId,
      messageCount: thread.messages?.length || 0,
      messages: thread.messages,
      historicalActivities,
      hasActivities: Object.keys(historicalActivities).length > 0
    };
    
    console.log('当前会话历史:', historyInfo);
    
    // 构建更友好的信息显示
    const infoText = `当前会话信息：
• 会话ID: ${historyInfo.threadId || '新会话'}
• 消息数量: ${historyInfo.messageCount}
• 活动记录: ${historyInfo.hasActivities ? '有' : '无'}

详细信息已输出到控制台。`;
    
    alert(infoText);
  }, [thread.messages, thread.threadId, historicalActivities]);


  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
        {error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-center gap-4 bg-white p-8 rounded-lg shadow-lg">
              <h1 className="text-2xl text-red-500 font-bold">错误</h1>
              <p className="text-red-600">{JSON.stringify(error)}</p>
              <Button
                variant="destructive"
                onClick={() => window.location.reload()}
              >
                重试
              </Button>
            </div>
          </div>
        ) : (
          <DiagnosticChatView
            messages={thread.messages}
            isLoading={thread.isLoading}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            liveActivityEvents={processedEventsTimeline}
            historicalActivities={historicalActivities}
            interrupt={thread.interrupt}
            onInterruptResume={handleInterruptResume}
            onNewSession={onNewSession}
            onViewHistory={handleViewHistory}
          />
        )}
      </main>
    </div>
  );
} 