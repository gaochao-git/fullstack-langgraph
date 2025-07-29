import React, { useState, useEffect } from 'react';
import { useTheme } from '../../../contexts/ThemeContext';
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Avatar, 
  Button, 
  Space, 
  Statistic, 
  Modal, 
  Form, 
  Input, 
  Select, 
  message,
  Table,
  Badge,
  Popconfirm,
  Tooltip
} from "antd";
import { 
  ApiOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  EyeOutlined,
  ExperimentOutlined,
  LinkOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined
} from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

// 模型类型配置
const MODEL_PROVIDERS = {
  ollama: {
    name: 'Ollama',
    icon: '🦙',
    color: '#52c41a',
    defaultEndpoint: 'http://localhost:11434',
    autoDiscover: true, // 支持自动发现
    apiFormat: 'ollama'
  },
  'openai-compatible': {
    name: 'OpenAI兼容',
    icon: '🔧',
    color: '#1890ff',
    defaultEndpoint: 'https://api.openai.com/v1',
    autoDiscover: false, // 手动输入
    apiFormat: 'openai'
  },
  deepseek: {
    name: 'DeepSeek',
    icon: '🧠',
    color: '#1890ff',
    defaultEndpoint: 'https://api.deepseek.com/v1',
    autoDiscover: false, // 手动输入
    apiFormat: 'openai'
  },
  qwen: {
    name: 'Qwen',
    icon: '🤖',
    color: '#722ed1',
    defaultEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    autoDiscover: false, // 手动输入
    apiFormat: 'openai'
  }
};

interface ModelConfig {
  id: string;
  name: string;
  provider: keyof typeof MODEL_PROVIDERS;
  model: string;
  endpoint: string;
  apiKey?: string;
  description?: string;
  status: 'active' | 'inactive' | 'testing';
  createdAt: string;
  updatedAt: string;
}

// API配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API调用函数
const fetchModels = async (): Promise<ModelConfig[]> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-models`);
  const data = await response.json();
  if (data.code === 200) {
    return data.data.items.map((item: any) => ({
      id: item.id,
      name: item.name,
      provider: item.provider,
      model: item.model,
      endpoint: item.endpoint,
      apiKey: item.apiKey,
      description: item.description,
      status: item.status,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt
    }));
  }
  throw new Error(data.message || '获取模型列表失败');
};

const createModel = async (modelData: Partial<ModelConfig>): Promise<ModelConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-models`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_name: modelData.name,
      model_provider: modelData.provider,
      model_type: modelData.model,
      endpoint_url: modelData.endpoint,
      api_key_value: modelData.apiKey,
      model_description: modelData.description
    })
  });
  const data = await response.json();
  if (data.code === 200) {
    const item = data.data;
    return {
      id: item.id,
      name: item.name,
      provider: item.provider,
      model: item.model,
      endpoint: item.endpoint,
      apiKey: item.apiKey,
      description: item.description,
      status: item.status,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt
    };
  }
  throw new Error(data.message || '创建模型失败');
};

const updateModel = async (modelId: string, modelData: Partial<ModelConfig>): Promise<ModelConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-models/${modelId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_name: modelData.name,
      model_provider: modelData.provider,
      model_type: modelData.model,
      endpoint_url: modelData.endpoint,
      api_key_value: modelData.apiKey,
      model_description: modelData.description,
      model_status: modelData.status
    })
  });
  const data = await response.json();
  if (data.code === 200) {
    const item = data.data;
    return {
      id: item.id,
      name: item.name,
      provider: item.provider,
      model: item.model,
      endpoint: item.endpoint,
      apiKey: item.apiKey,
      description: item.description,
      status: item.status,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt
    };
  }
  throw new Error(data.message || '更新模型失败');
};

const deleteModel = async (modelId: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-models/${modelId}`, {
    method: 'DELETE'
  });
  const data = await response.json();
  if (data.code !== 200) {
    throw new Error(data.message || '删除模型失败');
  }
};

const testModelConnection = async (modelData: any): Promise<any> => {
  console.log('测试连接参数:', {
    provider: modelData.provider,
    model: modelData.model,
    endpoint: modelData.endpoint,
    hasApiKey: !!modelData.apiKey,
    apiKeyLength: modelData.apiKey?.length || 0
  });
  
  const response = await fetch(`${API_BASE_URL}/api/v1/ai-models/test-connection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model_provider: modelData.provider,
      model_type: modelData.model,
      endpoint_url: modelData.endpoint,
      api_key_value: modelData.apiKey
    })
  });
  const data = await response.json();
  return data.data;
};

// 发现Ollama模型
const discoverOllamaModels = async (endpoint: string): Promise<string[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/ai-models/discover-ollama`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        endpoint_url: endpoint
      })
    });
    const data = await response.json();
    if (data.code === 200) {
      return data.data.models;
    }
    throw new Error(data.message || '发现模型失败');
  } catch (error) {
    console.error('发现Ollama模型失败:', error);
    throw error;
  }
};

const ModelsManagement = () => {
  const { isDark } = useTheme();
  const [models, setModels] = useState<ModelConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);
  const [formTestStatus, setFormTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [discoveredModels, setDiscoveredModels] = useState<string[]>([]);
  const [discoveringModels, setDiscoveringModels] = useState(false);
  const [testingModels, setTestingModels] = useState<Set<string>>(new Set());
  const [testResults, setTestResults] = useState<Map<string, 'success' | 'error'>>(new Map());
  const [form] = Form.useForm();

  // 加载模型列表
  const loadModels = async () => {
    setLoading(true);
    try {
      const modelList = await fetchModels();
      setModels(modelList);
    } catch (error) {
      console.error('加载模型列表失败:', error);
      // 更友好的错误提示
      if (error instanceof TypeError && error.message.includes('fetch')) {
        message.error('无法连接到后端服务，请检查网络连接或服务是否启动');
      } else {
        message.error(`加载模型列表失败: ${error instanceof Error ? error.message : '未知错误'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取模型列表
  useEffect(() => {
    loadModels();
  }, []);

  // 发现Ollama模型
  const handleDiscoverModels = async () => {
    try {
      const endpoint = form.getFieldValue('endpoint');
      if (!endpoint) {
        message.error('请先输入Ollama端点地址');
        return;
      }

      setDiscoveringModels(true);
      const models = await discoverOllamaModels(endpoint);
      setDiscoveredModels(models);
      
      if (models.length > 0) {
        message.success(`发现 ${models.length} 个模型`);
      } else {
        message.warning('未发现任何模型，请检查Ollama服务是否运行');
      }
    } catch (error: any) {
      console.error('发现模型失败:', error);
      message.error(error.message || '发现模型失败，请检查端点地址和网络连接');
    } finally {
      setDiscoveringModels(false);
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'testing': return 'processing';
      default: return 'default';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '运行中';
      case 'inactive': return '已停用';
      case 'testing': return '测试中';
      default: return '未知';
    }
  };

  // 添加模型
  const handleAddModel = () => {
    setEditingModel(null);
    setFormTestStatus('idle');
    setDiscoveredModels([]);
    form.resetFields();
    setModalVisible(true);
  };

  // 编辑模型
  const handleEditModel = (model: ModelConfig) => {
    setEditingModel(model);
    setFormTestStatus('idle');
    setDiscoveredModels([]);
    form.setFieldsValue(model);
    setModalVisible(true);
  };

  // 删除模型
  const handleDeleteModel = async (id: string) => {
    try {
      await deleteModel(id);
      setModels(models.filter(m => m.id !== id));
      message.success('模型删除成功');
    } catch (error) {
      console.error('删除模型失败:', error);
      message.error('删除模型失败');
    }
  };

  // 测试模型连接
  const handleTestModel = async (model: ModelConfig) => {
    try {
      setTestingModels(prev => new Set(prev).add(model.id));
      // 清除之前的测试结果
      setTestResults(prev => {
        const newMap = new Map(prev);
        newMap.delete(model.id);
        return newMap;
      });
      
      const result = await testModelConnection(model);
      
      if (result.status === 'success') {
        setTestResults(prev => new Map(prev).set(model.id, 'success'));
        message.success(`连接测试成功 (延迟: ${result.latency_ms}ms)`);
      } else {
        setTestResults(prev => new Map(prev).set(model.id, 'error'));
        message.error(`连接测试失败: ${result.message}`);
      }
    } catch (error) {
      setTestResults(prev => new Map(prev).set(model.id, 'error'));
      console.error('测试连接失败:', error);
      message.error('测试连接失败');
    } finally {
      setTestingModels(prev => {
        const newSet = new Set(prev);
        newSet.delete(model.id);
        return newSet;
      });
      
      // 3秒后清除测试结果状态
      setTimeout(() => {
        setTestResults(prev => {
          const newMap = new Map(prev);
          newMap.delete(model.id);
          return newMap;
        });
      }, 3000);
    }
  };

  // 切换模型状态
  const handleToggleModelStatus = async (model: ModelConfig) => {
    try {
      const newStatus = model.status === 'active' ? 'inactive' : 'active';
      const updatedModel = await updateModel(model.id, { status: newStatus });
      setModels(models.map(m => m.id === model.id ? updatedModel : m));
      message.success(`模型已${newStatus === 'active' ? '启用' : '停用'}`);
    } catch (error) {
      console.error('切换模型状态失败:', error);
      message.error('操作失败');
    }
  };

  // 表单中的测试连接
  const handleFormTestConnection = async () => {
    try {
      const values = await form.validateFields(['endpoint', 'provider', 'model']);
      // 获取完整的表单值包括apiKey
      const allValues = form.getFieldsValue();
      setFormTestStatus('testing');
      
      const result = await testModelConnection({
        provider: allValues.provider,
        model: allValues.model,
        endpoint: allValues.endpoint,
        apiKey: allValues.apiKey
      });
      
      if (result.status === 'success') {
        setFormTestStatus('success');
        message.success(`连接测试成功 (延迟: ${result.latency_ms}ms)`);
      } else {
        setFormTestStatus('error');
        message.error(`连接测试失败: ${result.message}`);
      }
      
      // 3秒后重置状态
      setTimeout(() => {
        setFormTestStatus('idle');
      }, 3000);
      
    } catch (error) {
      setFormTestStatus('error');
      console.error('测试连接失败:', error);
      message.error('请先完善连接配置信息');
      
      setTimeout(() => {
        setFormTestStatus('idle');
      }, 3000);
    }
  };

  // 保存模型
  const handleSaveModel = async (values: any) => {
    try {
      if (editingModel) {
        // 更新
        const updatedModel = await updateModel(editingModel.id, values);
        setModels(models.map(m => m.id === editingModel.id ? updatedModel : m));
        message.success('模型更新成功');
      } else {
        // 新增
        const newModel = await createModel(values);
        setModels([...models, newModel]);
        message.success('模型添加成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      setFormTestStatus('idle');
      setDiscoveredModels([]);
    } catch (error) {
      console.error('保存模型失败:', error);
      message.error('保存模型失败');
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text: string) => (
        <div style={{ fontWeight: 500 }}>
          {text}
        </div>
      ),
    },
    {
      title: '服务商',
      dataIndex: 'provider',
      key: 'provider',
      width: 120,
      render: (provider: keyof typeof MODEL_PROVIDERS) => (
        <Space>
          <span style={{ fontSize: '16px' }}>{MODEL_PROVIDERS[provider].icon}</span>
          <Tag color={MODEL_PROVIDERS[provider].color}>
            {MODEL_PROVIDERS[provider].name}
          </Tag>
        </Space>
      ),
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      width: 150,
      render: (text: string) => (
        <Text style={{ fontSize: '13px', fontFamily: 'monospace' }}>{text}</Text>
      ),
    },
    {
      title: '端点地址',
      dataIndex: 'endpoint',
      key: 'endpoint',
      width: 250,
      render: (text: string) => (
        <code style={{ 
          fontSize: '11px', 
          padding: '2px 4px', 
          background: isDark ? '#374151' : '#f5f5f5',
          color: isDark ? '#e5e7eb' : '#374151',
          borderRadius: '2px',
          wordBreak: 'break-all'
        }}>
          {text}
        </code>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Badge status={getStatusColor(status) as any} text={getStatusText(status)} />
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      width: 150,
      render: (text: string) => (
        <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      fixed: window.innerWidth >= 768 ? 'right' as const : undefined,
      render: (_, record: ModelConfig) => (
        <Space size={window.innerWidth < 768 ? 4 : 8}>
          <Tooltip title="测试连接">
            <Button 
              size="small" 
              icon={<LinkOutlined />} 
              loading={testingModels.has(record.id)}
              onClick={() => handleTestModel(record)}
              type={testResults.get(record.id) === 'success' ? 'primary' : 
                    testResults.get(record.id) === 'error' ? 'default' : 'default'}
              danger={testResults.get(record.id) === 'error'}
              style={{
                borderColor: testResults.get(record.id) === 'success' ? '#52c41a' : undefined,
                backgroundColor: testResults.get(record.id) === 'success' ? '#f6ffed' : undefined,
                color: testResults.get(record.id) === 'success' ? '#52c41a' : undefined
              }}
            />
          </Tooltip>
          <Tooltip title={record.status === 'active' ? '停用' : '启用'}>
            <Button 
              size="small" 
              icon={record.status === 'active' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleModelStatus(record)}
              type={record.status === 'active' ? 'default' : 'primary'}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              size="small" 
              icon={<EditOutlined />} 
              onClick={() => handleEditModel(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除这个模型配置吗？"
            onConfirm={() => handleDeleteModel(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ 
        marginBottom: 24, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: window.innerWidth < 768 ? 'flex-start' : 'center',
        flexDirection: window.innerWidth < 768 ? 'column' : 'row',
        gap: window.innerWidth < 768 ? 12 : 0
      }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>模型管理</Title>
          <Text type="secondary">配置和管理AI模型服务</Text>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleAddModel}
          style={window.innerWidth < 768 ? { alignSelf: 'flex-end' } : {}}
        >
          添加模型
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={models}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: models.length === 0 && !loading ? 
              '暂无模型数据，请检查后端服务连接状态' : 
              '暂无数据'
          }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个模型`,
            simple: window.innerWidth < 768
          }}
        />
      </Card>

      {/* 模型配置模态框 */}
      <Modal
        title={editingModel ? '编辑模型' : '添加模型'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setFormTestStatus('idle');
          setDiscoveredModels([]);
        }}
        footer={null}
        width={window.innerWidth < 768 ? '95vw' : 600}
        style={window.innerWidth < 768 ? { top: 20 } : {}}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveModel}
          initialValues={{
            provider: 'ollama',
            endpoint: MODEL_PROVIDERS.ollama.defaultEndpoint
          }}
        >
          <Form.Item
            label="模型名称"
            name="name"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如：本地Llama3" />
          </Form.Item>

          <Form.Item
            label="服务商"
            name="provider"
            rules={[{ required: true, message: '请选择服务商' }]}
          >
            <Select
              onChange={(value) => {
                const provider = MODEL_PROVIDERS[value as keyof typeof MODEL_PROVIDERS];
                form.setFieldsValue({
                  endpoint: provider.defaultEndpoint
                });
                // 清空已发现的模型和当前选择的模型
                setDiscoveredModels([]);
                form.setFieldsValue({ model: undefined });
              }}
            >
              {Object.entries(MODEL_PROVIDERS).map(([key, provider]) => (
                <Option key={key} value={key}>
                  <Space>
                    <span>{provider.icon}</span>
                    {provider.name}
                  </Space>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="端点地址" required>
            <Row gutter={8} align="middle" wrap={false}>
              <Col flex="auto">
                <Form.Item
                  name="endpoint"
                  noStyle
                  rules={[{ required: true, message: '请输入端点地址' }]}
                >
                  <Input placeholder="https://api.example.com" />
                </Form.Item>
              </Col>
              <Col>
                <Button 
                  type="primary"
                  loading={formTestStatus === 'testing'}
                  onClick={handleFormTestConnection}
                  icon={<ExperimentOutlined />}
                  style={{
                    borderColor: formTestStatus === 'success' ? '#52c41a' : 
                                formTestStatus === 'error' ? '#ff4d4f' : undefined,
                    backgroundColor: formTestStatus === 'success' ? '#f6ffed' : 
                                   formTestStatus === 'error' ? '#fff2f0' : undefined,
                    color: formTestStatus === 'success' ? '#52c41a' : 
                          formTestStatus === 'error' ? '#ff4d4f' : undefined
                  }}
                >
                  {formTestStatus === 'testing' ? '测试中' : 
                   formTestStatus === 'success' ? '测试成功' :
                   formTestStatus === 'error' ? '测试失败' : '测试连接'}
                </Button>
              </Col>
            </Row>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.provider !== currentValues.provider || currentValues.endpoint !== prevValues.endpoint
            }
          >
            {({ getFieldValue }) => {
              const provider = getFieldValue('provider') as keyof typeof MODEL_PROVIDERS;
              const providerConfig = MODEL_PROVIDERS[provider];
              const isAutoDiscover = providerConfig?.autoDiscover;
              
              if (isAutoDiscover) {
                // Ollama: 自动发现模式
                return (
                  <Form.Item label="模型" required>
                    <Row gutter={8} align="middle" wrap={false}>
                      <Col flex="auto">
                        <Form.Item
                          name="model"
                          noStyle
                          rules={[{ required: true, message: '请选择模型' }]}
                        >
                          <Select placeholder="点击发现按钮自动获取模型">
                            {/* Ollama发现的模型 */}
                            {discoveredModels.length > 0 && (
                              <>
                                {discoveredModels.map(model => (
                                  <Option key={`discovered-${model}`} value={model}>
                                    🔍 {model}
                                  </Option>
                                ))}
                              </>
                            )}
                            {/* 没有发现模型时的提示 */}
                            {discoveredModels.length === 0 && (
                              <Option disabled value="">
                                请点击"发现模型"按钮获取可用模型
                              </Option>
                            )}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col>
                        <Tooltip title="自动发现Ollama服务器上的模型">
                          <Button 
                            icon={<EyeOutlined />}
                            loading={discoveringModels}
                            onClick={handleDiscoverModels}
                          >
                            {discoveringModels ? '发现中' : '发现模型'}
                          </Button>
                        </Tooltip>
                      </Col>
                    </Row>
                  </Form.Item>
                );
              } else {
                // DeepSeek/Qwen: 手动输入模式
                return (
                  <Form.Item
                    label="模型"
                    name="model"
                    rules={[{ required: true, message: '请输入模型名称' }]}
                  >
                    <Input 
                      placeholder={
                        provider === 'openai-compatible' 
                          ? "例如：gpt-4, gpt-3.5-turbo, claude-3-sonnet" 
                          : provider === 'deepseek'
                          ? "例如：deepseek-chat, deepseek-coder, deepseek-r1"
                          : provider === 'qwen'
                          ? "例如：qwen-turbo, qwen-plus, qwen-max, qwen2.5-72b-instruct"
                          : "请输入模型名称"
                      }
                    />
                  </Form.Item>
                );
              }
            }}
          </Form.Item>

          <Form.Item
            label="API密钥"
            name="apiKey"
          >
            <Input.Password placeholder="可选，某些服务商需要" />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <Input.TextArea rows={3} placeholder="模型的描述信息" />
          </Form.Item>

          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'end', gap: 8 }}>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingModel ? '更新' : '添加'}
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ModelsManagement; 