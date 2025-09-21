import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Modal, Button, Tooltip, Dropdown, Input, Spin, message as antMessage, Tag, Checkbox, Divider, List } from 'antd';
import { 
  DeleteOutlined, 
  EditOutlined, 
  CompressOutlined,
  MoreOutlined,
  ExclamationCircleOutlined,
  SaveOutlined,
  CloseOutlined,
  ThunderboltOutlined,
  DownOutlined,
  RightOutlined
} from '@ant-design/icons';
import { Message } from '@/hooks/useStream';
import { cn } from '@/utils/lib-utils';
import { useTheme } from '@/hooks/ThemeContext';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import { estimateTokenCount } from '@/hooks/useMessageCompression';

const { TextArea } = Input;
const { confirm } = Modal;

// 扩展 Message 类型以包含 token_count
export type MessageWithTokenCount = Message & { token_count?: number };

export interface MessageContextManagerProps {
  messages: MessageWithTokenCount[];
  onUpdateMessages: (messages: MessageWithTokenCount[]) => void;
  onCompressMessages?: (messageIds: string[]) => Promise<MessageWithTokenCount[]>;
  className?: string;
  disabled?: boolean;
  selectedMessages?: Set<string>;
  onSelectionChange?: (selected: Set<string>) => void;
}

interface MessageItemProps {
  message: MessageWithTokenCount;
  index: number;
  onEdit: (index: number, newContent: string) => void;
  onDelete: (index: number) => void;
  onCompress: (index: number) => void;
  disabled?: boolean;
}

// 单条消息管理组件
const MessageItem: React.FC<MessageItemProps> = ({
  message,
  index,
  onEdit,
  onDelete,
  onCompress,
  disabled = false
}) => {
  const { isDark } = useTheme();
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content || '');
  const [isExpanded, setIsExpanded] = useState(false);
  
  // 使用消息自带的 token_count
  const tokenCount = message.token_count || estimateTokenCount(message.content || '');
  
  // 编辑时的 token 计数 - 使用估算
  const editTokenCount = useMemo(() => {
    return isEditing ? estimateTokenCount(editContent) : tokenCount;
  }, [editContent, isEditing, tokenCount]);
  
  // 根据token数量确定显示颜色
  const getTokenColor = (count: number) => {
    if (count < 500) return 'success';
    if (count < 1000) return 'default';
    if (count < 2000) return 'warning';
    return 'error';
  };

  const handleSaveEdit = useCallback(() => {
    onEdit(index, editContent);
    setIsEditing(false);
  }, [index, editContent, onEdit]);

  const handleCancelEdit = useCallback(() => {
    setEditContent(message.content || '');
    setIsEditing(false);
  }, [message.content]);

  const menuItems = [
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑消息',
      onClick: () => setIsEditing(true),
      disabled: disabled || message.type !== 'human'
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除消息',
      onClick: () => onDelete(index),
      disabled: disabled,
      danger: true
    },
    {
      key: 'compress',
      icon: <CompressOutlined />,
      label: '压缩消息',
      onClick: () => onCompress(index),
      disabled: disabled || message.type !== 'ai'
    }
  ];

  // 生成消息摘要
  const getMessageSummary = (content: string, message?: MessageWithTokenCount) => {
    // 跳过空消息
    if (!content || content.trim().length === 0) {
      // 对于工具消息，显示工具名称
      if (message?.type === 'tool' && message.name) {
        return `[工具: ${message.name}]`;
      }
      return '(空消息)';
    }
    
    // 移除多余的空白和换行
    const cleanContent = content.trim().replace(/\s+/g, ' ');
    const maxLength = 80; // 设置为80个字符
    
    if (cleanContent.length <= maxLength) return cleanContent;
    return cleanContent.substring(0, maxLength) + '...';
  };

  return (
    <div className={cn(
      "group relative p-3 rounded-lg mb-2 transition-all duration-200 cursor-pointer",
      isDark ? "bg-gray-800 hover:bg-gray-750" : "bg-gray-50 hover:bg-gray-100",
      "border",
      isDark ? "border-gray-700" : "border-gray-200"
    )}
    onClick={() => !isEditing && setIsExpanded(!isExpanded)}
    >
      {/* 折叠展开标题栏 */}
      <div className="flex items-center gap-2">
        {/* 展开/折叠按钮 - 固定宽度 */}
        <Button
          type="text"
          size="small"
          icon={isExpanded ? <DownOutlined /> : <RightOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          className="flex-shrink-0"
          style={{ width: '32px', minWidth: '32px', padding: '4px' }}
        />
        
        {/* 消息类型标识 - 固定宽度 */}
        <div className={cn(
          "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold",
          message.type === 'human' 
            ? (isDark ? "bg-blue-900 text-blue-200" : "bg-blue-100 text-blue-700")
            : message.type === 'ai'
            ? (isDark ? "bg-green-900 text-green-200" : "bg-green-100 text-green-700")
            : (isDark ? "bg-gray-700 text-gray-300" : "bg-gray-200 text-gray-600")
        )}>
          {message.type === 'human' ? 'U' : message.type === 'ai' ? 'A' : 'T'}
        </div>

        {/* 消息摘要 - 可变宽度但有最大宽度限制 */}
        {!isExpanded && !isEditing && (
          <div className={cn(
            "text-sm truncate flex-1",
            isDark ? "text-gray-300" : "text-gray-700"
          )}
          style={{ maxWidth: '600px' }} // 增加最大宽度以适应80个字符
          >
            {getMessageSummary(message.content || '', message)}
          </div>
        )}

        {/* 右侧固定宽度区域：Token信息和操作按钮 */}
        <div className="flex items-center gap-2 flex-shrink-0 ml-auto">
            <Tooltip title={`Token消耗: ${tokenCount}`}>
              <Tag 
                color={getTokenColor(tokenCount)}
                icon={<ThunderboltOutlined />}
                className="cursor-help"
              >
                {tokenCount} tokens
              </Tag>
            </Tooltip>
            {/* 如果消息被压缩过，显示压缩标记 */}
            {message.additional_kwargs?.compressed && (
              <Tooltip title={`已压缩，原始长度: ${message.additional_kwargs.original_length} 字符`}>
                <Tag color="purple" icon={<CompressOutlined />}>
                  已压缩
                </Tag>
              </Tooltip>
            )}
          
          {/* 操作按钮 */}
            <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <Dropdown
                menu={{ items: menuItems }}
                trigger={['click']}
                placement="bottomRight"
              >
                <Button
                  type="text"
                  icon={<MoreOutlined />}
                  onClick={(e) => e.stopPropagation()}
                  className={cn(
                    "text-gray-500 hover:text-gray-700",
                    isDark && "text-gray-400 hover:text-gray-200"
                  )}
                />
              </Dropdown>
            </div>
          </div>
        </div>

      {/* 展开时显示完整内容 */}
      {(isExpanded || isEditing) && (
        <div className="mt-3">
          {isEditing ? (
            <div className="space-y-2">
              <TextArea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                autoSize={{ minRows: 2, maxRows: 10 }}
                className={cn(
                  isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"
                )}
              />
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <Button
                    size="small"
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={handleSaveEdit}
                  >
                    保存
                  </Button>
                  <Button
                    size="small"
                    icon={<CloseOutlined />}
                    onClick={handleCancelEdit}
                  >
                    取消
                  </Button>
                </div>
                <div className="text-sm">
                  <span className={cn(
                    "mr-2",
                    isDark ? "text-gray-400" : "text-gray-600"
                  )}>
                    Token变化:
                  </span>
                  <Tag color={getTokenColor(editTokenCount)}>
                    {editTokenCount} tokens
                  </Tag>
                  {editTokenCount !== tokenCount && (
                    <span className={cn(
                      "ml-2",
                      editTokenCount > tokenCount ? "text-red-500" : "text-green-500"
                    )}>
                      ({editTokenCount > tokenCount ? '+' : ''}{editTokenCount - tokenCount})
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className={cn(
              "prose max-w-none",
              isDark ? "prose-invert" : ""
            )}>
              <MarkdownRenderer content={message.content || ''} />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 主组件
const MessageContextManager: React.FC<MessageContextManagerProps> = ({
  messages,
  onUpdateMessages,
  onCompressMessages,
  className,
  disabled = false,
  selectedMessages: externalSelectedMessages,
  onSelectionChange: externalOnSelectionChange
}) => {
  const { isDark } = useTheme();
  const [internalSelectedMessages, setInternalSelectedMessages] = useState<Set<number>>(new Set());
  const [isCompressing, setIsCompressing] = useState(false);
  const [sortBy, setSortBy] = useState<'default' | 'token-asc' | 'token-desc'>('default');
  const [filterBy, setFilterBy] = useState<'all' | 'high-token'>('all');

  // 使用外部传入的选择状态或内部状态
  const selectedMessages = externalSelectedMessages ? 
    new Set(messages
      .map((msg, index) => msg.id && externalSelectedMessages.has(msg.id) ? index : null)
      .filter(index => index !== null) as number[]) : 
    internalSelectedMessages;
    
  const setSelectedMessages = externalOnSelectionChange ? 
    (indices: Set<number>) => {
      const ids = new Set<string>();
      indices.forEach(index => {
        const msgId = messages[index]?.id;
        if (msgId) ids.add(msgId);
      });
      externalOnSelectionChange(ids);
    } : 
    setInternalSelectedMessages;

  // 获取消息的 token 数（使用消息自带的 token_count 或估算）
  const getMessageTokenCount = useCallback((message: MessageWithTokenCount) => {
    return message.token_count || estimateTokenCount(message.content || '');
  }, []);

  // 处理消息编辑
  const handleEditMessage = useCallback((index: number, newContent: string) => {
    const newMessages = [...messages];
    newMessages[index] = { ...newMessages[index], content: newContent };
    onUpdateMessages(newMessages);
    antMessage.success('消息已更新');
  }, [messages, onUpdateMessages]);

  // 处理消息删除
  const handleDeleteMessage = useCallback((index: number) => {
    confirm({
      title: '确认删除消息？',
      icon: <ExclamationCircleOutlined />,
      content: '删除后无法恢复，这可能会影响对话的连贯性。',
      okText: '删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk() {
        const newMessages = messages.filter((_, i) => i !== index);
        onUpdateMessages(newMessages);
        antMessage.success('消息已删除');
      }
    });
  }, [messages, onUpdateMessages]);

  // 处理消息压缩
  const handleCompressMessage = useCallback(async (index: number) => {
    if (!onCompressMessages) {
      antMessage.warning('压缩功能未启用');
      return;
    }

    confirm({
      title: '压缩消息？',
      icon: <CompressOutlined />,
      content: '将使用AI模型压缩此消息，保留关键信息。',
      okText: '压缩',
      cancelText: '取消',
      async onOk() {
        setIsCompressing(true);
        try {
          const messageId = messages[index].id;
          if (!messageId) {
            throw new Error('消息缺少ID');
          }
          
          const compressedMessages = await onCompressMessages([messageId]);
          if (compressedMessages && compressedMessages.length > 0) {
            const newMessages = [...messages];
            newMessages[index] = compressedMessages[0];
            onUpdateMessages(newMessages);
            antMessage.success('消息压缩成功');
          }
        } catch (error) {
          antMessage.error('压缩失败：' + (error as Error).message);
        } finally {
          setIsCompressing(false);
        }
      }
    });
  }, [messages, onCompressMessages, onUpdateMessages]);

  // 批量操作
  const handleBatchDelete = useCallback(() => {
    if (selectedMessages.size === 0) return;

    confirm({
      title: `确认删除 ${selectedMessages.size} 条消息？`,
      icon: <ExclamationCircleOutlined />,
      content: '删除后无法恢复，这可能会影响对话的连贯性。',
      okText: '删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk() {
        const newMessages = messages.filter((_, index) => !selectedMessages.has(index));
        onUpdateMessages(newMessages);
        setSelectedMessages(new Set());
        antMessage.success(`已删除 ${selectedMessages.size} 条消息`);
      }
    });
  }, [messages, selectedMessages, onUpdateMessages]);

  // 批量压缩
  const handleBatchCompress = useCallback(async () => {
    if (selectedMessages.size === 0 || !onCompressMessages) return;

    const messageIds = Array.from(selectedMessages)
      .map(index => messages[index]?.id)
      .filter((id): id is string => !!id);

    if (messageIds.length === 0) {
      antMessage.warning('选中的消息缺少ID');
      return;
    }

    confirm({
      title: `压缩 ${messageIds.length} 条消息？`,
      icon: <CompressOutlined />,
      content: '将使用AI模型批量压缩选中的消息。',
      okText: '压缩',
      cancelText: '取消',
      async onOk() {
        setIsCompressing(true);
        try {
          const compressedMessages = await onCompressMessages(messageIds);
          
          // 更新压缩后的消息
          const newMessages = [...messages];
          const idToCompressed = new Map(
            compressedMessages.map(msg => [msg.id, msg])
          );
          
          selectedMessages.forEach(index => {
            const originalId = messages[index].id;
            if (originalId && idToCompressed.has(originalId)) {
              newMessages[index] = idToCompressed.get(originalId)!;
            }
          });
          
          onUpdateMessages(newMessages);
          setSelectedMessages(new Set());
          antMessage.success(`成功压缩 ${compressedMessages.length} 条消息`);
        } catch (error) {
          antMessage.error('批量压缩失败：' + (error as Error).message);
        } finally {
          setIsCompressing(false);
        }
      }
    });
  }, [messages, selectedMessages, onCompressMessages, onUpdateMessages]);

  // 处理和排序消息
  const processedMessages = useMemo(() => {
    // 不过滤工具消息，它们可能有空内容但仍然有用
    let result = messages.filter(msg => {
      // 工具消息即使内容为空也保留
      if (msg.type === 'tool') return true;
      // 其他消息需要有内容
      return msg.content && msg.content.trim().length > 0;
    });
    
    // 筛选
    if (filterBy === 'high-token') {
      result = result.filter(msg => getMessageTokenCount(msg) > 1000);
    }
    
    // 排序
    if (sortBy === 'token-asc') {
      result.sort((a, b) => getMessageTokenCount(a) - getMessageTokenCount(b));
    } else if (sortBy === 'token-desc') {
      result.sort((a, b) => getMessageTokenCount(b) - getMessageTokenCount(a));
    }
    
    return result;
  }, [messages, sortBy, filterBy, getMessageTokenCount]);

  // 计算统计信息
  const stats = useMemo(() => {
    const humanCount = messages.filter(m => m.type === 'human').length;
    const aiCount = messages.filter(m => m.type === 'ai').length;
    const toolCount = messages.filter(m => m.type === 'tool').length;
    
    // 计算token最多的前5条消息
    const topTokenMessages = [...messages]
      .map((msg, index) => ({
        index,
        message: msg,
        tokens: getMessageTokenCount(msg)
      }))
      .sort((a, b) => b.tokens - a.tokens)
      .slice(0, 5);
    
    return {
      total: messages.length,
      human: humanCount,
      ai: aiCount,
      tool: toolCount,
      topTokenMessages
    };
  }, [messages, getMessageTokenCount]);

  return (
    <div className={cn("w-full", className)}>
      <Spin spinning={isCompressing} tip="正在压缩消息...">
        {/* 工具栏 */}
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* 全选按钮 */}
              <Checkbox
                checked={selectedMessages.size === messages.length && messages.length > 0}
                indeterminate={selectedMessages.size > 0 && selectedMessages.size < messages.length}
                onChange={(e) => {
                  if (e.target.checked) {
                    const allIndices = new Set(messages.map((_, index) => index));
                    setSelectedMessages(allIndices);
                  } else {
                    setSelectedMessages(new Set());
                  }
                }}
                disabled={disabled || messages.length === 0}
              >
                全选
              </Checkbox>
              
              <Divider type="vertical" />
              
              <span className={cn("text-sm", isDark ? "text-gray-300" : "text-gray-600")}>
                排序:
              </span>
              <Button.Group size="small">
                <Button
                  type={sortBy === 'default' ? 'primary' : 'default'}
                  onClick={() => setSortBy('default')}
                >
                  默认
                </Button>
                <Button
                  type={sortBy === 'token-desc' ? 'primary' : 'default'}
                  onClick={() => setSortBy('token-desc')}
                  icon={<ThunderboltOutlined />}
                >
                  Token↓
                </Button>
                <Button
                  type={sortBy === 'token-asc' ? 'primary' : 'default'}
                  onClick={() => setSortBy('token-asc')}
                  icon={<ThunderboltOutlined />}
                >
                  Token↑
                </Button>
              </Button.Group>
              
              <span className={cn("text-sm ml-4", isDark ? "text-gray-300" : "text-gray-600")}>
                筛选:
              </span>
              <Button.Group size="small">
                <Button
                  type={filterBy === 'all' ? 'primary' : 'default'}
                  onClick={() => setFilterBy('all')}
                >
                  全部
                </Button>
                <Button
                  type={filterBy === 'high-token' ? 'primary' : 'default'}
                  onClick={() => setFilterBy('high-token')}
                >
                  高Token (>1000)
                </Button>
              </Button.Group>
            </div>
            
            {/* Token消耗Top 5 */}
            <Tooltip
              title={
                <div>
                  <div className="font-semibold mb-2">Token消耗 Top 5</div>
                  {stats.topTokenMessages.map((item, i) => (
                    <div key={i} className="flex justify-between mb-1">
                      <span>
                        {item.message.type === 'human' ? '用户' : 'AI'} #{item.index + 1}
                      </span>
                      <span className="ml-4 font-mono">{item.tokens} tokens</span>
                    </div>
                  ))}
                </div>
              }
            >
              <Button size="small" icon={<ThunderboltOutlined />}>
                Top 5 高耗消息
              </Button>
            </Tooltip>
          </div>
        </div>
        
        {/* 消息列表 - 使用虚拟滚动 */}
        {processedMessages.length === 0 ? (
          <div className={cn(
            "text-center py-8 rounded-lg border",
            isDark ? "bg-gray-800 border-gray-700 text-gray-400" : "bg-gray-50 border-gray-200 text-gray-500"
          )}>
            {filterBy === 'high-token' ? '没有高Token消息（>1000 tokens）' : '暂无消息'}
          </div>
        ) : (
          <List
            className="message-list-container"
            style={{ height: '500px', overflow: 'auto' }}
            itemLayout="vertical"
            dataSource={processedMessages}
            renderItem={(message) => {
              // 获取消息在原始数组中的索引
              const originalIndex = messages.findIndex(m => m === message);
              return (
                <List.Item
                  key={message.id || originalIndex}
                  style={{ padding: '0', border: 'none' }}
                >
                  <div className="flex items-start gap-2 px-2 w-full">
                    <Checkbox
                      checked={selectedMessages.has(originalIndex)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedMessages);
                        if (e.target.checked) {
                          newSelected.add(originalIndex);
                        } else {
                          newSelected.delete(originalIndex);
                        }
                        setSelectedMessages(newSelected);
                      }}
                      disabled={disabled}
                      className="mt-5"
                    />
                    <div className="flex-1">
                      <MessageItem
                        message={message}
                        index={originalIndex}
                        onEdit={handleEditMessage}
                        onDelete={handleDeleteMessage}
                        onCompress={handleCompressMessage}
                        disabled={disabled}
                      />
                    </div>
                  </div>
                </List.Item>
              );
            }}
            // 启用虚拟滚动
            virtual
          />
        )}
      </Spin>
    </div>
  );
};

export default MessageContextManager;