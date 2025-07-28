import React, { useState, useEffect, useRef } from 'react';
import { 
  Modal, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Avatar,
  Spin,
  Card,
  Tag,
  message as antdMessage
} from "antd";
import { 
  SendOutlined, 
  RobotOutlined,
  ClearOutlined,
  UserOutlined,
  LoadingOutlined
} from "@ant-design/icons";
import { baseFetch, baseFetchJson } from '../utils/baseFetch';

const { TextArea } = Input;
const { Text, Title } = Typography;

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  id: string;
}

interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  capabilities: string[];
}

interface AgentChatDialogProps {
  open: boolean;
  onClose: () => void;
  agent: Agent | null;
}

const AgentChatDialog: React.FC<AgentChatDialogProps> = ({
  open,
  onClose,
  agent
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (open && agent) {
      // 重置对话状态
      setMessages([]);
      setInputValue('');
      setIsLoading(false);
    }
  }, [open, agent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !agent) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      id: Date.now().toString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // 调用后端API发送消息
      const data = await baseFetchJson(`/api/v1/agents/${agent.agent_id}/chat`, {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: `chat_${agent.id}_${Date.now()}`
        }),
      });
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response || '抱歉，我无法处理您的请求。',
        timestamp: new Date(),
        id: (Date.now() + 1).toString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('发送消息失败:', error);
      antdMessage.error('发送消息失败，请重试');
      
      const errorMessage: Message = {
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，请稍后再试。',
        timestamp: new Date(),
        id: (Date.now() + 1).toString()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';
    
    return (
      <div
        key={message.id}
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
            {message.timestamp.toLocaleTimeString()}
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

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
          <div>
            <Title level={5} style={{ margin: 0 }}>{agent?.display_name || '智能体对话'}</Title>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {agent?.description || '与智能体进行对话'}
            </Text>
          </div>
        </div>
      }
      open={open}
      onCancel={onClose}
      width={800}
      height={600}
      footer={null}
      styles={{
        body: { height: 500, padding: 0 }
      }}
    >
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* 智能体信息栏 */}
        {agent && (
          <Card 
            size="small" 
            style={{ marginBottom: 0, borderRadius: 0, borderLeft: 0, borderRight: 0, borderTop: 0 }}
            bodyStyle={{ padding: '12px 16px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {agent.capabilities.slice(0, 4).map(capability => (
                  <Tag key={capability} color="blue" style={{ fontSize: 11 }}>{capability}</Tag>
                ))}
                {agent.capabilities.length > 4 && (
                  <Tag color="default" style={{ fontSize: 11 }}>+{agent.capabilities.length - 4}</Tag>
                )}
              </div>
              <Button
                size="small"
                icon={<ClearOutlined />}
                onClick={clearMessages}
                title="清空对话"
                disabled={messages.length === 0}
              >
                清空
              </Button>
            </div>
          </Card>
        )}

        {/* 对话区域 */}
        <div 
          style={{ 
            flex: 1, 
            overflowY: 'auto', 
            padding: '16px',
            backgroundColor: '#fafafa'
          }}
        >
          {messages.length === 0 ? (
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
            messages.map(renderMessage)
          )}
          
          {isLoading && (
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
              disabled={isLoading}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              loading={isLoading}
            >
              发送
            </Button>
          </div>
          <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
            按 Enter 发送，Shift + Enter 换行
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default AgentChatDialog;