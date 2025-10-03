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
  Tag
} from 'antd';
import { 
  BulbOutlined,
  SearchOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

import { memoryApi, Memory } from '../../services/memoryApi';
import { agentApi } from '../../services/agentApi';

const { Title, Text } = Typography;
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
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();
  const [agents, setAgents] = useState<any[]>([]);
  const [currentLevel, setCurrentLevel] = useState<string | undefined>(undefined);
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>(undefined);
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(undefined);
  const [selectedRunId, setSelectedRunId] = useState<string | undefined>(undefined);

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
        const levelName = level ? getLevelName(level) : '所有';
        message.success(`加载了 ${memoriesData.length} 条${levelName}记忆`);
      } else {
        setMemories([]);
        message.info('暂无记忆数据');
      }
    } catch (error) {
      console.error('加载记忆失败:', error);
      message.error('加载记忆失败');
      setMemories([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取层级名称
   */
  const getLevelName = (level: string) => {
    const levelNames: Record<string, string> = {
      user: '👤 用户',
      agent: '🤖 智能体',
      user_agent: '💬 用户-智能体',
      session: '⏱️ 会话'
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
    setCurrentLevel(level);
    await loadMemoriesByLevel(level, selectedUserId, selectedAgentId, selectedRunId);
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

      const response = await memoryApi.addConversationMemory(
        messages,
        undefined, // 使用当前用户
        values.agent_id || 'test_agent', // 使用用户选择的智能体
        `test_${Date.now()}`,
        { source: 'manual_test', timestamp: new Date().toISOString() }
      );

      if (response.status === 'ok') {
        message.success('测试对话记忆添加成功');
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
      const values = await searchForm.validateFields();
      setSearchLoading(true);

      const response = await memoryApi.searchMemories({
        namespace: 'user_memories', // 简化命名空间
        query: values.query,
        limit: 20,
        namespace_params: {
          agent_id: values.agent_id || 'test_agent' // 使用用户选择的智能体
        }
      });

      if (response.status === 'ok' && response.data) {
        // 确保 data 是数组
        const memoriesData = Array.isArray(response.data) ? response.data : [];
        setMemories(memoriesData);
        message.success(`搜索到 ${memoriesData.length} 条相关记忆`);
      } else {
        setMemories([]);
        message.info('未找到相关记忆');
      }
    } catch (error) {
      console.error('搜索记忆失败:', error);
      message.error('搜索记忆失败');
    } finally {
      setSearchLoading(false);
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
      } else {
        message.error('清除失败');
      }
    } catch (error) {
      console.error('清除记忆失败:', error);
      message.error('清除记忆失败');
    }
  };

  /**
   * 记忆表格列定义
   */
  const columns = [
    {
      title: '层级',
      dataIndex: ['metadata', 'level'],
      key: 'level',
      width: 140,
      render: (level: string) => {
        if (!level) return <Tag>未分类</Tag>;
        const levelConfig: Record<string, { color: string; text: string }> = {
          user: { color: 'blue', text: '👤 用户' },
          agent: { color: 'green', text: '🤖 智能体' },
          user_agent: { color: 'orange', text: '💬 用户-智能体' },
          session: { color: 'gray', text: '⏱️ 会话' }
        };
        const config = levelConfig[level] || { color: 'default', text: level };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      render: (text: string) => text ? <Tag color="blue">{text}</Tag> : '-',
    },
    {
      title: '记忆内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string) => (
        <div style={{ maxWidth: 400 }}>
          {text || '-'}
        </div>
      ),
    },
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 280,
      render: (text: string) => (
        <Text code style={{ fontSize: '11px' }}>
          {text || '-'}
        </Text>
      ),
    },
  ];

  useEffect(() => {
    loadAgents();
    loadAllMemories();
  }, []);

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[0, 16]}>
        <Col span={24}>
          <Title level={2}>
            <BulbOutlined style={{ marginRight: 8 }} />
            AI 记忆系统
          </Title>
          
          <Alert
            message="基于 Mem0 的智能记忆管理"
            description="AI 会从对话中自动学习和记住重要信息，无需手动输入。您可以查看 AI 学到的记忆，搜索相关内容，或在需要时清理记忆。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </Col>

        <Col span={24}>
          <Card>
            {/* 层级筛选器 */}
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Space wrap>
                  <span style={{ fontWeight: 500 }}>记忆层级:</span>
                  <Select
                    style={{ width: 200 }}
                    placeholder="选择记忆层级"
                    value={currentLevel}
                    onChange={handleLevelChange}
                    allowClear
                  >
                    <Option value={undefined}>全部</Option>
                    <Option value="user">👤 用户</Option>
                    <Option value="agent">🤖 智能体</Option>
                    <Option value="user_agent">💬 用户-智能体</Option>
                    <Option value="session">⏱️ 会话</Option>
                  </Select>

                  {(currentLevel === 'agent' || currentLevel === 'user_agent') && (
                    <Select
                      style={{ width: 180 }}
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
                    <Input
                      style={{ width: 180 }}
                      placeholder="输入会话ID"
                      value={selectedRunId}
                      onChange={(e) => {
                        setSelectedRunId(e.target.value);
                        if (e.target.value) {
                          loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, e.target.value);
                        }
                      }}
                    />
                  )}
                </Space>
              </Col>
            </Row>

            <Divider style={{ margin: '12px 0' }} />

            <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
              <Col>
                <Space>
                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={loadAllMemories}
                    loading={loading}
                  >
                    刷新记忆
                  </Button>

                  <Button
                    icon={<SearchOutlined />}
                    onClick={() => setSearchModalVisible(true)}
                  >
                    搜索记忆
                  </Button>
                </Space>
              </Col>

              <Col>
                <Space>
                  <Button
                    icon={<PlusOutlined />}
                    onClick={() => setTestModalVisible(true)}
                  >
                    测试添加对话
                  </Button>
                  
                  <Popconfirm
                    title="确认清除所有记忆吗？"
                    description="此操作不可恢复，将删除当前用户的所有记忆数据。"
                    icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
                    onConfirm={handleDeleteAll}
                    okText="确认清除"
                    okType="danger"
                    cancelText="取消"
                  >
                    <Button 
                      danger 
                      icon={<DeleteOutlined />}
                    >
                      清除所有记忆
                    </Button>
                  </Popconfirm>
                </Space>
              </Col>
            </Row>

            <Table
              dataSource={memories}
              columns={columns}
              rowKey="id"
              loading={loading}
              scroll={{ x: 1000 }}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记忆`
              }}
              locale={{
                emptyText: (
                  <div style={{ padding: '40px', textAlign: 'center' }}>
                    <BulbOutlined style={{ fontSize: '24px', color: '#ccc', marginBottom: '8px' }} />
                    <div>暂无记忆数据</div>
                    <div style={{ color: '#999', fontSize: '12px', marginTop: '4px' }}>
                      AI 会在对话中自动学习和记住重要信息
                    </div>
                  </div>
                )
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 测试添加对话记忆模态框 */}
      <Modal
        title="测试添加对话记忆"
        open={testModalVisible}
        onOk={handleTestConversation}
        onCancel={() => {
          setTestModalVisible(false);
          form.resetFields();
        }}
        width={600}
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

          <Form.Item
            name="agent_id"
            label="智能体选择"
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
        </Form>
      </Modal>

      {/* 搜索记忆模态框 */}
      <Modal
        title="搜索记忆"
        open={searchModalVisible}
        onOk={handleSearchMemories}
        onCancel={() => {
          setSearchModalVisible(false);
          searchForm.resetFields();
        }}
        confirmLoading={searchLoading}
        okText="搜索"
        cancelText="取消"
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
              onPressEnter={handleSearchMemories}
            />
          </Form.Item>

          <Form.Item
            name="agent_id"
            label="智能体选择（可选）"
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