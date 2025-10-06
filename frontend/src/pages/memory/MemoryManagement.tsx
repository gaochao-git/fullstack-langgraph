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
  InputNumber,
  Select,
  App,
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
  BulbFilled,
  EditOutlined
} from '@ant-design/icons';

import { memoryApi, Memory } from '../../services/memoryApi';
import { agentApi } from '../../services/agentApi';
import { useAuth } from '../../hooks/useAuth';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

/**
 * AI 记忆管理页面组件
 */
const MemoryManagement: React.FC = () => {
  const { message } = App.useApp();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [editForm] = Form.useForm();
  const [form] = Form.useForm();
  const [searchForm] = Form.useForm();
  const [agents, setAgents] = useState<any[]>([]);
  const [currentLevel, setCurrentLevel] = useState<string>('user');
  const [selectedUserId, setSelectedUserId] = useState<string | undefined>(undefined);
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>(undefined);
  const [selectedRunId, setSelectedRunId] = useState<string | undefined>(undefined);
  const [stats, setStats] = useState({
    userCount: 0,
    agentCount: 0,
    sessionCount: 0,
    userAgentCount: 0
  });
  const [memoryLevel, setMemoryLevel] = useState<string>('user');
  const [searchKeyword, setSearchKeyword] = useState<string>('');  // 当前搜索关键词
  const [isSearchResult, setIsSearchResult] = useState<boolean>(false);  // 是否为搜索结果
  const [graphRelations, setGraphRelations] = useState<any[]>([]);  // 图关系数据

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
    setIsSearchResult(false);  // 清除搜索状态
    setSearchKeyword('');  // 清除搜索关键词
    try {
      // 检查必要参数是否提供
      if (level === 'user' && !userId) {
        message.warning('请输入用户名');
        setMemories([]);
        updateStats([]);
        setLoading(false);
        return;
      }
      if (level === 'agent' && !agentId) {
        message.warning('请选择智能体');
        setMemories([]);
        updateStats([]);
        setLoading(false);
        return;
      }
      if (level === 'user_agent' && (!userId || !agentId)) {
        message.warning('请输入用户名并选择智能体');
        setMemories([]);
        updateStats([]);
        setLoading(false);
        return;
      }
      if (level === 'session' && (!userId || !agentId || !runId)) {
        message.warning('请输入用户名、选择智能体并输入会话ID');
        setMemories([]);
        updateStats([]);
        setLoading(false);
        return;
      }

      // 使用Mem0标准API - 通过参数组合来查询不同层级的记忆
      const response = await memoryApi.getMemoriesByLevel(level as any, {
        userId,
        agentId,
        runId,
        limit: 100
      });
      console.log('Memory response:', response);

      if (response.status === 'ok' && response.data) {
        // 确保 data 是数组
        const memoriesData = Array.isArray(response.data) ? response.data : [];
        setMemories(memoriesData);
        updateStats(memoriesData);
        const levelName = level ? getLevelName(level) : '所有';
        if (memoriesData.length > 0) {
          message.success(`加载了 ${memoriesData.length} 条${levelName}记忆`);
        } else {
          message.info('暂无记忆数据');
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
    // 根据Mem0三层架构统计
    const userMemories = memoriesData.filter(m =>
      m.user_id && !m.agent_id && !m.run_id  // 纯用户记忆
    );
    const agentMemories = memoriesData.filter(m =>
      m.agent_id && !m.user_id  // 纯智能体记忆
    );
    const sessionMemories = memoriesData.filter(m =>
      m.run_id  // 有run_id的都算会话记忆
    );
    const userAgentMemories = memoriesData.filter(m =>
      m.user_id && m.agent_id && !m.run_id  // 用户-智能体交互记忆
    );

    setStats({
      userCount: userMemories.length,
      agentCount: agentMemories.length,
      sessionCount: sessionMemories.length,
      userAgentCount: userAgentMemories.length
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
  const handleLevelChange = async (level: string) => {
    setCurrentLevel(level);
    // 清空之前的筛选条件，重新开始
    setSelectedUserId(undefined);
    setSelectedAgentId(undefined);
    setSelectedRunId(undefined);
    // 切换层级后，等待用户输入参数
    setMemories([]);
    updateStats([]);
  };

  /**
   * 添加对话记忆
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
        // 用户记忆：只传user_id（必填）
        response = await memoryApi.addConversationMemory(messages, {
          userId: values.user_id,
          metadata
        });
      } else if (memoryLevel === 'agent') {
        // 智能体记忆：只传agent_id（必填）
        response = await memoryApi.addConversationMemory(messages, {
          agentId: values.agent_id,
          metadata
        });
      } else if (memoryLevel === 'user_agent') {
        // 用户-智能体记忆：传user_id和agent_id（全部必填）
        response = await memoryApi.addConversationMemory(messages, {
          userId: values.user_id,
          agentId: values.agent_id,
          metadata
        });
      } else if (memoryLevel === 'session') {
        // 会话记忆：传user_id + agent_id + run_id（全部必填）
        response = await memoryApi.addConversationMemory(messages, {
          userId: values.user_id,
          agentId: values.agent_id,
          runId: values.run_id,
          metadata
        });
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

      // 构造搜索参数对象
      const searchParams: any = {
        query: values.query,
        user_id: values.user_id || undefined,
        agent_id: values.agent_id || undefined,
        run_id: values.run_id || undefined,
        threshold: values.threshold || undefined,
        limit: values.limit || 20
      };

      // 调用搜索API
      const response = await memoryApi.searchMemories(searchParams);

      if (response.status === 'ok' && response.data) {
        // 处理图记忆格式: {vector_results: [...], graph_relations: [...]}
        let memoriesData: Memory[] = [];
        let relations: any[] = [];

        if (typeof response.data === 'object' && 'vector_results' in response.data) {
          // 新格式：包含向量和图关系
          memoriesData = response.data.vector_results || [];
          relations = response.data.graph_relations || [];
        } else if (typeof response.data === 'object' && 'results' in response.data) {
          // Mem0原生格式
          memoriesData = response.data.results || [];
          relations = response.data.relations || [];
        } else if (Array.isArray(response.data)) {
          // 旧格式：纯数组
          memoriesData = response.data;
        }

        // 如果有记忆类型筛选，在前端过滤
        if (values.memory_type && values.memory_type.length > 0) {
          memoriesData = memoriesData.filter((m: Memory) => {
            // 判断记忆类型
            if (values.memory_type.includes('user') && m.user_id && !m.agent_id && !m.run_id) return true;
            if (values.memory_type.includes('agent') && m.agent_id && !m.user_id) return true;
            if (values.memory_type.includes('user_agent') && m.user_id && m.agent_id && !m.run_id) return true;
            if (values.memory_type.includes('session') && m.run_id) return true;
            return false;
          });
        }

        setMemories(memoriesData);
        setGraphRelations(relations);  // 保存图关系
        updateStats(memoriesData);
        setSearchKeyword(values.query);  // 保存搜索关键词
        setIsSearchResult(true);  // 标记为搜索结果

        // 构建搜索结果提示信息
        let searchInfo = `搜索到 ${memoriesData.length} 条相关记忆`;
        if (relations.length > 0) {
          searchInfo += `，${relations.length} 条图关系`;
        }
        if (values.user_id) searchInfo = `用户 ${values.user_id} 的${memoriesData.length} 条记忆`;
        if (values.agent_id) {
          const agent = agents.find(a => a.agent_id === values.agent_id);
          if (agent) searchInfo += `（智能体：${agent.agent_name}）`;
        }
        if (values.threshold) searchInfo += `（距离≤${values.threshold}）`;

        message.success(searchInfo);
        setSearchModalVisible(false);
        searchForm.resetFields();
      } else {
        setMemories([]);
        updateStats([]);
        setIsSearchResult(false);
        message.error(response.msg || '搜索记忆失败');
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
   * 编辑记忆
   */
  const handleEditMemory = (memory: Memory) => {
    setEditingMemory(memory);
    editForm.setFieldsValue({
      memory: memory.memory
    });
    setEditModalVisible(true);
  };

  /**
   * 保存编辑的记忆
   */
  const handleSaveEdit = async () => {
    try {
      const values = await editForm.validateFields();
      if (!editingMemory) return;

      setLoading(true);

      const response = await memoryApi.updateMemory(editingMemory.id, {
        content: values.memory
      });

      if (response.status === 'ok') {
        message.success('记忆更新成功');
        setEditModalVisible(false);
        setEditingMemory(null);
        editForm.resetFields();
        await loadAllMemories();
      } else {
        message.error('更新失败');
      }
    } catch (error) {
      console.error('更新记忆失败:', error);
      message.error('更新记忆失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 删除单个记忆
   */
  const handleDeleteMemory = async (memoryId: string) => {
    try {
      setLoading(true);
      const response = await memoryApi.deleteMemory(memoryId);
      if (response.status === 'ok') {
        message.success('记忆删除成功');
        await loadAllMemories(); // 重新加载列表
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      console.error('删除记忆失败:', error);
      message.error('删除记忆失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 记忆表格列定义
   */
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => (
        <Tooltip
          title={id}
          overlayStyle={{ maxWidth: 'none' }}
          mouseEnterDelay={0.3}
        >
          <span style={{ fontFamily: 'monospace', fontSize: '12px', cursor: 'pointer' }}>
            {id ? id.substring(0, 8) + '...' : '-'}
          </span>
        </Tooltip>
      ),
    },
    {
      title: 'Hash',
      dataIndex: 'hash',
      key: 'hash',
      width: 100,
      render: (hash: string) => (
        <Tooltip
          title={hash}
          overlayStyle={{ maxWidth: 'none' }}
          mouseEnterDelay={0.3}
        >
          <span style={{ fontFamily: 'monospace', fontSize: '12px', cursor: 'pointer' }}>
            {hash ? hash.substring(0, 8) + '...' : '-'}
          </span>
        </Tooltip>
      ),
    },
    {
      title: '类型',
      dataIndex: ['metadata', 'level'],
      key: 'level',
      width: 130,
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

        return getLevelName(inferredLevel) || '-';
      },
    },
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
      render: (user_id: string) => user_id || '-',
    },
    {
      title: '智能体ID',
      key: 'agent_id',
      width: 150,
      render: (_: any, record: Memory) => {
        // agent_id 可能在根级别或metadata中
        const agent_id = record.agent_id || record.metadata?.agent_id;
        return agent_id || '-';
      },
    },
    {
      title: '会话ID',
      key: 'run_id',
      width: 150,
      render: (_: any, record: Memory) => {
        // run_id 可能在根级别或metadata中
        const run_id = record.run_id || record.metadata?.run_id;
        return run_id || '-';
      },
    },
    {
      title: '距离',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      sorter: (a: Memory, b: Memory) => (a.score || 999) - (b.score || 999),  // 升序，距离小的在前
      render: (score: number) => {
        if (score === undefined || score === null) return '-';
        return score.toFixed(2);
      },
    },
    {
      title: '记忆内容',
      dataIndex: 'memory',
      key: 'memory',
      width: 400,
      render: (text: string) => (
        <Input.TextArea
          value={text || '-'}
          readOnly
          autoSize={{ minRows: 2, maxRows: 4 }}
          style={{
            resize: 'none',
            backgroundColor: 'transparent',
            border: 'none',
            cursor: 'text'
          }}
        />
      ),
    },
    {
      title: '元数据',
      dataIndex: 'metadata',
      key: 'metadata',
      width: 300,
      render: (metadata: Record<string, any>) => {
        if (!metadata || Object.keys(metadata).length === 0) return '-';

        const metaStr = JSON.stringify(metadata, null, 2);
        return (
          <Input.TextArea
            value={metaStr}
            readOnly
            autoSize={{ minRows: 2, maxRows: 4 }}
            style={{
              resize: 'none',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'text',
              fontSize: '12px',
              fontFamily: 'monospace'
            }}
          />
        );
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      sorter: (a: Memory, b: Memory) => {
        const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return timeA - timeB;
      },
      render: (time: string) => time || '-'
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 160,
      sorter: (a: Memory, b: Memory) => {
        const timeA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
        const timeB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
        return timeA - timeB;
      },
      render: (time: string) => time || '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_: any, record: Memory) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              size="small"
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEditMemory(record)}
            />
          </Tooltip>
          <Popconfirm
            title="删除记忆"
            description="确定要删除这条记忆吗？此操作不可恢复。"
            onConfirm={() => handleDeleteMemory(record.id)}
            okText="确定"
            cancelText="取消"
            placement="left"
          >
            <Tooltip title="删除">
              <Button
                size="small"
                type="link"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  useEffect(() => {
    loadAgents();
  }, []);

  // 当用户信息加载后，自动设置用户名并加载该用户的记忆
  useEffect(() => {
    if (user?.username) {
      setSelectedUserId(user.username);
      loadMemoriesByLevel('user', user.username, undefined, undefined);
    }
  }, [user?.username]);

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
              title="用户-智能体"
              value={stats.userAgentCount}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card bordered={false}>
            <Statistic
              title="会话记忆"
              value={stats.sessionCount}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索结果提示 */}
      {isSearchResult && (
        <Alert
          message={`当前显示搜索结果：关键词 "${searchKeyword}"`}
          type="info"
          showIcon
          closable
          onClose={() => {
            setIsSearchResult(false);
            setSearchKeyword('');
            loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, selectedRunId);
          }}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 主要内容区 */}
      <Card bordered={false}>
        {/* 筛选和操作栏 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Space wrap size={16} style={{ width: '100%', justifyContent: 'space-between' }}>
              <Space wrap>
                <Segmented
                  options={[
                    { label: '用户', value: 'user', icon: <UserOutlined /> },
                    { label: '智能体', value: 'agent', icon: <RobotOutlined /> },
                    { label: '用户-智能体', value: 'user_agent', icon: <MessageOutlined /> },
                    { label: '会话', value: 'session', icon: <ClockCircleOutlined /> },
                  ]}
                  value={currentLevel || 'user'}
                  onChange={handleLevelChange}
                />

                {(currentLevel === 'user' || currentLevel === 'user_agent') && (
                  <Input
                    style={{ width: 180 }}
                    placeholder="输入用户名（回车搜索）"
                    value={selectedUserId}
                    onChange={(e) => {
                      setSelectedUserId(e.target.value);
                    }}
                    onPressEnter={(e) => {
                      loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, selectedRunId);
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
                      placeholder="输入用户名（回车搜索）"
                      value={selectedUserId}
                      onChange={(e) => {
                        setSelectedUserId(e.target.value);
                      }}
                      onPressEnter={(e) => {
                        loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, selectedRunId);
                      }}
                      allowClear
                      onClear={() => {
                        setSelectedUserId(undefined);
                        loadMemoriesByLevel(currentLevel, undefined, selectedAgentId, selectedRunId);
                      }}
                      prefix={<UserOutlined />}
                    />
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
                    <Input
                      style={{ width: 200 }}
                      placeholder="输入会话ID（回车搜索）"
                      value={selectedRunId}
                      onChange={(e) => {
                        setSelectedRunId(e.target.value);
                      }}
                      onPressEnter={(e) => {
                        loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, selectedRunId);
                      }}
                      allowClear
                      onClear={() => {
                        setSelectedRunId(undefined);
                        loadMemoriesByLevel(currentLevel, selectedUserId, selectedAgentId, undefined);
                      }}
                      prefix={<ClockCircleOutlined />}
                    />
                  </>
                )}
              </Space>

              <Space>
                <Badge dot={isSearchResult} offset={[-5, 5]}>
                  <Button
                    icon={<SearchOutlined />}
                    onClick={() => setSearchModalVisible(true)}
                  >
                    搜索记忆
                  </Button>
                </Badge>
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

        {/* 图关系展示 */}
        {graphRelations.length > 0 && (
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                <span>图关系 (Neo4j)</span>
                <Badge count={graphRelations.length} style={{ backgroundColor: '#52c41a' }} />
              </Space>
            }
            style={{ marginTop: 16 }}
            size="small"
          >
            <Table
              dataSource={graphRelations}
              rowKey={(record, index) => `relation-${index}`}
              pagination={false}
              size="small"
              columns={[
                {
                  title: '源实体',
                  dataIndex: 'source',
                  key: 'source',
                  render: (text: string) => <Tag color="blue">{text}</Tag>
                },
                {
                  title: '关系',
                  dataIndex: 'relationship',
                  key: 'relationship',
                  render: (text: string) => <Tag color="green">{text}</Tag>
                },
                {
                  title: '目标实体',
                  dataIndex: 'destination',
                  key: 'destination',
                  render: (text: string) => <Tag color="orange">{text}</Tag>
                }
              ]}
            />
          </Card>
        )}
      </Card>

      {/* 编辑记忆模态框 */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            编辑记忆
          </Space>
        }
        open={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingMemory(null);
          editForm.resetFields();
        }}
        confirmLoading={loading}
        width={700}
      >
        <Form
          form={editForm}
          layout="vertical"
        >
          <Form.Item
            name="memory"
            label="记忆内容"
            rules={[{ required: true, message: '请输入记忆内容' }]}
          >
            <TextArea
              rows={8}
              placeholder="输入记忆内容..."
            />
          </Form.Item>

          {editingMemory?.metadata && (
            <div style={{ marginTop: 16 }}>
              <Text strong>元数据（不可修改）：</Text>
              <pre style={{
                backgroundColor: '#f5f5f5',
                padding: '12px',
                borderRadius: '4px',
                marginTop: '8px',
                maxHeight: '200px',
                overflow: 'auto'
              }}>
                {JSON.stringify(editingMemory.metadata, null, 2)}
              </pre>
            </div>
          )}
        </Form>
      </Modal>

      {/* 测试添加对话记忆模态框 */}
      <Modal
        title={
          <Space>
            <ExperimentOutlined />
            添加对话记忆
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
            initialValue="user"
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

          {/* 根据记忆层级显示不同的选择器 */}
          {memoryLevel === 'user' && (
            <Form.Item
              name="user_id"
              label="用户名"
              rules={[{ required: true, message: '请输入用户名' }]}
              initialValue={user?.username}
            >
              <Input
                placeholder="输入用户名"
                prefix={<UserOutlined />}
              />
            </Form.Item>
          )}

          {memoryLevel === 'user_agent' && (
            <>
              <Form.Item
                name="user_id"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
                initialValue={user?.username}
              >
                <Input
                  placeholder="输入用户名"
                  prefix={<UserOutlined />}
                />
              </Form.Item>
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
            </>
          )}

          {memoryLevel === 'agent' && (
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

          {memoryLevel === 'session' && (
            <>
              <Form.Item
                name="user_id"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
                initialValue={user?.username}
              >
                <Input
                  placeholder="输入用户名"
                  prefix={<UserOutlined />}
                />
              </Form.Item>
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
              <Form.Item
                name="run_id"
                label="会话ID"
                rules={[{ required: true, message: '请输入会话ID' }]}
              >
                <Input
                  placeholder="输入会话ID"
                  prefix={<ClockCircleOutlined />}
                />
              </Form.Item>
            </>
          )}

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
        width={700}
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

          <Form.Item
            name="run_id"
            label="会话ID（可选）"
            tooltip="输入特定会话ID，精确搜索会话记忆"
          >
            <Input
              placeholder="输入会话ID"
              prefix={<ClockCircleOutlined />}
              allowClear
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="threshold"
                label="距离阈值"
                tooltip="保留距离≤阈值的记忆。余弦距离0-2（越小越相似），例如0.3表示只返回很相似的记忆"
                initialValue={undefined}
              >
                <InputNumber
                  min={0}
                  max={2}
                  step={0.1}
                  style={{ width: '100%' }}
                  placeholder="0.5"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="limit"
                label="返回数量"
                tooltip="最多返回多少条记忆"
                initialValue={20}
              >
                <InputNumber
                  min={1}
                  max={200}
                  step={10}
                  style={{ width: '100%' }}
                  placeholder="20"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="memory_type"
            label="记忆类型筛选"
            tooltip="选择要搜索的记忆类型"
          >
            <Select
              mode="multiple"
              placeholder="选择记忆类型（留空搜索所有类型）"
              allowClear
            >
              <Option value="user">用户记忆</Option>
              <Option value="agent">智能体记忆</Option>
              <Option value="user_agent">用户-智能体记忆</Option>
              <Option value="session">会话记忆</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MemoryManagement;