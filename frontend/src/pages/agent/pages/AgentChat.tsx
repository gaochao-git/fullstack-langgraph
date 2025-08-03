import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Spin, Alert } from 'antd';
import { Button } from '@/components/ui/button';
import ChatEngine from '../components/ChatEngine';
import GenericAgentWelcome from '../components/GenericAgentWelcome';
import { agentApi } from '../../../services/agentApi';
import { useTheme } from '../../../contexts/ThemeContext';
import { cn } from '@/lib/utils';

interface Agent {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_description: string;
  agent_capabilities: string[];
  agent_status: string;
  agent_enabled: string;
  is_builtin: string;
  llm_info?: {
    available_models?: string[];
    model_name?: string;
    temperature?: number;
    max_tokens?: number;
  };
  tools_info?: any;
  prompt_info?: any;
}

const AgentChat: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const [sessionKey, setSessionKey] = useState<number>(0);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isDark } = useTheme();
  
  // 新开会话功能 - 通过重新挂载组件完全重置所有状态
  const handleNewSession = useCallback(() => {
    const url = new URL(window.location.href);
    url.searchParams.delete('thread_id');
    window.history.replaceState({}, '', url.toString());
    setSessionKey(prev => prev + 1);
  }, []);

  useEffect(() => {
    const loadAgent = async () => {
      if (!agentId) {
        setError('智能体ID不存在');
        setLoading(false);
        return;
      }

      try {
        // 直接请求单个智能体，避免获取全部智能体列表
        const agent = await agentApi.getAgent(agentId);
        setAgent(agent);
      } catch (err) {
        console.error('加载智能体失败:', err);
        setError('未找到指定的智能体或加载失败');
      } finally {
        setLoading(false);
      }
    };

    loadAgent();
  }, [agentId]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-4">
        <Alert
          message="错误"
          description={error || '智能体不存在'}
          type="error"
          showIcon
        />
        <Button 
          onClick={() => window.history.back()}
        >
          返回
        </Button>
      </div>
    );
  }

  // 判断是否为诊断智能体，如果是则不传递WelcomeComponent，使用默认的DiagnosticAgentWelcome
  const isDiagnosticAgent = agentId === 'diagnostic_agent';
  const welcomeComponent = isDiagnosticAgent ? undefined : GenericAgentWelcome;

  return (
    <div className={cn(
      "flex h-screen font-sans antialiased overflow-x-hidden transition-colors duration-200",
      isDark 
        ? "bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-gray-100" 
        : "bg-gradient-to-br from-blue-50 via-white to-blue-50 text-gray-900"
    )}>
      <main className="h-full w-full overflow-x-hidden">
        <ChatEngine
          key={sessionKey}
          agentId={agentId!}
          agent={agent}
          WelcomeComponent={welcomeComponent}
          onNewSession={handleNewSession}
        />
      </main>
    </div>
  );
};

export default AgentChat;