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
  message 
} from 'antd';
import { 
  ToolOutlined, 
  ApiOutlined, 
  ClockCircleOutlined,
  RobotOutlined,
  SettingOutlined,
  UserOutlined,
  DatabaseOutlined,
  BulbOutlined,
  HeartOutlined,
  BookOutlined,
  CodeOutlined,
  CustomerServiceOutlined
} from '@ant-design/icons';
import { 
  Bot, 
  Settings, 
  User, 
  Database, 
  Lightbulb, 
  Heart, 
  Book, 
  Code, 
  Headphones,
  Brain,
  Sparkles,
  Shield,
  Search,
  MessageCircle,
  Zap,
  Target,
  TrendingUp,
  FileText,
  Globe,
  Music,
  Gamepad2,
  Camera,
  Palette,
  Calculator
} from 'lucide-react';
import ScheduledTaskManager from './ScheduledTaskManager';
import type { DataNode } from 'antd/es/tree';
import { agentApi, type CreateAgentRequest, type UpdateAgentRequest } from '../services/agentApi';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

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
  mcpConfig: {
    enabledServers: string[];
    selectedTools: string[];
    totalTools: number;
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
}

const AgentEditModal: React.FC<AgentEditModalProps> = ({
  visible,
  onCancel,
  onSave,
  agent,
  isCreating,
  mcpServers,
  availableModels,
  loading
}) => {
  const [form] = Form.useForm();
  
  // 工具选择状态
  const [editSystemTools, setEditSystemTools] = useState<string[]>([]);
  const [editMCPTools, setEditMCPTools] = useState<string[]>([]);
  const [editSystemCheckedKeys, setEditSystemCheckedKeys] = useState<string[]>([]);
  const [editSystemExpandedKeys, setEditSystemExpandedKeys] = useState<string[]>(['system-root']);
  const [editCheckedKeys, setEditCheckedKeys] = useState<string[]>([]);
  const [editExpandedKeys, setEditExpandedKeys] = useState<string[]>([]);

  // 定义分类颜色
  const categoryColors = {
    '基础': '#1677ff',    // 蓝色 - 基础功能
    '专业': '#722ed1',    // 紫色 - 专业技术
    '服务': '#13c2c2',    // 青色 - 服务类型
    '教育': '#52c41a',    // 绿色 - 教育知识
    '娱乐': '#fa8c16',    // 橙色 - 娱乐休闲
    '工具': '#eb2f96'     // 粉色 - 工具类型
  };

  // 可选图标定义 - 带颜色的 Lucide React 图标
  const availableIcons = [
    // 基础类型
    { value: 'Bot', label: '智能机器人', icon: <Bot size={16} color={categoryColors['基础']} />, description: '通用AI助手，适合各类智能体', category: '基础' },
    { value: 'Brain', label: '智慧大脑', icon: <Brain size={16} color={categoryColors['基础']} />, description: '强调智能和思考能力', category: '基础' },
    { value: 'Sparkles', label: '魔法星星', icon: <Sparkles size={16} color={categoryColors['基础']} />, description: '创意和灵感类智能体', category: '基础' },
    
    // 专业领域
    { value: 'Settings', label: '系统设置', icon: <Settings size={16} color={categoryColors['专业']} />, description: '系统管理、运维、配置类', category: '专业' },
    { value: 'Database', label: '数据库', icon: <Database size={16} color={categoryColors['专业']} />, description: '数据分析、存储、查询类', category: '专业' },
    { value: 'Code', label: '代码编程', icon: <Code size={16} color={categoryColors['专业']} />, description: '编程开发、技术支持类', category: '专业' },
    { value: 'Shield', label: '安全防护', icon: <Shield size={16} color={categoryColors['专业']} />, description: '安全分析、风险管控类', category: '专业' },
    { value: 'Search', label: '搜索查询', icon: <Search size={16} color={categoryColors['专业']} />, description: '信息检索、搜索优化类', category: '专业' },
    { value: 'TrendingUp', label: '趋势分析', icon: <TrendingUp size={16} color={categoryColors['专业']} />, description: '数据分析、趋势预测类', category: '专业' },
    
    // 服务类型
    { value: 'User', label: '用户服务', icon: <User size={16} color={categoryColors['服务']} />, description: '客户服务、用户支持类', category: '服务' },
    { value: 'Headphones', label: '客服支持', icon: <Headphones size={16} color={categoryColors['服务']} />, description: '客户服务、技术支持类', category: '服务' },
    { value: 'MessageCircle', label: '对话交流', icon: <MessageCircle size={16} color={categoryColors['服务']} />, description: '聊天对话、沟通交流类', category: '服务' },
    { value: 'Heart', label: '情感陪伴', icon: <Heart size={16} color={categoryColors['服务']} />, description: '心理支持、情感陪伴类', category: '服务' },
    
    // 知识教育
    { value: 'Book', label: '知识教育', icon: <Book size={16} color={categoryColors['教育']} />, description: '教育培训、知识问答类', category: '教育' },
    { value: 'FileText', label: '文档处理', icon: <FileText size={16} color={categoryColors['教育']} />, description: '文档编辑、内容创作类', category: '教育' },
    { value: 'Lightbulb', label: '创意建议', icon: <Lightbulb size={16} color={categoryColors['教育']} />, description: '创意策划、建议咨询类', category: '教育' },
    { value: 'Target', label: '目标导向', icon: <Target size={16} color={categoryColors['教育']} />, description: '任务规划、目标管理类', category: '教育' },
    
    // 娱乐生活
    { value: 'Music', label: '音乐娱乐', icon: <Music size={16} color={categoryColors['娱乐']} />, description: '音乐推荐、娱乐互动类', category: '娱乐' },
    { value: 'Gamepad2', label: '游戏娱乐', icon: <Gamepad2 size={16} color={categoryColors['娱乐']} />, description: '游戏相关、娱乐互动类', category: '娱乐' },
    { value: 'Camera', label: '图片处理', icon: <Camera size={16} color={categoryColors['娱乐']} />, description: '图像处理、视觉分析类', category: '娱乐' },
    { value: 'Palette', label: '艺术创作', icon: <Palette size={16} color={categoryColors['娱乐']} />, description: '设计创作、艺术相关类', category: '娱乐' },
    
    // 工具类
    { value: 'Calculator', label: '计算工具', icon: <Calculator size={16} color={categoryColors['工具']} />, description: '数学计算、数据处理类', category: '工具' },
    { value: 'Globe', label: '全球网络', icon: <Globe size={16} color={categoryColors['工具']} />, description: '网络服务、全球化应用类', category: '工具' },
    { value: 'Zap', label: '高速处理', icon: <Zap size={16} color={categoryColors['工具']} />, description: '快速响应、高效处理类', category: '工具' }
  ];

  // 根据图标名称渲染图标组件（带颜色）
  const renderIcon = (iconName: string, size: number = 18, color?: string) => {
    // 如果没有指定颜色，根据图标名称找到对应的分类颜色
    let iconColor = color;
    if (!iconColor) {
      const iconOption = availableIcons.find(icon => icon.value === iconName);
      if (iconOption) {
        iconColor = categoryColors[iconOption.category as keyof typeof categoryColors];
      }
    }
    
    const iconMap: { [key: string]: React.ReactNode } = {
      // Lucide React 图标（带颜色）
      'Bot': <Bot size={size} color={iconColor} />,
      'Brain': <Brain size={size} color={iconColor} />,
      'Sparkles': <Sparkles size={size} color={iconColor} />,
      'Settings': <Settings size={size} color={iconColor} />,
      'Database': <Database size={size} color={iconColor} />,
      'Code': <Code size={size} color={iconColor} />,
      'Shield': <Shield size={size} color={iconColor} />,
      'Search': <Search size={size} color={iconColor} />,
      'TrendingUp': <TrendingUp size={size} color={iconColor} />,
      'User': <User size={size} color={iconColor} />,
      'Headphones': <Headphones size={size} color={iconColor} />,
      'MessageCircle': <MessageCircle size={size} color={iconColor} />,
      'Heart': <Heart size={size} color={iconColor} />,
      'Book': <Book size={size} color={iconColor} />,
      'FileText': <FileText size={size} color={iconColor} />,
      'Lightbulb': <Lightbulb size={size} color={iconColor} />,
      'Target': <Target size={size} color={iconColor} />,
      'Music': <Music size={size} color={iconColor} />,
      'Gamepad2': <Gamepad2 size={size} color={iconColor} />,
      'Camera': <Camera size={size} color={iconColor} />,
      'Palette': <Palette size={size} color={iconColor} />,
      'Calculator': <Calculator size={size} color={iconColor} />,
      'Globe': <Globe size={size} color={iconColor} />,
      'Zap': <Zap size={size} color={iconColor} />,
      
      // 向后兼容 Ant Design 图标
      'RobotOutlined': <RobotOutlined />,
      'SettingOutlined': <SettingOutlined />,
      'UserOutlined': <UserOutlined />,
      'DatabaseOutlined': <DatabaseOutlined />,
      'BulbOutlined': <BulbOutlined />,
      'HeartOutlined': <HeartOutlined />,
      'BookOutlined': <BookOutlined />,
      'CodeOutlined': <CodeOutlined />,
      'CustomerServiceOutlined': <CustomerServiceOutlined />
    };
    return iconMap[iconName] || <Bot size={size} color={iconColor} />;
  };

  // 系统工具定义
  const systemTools = [
    { 
      name: 'get_sop_content', 
      category: 'sop', 
      description: '获取指定SOP的完整内容。用于查看标准操作程序的详细步骤和说明。\n\nArgs:\n    sop_id: SOP的唯一标识符\n\nReturns:\n    包含SOP完整内容的JSON字符串，包括标题、步骤、注意事项等'
    },
    { 
      name: 'get_sop_detail', 
      category: 'sop', 
      description: '获取SOP的详细信息和元数据。用于了解SOP的基本信息、分类和适用场景。\n\nArgs:\n    sop_id: SOP的唯一标识符\n\nReturns:\n    包含SOP详细信息的JSON字符串，包括创建时间、更新时间、分类、严重级别等'
    },
    { 
      name: 'list_sops', 
      category: 'sop', 
      description: '列出所有可用的SOP清单。用于浏览和发现相关的标准操作程序。\n\nArgs:\n    category: 可选，SOP分类筛选\n    limit: 可选，返回数量限制，默认为50\n\nReturns:\n    包含SOP列表的JSON字符串，每个条目包含ID、标题、分类等基本信息'
    },
    { 
      name: 'search_sops', 
      category: 'sop', 
      description: '搜索相关的SOP文档。用于根据关键词快速找到相关的操作程序。\n\nArgs:\n    query: 搜索关键词\n    category: 可选，限定搜索的分类\n\nReturns:\n    包含匹配SOP列表的JSON字符串，按相关性排序'
    },
    { 
      name: 'get_current_time', 
      category: 'general', 
      description: '获取当前的系统时间。用于记录操作时间点或进行时间相关的判断。\n\nArgs:\n    format: 可选，时间格式，默认为ISO 8601格式\n    timezone: 可选，时区，默认为系统时区\n\nReturns:\n    格式化的当前时间字符串'
    }
  ];

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
      if (line.trim().startsWith('Returns:')) {
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
            title: tool.name,
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
        disabled: server.status !== 'connected',
        children: (server.tools || []).map(tool => {
          const { summary, args, returns } = formatToolDescription(tool.description);
          
          return {
            title: tool.name,
            key: `tool-${tool.name}`,
            disabled: server.status !== 'connected',
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
      .filter(key => key.startsWith('system-') && !key.endsWith('-detail'))
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
        setEditSystemTools(['get_current_time']);
        setEditMCPTools([]);
        setEditSystemCheckedKeys(['system-get_current_time']);
        setEditCheckedKeys([]);
        setEditSystemExpandedKeys(['system-root']);
        setEditExpandedKeys([]);
        
        form.setFieldsValue({
          agent_capabilities: [],
          agent_icon: 'Bot',
          available_models: [availableModels.length > 0 ? availableModels[0].model : 'gpt-4'],
          temperature: 0.7,
          max_tokens: 2000,
          top_p: 1.0,
          frequency_penalty: 0.0,
          presence_penalty: 0.0,
          system_prompt: '',
          user_prompt_template: '',
          assistant_prompt_template: ''
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
      const fullAgent = await agentApi.getAgent(agent.agent_id);
      
      if (fullAgent) {
        // 直接设置表单值，不使用setTimeout避免覆盖用户正在编辑的内容
        form.setFieldsValue({
          agent_id: fullAgent.agent_id,
          agent_name: fullAgent.agent_name,
          agent_description: fullAgent.agent_description,
          agent_capabilities: fullAgent.agent_capabilities,
          agent_icon: fullAgent.agent_icon || 'Bot',
          available_models: fullAgent.llm_info?.available_models || [availableModels.length > 0 ? availableModels[0].model : 'gpt-4'],
          temperature: fullAgent.llm_info?.temperature || 0.7,
          max_tokens: fullAgent.llm_info?.max_tokens || 2000,
          top_p: fullAgent.llm_info?.top_p || 1.0,
          frequency_penalty: fullAgent.llm_info?.frequency_penalty || 0.0,
          presence_penalty: fullAgent.llm_info?.presence_penalty || 0.0,
          system_prompt: fullAgent.prompt_info?.system_prompt || `你是${fullAgent.agent_name}，请根据用户需求提供专业的帮助。`,
          user_prompt_template: fullAgent.prompt_info?.user_prompt_template || '',
          assistant_prompt_template: fullAgent.prompt_info?.assistant_prompt_template || ''
        });
      }
    } catch (error) {
      console.error('获取智能体详细配置失败:', error);
    }
  };

  const handleSubmit = async (values: any) => {
    // 构建工具配置
    const toolsConfig = {
      system_tools: editSystemTools,
      mcp_tools: mcpServers
        .filter(server => server.status === 'connected')
        .map(server => ({
          server_id: server.id,
          server_name: server.name,
          tools: (server.tools || [])
            .filter(tool => editMCPTools.includes(tool.name))
            .map(tool => tool.name)
        }))
        .filter(server => server.tools.length > 0)
    };

    // 构建LLM配置
    const availableModelsList = values.available_models || ['gpt-4'];
    const llmConfig = {
      available_models: availableModelsList,
      model_name: availableModelsList[0],
      temperature: values.temperature || 0.7,
      max_tokens: values.max_tokens || 2000,
      top_p: values.top_p || 1.0,
      frequency_penalty: values.frequency_penalty || 0.0,
      presence_penalty: values.presence_penalty || 0.0
    };

    // 构建提示词配置
    const promptConfig = {
      system_prompt: values.system_prompt || `你是${values.agent_name}，请根据用户需求提供专业的帮助。`,
      user_prompt_template: values.user_prompt_template || '',
      assistant_prompt_template: values.assistant_prompt_template || ''
    };

    const formData = {
      ...values,
      tools_info: toolsConfig,
      llm_info: llmConfig,
      prompt_info: promptConfig
    };

    await onSave(formData);
  };

  const handleCancel = () => {
    form.resetFields();
    setEditSystemTools([]);
    setEditMCPTools([]);
    setEditSystemCheckedKeys([]);
    setEditCheckedKeys([]);
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
              label="描述"
              name="agent_description"
            >
              <TextArea 
                rows={3}
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
                          
                          const allConnectedMCPKeys: string[] = [];
                          const allMCPToolNames: string[] = [];
                          mcpServers
                            .filter(s => s.status === 'connected')
                            .forEach(server => {
                              allConnectedMCPKeys.push(`server-${server.id}`);
                              (server.tools || []).forEach(tool => {
                                allConnectedMCPKeys.push(`tool-${tool.name}`);
                                allMCPToolNames.push(tool.name);
                              });
                            });
                          setEditCheckedKeys(allConnectedMCPKeys);
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
                        可用服务器: {mcpServers.filter(s => s.status === 'connected').length}/{mcpServers.length}
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
            <Row gutter={16}>
              <Col span={24}>
                <Form.Item
                  label="可用模型"
                  name="available_models"
                  rules={[{ required: true, message: '请至少选择一个模型' }]}
                >
                  <Select 
                    mode="multiple" 
                    placeholder="选择智能体可以使用的模型" 
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
                        <Option value="gpt-4">GPT-4 (备用)</Option>
                        <Option value="gpt-3.5-turbo">GPT-3.5 Turbo (备用)</Option>
                      </>
                    )}
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label={
                    <Tooltip title="模型单次生成的最大字符数量，影响回答长度">
                      最大Token数
                    </Tooltip>
                  }
                  name="max_tokens"
                  rules={[{ required: true, message: '请输入最大Token数' }]}
                >
                  <Input type="number" placeholder="2000" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label={
                    <Tooltip title="控制输出的随机性和创造性，0-2之间，值越高越随机">
                      温度
                    </Tooltip>
                  }
                  name="temperature"
                  rules={[{ required: true, message: '请输入温度值' }]}
                >
                  <Input type="number" min={0} max={2} step={0.1} placeholder="0.7" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label={
                    <Tooltip title="核采样参数，控制候选词汇范围，0-1之间，值越小越保守">
                      Top P
                    </Tooltip>
                  }
                  name="top_p"
                >
                  <Input type="number" min={0} max={1} step={0.1} placeholder="1.0" />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label={
                    <Tooltip title="降低重复词汇出现频率，-2到2之间，正值减少重复">
                      频率惩罚
                    </Tooltip>
                  }
                  name="frequency_penalty"
                >
                  <Input type="number" min={-2} max={2} step={0.1} placeholder="0.0" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label={
                    <Tooltip title="鼓励讨论新话题，-2到2之间，正值增加新内容倾向">
                      存在惩罚
                    </Tooltip>
                  }
                  name="presence_penalty"
                >
                  <Input type="number" min={-2} max={2} step={0.1} placeholder="0.0" />
                </Form.Item>
              </Col>
            </Row>
          </TabPane>

          {/* 提示词配置 */}
          <TabPane tab="提示词配置" key="prompt">
            <Form.Item
              label="系统提示词"
              name="system_prompt"
              rules={[{ required: true, message: '请输入系统提示词' }]}
            >
              <TextArea 
                rows={4}
                placeholder="定义智能体的角色、行为准则和回答风格..."
                maxLength={2000}
                showCount
              />
            </Form.Item>

            <Form.Item
              label="用户提示词模板"
              name="user_prompt_template"
              extra="可选，用于格式化用户输入"
            >
              <TextArea 
                rows={3}
                placeholder="例如: 用户问题：{user_input}\n请详细回答上述问题。"
                maxLength={1000}
                showCount
              />
            </Form.Item>

            <Form.Item
              label="助手回复模板"
              name="assistant_prompt_template"
              extra="可选，用于格式化助手回复"
            >
              <TextArea 
                rows={3}
                placeholder="例如: 基于以上分析，我的建议是：{assistant_response}"
                maxLength={1000}
                showCount
              />
            </Form.Item>
          </TabPane>

          {/* 定时任务配置 */}
          <TabPane tab={<span><ClockCircleOutlined />定时任务</span>} key="scheduled-tasks">
            <ScheduledTaskManager 
              agentId={agent?.agent_id || ''}
            />
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