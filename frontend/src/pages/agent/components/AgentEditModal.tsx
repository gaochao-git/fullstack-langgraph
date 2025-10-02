import React, { useState, useEffect } from 'react';
import { 
  Modal, 
  Form, 
  Input, 
  Select, 
  Button, 
  Tabs, 
  Row, 
  Col, 
  Tree, 
  Space, 
  Tooltip,
  App,
  Radio,
  Tag,
  InputNumber
} from 'antd';
import { 
  ToolOutlined, 
  ApiOutlined, 
  ClockCircleOutlined,
  LockOutlined,
  TeamOutlined,
  GlobalOutlined,
  UserOutlined,
  PlusOutlined,
  CloseOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import { 
  iconConfig,
  renderIcon
} from './AgentIconSystem';
import type { DataNode } from 'antd/es/tree';
import { agentApi } from '@/services/agentApi';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

// 智能体分类选项
const AGENT_TYPES = [
  { value: '日志分析', label: '日志分析' },
  { value: '监控告警', label: '监控告警' },
  { value: '故障诊断', label: '故障诊断' },
  { value: '性能优化', label: '性能优化' },
  { value: '资源管理', label: '资源管理' },
  { value: '运维部署', label: '运维部署' },
  { value: '安全防护', label: '安全防护' },
  { value: '合规审计', label: '合规审计' },
  { value: '合同履约', label: '合同履约' },
  { value: '变更管理', label: '变更管理' },
  { value: '其他', label: '其他' },
];

interface LocalAgent {
  id: number;
  agent_id: string;
  agent_name: string;
  agent_version: string;
  displayName: string;
  agent_description: string;
  agent_status: string;
  agent_enabled: string;
  agent_icon?: string;
  lastUsed?: string;
  totalRuns: number;
  successRate: number;
  avgResponseTime: number;
  is_builtin: string;
  agent_capabilities: string[];
  agent_key?: string;
  agent_owner?: string;
  mcpConfig: {
    enabledServers: string[];
    selectedTools: string[];
    totalTools: number;
  };
  llm_info?: {
    model_name?: string;
    available_models?: string[];
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  } | Array<{
    model_name: string;
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  }>;
  prompt_info?: {
    system_prompt?: string;
    user_prompt_template?: string;
    assistant_prompt_template?: string;
  };
  memory_info?: {
    enable_memory?: boolean;
    memory_types?: string[];
    memory_search_limit?: number;
    memory_similarity_threshold?: number;
    memory_save_strategy?: 'auto' | 'manual' | 'session_end';
    memory_scope?: 'user' | 'team' | 'organization';
  };
  tools_info?: {
    system_tools?: string[];
    mcp_tools?: Array<{
      server_id: string;
      server_name: string;
      tools: string[];
    }>;
  };
}

interface LocalMCPServer {
  id: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  tools: Array<{
    name: string;
    category: string;
    description: string;
  }>;
}

interface AgentEditModalProps {
  visible: boolean;
  onCancel: () => void;
  onSave: (values: any) => Promise<void>;
  agent: LocalAgent | null;
  isCreating: boolean;
  mcpServers: LocalMCPServer[];
  availableModels: any[];
  loading: boolean;
  onRefresh?: () => Promise<void>;
  currentUser?: { username: string } | null;
}

const AgentEditModal: React.FC<AgentEditModalProps> = ({
  visible,
  onCancel,
  onSave,
  agent,
  isCreating,
  mcpServers,
  availableModels,
  loading,
  onRefresh,
  currentUser
}) => {
  const [form] = Form.useForm();
  const { message } = App.useApp();
  
  // 工具选择状态
  const [editSystemTools, setEditSystemTools] = useState<string[]>([]);
  const [editMCPTools, setEditMCPTools] = useState<string[]>([]);
  const [editSystemCheckedKeys, setEditSystemCheckedKeys] = useState<string[]>([]);
  const [editSystemExpandedKeys, setEditSystemExpandedKeys] = useState<string[]>(['system-root']);
  const [editCheckedKeys, setEditCheckedKeys] = useState<string[]>([]);
  const [editExpandedKeys, setEditExpandedKeys] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [modelConfigs, setModelConfigs] = useState<Record<string, any>>({});
  // showAgentKey 和 resetKeyLoading 状态已移除，密钥管理通过权限系统进行

  // 将图标配置转换为选择器需要的格式
  const availableIcons = iconConfig.map(icon => ({
    value: icon.name,
    label: icon.label,
    icon: renderIcon(icon.name, 16),
    description: `${icon.label} - 适合${icon.category}类智能体`,
    category: icon.category
  }));

  // 系统工具列表状态
  const [systemTools, setSystemTools] = useState<Array<{
    name: string;
    display_name: string;
    description: string;
    module?: string;
  }>>([]);

  // 获取系统工具列表
  const fetchSystemTools = async () => {
    try {
      const response = await agentApi.getSystemTools();
      console.log('系统工具API响应:', response);
      
      // 处理响应数据 - 假设响应格式为 { status: 'ok', data: [...] }
      if (response && response.status === 'ok' && Array.isArray(response.data)) {
        setSystemTools(response.data);
      } else if (Array.isArray(response)) {
        // 如果直接返回数组
        setSystemTools(response);
      } else {
        console.error('系统工具响应格式错误:', response);
        setSystemTools([]);
      }
    } catch (error) {
      console.error('获取系统工具失败:', error);
      setSystemTools([]);
    }
  };

  // 组件挂载时获取系统工具
  useEffect(() => {
    fetchSystemTools();
  }, []);

  // 格式化工具描述
  const formatToolDescription = (description: string) => {
    const lines = description.split('\n');
    const summary = lines[0] || description;
    
    let args = '';
    let returns = '';
    let inArgs = false;
    let inReturns = false;
    
    for (const line of lines) {
      if (line.trim().startsWith('Args:')) {
        inArgs = true;
        inReturns = false;
        continue;
      }
      if (line.trim().startsWith('ReturFns:')) {
        inReturns = true;
        inArgs = false;
        continue;
      }
      
      if (inArgs && line.trim()) {
        args += line.trim() + '\n';
      }
      if (inReturns && line.trim()) {
        returns += line.trim() + '\n';
      }
    }
    
    return {
      summary: summary.replace(/^执行|^获取|^分析/, '').trim(),
      args: args.trim(),
      returns: returns.trim()
    };
  };

  // 构建系统工具树形数据
  const buildSystemTreeData = (): DataNode[] => {
    return [
      {
        title: '内置工具',
        key: 'system-root',
        children: systemTools.map(tool => {
          const { summary, args, returns } = formatToolDescription(tool.description);
          
          return {
            title: tool.display_name || tool.name,
            key: `system-${tool.name}`,
            children: [
              {
                title: (
                  <div className="space-y-2 p-1">
                    <div>
                      <div className="text-xs font-medium text-gray-700 mb-1">工具描述</div>
                      <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded leading-tight">
                        {summary}
                      </div>
                    </div>
                    
                    {args && (
                      <div>
                        <div className="text-xs font-medium text-gray-700 mb-1">参数说明</div>
                        <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs leading-tight">{args}</pre>
                        </div>
                      </div>
                    )}
                    
                    {returns && (
                      <div>
                        <div className="text-xs font-medium text-gray-700 mb-1">返回值说明</div>
                        <div className="text-xs text-gray-600 bg-green-50 p-2 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs leading-tight">{returns}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                ),
                key: `system-${tool.name}-detail`,
                isLeaf: true,
                selectable: false,
                checkable: false
              }
            ]
          };
        })
      }
    ];
  };

  // 构建MCP工具树形数据
  const buildTreeData = (): DataNode[] => {
    if (!mcpServers || mcpServers.length === 0) {
      return [
        {
          title: '暂无MCP服务器数据',
          key: 'no-data',
          disabled: true,
          isLeaf: true
        }
      ];
    }
    
    return mcpServers.map(server => {
      return {
        title: `${server.name} - ${server.tools?.length || 0}工具`,
        key: `server-${server.id}`,
        disabled: false, // 移除状态判断，所有服务器都可用
        children: (server.tools || []).map(tool => {
          const { args, returns } = formatToolDescription(tool.description);
          
          return {
            title: tool.name,
            key: `tool-${tool.name}`,
            disabled: false, // 移除状态判断，所有工具都可勾选
            children: [
              {
                title: (
                  <div className="space-y-2 p-1">
                    <div>
                      <div className="text-xs font-medium text-gray-700 mb-1">工具描述</div>
                      <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded leading-tight">
                        {tool.description}
                      </div>
                    </div>
                    
                    {args && (
                      <div>
                        <div className="text-xs font-medium text-gray-700 mb-1">参数说明</div>
                        <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs leading-tight">{args}</pre>
                        </div>
                      </div>
                    )}
                    
                    {returns && (
                      <div>
                        <div className="text-xs font-medium text-gray-700 mb-1">返回值说明</div>
                        <div className="text-xs text-gray-600 bg-green-50 p-2 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs leading-tight">{returns}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                ),
                key: `tool-${tool.name}-detail`,
                isLeaf: true,
                selectable: false,
                checkable: false
              }
            ]
          };
        })
      };
    });
  };

  // 处理系统工具选择
  const handleEditSystemTreeCheck = (checked: React.Key[] | { checked: React.Key[]; halfChecked: React.Key[] }) => {
    const checkedKeyArray = Array.isArray(checked) ? checked : checked.checked;
    const stringKeys = checkedKeyArray.map(key => String(key));
    setEditSystemCheckedKeys(stringKeys);
    
    const selectedTools = stringKeys
      .filter(key => key.startsWith('system-') && !key.endsWith('-detail') && key !== 'system-root')
      .map(key => key.replace('system-', ''));
    
    setEditSystemTools(selectedTools);
  };

  // 处理MCP工具选择
  const handleEditTreeCheck = (checked: React.Key[] | { checked: React.Key[]; halfChecked: React.Key[] }) => {
    const checkedKeyArray = Array.isArray(checked) ? checked : checked.checked;
    const stringKeys = checkedKeyArray.map(key => String(key));
    setEditCheckedKeys(stringKeys);
    
    const selectedTools: string[] = [];
    
    stringKeys.forEach(key => {
      if (key.startsWith('tool-')) {
        const toolName = key.replace('tool-', '');
        selectedTools.push(toolName);
      }
    });
    
    setEditMCPTools(selectedTools);
  };

  // 初始化表单数据
  useEffect(() => {
    if (visible) {
      form.resetFields(); // 重置表单避免状态残留
      
      if (isCreating) {
        // 新建时的默认值
        setEditSystemTools([]);
        setEditMCPTools([]);
        setEditSystemCheckedKeys([]);
        setEditCheckedKeys([]);
        setEditSystemExpandedKeys(['system-root']);
        setEditExpandedKeys([]);
        
        form.setFieldsValue({
          agent_type: '故障诊断',
          agent_capabilities: [],
          agent_icon: 'Bot',
          llm_configs: [{
            model_name: availableModels.length > 0 ? availableModels[0].model : 'deepseek-chat',
            model_args: {
              temperature: 0.7,
              max_tokens: 2000,
              top_p: 1.0
            }
          }],
          system_prompt: '',
          user_prompt_template: '',
          assistant_prompt_template: '',
          visibility_type: 'private',
          visibility_additional_users: []
        });
      } else if (agent) {
        // 编辑时的初始化
        const mcpToolNames = mcpServers.flatMap(s => (s.tools || []).map(t => t.name));
        const systemToolNames = agent.mcpConfig.selectedTools.filter(tool => 
          systemTools.some(st => st.name === tool)
        );
        const mcpSelectedTools = agent.mcpConfig.selectedTools.filter(tool => 
          mcpToolNames.includes(tool)
        );
        
        setEditSystemTools(systemToolNames);
        setEditMCPTools(mcpSelectedTools);
        
        const systemCheckedKeys = systemToolNames.map(name => `system-${name}`);
        const mcpCheckedKeys = mcpSelectedTools.map(name => `tool-${name}`);
        
        setEditSystemCheckedKeys(systemCheckedKeys);
        setEditCheckedKeys(mcpCheckedKeys);
        setEditSystemExpandedKeys(['system-root']);
        setEditExpandedKeys([]);

        // 获取详细配置
        loadAgentDetails();
      }
    }
  }, [visible, isCreating, agent?.agent_id]);

  const loadAgentDetails = async () => {
    if (!agent) return;
    
    try {
      // 使用具体的智能体ID接口，而不是获取全部后过滤
      const response = await agentApi.getAgent(agent.agent_id);
      
      // 处理统一响应格式
      if (response.status === 'ok' && response.data) {
        const fullAgent = response.data;
        
        // 添加调试日志
        console.log('Agent details loaded:', fullAgent);
        console.log('LLM info:', fullAgent.llm_info);
        
        // 直接设置表单值，只设置实际存在的值，避免默认值覆盖
        const formValues: any = {
          agent_id: fullAgent.agent_id,
          agent_name: fullAgent.agent_name,
          agent_type: fullAgent.agent_type,
          agent_description: fullAgent.agent_description,
          agent_capabilities: fullAgent.agent_capabilities,
          agent_icon: fullAgent.agent_icon,
          visibility_type: fullAgent.visibility_type || 'private',
          visibility_additional_users: fullAgent.visibility_additional_users || [],
        };

        // LLM 配置 - 支持新旧两种数据结构
        if (fullAgent.llm_info) {
          if (Array.isArray(fullAgent.llm_info)) {
            // 新的数据结构：数组格式
            formValues.llm_configs = fullAgent.llm_info;
          } else if (typeof fullAgent.llm_info === 'object') {
            // 旧的数据结构：单个对象，转换为数组
            const legacyConfig = {
              model_name: fullAgent.llm_info.model_name || '',
              temperature: fullAgent.llm_info.temperature ?? 0.7,
              max_tokens: fullAgent.llm_info.max_tokens ?? 2000,
              top_p: fullAgent.llm_info.top_p ?? 0.9,
              frequency_penalty: fullAgent.llm_info.frequency_penalty ?? 0,
              presence_penalty: fullAgent.llm_info.presence_penalty ?? 0
            };
            formValues.llm_configs = [legacyConfig];
            console.log('Converted legacy LLM config to new format:', formValues.llm_configs);
          } else {
            // 未知格式
            console.warn('Unknown LLM config format:', fullAgent.llm_info);
            formValues.llm_configs = [];
          }
        } else {
          // 没有LLM配置
          console.warn('No LLM config found for agent');
          formValues.llm_configs = [];
        }

        // 提示词配置 - 只设置实际存在的值
        if (fullAgent.prompt_info) {
          if (fullAgent.prompt_info.system_prompt) {
            formValues.system_prompt = fullAgent.prompt_info.system_prompt;
          }
          if (fullAgent.prompt_info.user_prompt_template) {
            formValues.user_prompt_template = fullAgent.prompt_info.user_prompt_template;
          }
          if (fullAgent.prompt_info.assistant_prompt_template) {
            formValues.assistant_prompt_template = fullAgent.prompt_info.assistant_prompt_template;
          }
        }

        // 记忆配置 - 设置记忆相关配置
        if (fullAgent.memory_info) {
          formValues.enable_memory = fullAgent.memory_info.enable_memory || false;
          formValues.memory_types = fullAgent.memory_info.memory_types || [];
          formValues.memory_search_limit = fullAgent.memory_info.memory_search_limit || 5;
          formValues.memory_similarity_threshold = fullAgent.memory_info.memory_similarity_threshold || 0.7;
          formValues.memory_save_strategy = fullAgent.memory_info.memory_save_strategy || 'auto';
          formValues.memory_scope = fullAgent.memory_info.memory_scope || 'user';
        } else {
          // 设置默认值
          formValues.enable_memory = false;
          formValues.memory_search_limit = 5;
          formValues.memory_save_strategy = 'auto';
          formValues.memory_scope = 'user';
        }

        form.setFieldsValue(formValues);
        
        // 处理工具配置
        if (fullAgent.tools_info) {
          // 处理系统工具
          const systemToolsFromAgent = fullAgent.tools_info.system_tools || [];
          setEditSystemTools(systemToolsFromAgent);
          setEditSystemCheckedKeys(systemToolsFromAgent.map((name: string) => `system-${name}`));
          
          // 处理MCP工具
          const mcpToolsFromAgent = fullAgent.tools_info.mcp_tools || [];
          const mcpToolNames = mcpToolsFromAgent.flatMap((mcpTool: any) => mcpTool.tools || []);
          setEditMCPTools(mcpToolNames);
          setEditCheckedKeys(mcpToolNames.map((name: string) => `tool-${name}`));
          
          // 展开已选中工具的服务器
          const selectedServerIds = mcpToolsFromAgent.map((mcpTool: any) => `server-${mcpTool.server_id}`);
          setEditExpandedKeys(selectedServerIds);
        }
      } else if (response.status === 'error') {
        // 获取智能体详细配置失败
        message.error(response.msg || '获取智能体详细配置失败');
      }
    } catch (error) {
      // 获取智能体详细配置失败
      message.error('获取智能体详细配置失败');
    }
  };

  const handleSubmit = async (values: any) => {
    // 构建工具配置
    const toolsConfig = {
      system_tools: editSystemTools,
      mcp_tools: mcpServers
        // 移除状态过滤，包含所有服务器
        .map(server => ({
          server_id: server.id,
          server_name: server.name,
          tools: (server.tools || [])
            .filter(tool => editMCPTools.includes(tool.name))
            .map(tool => tool.name)
        }))
        .filter(server => server.tools.length > 0)
    };

    // 构建LLM配置 - 新的数据结构
    let llmConfig = values.llm_configs || [];
    
    // 如果是编辑模式且没有提供新的LLM配置，保留原有配置
    if (!isCreating && agent && (!llmConfig || llmConfig.length === 0)) {
      // 尝试从agent对象中获取原有的llm_info
      if (agent.llm_info) {
        if (Array.isArray(agent.llm_info)) {
          llmConfig = agent.llm_info;
        } else if (typeof agent.llm_info === 'object') {
          // 兼容旧格式
          llmConfig = [{
            model_name: agent.llm_info.model_name || '',
            temperature: agent.llm_info.temperature ?? 0.7,
            max_tokens: agent.llm_info.max_tokens ?? 2000,
            top_p: agent.llm_info.top_p ?? 0.9,
            frequency_penalty: agent.llm_info.frequency_penalty ?? 0,
            presence_penalty: agent.llm_info.presence_penalty ?? 0
          }];
        }
      }
      console.log('Preserving original LLM config:', llmConfig);
    }

    // 构建提示词配置
    const promptConfig: any = {};
    
    // 如果是编辑模式，先复制原有的配置
    if (!isCreating && agent?.prompt_info) {
      Object.assign(promptConfig, agent.prompt_info);
    }
    
    // 然后只更新表单中实际修改的字段
    if (values.system_prompt !== undefined) {
      promptConfig.system_prompt = values.system_prompt;
    }
    if (values.user_prompt_template !== undefined) {
      promptConfig.user_prompt_template = values.user_prompt_template;
    }
    if (values.assistant_prompt_template !== undefined) {
      promptConfig.assistant_prompt_template = values.assistant_prompt_template;
    }

    // 构建记忆配置
    const memoryConfig: any = {
      enable_memory: values.enable_memory || false,
      memory_types: values.memory_types || [],
      memory_search_limit: values.memory_search_limit || 5,
      memory_similarity_threshold: values.memory_similarity_threshold || 0.7,
      memory_save_strategy: values.memory_save_strategy || 'auto',
      memory_scope: values.memory_scope || 'user'
    };
    
    // 如果是编辑模式且原有记忆配置，合并配置
    if (!isCreating && agent?.memory_info) {
      Object.assign(memoryConfig, agent.memory_info, {
        enable_memory: values.enable_memory,
        memory_types: values.memory_types,
        memory_search_limit: values.memory_search_limit,
        memory_similarity_threshold: values.memory_similarity_threshold,
        memory_save_strategy: values.memory_save_strategy,
        memory_scope: values.memory_scope
      });
    }

    // 清理表单值，移除不需要提交的字段
    const {
      llm_configs,
      system_prompt,
      user_prompt_template,
      assistant_prompt_template,
      enable_memory,
      memory_types,
      memory_search_limit,
      memory_save_strategy,
      memory_scope,
      ...baseValues
    } = values;

    const formData = {
      ...baseValues,
      tools_info: toolsConfig,
      llm_info: llmConfig,
      prompt_info: promptConfig,
      memory_info: memoryConfig,
      // 确保权限字段被包含
      visibility_type: values.visibility_type || 'private',
      visibility_additional_users: values.visibility_additional_users || []
    };


    await onSave(formData);
  };

  // handleResetKey 函数已移除，密钥管理通过权限系统进行

  const handleCancel = () => {
    form.resetFields();
    setEditSystemTools([]);
    setEditMCPTools([]);
    setEditSystemCheckedKeys([]);
    setEditCheckedKeys([]);
    setEditExpandedKeys([]);
    setEditSystemExpandedKeys(['system-root']);
    onCancel();
  };

  return (
    <Modal
      title={isCreating ? "新建智能体" : "编辑智能体"}
      open={visible}
      onCancel={handleCancel}
      width={900}
      footer={null}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Tabs defaultActiveKey="basic" type="card">
          {/* 基本信息 */}
          <TabPane tab="基本信息" key="basic">
            <Form.Item
              label="智能体名称"
              name="agent_name"
              rules={[{ required: true, message: '请输入智能体名称' }]}
            >
              <Input placeholder="例如: 我的自定义智能体" />
            </Form.Item>

            <Form.Item
              label="智能体分类"
              name="agent_type"
              rules={[{ required: true, message: '请选择智能体分类' }]}
            >
              <Select placeholder="请选择分类">
                {AGENT_TYPES.map(type => (
                  <Option key={type.value} value={type.value}>{type.label}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item
              label="描述"
              name="agent_description"
            >
              <TextArea 
                rows={1}
                placeholder="描述这个智能体的功能和用途..."
                maxLength={500}
                showCount
              />
            </Form.Item>
            <Form.Item
              label="核心能力"
              name="agent_capabilities"
            >
              <Select
                mode="tags"
                placeholder="添加智能体的核心能力标签，按回车确认"
                style={{ width: '100%' }}
                tokenSeparators={[',']}
              />
            </Form.Item>
            <Form.Item
              label="智能体图标"
              name="agent_icon"
              rules={[{ required: true, message: '请选择智能体图标' }]}
              extra="选择合适的图标来代表您的智能体特性"
            >
              <Select 
                placeholder="选择智能体显示图标"
                showSearch
                optionFilterProp="children"
                style={{ width: '100%' }}
                size="large"
                dropdownStyle={{ maxHeight: '400px' }}
                optionRender={(option) => {
                  const iconOption = availableIcons.find(icon => icon.value === option.value);
                  if (!iconOption) return option.label;
                  
                  return (
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px'
                    }}>
                      <div style={{ 
                        width: '16px',
                        height: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        {renderIcon(iconOption.value, 14)}
                      </div>
                      <span>{iconOption.label}</span>
                    </div>
                  );
                }}
              >
                {/* 按分类分组显示图标 */}
                {['基础', '专业', '服务', '教育', '娱乐', '工具'].map(category => (
                  <Select.OptGroup key={category} label={`${category}类型`}>
                    {availableIcons
                      .filter(icon => icon.category === category)
                      .map(iconOption => (
                        <Option 
                          key={iconOption.value} 
                          value={iconOption.value}
                          label={iconOption.label}
                        >
                          <div style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: '8px',
                            padding: '6px 0',
                            width: '100%'
                          }}>
                            <div style={{ 
                              width: '20px',
                              height: '20px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              flexShrink: 0
                            }}>
                              {renderIcon(iconOption.value, 16)}
                            </div>
                            <div style={{ 
                              flex: 1,
                              overflow: 'hidden'
                            }}>
                              <div style={{ 
                                fontWeight: 500,
                                fontSize: '14px',
                                lineHeight: '20px',
                                color: '#262626'
                              }}>
                                {iconOption.label}
                              </div>
                              <div style={{ 
                                color: '#8c8c8c', 
                                fontSize: '12px', 
                                lineHeight: '16px',
                                marginTop: '1px',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis'
                              }}>
                                {iconOption.description}
                              </div>
                            </div>
                          </div>
                        </Option>
                    ))}
                  </Select.OptGroup>
                ))}
              </Select>
            </Form.Item>

            {/* 权限配置 */}
            <Form.Item
              label="可见性权限"
              name="visibility_type"
              rules={[{ required: true, message: '请选择可见性权限' }]}
              initialValue="private"
              extra="设置谁可以看到并使用这个智能体"
            >
              <Radio.Group>
                <Space direction="vertical">
                  <Radio value="private">
                    <Space>
                      <LockOutlined />
                      <span>仅自己可见</span>
                      <Tag color="red">私有</Tag>
                    </Space>
                  </Radio>
                  <Radio value="team">
                    <Space>
                      <TeamOutlined />
                      <span>团队可见</span>
                      <Tag color="orange">团队共享</Tag>
                    </Space>
                  </Radio>
                  <Radio value="department">
                    <Space>
                      <TeamOutlined />
                      <span>部门可见</span>
                      <Tag color="blue">部门共享</Tag>
                    </Space>
                  </Radio>
                  <Radio value="public">
                    <Space>
                      <GlobalOutlined />
                      <span>所有人可见</span>
                      <Tag color="green">公开</Tag>
                    </Space>
                  </Radio>
                </Space>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              label="额外授权用户"
              name="visibility_additional_users"
              extra="输入用户名，按回车添加。这些用户将获得访问权限"
            >
              <Select
                mode="tags"
                placeholder="输入用户名并按回车"
                style={{ width: '100%' }}
                tokenSeparators={[',']}
              />
            </Form.Item>

            {/* agent_key 管理功能已移除，密钥管理通过权限系统进行 */}
          </TabPane>

          {/* 工具配置 */}
          <TabPane tab="工具配置" key="tools">
            <div className="space-y-4">
              {/* 顶部操作栏 */}
              <div className="p-3 bg-gray-50 rounded-lg">
                <Row gutter={16} align="middle">
                  <Col span={12}>
                    <Space>
                      <Button 
                        size="small"
                        onClick={() => {
                          const allSystemToolNames = systemTools.map(t => t.name);
                          setEditSystemTools(allSystemToolNames);
                          setEditSystemCheckedKeys(allSystemToolNames.map(name => `system-${name}`));
                          
                          const allMCPKeys: string[] = [];
                          const allMCPToolNames: string[] = [];
                          mcpServers
                            // 移除状态过滤，选择所有服务器
                            .forEach(server => {
                              allMCPKeys.push(`server-${server.id}`);
                              (server.tools || []).forEach(tool => {
                                allMCPKeys.push(`tool-${tool.name}`);
                                allMCPToolNames.push(tool.name);
                              });
                            });
                          setEditCheckedKeys(allMCPKeys);
                          setEditMCPTools(allMCPToolNames);
                        }}
                      >
                        全选可用
                      </Button>
                      <Button 
                        size="small"
                        onClick={() => {
                          setEditSystemTools([]);
                          setEditSystemCheckedKeys([]);
                          setEditCheckedKeys([]);
                          setEditMCPTools([]);
                        }}
                      >
                        清空选择
                      </Button>
                      <Button 
                        size="small"
                        onClick={() => {
                          setEditSystemExpandedKeys(['system-root']);
                          setEditExpandedKeys(mcpServers.map(s => `server-${s.id}`));
                        }}
                      >
                        展开全部
                      </Button>
                      <Button 
                        size="small"
                        onClick={() => {
                          setEditSystemExpandedKeys([]);
                          setEditExpandedKeys([]);
                        }}
                      >
                        收起全部
                      </Button>
                    </Space>
                  </Col>
                  <Col span={12} className="text-right">
                    <Space>
                      <span className="text-sm text-gray-600">
                        服务器总数: {mcpServers.length}
                      </span>
                      <span className="text-sm text-gray-600">
                        总工具数: {systemTools.length + mcpServers.reduce((sum, s) => sum + (s.tools?.length || 0), 0)}
                      </span>
                    </Space>
                  </Col>
                </Row>
              </div>
              
              {/* 系统工具配置 */}
              <div>
                <div className="text-sm font-medium text-gray-800 mb-2 flex items-center justify-between">
                  <div className="flex items-center">
                    <ToolOutlined className="mr-2" />
                    系统工具配置
                  </div>
                  <div className="text-xs text-gray-500">
                    已选: {editSystemTools.length}/{systemTools.length}
                  </div>
                </div>
                <div className="border rounded-lg p-4 max-h-60 overflow-y-auto">
                  <Tree
                    checkable
                    checkedKeys={editSystemCheckedKeys}
                    expandedKeys={editSystemExpandedKeys}
                    onCheck={handleEditSystemTreeCheck}
                    onExpand={(expandedKeys) => setEditSystemExpandedKeys(expandedKeys.map(key => String(key)))}
                    treeData={buildSystemTreeData()}
                    showLine
                    showIcon={false}
                    className="w-full"
                  />
                </div>
              </div>

              {/* MCP工具配置 */}
              <div>
                <div className="text-sm font-medium text-gray-800 mb-2 flex items-center justify-between">
                  <div className="flex items-center">
                    <ApiOutlined className="mr-2" />
                    MCP工具配置
                  </div>
                  <div className="text-xs text-gray-500">
                    已选: {editMCPTools.length}工具
                  </div>
                </div>
                <div className="border rounded-lg p-4 max-h-60 overflow-y-auto">
                  {mcpServers.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <div>暂无MCP服务器</div>
                    </div>
                  ) : (
                    <Tree
                      checkable
                      checkedKeys={editCheckedKeys}
                      expandedKeys={editExpandedKeys}
                      onCheck={handleEditTreeCheck}
                      onExpand={(expandedKeys) => setEditExpandedKeys(expandedKeys.map(key => String(key)))}
                      treeData={buildTreeData()}
                      showLine
                      showIcon={false}
                      className="w-full"
                    />
                  )}
                </div>
              </div>
            </div>
          </TabPane>

          {/* LLM配置 */}
          <TabPane tab="大模型配置" key="llm">
            <Form.List name="llm_configs">
              {(fields, { add, remove }) => (
                <>
                  <div style={{ marginBottom: 16 }}>
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      添加模型配置
                    </Button>
                  </div>
                  {fields.map(({ key, name, ...restField }) => (
                    <div key={key} style={{ 
                      marginBottom: 16, 
                      padding: 16, 
                      border: '1px solid #f0f0f0',
                      borderRadius: 8,
                      position: 'relative'
                    }}>
                      <CloseOutlined
                        style={{ 
                          position: 'absolute', 
                          right: 8, 
                          top: 8,
                          cursor: 'pointer',
                          color: '#ff4d4f'
                        }}
                        onClick={() => remove(name)}
                      />
                      <Row gutter={16}>
                        <Col span={24}>
                          <Form.Item
                            {...restField}
                            name={[name, 'model_name']}
                            label="选择模型"
                            rules={[{ required: true, message: '请选择模型' }]}
                          >
                            <Select 
                              placeholder="选择模型" 
                              showSearch
                              optionFilterProp="children"
                            >
                              {availableModels.length > 0 ? (
                                availableModels.map(model => (
                                  <Option key={model.id} value={model.model}>
                                    <span style={{ fontWeight: 500 }}>{model.name}</span>
                                    <span style={{ marginLeft: 8, color: '#666', fontSize: '12px' }}>
                                      ({model.provider})
                                    </span>
                                  </Option>
                                ))
                              ) : (
                                <>
                                  <Option value="deepseek-chat">DeepSeek Chat</Option>
                                  <Option value="gpt-4">GPT-4</Option>
                                  <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
                                </>
                              )}
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>
                      <Row gutter={16}>
                        <Col span={8}>
                          <Form.Item
                            {...restField}
                            name={[name, 'model_args', 'temperature']}
                            label={
                              <Tooltip title="控制输出的随机性和创造性，0-2之间，值越高越随机">
                                温度
                              </Tooltip>
                            }
                            rules={[{ required: true, message: '请输入温度值' }]}
                            initialValue={0.7}
                          >
                            <InputNumber 
                              min={0} 
                              max={2} 
                              step={0.1} 
                              placeholder="0.7"
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item
                            {...restField}
                            name={[name, 'model_args', 'max_tokens']}
                            label={
                              <Tooltip title="模型单次生成的最大字符数量，影响回答长度">
                                最大Token数
                              </Tooltip>
                            }
                            rules={[{ required: true, message: '请输入最大Token数' }]}
                            initialValue={2000}
                          >
                            <InputNumber 
                              min={1}
                              max={100000}
                              placeholder="2000"
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={8}>
                          <Form.Item
                            {...restField}
                            name={[name, 'model_args', 'top_p']}
                            label={
                              <Tooltip title="核采样参数，控制候选词汇范围，0-1之间，值越小越保守">
                                Top P
                              </Tooltip>
                            }
                            initialValue={1.0}
                          >
                            <InputNumber 
                              min={0} 
                              max={1} 
                              step={0.1} 
                              placeholder="1.0"
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                      </Row>
                    </div>
                  ))}
                </>
              )}
            </Form.List>
          </TabPane>

          {/* 提示词配置 */}
          <TabPane tab="提示词配置" key="prompt">
            <Form.Item
              label="系统提示词"
              name="system_prompt"
              rules={[{ required: true, message: '请输入系统提示词' }]}
            >
              <TextArea 
                rows={10}
                placeholder="定义智能体的角色、行为准则和回答风格..."
                maxLength={5000}
                showCount
              />
            </Form.Item>

          </TabPane>

          {/* 记忆配置 */}
          <TabPane tab="记忆配置" key="memory">
            <div className="space-y-4">
              {/* 功能说明提示 */}
              <div className="p-3 bg-blue-50 rounded-lg mb-4">
                <div className="text-sm text-blue-800">
                  <strong>💡 提示：</strong>
                  <ul className="mt-1 ml-5 list-disc">
                    <li>启用记忆功能后，智能体将能够记住用户的历史信息和偏好</li>
                    <li>记忆数据会自动加密存储，确保隐私安全</li>
                    <li>可以通过"记忆管理"页面查看和管理所有记忆数据</li>
                  </ul>
                </div>
              </div>
              {/* 启用记忆功能 */}
              <Form.Item
                name="enable_memory"
                label="启用记忆功能"
                tooltip="启用后，智能体会记住用户的历史对话和偏好"
                initialValue={false}
              >
                <Radio.Group>
                  <Radio value={true}>启用</Radio>
                  <Radio value={false}>禁用</Radio>
                </Radio.Group>
              </Form.Item>

              {/* 记忆类型和检索配置 - 同一行 */}
              <Form.Item
                dependencies={['enable_memory']}
                noStyle
              >
                {({ getFieldValue }) => (
                  <Row gutter={16}>
                    <Col span={16}>
                      <Form.Item
                        name="memory_types"
                        label="记忆类型"
                        tooltip="选择智能体需要记忆的信息类型"
                      >
                        <Select
                          mode="multiple"
                          placeholder="选择需要记忆的信息类型"
                          disabled={!getFieldValue('enable_memory')}
                        >
                          <Option value="user_profile">用户档案</Option>
                          <Option value="user_expertise">用户技能</Option>
                          <Option value="user_preferences">用户偏好</Option>
                          <Option value="system_topology">系统拓扑</Option>
                          <Option value="incident_history">故障历史</Option>
                          <Option value="solution_patterns">解决方案模式</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item
                        name="memory_search_limit"
                        label="记忆检索数量"
                        tooltip="每次对话时检索的相关记忆数量"
                        initialValue={5}
                      >
                        <InputNumber
                          min={1}
                          max={20}
                          style={{ width: '100%' }}
                          disabled={!getFieldValue('enable_memory')}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                )}
              </Form.Item>

              {/* 相似性阈值配置 */}
              <Form.Item
                dependencies={['enable_memory']}
                noStyle
              >
                {({ getFieldValue }) => (
                  <Form.Item
                    name="memory_similarity_threshold"
                    label="相似性阈值"
                    tooltip="相似度阈值，0.7表示70%相似度"
                    initialValue={0.7}
                  >
                    <InputNumber
                      min={0}
                      max={1}
                      step={0.1}
                      style={{ width: 200 }}
                      disabled={!getFieldValue('enable_memory')}
                      formatter={value => `${value}`}
                      parser={value => parseFloat(value)}
                    />
                  </Form.Item>
                )}
              </Form.Item>


              {/* 记忆保存策略 */}
              <Form.Item
                dependencies={['enable_memory']}
                noStyle
              >
                {({ getFieldValue }) => (
                  <Form.Item
                    name="memory_save_strategy"
                    label="记忆保存策略"
                    tooltip="控制何时保存新的记忆"
                    initialValue="auto"
                  >
                    <Radio.Group 
                      disabled={!getFieldValue('enable_memory')}
                    >
                      <Radio value="auto">自动保存（推荐）</Radio>
                      <Radio value="manual">手动确认</Radio>
                      <Radio value="session_end">会话结束时</Radio>
                    </Radio.Group>
                  </Form.Item>
                )}
              </Form.Item>

              {/* 记忆权限配置 */}
              <Form.Item
                dependencies={['enable_memory']}
                noStyle
              >
                {({ getFieldValue }) => (
                  <Form.Item
                    name="memory_scope"
                    label="记忆共享范围"
                    tooltip="控制记忆的可见范围"
                    initialValue="user"
                  >
                    <Radio.Group 
                      disabled={!getFieldValue('enable_memory')}
                    >
                      <Radio value="user">仅当前用户</Radio>
                      <Radio value="team">团队共享</Radio>
                      <Radio value="organization">组织共享</Radio>
                    </Radio.Group>
                  </Form.Item>
                )}
              </Form.Item>
            </div>
          </TabPane>
        </Tabs>

        <div className="flex justify-end space-x-2 mt-4 pt-4 border-t">
          <Button onClick={handleCancel}>
            取消
          </Button>
          <Button 
            type="primary" 
            htmlType="submit"
            loading={loading}
          >
            {isCreating ? '创建智能体' : '保存修改'}
          </Button>
        </div>
      </Form>
    </Modal>
  );
};

export default AgentEditModal;