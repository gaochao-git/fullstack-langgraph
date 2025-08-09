import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Spin, Alert } from 'antd';
import { Button } from '@/components/ui/button';
import ChatEngine from './components/ChatEngine';
import GenericAgentWelcome from './components/GenericAgentWelcome';
import { agentApi, type Agent } from '@/services/agentApi';

const AgentChat: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const [sessionKey, setSessionKey] = useState<number>(0);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
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
        const response = await agentApi.getAgent(agentId);
        
        // 处理统一响应格式
        if (response.status === 'ok' && response.data) {
          setAgent(response.data);
        } else {
          setError(response.msg || '加载智能体失败');
        }
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
    <ChatEngine
      key={sessionKey}
      agentId={agentId!}
      agent={agent}
      WelcomeComponent={welcomeComponent}
      onNewSession={handleNewSession}
    />
  );
};

export default AgentChat;