import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { DiagnosticChatView } from "./DiagnosticChatView";
import type { ProcessedEvent } from "./DiagnosticChatView";
import { Drawer } from "antd";

export default function DiagnosticAgent() {
  const [sessionKey, setSessionKey] = useState<number>(0); // 用于强制重新挂载组件
  
  // 新开会话功能 - 通过重新挂载组件完全重置所有状态
  const handleNewSession = useCallback(() => {
    // 清除URL中的线程ID参数
    const url = new URL(window.location.href);
    url.searchParams.delete('thread_id');
    window.history.replaceState({}, '', url.toString());
    
    setSessionKey(prev => prev + 1);
  }, []);

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans antialiased overflow-x-hidden">
      <main className="h-full w-full overflow-x-hidden">
        <DiagnosticSession key={sessionKey} onNewSession={handleNewSession} />
      </main>
    </div>
  );
}

// 历史会话类型定义
interface HistoryThread {
  thread_id: string;
  thread_title: string;
  create_at: string;
  update_at: string;
}

// 内部组件，管理单个会话的所有状态
function DiagnosticSession({ onNewSession }: { onNewSession: () => void }) {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<ProcessedEvent[]>([]);
  const [historicalActivities, setHistoricalActivities] = useState<Record<string, ProcessedEvent[]>>({});
  const hasFinalizeEventOccurredRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false); // 历史会话抽屉状态
  const [historyThreads, setHistoryThreads] = useState<HistoryThread[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // 从URL参数中获取线程ID
  const getThreadIdFromUrl = () => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('thread_id') || null;
  };

  // 获取线程ID配置 - 只有当URL中有线程ID时才传递，否则让LangGraph自动生成
  const getThreadIdConfig = () => {
    const threadIdFromUrl = getThreadIdFromUrl();
    return threadIdFromUrl ? { threadId: threadIdFromUrl } : {};
  };

  const thread = useStream<{
    messages: Message[];
  }>({
    apiUrl: import.meta.env.VITE_API_BASE_URL,
    assistantId: "diagnostic_agent",
    messagesKey: "messages",
    ...getThreadIdConfig(), // 只有历史会话才传递threadId
    onUpdateEvent: (event: any) => {
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

  // 当新线程创建时，将线程ID同步到URL
  useEffect(() => {
    if (thread.threadId && !getThreadIdFromUrl()) {
      const url = new URL(window.location.href);
      url.searchParams.set('thread_id', thread.threadId);
      window.history.replaceState({}, '', url.toString());
    }
  }, [thread.threadId]);

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
        user_name: "zhangsan123", // 临时固定用户名，后续可从用户系统获取
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
  }, [thread]);

  const handleInterruptResume = useCallback((approved: boolean) => {

    thread.submit(undefined, { 
      command: { resume: approved },
      user_name: "zhangsan123" // 临时固定用户名，后续可从用户系统获取
    });
  }, [thread]);



  // 加载历史线程数据
  const loadHistoryThreads = useCallback(async () => {
    setLoadingHistory(true);
    try {
      
      // 调用新的用户线程接口
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/users/zhangsan123/threads?limit=20&offset=0`
      );

      if (response.ok) {
        const data = await response.json();
        const threads = data.threads || [];
        setHistoryThreads(threads);
      } else {
        setError('获取历史线程失败');
      }
    } catch (error) {
      setError('获取历史线程出错');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  // 切换历史会话抽屉显示/隐藏
  const handleToggleHistoryDrawer = useCallback(() => {
    setShowHistoryDrawer(prev => !prev);
    // 如果抽屉要打开，加载历史数据
    if (!showHistoryDrawer) {
      loadHistoryThreads();
    }
  }, [showHistoryDrawer, loadHistoryThreads]);


  // 切换到历史会话
  const handleSwitchToThread = useCallback((threadId: string) => {
    
    // 使用一个简单直接的方法：重新加载页面并传递线程ID
    // 这样可以确保完全重新初始化到指定线程
    const url = new URL(window.location.href);
    url.searchParams.set('thread_id', threadId);
    window.location.href = url.toString();
    // 注意：这里不关闭侧边栏，让用户自己控制
  }, []);


  return (
    <div className="flex h-full font-sans antialiased overflow-x-hidden" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 50%, #1E3A8A 100%)' }}>
      {/* 主内容区域 */}
      <main className="h-full relative flex-1 min-w-0">        
        {error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-center gap-4 p-8 rounded-lg shadow-lg border border-red-600" style={{ backgroundColor: '#1E293B' }}>
              <h1 className="text-2xl text-red-400 font-bold">错误</h1>
              <p className="text-red-300">{JSON.stringify(error)}</p>
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
            onHistoryToggle={handleToggleHistoryDrawer}
          />
        )}
      </main>
      
      {/* 历史会话抽屉 */}
      <Drawer
        title="历史会话"
        placement="right"
        onClose={() => setShowHistoryDrawer(false)}
        open={showHistoryDrawer}
        width={400}
        style={{ 
          backgroundColor: '#1E293B',
        }}
        headerStyle={{
          backgroundColor: '#0F172A',
          color: '#fff',
          borderBottom: '1px solid #3B82F6'
        }}
        bodyStyle={{
          backgroundColor: '#1E293B',
          padding: '16px'
        }}
      >
        <div className="space-y-3">
          {loadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-blue-300">加载中...</div>
            </div>
          ) : historyThreads.length > 0 ? (
            historyThreads.map((historyThread) => (
              <div
                key={historyThread.thread_id}
                className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-md ${
                  thread.threadId === historyThread.thread_id 
                    ? 'bg-blue-800/50 border-blue-400 shadow-sm' 
                    : 'border-blue-600 hover:bg-blue-800/30 bg-slate-700'
                }`}
                onClick={() => {
                  handleSwitchToThread(historyThread.thread_id);
                  setShowHistoryDrawer(false);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-blue-200 truncate">
                      {historyThread.thread_title || '未命名对话'}
                    </div>
                    <div className="text-xs text-blue-300 mt-1">
                      {new Date(historyThread.create_at).toLocaleString('zh-CN', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className="text-xs text-blue-400 mt-1 font-mono">
                      ID: {historyThread.thread_id.substring(0, 8)}...
                    </div>
                  </div>
                  {thread.threadId === historyThread.thread_id && (
                    <div className="text-xs text-cyan-400 font-medium ml-2">
                      当前
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-blue-300">
              暂无历史会话
            </div>
          )}
        </div>
      </Drawer>
    </div>
  );
} 