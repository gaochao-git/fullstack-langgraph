import React, { useState, useRef, useEffect } from 'react';
import { Button, Input, Modal, Card } from 'antd';
import { SendOutlined, MessageOutlined } from '@ant-design/icons';

interface ChatMessage {
  id: string;
  type: 'user' | 'system';
  content: string;
  timestamp: string;
}

interface ChatDialogProps {
  onQuerySubmit: (query: string) => void;
}

export function ChatDialog({ onQuerySubmit }: ChatDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'system',
      content: '您好！我是IDC监控分析助手。您可以询问关于数据中心运行状况、性能分析、机房比对等问题。',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);

    // 触发查询分析
    onQuerySubmit(inputValue);

    // 模拟AI响应
    setTimeout(() => {
      const aiResponse = generateAIResponse(inputValue);
      const systemMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: aiResponse,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, systemMessage]);
    }, 1000);

    setInputValue('');
  };

  const generateAIResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('比对') || lowerQuery.includes('对比')) {
      return '我将为您生成多机房性能比对分析报告。请在下方选择需要比对的数据中心，系统将自动生成详细的比对图表和分析建议。';
    } else if (lowerQuery.includes('应用') || lowerQuery.includes('业务') || lowerQuery.includes('服务')) {
      return '我将为您展示应用程序监控页面，包括不同数据中心中的业务应用运行情况、跨数据中心业务比较以及独有业务的性能分析。';
    } else if (lowerQuery.includes('支付') || lowerQuery.includes('备付金') || lowerQuery.includes('风控')) {
      return '我将为您展示相关业务应用的运行状况，包括应用服务器、数据库服务器、缓存服务器的性能指标和跨数据中心部署情况。';
    } else if (lowerQuery.includes('性能') || lowerQuery.includes('负载')) {
      return '我将为您展示各数据中心的实时性能监控数据，包括CPU使用率、内存占用、网络负载等关键指标。';
    } else if (lowerQuery.includes('稳定性') || lowerQuery.includes('故障')) {
      return '我将为您分析各数据中心的稳定性指标，包括正常运行时间、故障频率和稳定性评分。';
    } else if (lowerQuery.includes('温度') || lowerQuery.includes('环境')) {
      return '我将为您展示各数据中心的环境监控数据，包括温度、湿度和电力使用情况。';
    } else {
      return '我已收到您的查询请求。系统将在下方展示相关的监控数据和分析结果。您可以进一步选择特定的数据中心进行详细分析。';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <>
      <Button
        type="primary"
        size="large"
        icon={<MessageOutlined />}
        onClick={() => setIsOpen(true)}
      >
        发起对话分析
      </Button>

      <Modal
        title="IDC监控分析助手"
        open={isOpen}
        onCancel={() => setIsOpen(false)}
        footer={null}
        width={800}
        styles={{ body: { height: '600px', display: 'flex', flexDirection: 'column' } }}
      >
        <div
          ref={scrollAreaRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px 0',
            marginBottom: 16
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {messages.map((message) => (
              <div
                key={message.id}
                style={{
                  display: 'flex',
                  justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <Card
                  size="small"
                  style={{
                    maxWidth: '80%',
                    backgroundColor: message.type === 'user' ? 'var(--color-primary)' : 'var(--color-muted)',
                    color: message.type === 'user' ? 'var(--color-primary-foreground)' : 'var(--color-foreground)',
                    border: 'none'
                  }}
                  styles={{ body: { padding: '8px 12px' } }}
                >
                  <p style={{ margin: 0, marginBottom: 4, color: 'inherit' }}>
                    {message.content}
                  </p>
                  <p style={{
                    margin: 0,
                    fontSize: 12,
                    opacity: 0.7,
                    color: 'inherit'
                  }}>
                    {formatTime(message.timestamp)}
                  </p>
                </Card>
              </div>
            ))}
          </div>
        </div>

        <div style={{
          display: 'flex',
          gap: 8,
          paddingTop: 16,
          borderTop: '1px solid var(--color-border)'
        }}>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="请输入您的查询需求..."
            onPressEnter={handleSendMessage}
            style={{ flex: 1, backgroundColor: 'var(--color-input-background)', borderColor: 'var(--color-border)' }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
          />
        </div>
      </Modal>
    </>
  );
}
