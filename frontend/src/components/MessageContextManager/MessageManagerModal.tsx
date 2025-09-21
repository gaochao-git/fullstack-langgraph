import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Modal, Button, Card, Statistic, Row, Col, Divider, Space, Tag, Tooltip, Checkbox, message as antMessage } from 'antd';
import { 
  DeleteOutlined, 
  EditOutlined, 
  CompressOutlined,
  RobotOutlined,
  UserOutlined,
  ToolOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  CloseOutlined,
  CheckOutlined,
  ScissorOutlined,
  MergeOutlined
} from '@ant-design/icons';
import { Message } from '@/hooks/useStream';
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';
import MessageContextManager from './MessageContextManager';
import { useTokenCount } from '@/hooks/useTokenCount';
import { useMessageCompression } from '@/hooks/useMessageCompression';

export interface MessageManagerModalProps {
  visible: boolean;
  onClose: () => void;
  messages: Message[];
  onUpdateMessages: (messages: Message[]) => void;
  threadId?: string;
  maxContextLength?: number;
}

const MessageManagerModal: React.FC<MessageManagerModalProps> = ({
  visible,
  onClose,
  messages,
  onUpdateMessages,
  threadId,
  maxContextLength = 128000
}) => {
  const { isDark } = useTheme();
  const { getBatchTokenCount, estimateTokenCount } = useTokenCount();
  const { compressMessages, isCompressing } = useMessageCompression();
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(new Set());
  const [messageTokenCounts, setMessageTokenCounts] = useState<Map<string, number>>(new Map());

  // 批量获取所有消息的token计数
  useEffect(() => {
    if (visible && messages.length > 0) {
      const texts = messages.map(m => m.content);
      getBatchTokenCount(texts).then(results => {
        const newCounts = new Map<string, number>();
        messages.forEach((msg, index) => {
          if (results[index]) {
            newCounts.set(msg.content, results[index].token_count);
          }
        });
        setMessageTokenCounts(newCounts);
      });
    }
  }, [visible, messages, getBatchTokenCount]);

  // 计算统计数据
  const statistics = useMemo(() => {
    const stats = {
      user: { count: 0, tokens: 0 },
      ai: { count: 0, tokens: 0 },
      tool: { count: 0, tokens: 0 },
      total: { count: 0, tokens: 0 }
    };

    messages.forEach(msg => {
      const tokenCount = messageTokenCounts.get(msg.content) || estimateTokenCount(msg.content);
      
      switch (msg.type) {
        case 'human':
          stats.user.count++;
          stats.user.tokens += tokenCount;
          break;
        case 'ai':
          stats.ai.count++;
          stats.ai.tokens += tokenCount;
          break;
        case 'tool':
          stats.tool.count++;
          stats.tool.tokens += tokenCount;
          break;
      }
      
      stats.total.count++;
      stats.total.tokens += tokenCount;
    });

    return stats;
  }, [messages, messageTokenCounts, estimateTokenCount]);

  // 计算使用率
  const usage = (statistics.total.tokens / maxContextLength) * 100;

  // 一键智能压缩
  const handleAutoCompress = useCallback(async () => {
    // 找出最大的AI消息进行压缩
    const aiMessages = messages
      .filter(msg => msg.type === 'ai' && msg.id)
      .map(msg => ({
        message: msg,
        tokens: messageTokenCounts.get(msg.content) || estimateTokenCount(msg.content)
      }))
      .sort((a, b) => b.tokens - a.tokens);

    if (aiMessages.length === 0) {
      antMessage.warning('没有可压缩的AI消息');
      return;
    }

    // 选择前5个最大的AI消息
    const toCompress = aiMessages.slice(0, 5).map(item => item.message);
    
    try {
      const compressed = await compressMessages(toCompress, {
        compressionLevel: 'medium',
        preserveContext: true,
        targetTokenRatio: 0.5
      });

      // 更新消息列表
      const newMessages = [...messages];
      const compressedMap = new Map(compressed.map(msg => [msg.id, msg]));
      
      newMessages.forEach((msg, index) => {
        if (msg.id && compressedMap.has(msg.id)) {
          newMessages[index] = compressedMap.get(msg.id)!;
        }
      });

      onUpdateMessages(newMessages);
      antMessage.success(`成功压缩 ${compressed.length} 条消息`);
    } catch (error) {
      antMessage.error('自动压缩失败');
    }
  }, [messages, messageTokenCounts, estimateTokenCount, compressMessages, onUpdateMessages]);

  // 批量压缩选中的消息
  const handleBatchCompress = useCallback(async () => {
    const selectedMsgs = messages.filter(msg => msg.id && selectedMessages.has(msg.id));
    
    if (selectedMsgs.length === 0) {
      antMessage.warning('请先选择要压缩的消息');
      return;
    }

    try {
      const compressed = await compressMessages(selectedMsgs);
      
      // 更新消息列表
      const newMessages = [...messages];
      const compressedMap = new Map(compressed.map(msg => [msg.id, msg]));
      
      newMessages.forEach((msg, index) => {
        if (msg.id && compressedMap.has(msg.id)) {
          newMessages[index] = compressedMap.get(msg.id)!;
        }
      });

      onUpdateMessages(newMessages);
      setSelectedMessages(new Set());
      antMessage.success(`成功压缩 ${compressed.length} 条消息`);
    } catch (error) {
      antMessage.error('批量压缩失败');
    }
  }, [messages, selectedMessages, compressMessages, onUpdateMessages]);

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <BarChartOutlined />
          <span>消息上下文管理</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={1200}
      style={{ top: 20 }}
      bodyStyle={{ maxHeight: 'calc(100vh - 200px)', overflow: 'auto' }}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        selectedMessages.size > 0 && (
          <Button
            key="batch-compress"
            type="primary"
            icon={<CompressOutlined />}
            onClick={handleBatchCompress}
            loading={isCompressing}
          >
            压缩选中 ({selectedMessages.size})
          </Button>
        ),
        <Button
          key="auto-compress"
          type="primary"
          danger
          icon={<ScissorOutlined />}
          onClick={handleAutoCompress}
          loading={isCompressing}
        >
          一键智能压缩
        </Button>
      ].filter(Boolean)}
      className={cn(isDark && "dark-modal")}
    >
      {/* 统计信息卡片 */}
      <Card className="mb-4">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title={
                <Space>
                  <UserOutlined style={{ color: '#1890ff' }} />
                  用户消息
                </Space>
              }
              value={statistics.user.count}
              suffix={`条`}
              valueStyle={{ color: '#1890ff' }}
            />
            <div className="text-sm text-gray-500 mt-1">
              {statistics.user.tokens.toLocaleString()} tokens
            </div>
          </Col>
          
          <Col span={6}>
            <Statistic
              title={
                <Space>
                  <RobotOutlined style={{ color: '#52c41a' }} />
                  助手消息
                </Space>
              }
              value={statistics.ai.count}
              suffix={`条`}
              valueStyle={{ color: '#52c41a' }}
            />
            <div className="text-sm text-gray-500 mt-1">
              {statistics.ai.tokens.toLocaleString()} tokens
            </div>
          </Col>
          
          <Col span={6}>
            <Statistic
              title={
                <Space>
                  <ToolOutlined style={{ color: '#fa8c16' }} />
                  工具调用
                </Space>
              }
              value={statistics.tool.count}
              suffix={`次`}
              valueStyle={{ color: '#fa8c16' }}
            />
            <div className="text-sm text-gray-500 mt-1">
              {statistics.tool.tokens.toLocaleString()} tokens
            </div>
          </Col>
          
          <Col span={6}>
            <Statistic
              title={
                <Space>
                  <ThunderboltOutlined style={{ color: '#f5222d' }} />
                  总计
                </Space>
              }
              value={statistics.total.count}
              suffix="条"
              valueStyle={{ color: '#262626' }}
            />
            <div className="text-sm text-gray-500 mt-1 mb-3">
              {statistics.total.tokens.toLocaleString()} tokens
            </div>
          </Col>
        </Row>
        
        {/* 使用率进度条单独显示 */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">使用率</span>
            <span className="text-sm font-medium">{usage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={cn(
                "h-3 rounded-full transition-all duration-300",
                usage > 80 ? 'bg-red-500' : usage > 60 ? 'bg-yellow-500' : 'bg-green-500'
              )}
              style={{ width: `${Math.min(usage, 100)}%` }}
            />
          </div>
        </div>
      </Card>

      <Divider className="my-4" />

      {/* 使用原有的MessageContextManager组件，并传入选择状态 */}
      <MessageContextManager
        messages={messages}
        onUpdateMessages={onUpdateMessages}
        onCompressMessages={async (messageIds) => {
          const messagesToCompress = messages.filter(m => m.id && messageIds.includes(m.id));
          return await compressMessages(messagesToCompress);
        }}
        disabled={isCompressing}
        // 传入选择状态管理
        selectedMessages={selectedMessages}
        onSelectionChange={setSelectedMessages}
      />
    </Modal>
  );
};

export default MessageManagerModal;