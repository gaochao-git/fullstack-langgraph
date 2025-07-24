import React, { useState, useEffect } from 'react';
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
  ExperimentOutlined
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
    models: ['qwen3:4b', 'qwen3:8b', 'qwen3:0.6b', 'deepseek-r1:1.5b', 'llama2', 'llama3', 'codellama', 'mistral']
  },
  deepseek: {
    name: 'DeepSeek',
    icon: '🧠',
    color: '#1890ff',
    defaultEndpoint: 'https://api.deepseek.com',
    models: ['deepseek-chat', 'deepseek-coder']
  },
  qwen: {
    name: 'Qwen',
    icon: '🤖',
    color: '#722ed1',
    defaultEndpoint: 'https://dashscope.aliyuncs.com',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max']
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

const mockModels: ModelConfig[] = [
  {
    id: "ollama-1",
    name: "本地Llama3",
    provider: "ollama",
    model: "llama3",
    endpoint: "http://localhost:11434",
    description: "本地部署的Llama3模型",
    status: "active",
    createdAt: "2024-01-15 10:30:00",
    updatedAt: "2024-01-15 10:30:00"
  },
  {
    id: "deepseek-1", 
    name: "DeepSeek Chat",
    provider: "deepseek",
    model: "deepseek-chat",
    endpoint: "https://api.deepseek.com",
    apiKey: "sk-***",
    description: "DeepSeek聊天模型",
    status: "active",
    createdAt: "2024-01-15 11:00:00",
    updatedAt: "2024-01-15 11:00:00"
  }
];

const ModelsManagement = () => {
  const [models, setModels] = useState<ModelConfig[]>(mockModels);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);
  const [formTestStatus, setFormTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [form] = Form.useForm();

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
    form.resetFields();
    setModalVisible(true);
  };

  // 编辑模型
  const handleEditModel = (model: ModelConfig) => {
    setEditingModel(model);
    setFormTestStatus('idle');
    form.setFieldsValue(model);
    setModalVisible(true);
  };

  // 删除模型
  const handleDeleteModel = (id: string) => {
    setModels(models.filter(m => m.id !== id));
    message.success('模型删除成功');
  };

  // 测试模型连接
  const handleTestModel = async (model: ModelConfig) => {
    message.loading('正在测试连接...', 0);
    // 模拟测试
    setTimeout(() => {
      message.destroy();
      message.success('连接测试成功');
    }, 2000);
  };

  // 表单中的测试连接
  const handleFormTestConnection = async () => {
    try {
      const values = await form.validateFields(['endpoint', 'provider', 'model', 'apiKey']);
      setFormTestStatus('testing');
      
      // 模拟测试连接
      setTimeout(() => {
        const success = Math.random() > 0.3; // 70% 成功率
        if (success) {
          setFormTestStatus('success');
          message.success('连接测试成功');
        } else {
          setFormTestStatus('error');
          message.error('连接测试失败，请检查配置');
        }
        
        // 3秒后重置状态
        setTimeout(() => {
          setFormTestStatus('idle');
        }, 3000);
      }, 2000);
    } catch (error) {
      message.error('请先完善连接配置信息');
    }
  };

  // 保存模型
  const handleSaveModel = async (values: any) => {
    const now = new Date().toLocaleString();
    
    if (editingModel) {
      // 更新
      const updatedModel = {
        ...editingModel,
        ...values,
        updatedAt: now
      };
      setModels(models.map(m => m.id === editingModel.id ? updatedModel : m));
      message.success('模型更新成功');
    } else {
      // 新增
      const newModel: ModelConfig = {
        id: `model-${Date.now()}`,
        ...values,
        status: 'inactive',
        createdAt: now,
        updatedAt: now
      };
      setModels([...models, newModel]);
      message.success('模型添加成功');
    }
    
    setModalVisible(false);
    form.resetFields();
    setFormTestStatus('idle');
  };

  // 表格列定义
  const columns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ModelConfig) => (
        <Space>
          <span style={{ fontSize: '18px' }}>{MODEL_PROVIDERS[record.provider].icon}</span>
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {MODEL_PROVIDERS[record.provider].name} - {record.model}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: '服务商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: keyof typeof MODEL_PROVIDERS) => (
        <Tag color={MODEL_PROVIDERS[provider].color}>
          {MODEL_PROVIDERS[provider].name}
        </Tag>
      ),
    },
    {
      title: '端点地址',
      dataIndex: 'endpoint',
      key: 'endpoint',
      render: (text: string) => (
        <code style={{ fontSize: '12px', padding: '2px 4px', background: '#f5f5f5', borderRadius: '2px' }}>
          {text}
        </code>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={getStatusColor(status) as any} text={getStatusText(status)} />
      ),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      render: (text: string) => (
        <Text type="secondary" style={{ fontSize: '12px' }}>{text}</Text>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: ModelConfig) => (
        <Space>
          <Tooltip title="测试连接">
            <Button 
              size="small" 
              icon={<ExperimentOutlined />} 
              onClick={() => handleTestModel(record)}
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
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>模型管理</Title>
          <Text type="secondary">配置和管理AI模型服务</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAddModel}>
          添加模型
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={models}
          rowKey="id"
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个模型`
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
        }}
        footer={null}
        width={600}
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
                  endpoint: provider.defaultEndpoint,
                  model: provider.models[0]
                });
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

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.provider !== currentValues.provider
            }
          >
            {({ getFieldValue }) => {
              const provider = getFieldValue('provider') as keyof typeof MODEL_PROVIDERS;
              const providerConfig = MODEL_PROVIDERS[provider];
              
              return (
                <Form.Item
                  label="模型"
                  name="model"
                  rules={[{ required: true, message: '请选择模型' }]}
                >
                  <Select>
                    {providerConfig?.models.map(model => (
                      <Option key={model} value={model}>{model}</Option>
                    ))}
                  </Select>
                </Form.Item>
              );
            }}
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