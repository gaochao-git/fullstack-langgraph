import { useState, useCallback } from "react";
import { UnifiedAgentChat } from "../../../agent";
import { useTheme } from "@/contexts/ThemeContext";
import { cn } from "@/lib/utils";

export default function DiagnosticAgent() {
  const [sessionKey, setSessionKey] = useState<number>(0);
  const { isDark } = useTheme();
  
  // 新开会话功能 - 通过重新挂载组件完全重置所有状态
  const handleNewSession = useCallback(() => {
    // 清除URL中的线程ID参数
    const url = new URL(window.location.href);
    url.searchParams.delete('thread_id');
    window.history.replaceState({}, '', url.toString());
    
    setSessionKey(prev => prev + 1);
  }, []);

  // 诊断智能体信息
  const diagnosticAgent = {
    id: "diagnostic_agent",
    name: "diagnostic_agent", 
    display_name: "故障诊断智能体",
    description: "专业的IT系统故障诊断助手",
    capabilities: ["故障诊断", "系统分析", "问题排查"],
    is_builtin: "yes"
  };

  return (
    <div className={cn(
      "flex h-screen font-sans antialiased overflow-x-hidden transition-colors duration-200",
      isDark 
        ? "bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-gray-100" 
        : "bg-gradient-to-br from-blue-50 via-white to-blue-50 text-gray-900"
    )}>
      <main className="h-full w-full overflow-x-hidden">
        <UnifiedAgentChat
          key={sessionKey}
          agentId="diagnostic_agent"
          agent={diagnosticAgent}
          WelcomeComponent={undefined} // 诊断智能体使用默认的FaultWelcomeSimple
          onNewSession={handleNewSession}
        />
      </main>
    </div>
  );
}

