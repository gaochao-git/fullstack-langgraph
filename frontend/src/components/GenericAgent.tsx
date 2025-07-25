import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Select, 
  Switch, 
  Form, 
  Divider,
  Tag,
  message,
  Spin,
  Avatar,
  Modal,
  Slider,
  InputNumber,
  Collapse
} from "antd";
import { 
  SendOutlined, 
  SettingOutlined, 
  RobotOutlined,
  ToolOutlined,
  BrainCircuitOutlined,
  MessageOutlined,
  ClearOutlined,
  SaveOutlined,
  LoadingOutlined
} from "@ant-design/icons";
import { useStream } from "@langchain/langgraph-sdk/react";

const { TextArea } = Input;
const { Text, Title } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

interface GenericAgentProps {
  agentId: string;
  initialConfig?: AgentConfig;
  onConfigChange?: (config: AgentConfig) => void;
}

interface AgentConfig {
  agent_id: string;
  agent_name: string;
  agent_description: string;
  model_provider: string;
  model_name: string;
  model_temperature: number;
  model_max_tokens: number;
  workflow_type: string;
  max_iterations: number;
  enable_memory: boolean;
  enable_streaming: boolean;
  enabled_tool_categories: string[];
  personality_traits: string[];
  role_description: string;
  max_tool_calls_per_turn: number;
  timeout_seconds: number;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  id: string;
}

const TOOL_CATEGORIES = [
  { value: 'search', label: '搜索工具', icon: '🔍' },
  { value: 'calculation', label: '计算工具', icon: '🧮' },
  { value: 'text_processing', label: '文本处理', icon: '📝' },
  { value: 'time', label: '时间工具', icon: '⏰' },
  { value: 'data_processing', label: '数据处理', icon: '📊' },
  { value: 'system', label: '系统工具', icon: '💻' }
];

const PERSONALITY_TRAITS = [
  { value: 'helpful', label: '乐于助人' },
  { value: 'professional', label: '专业严谨' },
  { value: 'friendly', label: '友好亲切' },
  { value: 'patient', label: '耐心细致' },
  { value: 'creative', label: '富有创意' },
  { value: 'analytical', label: '逻辑清晰' },
  { value: 'empathetic', label: '善解人意' },
  { value: 'accurate', label: '追求精确' },
  { value: 'efficient', label: '注重效率' }
];

const MODEL_PROVIDERS = [
  { value: 'deepseek', label: 'DeepSeek', models: ['deepseek-chat', 'deepseek-coder'] },
  { value: 'openai', label: 'OpenAI', models: ['gpt-4', 'gpt-3.5-turbo'] },
  { value: 'ollama', label: 'Ollama', models: ['llama2', 'llama3', 'mistral'] },
  { value: 'qwen', label: 'Qwen', models: ['qwen-turbo', 'qwen-plus', 'qwen-max'] }
];

const GenericAgent: React.FC<GenericAgentProps> = ({
  agentId,
  initialConfig,
  onConfigChange
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConfigModalVisible, setIsConfigModalVisible] = useState(false);
  const [agentConfig, setAgentConfig] = useState<AgentConfig>(
    initialConfig || {
      agent_id: agentId,
      agent_name: '通用智能体',
      agent_description: '可配置的通用智能体',
      model_provider: 'deepseek',
      model_name: 'deepseek-chat',
      model_temperature: 0.1,
      model_max_tokens: 4000,
      workflow_type: 'react',
      max_iterations: 10,
      enable_memory: true,
      enable_streaming: true,
      enabled_tool_categories: ['search', 'calculation', 'text_processing'],
      personality_traits: ['helpful', 'professional'],
      role_description: '你是一个有用的AI助手，能够使用各种工具来帮助用户解决问题。',
      max_tool_calls_per_turn: 5,
      timeout_seconds: 300
    }
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [form] = Form.useForm();

  // 使用LangGraph SDK的流式处理
  const { stream, isStreaming } = useStream({
    apiUrl: import.meta.env.VITE_API_BASE_URL,
    assistantId: agentId,
    config: {
      configurable: agentConfig
    }
  });

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    form.setFieldsValue(agentConfig);
  }, [agentConfig, form]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
      id: Date.now().toString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    try {
      // 创建助手消息占位符
      const assistantMessage: Message = {
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        id: (Date.now() + 1).toString()
      };
      
      setMessages(prev => [...prev, assistantMessage]);

      // 启动流式处理
      const streamResult = await stream({
        messages: [{ role: 'user', content: userMessage.content }]
      });

      // 处理流式响应
      for await (const chunk of streamResult) {
        if (chunk.data && chunk.data.messages) {
          const lastMessage = chunk.data.messages[chunk.data.messages.length - 1];
          if (lastMessage.role === 'assistant') {
            setMessages(prev => 
              prev.map(msg => 
                msg.id === assistantMessage.id 
                  ? { ...msg, content: lastMessage.content }
                  : msg
              )
            );
          }
        }
      }

    } catch (error) {
      console.error('发送消息失败:', error);
      message.error('发送消息失败，请重试');
      
      // 移除失败的助手消息
      setMessages(prev => prev.filter(msg => msg.id !== (Date.now() + 1).toString()));
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleConfigSave = async () => {
    try {
      const values = await form.validateFields();
      const newConfig = { ...agentConfig, ...values };
      setAgentConfig(newConfig);
      setIsConfigModalVisible(false);
      
      if (onConfigChange) {
        onConfigChange(newConfig);
      }
      
      message.success('配置已保存');
    } catch (error) {
      console.error('保存配置失败:', error);
      message.error('配置验证失败');
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
          <div>{message.content}</div>
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
            style={{ 
              backgroundColor: '#52c41a', 
              marginLeft: 8,
              flexShrink: 0
            }} 
          >
            U
          </Avatar>
        )}
      </div>
    );
  };

  const getAvailableModels = () => {
    const provider = form.getFieldValue('model_provider') || agentConfig.model_provider;
    const providerInfo = MODEL_PROVIDERS.find(p => p.value === provider);
    return providerInfo?.models || [];
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部工具栏 */}
      <Card 
        size="small" 
        style={{ marginBottom: 16, flexShrink: 0 }}
        bodyStyle={{ padding: '12px 16px' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <RobotOutlined style={{ fontSize: 20, color: '#1890ff' }} />
            <div>
              <Title level={5} style={{ margin: 0 }}>{agentConfig.agent_name}</Title>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {agentConfig.agent_description}
              </Text>
            </div>
          </div>
          
          <Space>
            <Button
              size="small"
              icon={<ClearOutlined />}
              onClick={clearMessages}
              title="清空对话"
            >
              清空
            </Button>
            <Button
              size="small"
              icon={<SettingOutlined />}
              onClick={() => setIsConfigModalVisible(true)}
              title="配置Agent"
            >
              配置
            </Button>
          </Space>
        </div>
        
        {/* Agent状态显示 */}
        <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Tag color="blue">{agentConfig.model_provider}</Tag>
          <Tag color="green">{agentConfig.workflow_type}</Tag>
          {agentConfig.enabled_tool_categories.map(category => {
            const categoryInfo = TOOL_CATEGORIES.find(c => c.value === category);
            return (
              <Tag key={category} color="orange">
                {categoryInfo?.icon} {categoryInfo?.label}
              </Tag>
            );
          })}
        </div>
      </Card>

      {/* 对话区域 */}
      <Card 
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ padding: 16, flex: 1, display: 'flex', flexDirection: 'column' }}
      >
        <div 
          style={{ 
            flex: 1, 
            overflowY: 'auto', 
            marginBottom: 16,
            paddingRight: 8
          }}
        >
          {messages.length === 0 ? (
            <div 
              style={{ 
                textAlign: 'center', 
                color: '#999', 
                marginTop: 40,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 16
              }}
            >
              <RobotOutlined style={{ fontSize: 48, opacity: 0.3 }} />
              <div>
                <div>你好！我是 {agentConfig.agent_name}</div>
                <div style={{ fontSize: 14, marginTop: 4 }}>
                  {agentConfig.role_description}
                </div>
              </div>
            </div>
          ) : (
            messages.map(renderMessage)
          )}
          
          {isStreaming && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16 }}>
              <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff' }} />
              <Spin indicator={<LoadingOutlined style={{ fontSize: 14 }} spin />} />
              <Text type="secondary">思考中...</Text>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="输入消息..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ flex: 1 }}
            disabled={isStreaming}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isStreaming}
            loading={isStreaming}
          >
            发送
          </Button>
        </div>
      </Card>

      {/* 配置模态框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <SettingOutlined />
            配置 {agentConfig.agent_name}
          </div>
        }
        open={isConfigModalVisible}
        onCancel={() => setIsConfigModalVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setIsConfigModalVisible(false)}>
            取消
          </Button>,
          <Button key="save" type="primary" icon={<SaveOutlined />} onClick={handleConfigSave}>
            保存配置
          </Button>
        ]}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={agentConfig}
        >
          <Collapse defaultActiveKey={['basic', 'model']}>
            <Panel header="基础配置" key="basic">
              <Form.Item label="Agent名称" name="agent_name">
                <Input placeholder="请输入Agent名称" />
              </Form.Item>
              
              <Form.Item label="Agent描述" name="agent_description">
                <TextArea rows={2} placeholder="请输入Agent描述" />
              </Form.Item>
              
              <Form.Item label="角色描述" name="role_description">
                <TextArea rows={3} placeholder="请描述Agent的角色和职责" />
              </Form.Item>
            </Panel>

            <Panel header="模型配置" key="model">
              <Form.Item label="模型提供商" name="model_provider">
                <Select onChange={() => form.setFieldsValue({ model_name: undefined })}>
                  {MODEL_PROVIDERS.map(provider => (
                    <Option key={provider.value} value={provider.value}>
                      {provider.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item label="模型名称" name="model_name">
                <Select>
                  {getAvailableModels().map(model => (
                    <Option key={model} value={model}>{model}</Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item label="温度参数" name="model_temperature">
                <Slider min={0} max={2} step={0.1} marks={{ 0: '0', 1: '1', 2: '2' }} />
              </Form.Item>
              
              <Form.Item label="最大Token数" name="model_max_tokens">
                <InputNumber min={100} max={20000} step={100} style={{ width: '100%' }} />
              </Form.Item>
            </Panel>

            <Panel header="工作流配置" key="workflow">
              <Form.Item label="工作流类型" name="workflow_type">
                <Select>
                  <Option value="react">ReAct (推理-行动)</Option>
                  <Option value="custom">自定义工作流</Option>
                </Select>
              </Form.Item>
              
              <Form.Item label="最大迭代次数" name="max_iterations">
                <InputNumber min={1} max={50} style={{ width: '100%' }} />
              </Form.Item>
              
              <Form.Item label="每轮最大工具调用次数" name="max_tool_calls_per_turn">
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
              
              <Form.Item name="enable_memory" valuePropName="checked">
                <Switch checkedChildren="启用记忆" unCheckedChildren="禁用记忆" />
              </Form.Item>
              
              <Form.Item name="enable_streaming" valuePropName="checked">
                <Switch checkedChildren="启用流式输出" unCheckedChildren="禁用流式输出" />
              </Form.Item>
            </Panel>

            <Panel header="工具配置" key="tools">
              <Form.Item label="启用的工具类别" name="enabled_tool_categories">
                <Select mode="multiple" placeholder="选择工具类别">
                  {TOOL_CATEGORIES.map(category => (
                    <Option key={category.value} value={category.value}>
                      {category.icon} {category.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Panel>

            <Panel header="性格特征" key="personality">
              <Form.Item label="性格特征" name="personality_traits">
                <Select mode="multiple" placeholder="选择性格特征">
                  {PERSONALITY_TRAITS.map(trait => (
                    <Option key={trait.value} value={trait.value}>
                      {trait.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Panel>
          </Collapse>
        </Form>
      </Modal>
    </div>
  );
};

export default GenericAgent;