import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Button, 
  Space, 
  Spin, 
  Alert, 
  Input, 
  Typography, 
  Tag,
  Avatar,
  Card,
  message as antdMessage
} from 'antd';
import { 
  ArrowLeftOutlined,
  SendOutlined, 
  RobotOutlined,
  ClearOutlined,
  UserOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { agentApi } from '../services/agentApi';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  capabilities: string[];
}

const GenericAgentChat: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 获取线程ID配置
  const getThreadIdConfig = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const threadIdFromUrl = urlParams.get('thread_id');
    return threadIdFromUrl ? { threadId: threadIdFromUrl } : {};
  };

  // 根据智能体类型选择不同的assistantId
  const getAssistantId = () => {
    if (!agent) return "diagnostic_agent"; // 默认使用diagnostic_agent
    
    // 内置智能体直接使用其ID
    if (agent.id === 'diagnostic_agent' || agent.id === 'research_agent') {
      return agent.id;
    }
    
    // 自定义智能体使用generic_agent
    return "generic_agent";
  };

  // 使用LangGraph SDK的useStream hook
  const thread = useStream<{
    messages: Message[];
  }>({
    apiUrl: import.meta.env.VITE_API_BASE_URL,
    assistantId: getAssistantId(),
    messagesKey: "messages",
    ...getThreadIdConfig(),
    config: {
      configurable: {
        agent_id: agentId, // 传递URL参数中的agentId
        custom_agent_config: agent?.id !== getAssistantId() ? {
          // 如果是自定义智能体，传递其配置
          agent_name: agent?.display_name,
          system_prompt: agent?.description,
          capabilities: agent?.capabilities
        } : undefined
      }
    },
    onError: (error: any) => {
      console.error('Thread error:', error);
      antdMessage.error('对话发生错误，请重试');
    },
  });

  useEffect(() => {
    const loadAgent = async () => {
      if (!agentId) {
        setError('智能体ID不存在');
        setLoading(false);
        return;
      }

      try {
        const agents = await agentApi.getAgents();
        const foundAgent = agents.find(a => a.id === agentId);
        
        if (foundAgent) {
          setAgent({
            id: foundAgent.id,
            name: foundAgent.name,
            display_name: foundAgent.display_name,
            description: foundAgent.description,
            capabilities: foundAgent.capabilities
          });
        } else {
          setError('未找到指定的智能体');
        }
      } catch (err) {
        console.error('加载智能体失败:', err);
        setError('加载智能体失败');
      } finally {
        setLoading(false);
      }
    };

    loadAgent();
  }, [agentId]);

  useEffect(() => {
    scrollToBottom();
  }, [thread.messages]);

  // 当新线程创建时，将线程ID同步到URL
  useEffect(() => {
    if ((thread as any).threadId) {
      const url = new URL(window.location.href);
      url.searchParams.set('thread_id', (thread as any).threadId);
      window.history.replaceState({}, '', url.toString());
    }
  }, [(thread as any).threadId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || thread.isLoading || !agent) return;

    const messageContent = inputValue.trim();
    setInputValue('');

    try {
      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: messageContent,
          id: Date.now().toString(),
        },
      ];
      
      const submitData = {
        messages: newMessages,
      };
      
      // 根据智能体类型传递不同的配置
      const submitOptions = {
        config: {
          configurable: {
            agent_id: agentId,
            custom_agent_config: agent?.id !== getAssistantId() ? {
              // 如果是自定义智能体，传递其配置
              agent_name: agent?.display_name,
              system_prompt: agent?.description,
              capabilities: agent?.capabilities
            } : undefined
          }
        }
      };
      
      thread.submit(submitData, submitOptions);
    } catch (error) {
      console.error('发送消息失败:', error);
      antdMessage.error('发送消息失败，请重试');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearMessages = () => {
    // 创建新会话，清空当前对话
    const url = new URL(window.location.href);
    url.searchParams.delete('thread_id');
    window.history.replaceState({}, '', url.toString());
    window.location.reload();
  };

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.type === 'human';
    
    return (
      <div
        key={index}
        style={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16,
          alignItems: 'flex-start'
        }}
      >
        {!isUser && (
          <Avatar 
            icon={<RobotOutlined />} 
            style={{ 
              backgroundColor: '#1890ff', 
              marginRight: 8,
              flexShrink: 0
            }} 
          />
        )}
        
        <div
          style={{
            maxWidth: '70%',
            backgroundColor: isUser ? '#1890ff' : '#f5f5f5',
            color: isUser ? 'white' : 'black',
            padding: '12px 16px',
            borderRadius: '12px',
            wordBreak: 'break-word'
          }}
        >
          <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          <div
            style={{
              fontSize: '12px',
              opacity: 0.7,
              marginTop: 4,
              textAlign: 'right'
            }}
          >
            {new Date().toLocaleTimeString()}
          </div>
        </div>
        
        {isUser && (
          <Avatar 
            icon={<UserOutlined />}
            style={{ 
              backgroundColor: '#52c41a', 
              marginLeft: 8,
              flexShrink: 0
            }} 
          />
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center' 
      }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        flexDirection: 'column',
        gap: 16
      }}>
        <Alert
          message="错误"
          description={error || '智能体不存在'}
          type="error"
          showIcon
        />
        <Space>
          <Button 
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          >
            返回智能体广场
          </Button>
          <Button 
            type="primary"
            onClick={() => navigate('/agents')}
          >
            智能体管理
          </Button>
        </Space>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部导航栏 */}
      <div style={{ 
        padding: '12px 16px', 
        borderBottom: '1px solid #f0f0f0',
        backgroundColor: '#fff'
      }}>
        <Space>
          <Button 
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
          >
            返回
          </Button>
          <span style={{ fontSize: 16, fontWeight: 500 }}>
            与 {agent.display_name} 对话
          </span>
        </Space>
      </div>

      {/* 对话区域 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 智能体信息栏 */}
        <Card 
          size="small" 
          style={{ marginBottom: 0, borderRadius: 0, borderLeft: 0, borderRight: 0 }}
          bodyStyle={{ padding: '12px 16px' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Avatar 
                icon={<RobotOutlined />} 
                style={{ backgroundColor: '#1890ff' }} 
              />
              <div>
                <Title level={5} style={{ margin: 0 }}>{agent.display_name}</Title>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {agent.description || '与智能体进行对话'}
                </Text>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {agent.capabilities.slice(0, 4).map(capability => (
                <Tag key={capability} color="blue" style={{ fontSize: 11 }}>{capability}</Tag>
              ))}
              {agent.capabilities.length > 4 && (
                <Tag color="default" style={{ fontSize: 11 }}>+{agent.capabilities.length - 4}</Tag>
              )}
              <Button
                size="small"
                icon={<ClearOutlined />}
                onClick={clearMessages}
                title="清空对话"
                disabled={(thread.messages?.length || 0) === 0}
              >
                清空
              </Button>
            </div>
          </div>
        </Card>

        {/* 对话消息区域 */}
        <div 
          style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: '16px',
            backgroundColor: '#fafafa'
          }}
        >
          {(thread.messages?.length || 0) === 0 ? (
            <div 
              style={{ 
                textAlign: 'center', 
                color: '#999', 
                marginTop: 60,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 16
              }}
            >
              <RobotOutlined style={{ fontSize: 48, opacity: 0.3 }} />
              <div>
                <div>你好！我是 {agent?.display_name}</div>
                <div style={{ fontSize: 14, marginTop: 4, maxWidth: 300 }}>
                  {agent?.description}
                </div>
                <div style={{ fontSize: 12, marginTop: 8, color: '#ccc' }}>
                  请输入您的问题开始对话
                </div>
              </div>
            </div>
          ) : (
            thread.messages?.map(renderMessage)
          )}
          
          {thread.isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16 }}>
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <Spin indicator={<LoadingOutlined style={{ fontSize: 14 }} spin />} />
              <Text type="secondary">正在思考...</Text>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div style={{ 
          padding: '16px', 
          borderTop: '1px solid #f0f0f0',
          backgroundColor: 'white'
        }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="输入您的问题..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{ flex: 1 }}
              disabled={thread.isLoading}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || thread.isLoading}
              loading={thread.isLoading}
            >
              发送
            </Button>
          </div>
          <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
            按 Enter 发送，Shift + Enter 换行
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenericAgentChat;