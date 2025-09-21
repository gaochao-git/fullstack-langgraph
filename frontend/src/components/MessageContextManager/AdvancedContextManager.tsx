import React, { useState, useCallback, useMemo } from 'react';
import { Modal, Button, Select, Slider, Switch, Tabs, Card, Progress, Statistic, Space, message as antMessage } from 'antd';
import { 
  CompressOutlined,
  ScissorOutlined,
  MergeOutlined,
  FilterOutlined,
  BarChartOutlined,
  RobotOutlined,
  SaveOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import { Message } from '@/hooks/useStream';
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';
import MessageContextManager from './MessageContextManager';
import { useMessageCompression, COMPRESSION_LEVEL_MAP, estimateTokenCount } from '@/hooks/useMessageCompression';

const { Option } = Select;
const { TabPane } = Tabs;

export interface AdvancedContextManagerProps {
  messages: Message[];
  onUpdateMessages: (messages: Message[]) => void;
  threadId: string;
  maxContextLength?: number;
  className?: string;
  disabled?: boolean;
}

interface CompressionStrategy {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  action: (messages: Message[]) => Promise<Message[]>;
}

const AdvancedContextManager: React.FC<AdvancedContextManagerProps> = ({
  messages,
  onUpdateMessages,
  threadId,
  maxContextLength = 128000,
  className,
  disabled = false
}) => {
  const { isDark } = useTheme();
  const [activeTab, setActiveTab] = useState('manage');
  const { compressMessages, isCompressing } = useMessageCompression();

  // 计算当前上下文统计
  const contextStats = useMemo(() => {
    const totalTokens = messages.reduce((sum, msg) => sum + estimateTokenCount(msg.content), 0);
    const humanTokens = messages
      .filter(m => m.type === 'human')
      .reduce((sum, msg) => sum + estimateTokenCount(msg.content), 0);
    const aiTokens = messages
      .filter(m => m.type === 'ai')
      .reduce((sum, msg) => sum + estimateTokenCount(msg.content), 0);
    const toolTokens = messages
      .filter(m => m.type === 'tool')
      .reduce((sum, msg) => sum + estimateTokenCount(msg.content), 0);
    
    const usage = (totalTokens / maxContextLength) * 100;
    
    return {
      totalTokens,
      humanTokens,
      aiTokens,
      toolTokens,
      usage,
      remaining: maxContextLength - totalTokens
    };
  }, [messages, maxContextLength]);

  // 压缩策略
  const compressionStrategies: CompressionStrategy[] = [
    {
      id: 'smart',
      name: '智能压缩',
      description: 'AI自动识别并压缩冗余信息，保留关键上下文',
      icon: <RobotOutlined />,
      action: async (msgs) => {
        return await compressMessages(msgs, { 
          compressionLevel: 'medium',
          preserveContext: true,
          targetTokenRatio: 0.6
        });
      }
    },
    {
      id: 'aggressive',
      name: '激进压缩',
      description: '最大程度压缩，仅保留核心信息',
      icon: <ScissorOutlined />,
      action: async (msgs) => {
        return await compressMessages(msgs, { 
          compressionLevel: 'heavy',
          preserveContext: false,
          targetTokenRatio: 0.3
        });
      }
    },
    {
      id: 'merge',
      name: '合并相似',
      description: '合并相似或重复的消息内容',
      icon: <MergeOutlined />,
      action: async (msgs) => {
        // 这里需要后端支持合并相似消息的API
        antMessage.info('合并相似消息功能开发中...');
        return msgs;
      }
    },
    {
      id: 'summarize',
      name: '摘要生成',
      description: '为长对话生成摘要，替换早期消息',
      icon: <FilterOutlined />,
      action: async (msgs) => {
        // 这里需要后端支持生成摘要的API
        antMessage.info('摘要生成功能开发中...');
        return msgs;
      }
    }
  ];

  // 执行压缩策略
  const handleCompressionStrategy = useCallback(async (strategy: CompressionStrategy) => {
    try {
      const compressedMessages = await strategy.action(messages);
      onUpdateMessages(compressedMessages);
      
      // 计算压缩效果
      const originalTokens = contextStats.totalTokens;
      const newTokens = compressedMessages.reduce((sum, msg) => sum + estimateTokenCount(msg.content), 0);
      const savedTokens = originalTokens - newTokens;
      const savedRatio = ((savedTokens / originalTokens) * 100).toFixed(1);
      
      antMessage.success(`压缩成功！节省了 ${savedTokens} tokens (${savedRatio}%)`);
    } catch (error) {
      antMessage.error('压缩失败：' + (error as Error).message);
    }
  }, [messages, onUpdateMessages, contextStats.totalTokens]);

  // 自动优化建议
  const optimizationSuggestions = useMemo(() => {
    const suggestions = [];
    
    if (contextStats.usage > 80) {
      suggestions.push({
        type: 'warning',
        message: '上下文使用率过高，建议立即压缩或清理消息'
      });
    }
    
    if (contextStats.toolTokens > contextStats.totalTokens * 0.4) {
      suggestions.push({
        type: 'info',
        message: '工具调用消息占比较高，可以考虑删除部分调试信息'
      });
    }
    
    const longMessages = messages.filter(m => estimateTokenCount(m.content) > 2000);
    if (longMessages.length > 0) {
      suggestions.push({
        type: 'info',
        message: `发现 ${longMessages.length} 条超长消息，建议单独压缩`
      });
    }
    
    return suggestions;
  }, [contextStats, messages]);

  return (
    <div className={cn("w-full", className)}>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="消息管理" key="manage">
          <MessageContextManager
            messages={messages}
            onUpdateMessages={onUpdateMessages}
            onCompressMessages={async (messageIds) => {
              const messagesToCompress = messages.filter(m => m.id && messageIds.includes(m.id));
              return await compressMessages(messagesToCompress);
            }}
            disabled={disabled}
          />
        </TabPane>

          <TabPane tab="智能压缩" key="compress">
            <div className="space-y-4">
              {/* 压缩策略选择 */}
              <div className="grid grid-cols-2 gap-4">
                {compressionStrategies.map(strategy => (
                  <Card
                    key={strategy.id}
                    hoverable
                    onClick={() => handleCompressionStrategy(strategy)}
                    className={cn(
                      "cursor-pointer transition-all duration-200",
                      isDark ? "bg-gray-800 hover:bg-gray-700" : "bg-gray-50 hover:bg-gray-100"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <div className="text-2xl">{strategy.icon}</div>
                      <div className="flex-1">
                        <h4 className="font-semibold mb-1">{strategy.name}</h4>
                        <p className={cn(
                          "text-sm",
                          isDark ? "text-gray-400" : "text-gray-600"
                        )}>
                          {strategy.description}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {/* 优化建议 */}
              {optimizationSuggestions.length > 0 && (
                <Card title="优化建议" className={cn(
                  isDark ? "bg-gray-800" : "bg-gray-50"
                )}>
                  <ul className="space-y-2">
                    {optimizationSuggestions.map((suggestion, index) => (
                      <li key={index} className={cn(
                        "flex items-start gap-2",
                        suggestion.type === 'warning' ? "text-orange-500" : "text-blue-500"
                      )}>
                        <span>•</span>
                        <span>{suggestion.message}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          </TabPane>

          <TabPane tab="上下文分析" key="analysis">
            <div className="space-y-4">
              {/* Token使用统计 */}
              <Card title="Token 使用统计">
                <div className="space-y-4">
                  <Progress
                    percent={contextStats.usage}
                    status={contextStats.usage > 90 ? 'exception' : contextStats.usage > 80 ? 'warning' : 'active'}
                    format={percent => `${percent.toFixed(1)}%`}
                  />
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Statistic
                      title="总Token数"
                      value={contextStats.totalTokens}
                      suffix={`/ ${maxContextLength}`}
                    />
                    <Statistic
                      title="用户消息"
                      value={contextStats.humanTokens}
                      suffix="tokens"
                    />
                    <Statistic
                      title="AI回复"
                      value={contextStats.aiTokens}
                      suffix="tokens"
                    />
                    <Statistic
                      title="工具调用"
                      value={contextStats.toolTokens}
                      suffix="tokens"
                    />
                  </div>
                </div>
              </Card>

              {/* 消息分布图 */}
              <Card title="消息类型分布">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span>用户消息</span>
                    <Progress
                      percent={(contextStats.humanTokens / contextStats.totalTokens) * 100}
                      size="small"
                      style={{ width: '60%' }}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span>AI回复</span>
                    <Progress
                      percent={(contextStats.aiTokens / contextStats.totalTokens) * 100}
                      size="small"
                      style={{ width: '60%' }}
                      strokeColor="#52c41a"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span>工具调用</span>
                    <Progress
                      percent={(contextStats.toolTokens / contextStats.totalTokens) * 100}
                      size="small"
                      style={{ width: '60%' }}
                      strokeColor="#722ed1"
                    />
                  </div>
                </div>
              </Card>
            </div>
          </TabPane>

          <TabPane tab="历史版本" key="history">
            <div className={cn(
              "text-center py-8",
              isDark ? "text-gray-400" : "text-gray-500"
            )}>
              <HistoryOutlined className="text-4xl mb-4" />
              <p>消息历史版本管理功能开发中...</p>
              <p className="text-sm mt-2">将支持查看和恢复历史版本的消息</p>
            </div>
          </TabPane>
        </Tabs>
    </div>
  );
};

export default AdvancedContextManager;