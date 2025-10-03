/**
 * AI 记忆管理页面
 *
 * 基于 Mem0 标准三层架构：
 * - 用户记忆: 使用 user_id
 * - 智能体记忆: 使用 agent_id
 * - 会话记忆: 使用 run_id
 *
 * 支持组合使用：
 * - user_id + agent_id: 用户与特定智能体的交互记忆
 * - user_id + run_id: 用户的特定会话记忆
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Typography,
  Alert,
  Divider,
  Row,
  Col,
  Tag,
  Statistic,
  Empty,
  Tooltip,
  Badge,
  Segmented,
  Descriptions,
  Spin
} from 'antd';
import {
  BulbOutlined,
  SearchOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  RobotOutlined,
  MessageOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  FilterOutlined,
  ExperimentOutlined,
  InfoCircleOutlined,
  BulbFilled
} from '@ant-design/icons';

import { memoryApi, Memory } from '../../services/memoryApi';
import { agentApi } from '../../services/agentApi';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

/**
 * AI 记忆管理页面组件
 */
const MemoryManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [memoryDetailVisible, setMemoryDetailVisible] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();
  const [agents, setAgents] = useState<any[]>([]);
  const [currentLevel, setCurrentLevel] = useState<string | undefined>(undefined);
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>(undefined);
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(undefined);
  const [selectedRunId, setSelectedRunId] = useState<string | undefined>(undefined);
  const [stats, setStats] = useState({
    total: 0,
    userCount: 0,
    agentCount: 0,
    sessionCount: 0
  });
  const [memoryLevel, setMemoryLevel] = useState<string>('user_agent');

  /**
   * 加载智能体列表
   */
  const loadAgents = async () => {
    try {
      const response = await agentApi.getAgents({ enabled_only: true });
      if (response.status === 'ok' && response.data?.items) {
        setAgents(response.data.items);
      }
    } catch (error) {
      console.error('加载智能体列表失败:', error);
    }
  };

  /**
   * 按层级加载记忆
   */
  const loadMemoriesByLevel = async (level?: string, userId?: string, agentId?: string, runId?: string) => {
    setLoading(true);
    try {
      const response = await memoryApi.listMemoriesByLevel(level, userId, agentId, runId, 100);
      console.log('Memory response:', response);

      if (response.status === 'ok' && response.data) {
        // 确保 data 是数组
        const memoriesData = Array.isArray(response.data) ? response.data : [];
        setMemories(memoriesData);
        updateStats(memoriesData);
        const levelName = level ? getLevelName(level) : '所有';
        if (memoriesData.length > 0) {
          message.success(`加载了 ${memoriesData.length} 条${levelName}记忆`);
        }
      } else {
        setMemories([]);
        updateStats([]);
        message.info('暂无记忆数据');
      }
    } catch (error) {
      console.error('加载记忆失败:', error);
      message.error('加载记忆失败');
      setMemories([]);
      updateStats([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 更新统计数据
   */
  const updateStats = (memoriesData: Memory[]) => {
    const userMemories = memoriesData.filter(m =>
      m.metadata?.level === 'user' || (!m.metadata?.level && m.user_id)
    );
    const agentMemories = memoriesData.filter(m =>
      m.metadata?.level === 'agent'
    );
    const sessionMemories = memoriesData.filter(m =>
      m.metadata?.level === 'session'
    );

    setStats({
      total: memoriesData.length,
      userCount: userMemories.length,
      agentCount: agentMemories.length,
      sessionCount: sessionMemories.length
    });
  };

  /**
   * 获取层级名称
   */
  const getLevelName = (level: string) => {
    const levelNames: Record<string, string> = {
      user: '用户',
      agent: '智能体',
      user_agent: '用户-智能体',
      session: '会话'
    };
    return levelNames[level] || level;
  };

  /**
   * 加载所有记忆（兼容旧方法）
   */
  const loadAllMemories = async () => {
    await loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, selectedRunId);
  };

  /**
   * 处理层级切换
   */
  const handleLevelChange = async (level: string | undefined) => {
    setCurrentLevel(level === '全部' ? undefined : level);
    await loadMemoriesByLevel(level === '全部' ? undefined : level, selectedUserId, selectedAgentId, selectedRunId);
  };

  /**
   * 测试添加对话记忆
   */
  const handleTestConversation = async () => {
    try {
      const values = await form.validateFields();

      // 构建对话消息
      const messages = [
        { role: 'user', content: values.userMessage },
        { role: 'assistant', content: values.assistantMessage || '好的，我记住了' }
      ];

      // 准备元数据
      const metadata: Record<string, any> = {
        source: 'manual_test',
        timestamp: new Date().toISOString(),
        level: values.memoryLevel
      };

      // 如果有标签，添加到元数据
      if (values.metadata && values.metadata.length > 0) {
        metadata.tags = values.metadata;
      }

      // 根据不同的记忆层级，调用不同的参数
      let response;
      const memoryLevel = values.memoryLevel;

      if (memoryLevel === 'user') {
        // 用户记忆：只传user_id
        response = await memoryApi.addConversationMemory(
          messages,
          values.user_id || undefined, // 使用指定用户或当前用户
          undefined, // 不传agent_id
          undefined, // 不传run_id
          metadata
        );
      } else if (memoryLevel === 'agent') {
        // 智能体记忆：只传agent_id
        response = await memoryApi.addConversationMemory(
          messages,
          undefined, // 不传user_id
          values.agent_id,
          undefined, // 不传run_id
          metadata
        );
      } else if (memoryLevel === 'user_agent') {
        // 用户-智能体记忆：传user_id和agent_id
        response = await memoryApi.addConversationMemory(
          messages,
          undefined, // 使用当前用户
          values.agent_id,
          undefined, // 不传run_id
          metadata
        );
      } else if (memoryLevel === 'session') {
        // 会话记忆：传user_id和run_id
        response = await memoryApi.addConversationMemory(
          messages,
          undefined, // 使用当前用户
          undefined, // 不传agent_id
          values.run_id || `session_${Date.now()}`, // 使用指定的或生成新的会话ID
          metadata
        );
      }

      if (response && response.status === 'ok') {
        const levelName = getLevelName(memoryLevel);
        message.success(`${levelName}记忆添加成功`);
        setTestModalVisible(false);
        form.resetFields();
        await loadAllMemories(); // 重新加载记忆列表
      } else {
        message.error('添加失败');
      }
    } catch (error) {
      console.error('添加对话记忆失败:', error);
      message.error('添加对话记忆失败');
    }
  };

  /**
   * 搜索记忆
   */
  const handleSearchMemories = async () => {
    try {
      setSearchLoading(true);
      const values = await searchForm.validateFields();

      // 直接使用Mem0原生搜索方法
      const response = await memoryApi.searchMemories(
        values.query,
        values.user_id || undefined, // user_id - 如果指定了用户名则使用，否则使用当前用户
        values.agent_id, // agent_id - 可选
        undefined, // run_id
        20 // limit
      );

      if (response.status === 'ok' && response.data) {
        // 确保 data 是数组
        const memoriesData = Array.isArray(response.data) ? response.data : [];
        setMemories(memoriesData);
        updateStats(memoriesData);
        const userInfo = values.user_id ? `用户 ${values.user_id} 的` : '';
        message.success(`搜索到 ${userInfo}${memoriesData.length} 条相关记忆`);
      } else {
        setMemories([]);
        updateStats([]);
        message.info('未找到相关记忆');
      }
    } catch (error) {
      console.error('搜索记忆失败:', error);
      message.error('搜索记忆失败');
    } finally {
      setSearchLoading(false);
      setSearchModalVisible(false);
    }
  };

  /**
   * 清除所有记忆
   */
  const handleDeleteAll = async () => {
    try {
      const response = await memoryApi.deleteAllMemories();

      if (response.status === 'ok') {
        message.success('所有记忆已清除');
        setMemories([]);
        updateStats([]);
      } else {
        message.error('清除失败');
      }
    } catch (error) {
      console.error('清除记忆失败:', error);
      message.error('清除记忆失败');
    }
  };

  /**
   * 显示记忆详情
   */
  const showMemoryDetail = (memory: Memory) => {
    setSelectedMemory(memory);
    setMemoryDetailVisible(true);
  };

  /**
   * 记忆表格列定义
   */
  const columns = [
    {
      title: '类型',
      dataIndex: ['metadata', 'level'],
      key: 'level',
      width: 100,
      render: (level: string, record: Memory) => {
        // 根据数据推断层级
        let inferredLevel = level;
        if (!level) {
          if (record.user_id && !record.metadata?.agent_id) {
            inferredLevel = 'user';
          } else if (record.metadata?.agent_id && !record.user_id) {
            inferredLevel = 'agent';
          } else if (record.user_id && record.metadata?.agent_id) {
            inferredLevel = 'user_agent';
          }
        }

        const levelIcons: Record<string, React.ReactNode> = {
          user: <UserOutlined />,
          agent: <RobotOutlined />,
          user_agent: <MessageOutlined />,
          session: <ClockCircleOutlined />
        };

        const levelColors: Record<string, string> = {
          user: 'blue',
          agent: 'green',
          user_agent: 'orange',
          session: 'purple'
        };

        return (
          <Tag
            icon={levelIcons[inferredLevel]}
            color={levelColors[inferredLevel] || 'default'}
          >
            {getLevelName(inferredLevel)}
          </Tag>
        );
      },
    },
    {
      title: '记忆内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string, record: Memory) => (
        <Tooltip title={text}>
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ marginBottom: 0, cursor: 'pointer' }}
            onClick={() => showMemoryDetail(record)}
          >
            {text || '-'}
          </Paragraph>
        </Tooltip>
      ),
    },
    {
      title: '相关性',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      sorter: (a: Memory, b: Memory) => (a.score || 0) - (b.score || 0),
      render: (score: number) => {
        if (!score) return '-';
        const percent = Math.round(score * 100);
        let color = 'default';
        if (percent >= 80) color = 'success';
        else if (percent >= 60) color = 'warning';
        else if (percent >= 40) color = 'processing';

        return (
          <Badge
            count={`${percent}%`}
            showZero
            color={color}
            style={{ backgroundColor: color }}
          />
        );
      },
    },
    {
      title: '元数据',
      dataIndex: 'metadata',
      key: 'metadata',
      width: 200,
      render: (metadata: Record<string, any>) => {
        if (!metadata || Object.keys(metadata).length === 0) return '-';

        const importantKeys = ['type', 'source', 'timestamp'];
        const displayItems = importantKeys
          .filter(key => metadata[key])
          .slice(0, 2);

        return (
          <Space size={4} wrap>
            {displayItems.map(key => (
              <Tag key={key} color="blue">
                {key}: {metadata[key]}
              </Tag>
            ))}
            {Object.keys(metadata).length > 2 && (
              <Tag>+{Object.keys(metadata).length - 2}</Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_: any, record: Memory) => (
        <Space>
          <Button
            size="small"
            type="link"
            onClick={() => showMemoryDetail(record)}
          >
            详情
          </Button>
        </Space>
      ),
    },
  ];

  useEffect(() => {
    loadAgents();
    loadAllMemories();
  }, []);

  return (
    <div style={{ padding: '24px', backgroundColor: '#f0f2f5', minHeight: '100vh' }}>
      {/* 页面标题和说明 */}
      <Card bordered={false} style={{ marginBottom: 16 }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Space align="center">
              <BulbFilled style={{ fontSize: 32, color: '#1890ff' }} />
              <div>
                <Title level={3} style={{ margin: 0 }}>AI 记忆系统</Title>
                <Text type="secondary">
                  基于 Mem0 的智能记忆管理 - AI会从对话中自动学习和记忆重要信息，无需手动输入
                </Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                type="primary"
                icon={<ExperimentOutlined />}
                onClick={() => setTestModalVisible(true)}
              >
                测试添加对话
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card bordered={false}>
            <Statistic
              title="总记忆数"
              value={stats.total}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card bordered={false}>
            <Statistic
              title="用户记忆"
              value={stats.userCount}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card bordered={false}>
            <Statistic
              title="智能体记忆"
              value={stats.agentCount}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card bordered={false}>
            <Statistic
              title="会话记忆"
              value={stats.sessionCount}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要内容区 */}
      <Card bordered={false}>
        {/* 筛选和操作栏 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Space wrap size={16} style={{ width: '100%', justifyContent: 'space-between' }}>
              <Space wrap>
                <Segmented
                  options={[
                    { label: '全部', value: '全部', icon: <DatabaseOutlined /> },
                    { label: '用户', value: 'user', icon: <UserOutlined /> },
                    { label: '智能体', value: 'agent', icon: <RobotOutlined /> },
                    { label: '用户-智能体', value: 'user_agent', icon: <MessageOutlined /> },
                    { label: '会话', value: 'session', icon: <ClockCircleOutlined /> },
                  ]}
                  value={currentLevel || '全部'}
                  onChange={handleLevelChange}
                />

                {(currentLevel === 'user' || currentLevel === 'user_agent') && (
                  <Input
                    style={{ width: 180 }}
                    placeholder="输入用户名（可选）"
                    value={selectedUserId}
                    onChange={(e) => {
                      setSelectedUserId(e.target.value);
                      loadMemoriesByLevel(currentLevel, e.target.value, selectedAgentId, selectedRunId);
                    }}
                    allowClear
                    onClear={() => {
                      setSelectedUserId(undefined);
                      loadMemoriesByLevel(currentLevel, undefined, selectedAgentId, selectedRunId);
                    }}
                    prefix={<UserOutlined />}
                  />
                )}

                {(currentLevel === 'agent' || currentLevel === 'user_agent') && (
                  <Select
                    style={{ width: 200 }}
                    placeholder="选择智能体"
                    value={selectedAgentId}
                    onChange={(value) => {
                      setSelectedAgentId(value);
                      loadMemoriesByLevel(currentLevel, selectedUserId, value, selectedRunId);
                    }}
                    allowClear
                    loading={agents.length === 0}
                  >
                    {agents.map(agent => (
                      <Option key={agent.agent_id} value={agent.agent_id}>
                        {agent.agent_name}
                      </Option>
                    ))}
                  </Select>
                )}

                {currentLevel === 'session' && (
                  <>
                    <Input
                      style={{ width: 180 }}
                      placeholder="输入用户名（可选）"
                      value={selectedUserId}
                      onChange={(e) => {
                        setSelectedUserId(e.target.value);
                        if (selectedRunId) {
                          loadMemoriesByLevel(currentLevel, e.target.value, selectedAgentId, selectedRunId);
                        }
                      }}
                      allowClear
                      onClear={() => {
                        setSelectedUserId(undefined);
                        if (selectedRunId) {
                          loadMemoriesByLevel(currentLevel, undefined, selectedAgentId, selectedRunId);
                        }
                      }}
                      prefix={<UserOutlined />}
                    />
                    <Input
                      style={{ width: 200 }}
                      placeholder="输入会话ID"
                      value={selectedRunId}
                      onChange={(e) => {
                        setSelectedRunId(e.target.value);
                        if (e.target.value) {
                          loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, e.target.value);
                        }
                      }}
                      prefix={<ClockCircleOutlined />}
                    />
                  </>
                )}
              </Space>

              <Space>
                <Button
                  icon={<SearchOutlined />}
                  onClick={() => setSearchModalVisible(true)}
                >
                  搜索记忆
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadAllMemories}
                  loading={loading}
                >
                  刷新
                </Button>
                <Popconfirm
                  title="确认清除"
                  description="此操作将删除所有记忆数据，不可恢复"
                  icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
                  onConfirm={handleDeleteAll}
                  okText="确认清除"
                  okType="danger"
                  cancelText="取消"
                >
                  <Button danger icon={<DeleteOutlined />}>
                    清除所有记忆
                  </Button>
                </Popconfirm>
              </Space>
            </Space>
          </Col>
        </Row>

        <Divider style={{ margin: '12px 0' }} />

        {/* 记忆列表 */}
        <Spin spinning={loading}>
          <Table
            dataSource={memories}
            columns={columns}
            rowKey="id"
            scroll={{ x: 800 }}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description={
                    <span>
                      暂无记忆数据
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        AI 会在对话中自动学习和记住重要信息
                      </Text>
                    </span>
                  }
                >
                  <Button
                    type="primary"
                    icon={<ExperimentOutlined />}
                    onClick={() => setTestModalVisible(true)}
                  >
                    测试添加对话
                  </Button>
                </Empty>
              )
            }}
          />
        </Spin>
      </Card>

      {/* 记忆详情模态框 */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            记忆详情
          </Space>
        }
        open={memoryDetailVisible}
        onCancel={() => {
          setMemoryDetailVisible(false);
          setSelectedMemory(null);
        }}
        footer={[
          <Button key="close" onClick={() => {
            setMemoryDetailVisible(false);
            setSelectedMemory(null);
          }}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {selectedMemory && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="记忆ID">
              <Text code copyable>{selectedMemory.id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="记忆内容">
              <Paragraph copyable>{selectedMemory.content}</Paragraph>
            </Descriptions.Item>
            {selectedMemory.user_id && (
              <Descriptions.Item label="用户ID">
                <Tag color="blue">{selectedMemory.user_id}</Tag>
              </Descriptions.Item>
            )}
            {selectedMemory.score && (
              <Descriptions.Item label="相关性分数">
                <Badge
                  count={`${Math.round(selectedMemory.score * 100)}%`}
                  showZero
                  color="processing"
                />
              </Descriptions.Item>
            )}
            {selectedMemory.metadata && (
              <Descriptions.Item label="元数据">
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(selectedMemory.metadata, null, 2)}
                </pre>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* 测试添加对话记忆模态框 */}
      <Modal
        title={
          <Space>
            <ExperimentOutlined />
            测试添加对话记忆
          </Space>
        }
        open={testModalVisible}
        onOk={handleTestConversation}
        onCancel={() => {
          setTestModalVisible(false);
          form.resetFields();
        }}
        width={650}
        okText="添加记忆"
        cancelText="取消"
      >
        <Alert
          message="模拟对话测试"
          description="输入一段对话内容，AI 会从中提取和学习重要信息作为长期记忆。"
          type="info"
          style={{ marginBottom: 16 }}
        />

        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="memoryLevel"
            label="记忆层级"
            rules={[{ required: true, message: '请选择记忆层级' }]}
            initialValue="user_agent"
            tooltip="选择记忆的存储层级，决定记忆的共享范围"
          >
            <Segmented
              block
              onChange={(value) => {
                setMemoryLevel(value as string);
                form.setFieldsValue({ memoryLevel: value });
              }}
              options={[
                {
                  label: (
                    <Space>
                      <UserOutlined />
                      <span>用户记忆</span>
                    </Space>
                  ),
                  value: 'user',
                },
                {
                  label: (
                    <Space>
                      <RobotOutlined />
                      <span>智能体记忆</span>
                    </Space>
                  ),
                  value: 'agent',
                },
                {
                  label: (
                    <Space>
                      <MessageOutlined />
                      <span>用户-智能体</span>
                    </Space>
                  ),
                  value: 'user_agent',
                },
                {
                  label: (
                    <Space>
                      <ClockCircleOutlined />
                      <span>会话记忆</span>
                    </Space>
                  ),
                  value: 'session',
                },
              ]}
            />
          </Form.Item>

          {/* 记忆层级说明 */}
          <div style={{
            background: '#f6f8fa',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '13px',
            color: '#586069'
          }}>
            {memoryLevel === 'user' && (
              <>
                <strong>👤 用户记忆：</strong>跨所有智能体共享，适合存储个人信息、偏好设置等
              </>
            )}
            {memoryLevel === 'agent' && (
              <>
                <strong>🤖 智能体记忆：</strong>该智能体的所有用户共享，适合存储智能体学到的通用知识
              </>
            )}
            {memoryLevel === 'user_agent' && (
              <>
                <strong>💬 用户-智能体记忆：</strong>仅在您与该智能体的对话中使用，最常用的记忆类型
              </>
            )}
            {memoryLevel === 'session' && (
              <>
                <strong>⏱️ 会话记忆：</strong>仅在当前会话中有效，适合临时信息
              </>
            )}
          </div>

          <Form.Item
            name="userMessage"
            label="用户消息"
            rules={[{ required: true, message: '请输入用户消息' }]}
          >
            <TextArea
              rows={3}
              placeholder="例如：我是高超，是一名资深运维工程师，擅长 Kubernetes 和 Python..."
            />
          </Form.Item>

          <Form.Item
            name="assistantMessage"
            label="AI 回复（可选）"
          >
            <TextArea
              rows={2}
              placeholder="例如：好的，我记住了您的专业背景..."
            />
          </Form.Item>

          {/* 根据记忆层级显示不同的选择器 */}
          {(memoryLevel === 'user_agent' ||
            memoryLevel === 'agent') && (
            <Form.Item
              name="agent_id"
              label="智能体选择"
              rules={[{ required: true, message: '请选择智能体' }]}
              initialValue={agents.length > 0 ? agents[0].agent_id : undefined}
            >
              <Select placeholder="选择智能体" loading={agents.length === 0}>
                {agents.map(agent => (
                  <Option key={agent.agent_id} value={agent.agent_id}>
                    {agent.agent_name}
                  </Option>
                ))}
              </Select>
            </Form.Item>
          )}

          {memoryLevel === 'user' && (
            <Form.Item
              name="user_id"
              label="用户名（可选）"
              tooltip="留空则为当前用户添加记忆"
            >
              <Input
                placeholder="输入用户名，默认为当前用户"
                prefix={<UserOutlined />}
              />
            </Form.Item>
          )}

          {memoryLevel === 'session' && (
            <Form.Item
              name="run_id"
              label="会话ID（可选）"
              tooltip="指定会话ID，留空则自动生成"
            >
              <Input
                placeholder="输入会话ID或留空自动生成"
                prefix={<ClockCircleOutlined />}
              />
            </Form.Item>
          )}

          <Form.Item
            name="metadata"
            label="元数据标签（可选）"
            tooltip="添加额外的标签信息，如：type, category, importance等"
          >
            <Select
              mode="tags"
              placeholder="输入标签，如：重要、技术知识、个人信息"
              style={{ width: '100%' }}
            >
              <Option value="important">重要</Option>
              <Option value="technical">技术知识</Option>
              <Option value="personal">个人信息</Option>
              <Option value="preference">偏好设置</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 搜索记忆模态框 */}
      <Modal
        title={
          <Space>
            <SearchOutlined />
            搜索记忆
          </Space>
        }
        open={searchModalVisible}
        onOk={handleSearchMemories}
        onCancel={() => {
          setSearchModalVisible(false);
          searchForm.resetFields();
        }}
        confirmLoading={searchLoading}
        okText="搜索"
        cancelText="取消"
        width={600}
      >
        <Form
          form={searchForm}
          layout="vertical"
        >
          <Form.Item
            name="query"
            label="搜索关键词"
            rules={[{ required: true, message: '请输入搜索关键词' }]}
          >
            <Input
              placeholder="例如：运维、技能、偏好..."
              prefix={<SearchOutlined />}
              onPressEnter={handleSearchMemories}
            />
          </Form.Item>

          <Form.Item
            name="user_id"
            label="用户选择（可选）"
            tooltip="留空则搜索当前用户的记忆"
          >
            <Input
              placeholder="输入用户名，例如：admin、zhangsan"
              prefix={<UserOutlined />}
              allowClear
            />
          </Form.Item>

          <Form.Item
            name="agent_id"
            label="智能体选择（可选）"
            tooltip="选择特定智能体，缩小搜索范围"
          >
            <Select placeholder="选择智能体（留空搜索所有）" allowClear loading={agents.length === 0}>
              {agents.map(agent => (
                <Option key={agent.agent_id} value={agent.agent_id}>
                  {agent.agent_name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MemoryManagement;