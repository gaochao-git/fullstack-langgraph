import React, { useCallback, useEffect, useState } from 'react';
import { Spin, Alert } from 'antd';
import { Button } from '@/components/ui/button';
import ChatEngine from '@/pages/agent/components/ChatEngine';
import GenericAgentWelcome from '@/pages/agent/components/GenericAgentWelcome';
import { agentApi, type Agent } from '@/services/agentApi';

export interface AgentChatWidgetProps {
  agentId: string;
  className?: string;
  style?: React.CSSProperties;
  height?: number | string; // container height control
  onUserMessage?: (message: string, fileIds?: string[]) => void; // 外部页面联动回调
}

/**
 * AgentChatWidget
 * - Embeddable chat widget that reuses the full Agent Chat experience.
 * - Keeps parity with existing Agent features and evolves with them.
 */
const AgentChatWidget: React.FC<AgentChatWidgetProps> = ({ agentId, className, style, height, onUserMessage }) => {
  const [sessionKey, setSessionKey] = useState<number>(0);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New session: clear thread_id and remount ChatEngine to reset internal state
  const handleNewSession = useCallback(() => {
    const url = new URL(window.location.href);
    url.searchParams.delete('thread_id');
    window.history.replaceState({}, '', url.toString());
    setSessionKey((prev) => prev + 1);
  }, []);

  useEffect(() => {
    const loadAgent = async () => {
      if (!agentId) {
        setError('智能体ID不存在');
        setLoading(false);
        return;
      }
      try {
        const response = await agentApi.getAgent(agentId);
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

  // layout container style
  const containerStyle: React.CSSProperties = {
    height: height ?? '100%',
    display: 'flex',
    flexDirection: 'column',
    ...(style || {}),
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center ${className || ''}`} style={containerStyle}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className={`flex items-center justify-center flex-col gap-4 ${className || ''}`} style={containerStyle}>
        <Alert message="错误" description={error || '智能体不存在'} type="error" showIcon />
        <Button onClick={() => window.history.back()}>返回</Button>
      </div>
    );
  }

  // keep DiagnosticAgent welcome behavior
  const isDiagnosticAgent = agentId === 'diagnostic_agent';
  const welcomeComponent = isDiagnosticAgent ? undefined : GenericAgentWelcome;

  return (
    <div className={className} style={containerStyle}>
      <ChatEngine
        key={sessionKey}
        agentId={agentId}
        agent={agent}
        WelcomeComponent={welcomeComponent}
        onNewSession={handleNewSession}
        onUserMessage={onUserMessage}
      />
    </div>
  );
};

export default AgentChatWidget;
