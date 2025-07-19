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
    // 清除URL中的线程ID参数
    const url = new URL(window.location.href);
    url.searchParams.delete('thread_id');
    window.history.replaceState({}, '', url.toString());
    
    setSessionKey(prev => prev + 1);
    console.log('创建新会话 - 重新挂载组件');
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
  const [showHistory, setShowHistory] = useState(true); // 默认展开
  const [historyThreads, setHistoryThreads] = useState<HistoryThread[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(260); // 侧边栏宽度状态

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
    apiUrl: import.meta.env.DEV
      ? "http://localhost:8000"
      : "http://localhost:8123",
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
      console.log('新线程创建，同步线程ID到URL:', thread.threadId);
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
    window.location.reload();
  }, [thread]);

  const handleInterruptResume = useCallback((approved: boolean) => {
    console.log('🔧 处理中断恢复:', approved);
    console.log('🔧 当前线程ID:', thread.threadId);
    console.log('🔧 URL中的线程ID:', getThreadIdFromUrl());
    
    thread.submit(undefined, { 
      command: { resume: approved },
      user_name: "zhangsan123" // 临时固定用户名，后续可从用户系统获取
    });
  }, [thread]);


  // 切换侧边栏显示/隐藏
  const handleToggleSidebar = useCallback(() => {
    setShowHistory(prev => !prev);
  }, []);

  // 加载历史线程数据
  const loadHistoryThreads = useCallback(async () => {
    setLoadingHistory(true);
    try {
      console.log('开始获取用户历史线程数据...');
      
      // 调用新的用户线程接口
      const response = await fetch(
        import.meta.env.DEV 
          ? "http://localhost:8000/users/zhangsan123/threads?limit=20&offset=0" 
          : "http://localhost:8123/users/zhangsan123/threads?limit=20&offset=0"
      );

      if (response.ok) {
        const data = await response.json();
        const threads = data.threads || [];
        console.log('获取到的用户历史线程:', data);
        setHistoryThreads(threads);
      } else {
        console.error('获取用户历史线程失败:', response.status, response.statusText);
        setError('获取历史线程失败');
      }
    } catch (error) {
      console.error('获取用户历史线程出错:', error);
      setError('获取历史线程出错');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  // 组件加载时获取历史线程数据
  useEffect(() => {
    loadHistoryThreads();
  }, [loadHistoryThreads]);

  // 侧边栏拖动调整宽度功能
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = startWidth + (e.clientX - startX);
      // 限制宽度范围：最小150px，最大400px
      const clampedWidth = Math.max(150, Math.min(400, newWidth));
      setSidebarWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [sidebarWidth]);

  // 切换到历史会话
  const handleSwitchToThread = useCallback((threadId: string) => {
    console.log('切换到线程:', threadId);
    
    // 使用一个简单直接的方法：重新加载页面并传递线程ID
    // 这样可以确保完全重新初始化到指定线程
    const url = new URL(window.location.href);
    url.searchParams.set('thread_id', threadId);
    window.location.href = url.toString();
    // 注意：这里不关闭侧边栏，让用户自己控制
  }, []);


  return (
    <div className="flex h-full font-sans antialiased overflow-x-hidden" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 50%, #1E3A8A 100%)' }}>
      {/* 历史会话侧边栏 */}
      {showHistory && (
        <div 
          className="border-r border-blue-600 flex flex-col relative overflow-x-visible"
          style={{ width: `${sidebarWidth}px`, background: 'linear-gradient(180deg, #0F172A 0%, #1E293B 100%)' }}
        >
          <div className="p-4 border-b border-blue-600">
            {/* 新对话按钮 */}
            <Button
              onClick={onNewSession}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              新对话
            </Button>
          </div>
          
          <div className="flex-1 overflow-y-auto overflow-x-hidden p-4">
            {loadingHistory ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-blue-300">加载中...</div>
              </div>
            ) : historyThreads.length > 0 ? (
              <div className="space-y-2">
                {historyThreads.map((historyThread) => (
                  <div
                    key={historyThread.thread_id}
                    className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 hover:shadow-md ${
                      thread.threadId === historyThread.thread_id 
                        ? 'bg-blue-800/50 border-blue-400 shadow-sm' 
                        : 'border-blue-600 hover:bg-blue-800/30'
                    }`}
                    style={{ backgroundColor: thread.threadId === historyThread.thread_id ? '#1E40AF' : '#1E293B' }}
                    onClick={() => handleSwitchToThread(historyThread.thread_id)}
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
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-blue-300">
                暂无历史会话
              </div>
            )}
          </div>
          
          {/* 拖动区域 - 位于侧边栏右边界 */}
          <div
            className="absolute top-0 right-0 w-1 h-full cursor-col-resize bg-blue-600 hover:bg-cyan-400 transition-colors duration-200 opacity-0 hover:opacity-100 z-50 group"
            onMouseDown={handleMouseDown}
            title="拖动调整宽度"
          />
          
          {/* 折叠按钮 - 参考设计样式 */}
          <button
            onClick={handleToggleSidebar}
            className="absolute top-2 -right-6 w-6 h-8 hover:bg-blue-800 rounded-sm transition-colors duration-200 flex items-center justify-center border border-blue-600 z-50"
            style={{ backgroundColor: '#1E293B' }}
            title="折叠侧边栏"
          >
            <svg className="w-3 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
      )}
      
      {/* 主内容区域 */}
      <main className="h-full relative flex-1 min-w-0">
        {/* 当侧边栏关闭时显示的打开按钮 */}
        {!showHistory && (
          <button
            onClick={handleToggleSidebar}
            className="absolute top-2 left-2 z-10 w-6 h-8 border border-blue-600 rounded-sm hover:bg-blue-800 transition-all duration-200 flex items-center justify-center"
            style={{ backgroundColor: '#1E293B' }}
            title="打开侧边栏"
          >
            <svg className="w-3 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        )}
        
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
          />
        )}
      </main>
    </div>
  );
} 