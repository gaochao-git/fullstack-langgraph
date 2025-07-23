import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Input, 
  Select, 
  Space, 
  Tag, 
  App, 
  Row,
  Col,
  Switch,
  Modal,
  Descriptions,
  Badge,
  Divider,
  Statistic,
  Avatar,
  Tabs,
  Tree,
  Form
} from 'antd';
import { 
  RobotOutlined,
  SettingOutlined,
  EyeOutlined,
  ToolOutlined,
  ApiOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  CloudOutlined,
  GlobalOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import type { DataNode, Key } from 'antd/es/tree';
import { agentApi, type Agent, type MCPServer, type MCPTool, type CreateAgentRequest, type UpdateAgentRequest } from '../services/agentApi';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

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

// 本地状态类型（兼容旧的驼峰命名）
interface LocalAgent extends Omit<Agent, 'display_name' | 'last_used' | 'total_runs' | 'success_rate' | 'avg_response_time' | 'mcp_config'> {
  displayName: string;
  lastUsed?: string;
  totalRuns: number;
  successRate: number;
  avgResponseTime: number;
  is_builtin: boolean;
  mcpConfig: {
    enabledServers: string[];
    selectedTools: string[];
    totalTools: number;
  };
}

interface LocalMCPTool extends Omit<MCPTool, 'server_id' | 'server_name'> {
  serverId: string;
  serverName: string;
}

interface LocalMCPServer extends MCPServer {
  status: 'connected' | 'disconnected' | 'error';
  tools: LocalMCPTool[];
}

// 数据转换工具函数
const transformAgentToLocal = (agent: Agent): LocalAgent => ({
  ...agent,
  displayName: agent.display_name,
  lastUsed: agent.last_used,
  totalRuns: agent.total_runs,
  successRate: agent.success_rate,
  avgResponseTime: agent.avg_response_time,
  mcpConfig: {
    enabledServers: agent.mcp_config.enabled_servers,
    selectedTools: agent.mcp_config.selected_tools,
    totalTools: agent.mcp_config.total_tools
  }
});

const transformMCPServerToLocal = (server: MCPServer): LocalMCPServer => ({
  ...server,
  status: server.status as 'connected' | 'disconnected' | 'error',
  tools: server.tools.map(tool => ({
    ...tool,
    serverId: tool.server_id,
    serverName: tool.server_name
  }))
});

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<LocalAgent[]>([]);
  const [mcpServers, setMcpServers] = useState<LocalMCPServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  // 模态框状态
  const [agentDetailModal, setAgentDetailModal] = useState(false);
  const [agentEditModal, setAgentEditModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<LocalAgent | null>(null);
  const [editingAgent, setEditingAgent] = useState<LocalAgent | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  
  // 表单相关状态
  const [editForm] = Form.useForm();
  const [formSubmitting, setFormSubmitting] = useState(false);
  
  // 新建/编辑时的工具选择状态
  const [editSystemTools, setEditSystemTools] = useState<string[]>([]);
  const [editMCPTools, setEditMCPTools] = useState<string[]>([]);
  const [editSystemCheckedKeys, setEditSystemCheckedKeys] = useState<string[]>([]);
  const [editSystemExpandedKeys, setEditSystemExpandedKeys] = useState<string[]>(['system-root']);
  const [editCheckedKeys, setEditCheckedKeys] = useState<string[]>([]);
  const [editExpandedKeys, setEditExpandedKeys] = useState<string[]>([]);
  
  const { message, modal } = App.useApp();

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


  // 构建树形数据
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
    
    console.log('构建树形数据，服务器数量:', mcpServers.length);
    
    return mcpServers.map(server => {
      console.log('处理服务器:', server.name, '工具数量:', server.tools?.length);
      
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

  // 数据加载
  const loadData = async () => {
    setLoading(true);
    try {
      const [agentsData, mcpServersData] = await Promise.all([
        agentApi.getAgents(),
        agentApi.getMCPServers()
      ]);
      
      setAgents(agentsData.map(transformAgentToLocal));
      setMcpServers(mcpServersData.map(transformMCPServerToLocal));
    } catch (error) {
      console.error('加载数据失败:', error);
      message.error('加载数据失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadData();
  }, []);

  // 获取状态颜色
  const getStatusColor = (status: string): string => {
    const colors = {
      running: 'green',
      stopped: 'orange',
      error: 'red'
    };
    return colors[status];
  };

  // 获取状态文本
  const getStatusText = (status: string): string => {
    const texts = {
      running: '运行中',
      stopped: '已停止',
      error: '错误'
    };
    return texts[status];
  };

  // 获取工具类别图标
  const getCategoryIcon = (category: string) => {
    const icons: Record<string, React.ReactNode> = {
      database: <DatabaseOutlined />,
      monitoring: <MonitorOutlined />,
      analysis: <EyeOutlined />,
      network: <GlobalOutlined />,
      cloud: <CloudOutlined />,
      sop: <SettingOutlined />,
      general: <ToolOutlined />
    };
    return icons[category] || <ToolOutlined />;
  };

  // 获取工具类别颜色
  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      database: 'blue',
      monitoring: 'green',
      analysis: 'purple',
      network: 'orange',
      cloud: 'cyan',
      sop: 'gold',
      general: 'gray'
    };
    return colors[category] || 'default';
  };

  // 过滤智能体
  const filteredAgents = agents.filter(agent => {
    const matchSearch = !searchText || 
      agent.displayName.toLowerCase().includes(searchText.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchText.toLowerCase());
    const matchStatus = !statusFilter || agent.status === statusFilter;
    return matchSearch && matchStatus;
  });

  // 切换智能体启用状态
  const toggleAgentEnabled = async (agentId: string) => {
    try {
      await agentApi.toggleAgentStatus(agentId);
      
      setAgents(prevAgents =>
        prevAgents.map(agent => {
          if (agent.id === agentId) {
            const newEnabled = !agent.enabled;
            return { 
              ...agent, 
              enabled: newEnabled,
              status: newEnabled ? 'running' : 'stopped'
            };
          }
          return agent;
        })
      );
      message.success('智能体状态已更新');
    } catch (error) {
      console.error('切换智能体状态失败:', error);
      message.error('切换智能体状态失败，请重试');
    }
  };

  // 查看智能体详情
  const handleViewAgent = (agent: LocalAgent) => {
    setSelectedAgent(agent);
    setAgentDetailModal(true);
  };


  // 处理编辑表单的系统工具选择
  const handleEditSystemTreeCheck = (checked: Key[] | { checked: Key[]; halfChecked: Key[] }) => {
    const checkedKeyArray = Array.isArray(checked) ? checked : checked.checked;
    const stringKeys = checkedKeyArray.map(key => String(key));
    setEditSystemCheckedKeys(stringKeys);
    
    const selectedTools = stringKeys
      .filter(key => key.startsWith('system-') && !key.endsWith('-detail'))
      .map(key => key.replace('system-', ''));
    
    setEditSystemTools(selectedTools);
  };

  // 处理编辑表单的MCP工具选择
  const handleEditTreeCheck = (checked: Key[] | { checked: Key[]; halfChecked: Key[] }) => {
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

  // 新建智能体
  const handleCreateAgent = () => {
    setEditingAgent(null);
    setIsCreating(true);
    // 重置工具选择状态
    setEditSystemTools(['get_current_time']); // 默认给新智能体基础工具
    setEditMCPTools([]);
    setEditSystemCheckedKeys(['system-get_current_time']);
    setEditCheckedKeys([]);
    setEditSystemExpandedKeys(['system-root']);
    setEditExpandedKeys([]);
    setAgentEditModal(true);
  };

  // 编辑智能体
  const handleEditAgent = async (agent: LocalAgent) => {
    setEditingAgent(agent);
    setIsCreating(false);
    
    // 初始化工具选择状态
    const mcpToolNames = mcpServers.flatMap(s => s.tools.map(t => t.name));
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
    
    // 获取完整的智能体配置信息
    try {
      const agentDetails = await agentApi.getAgents();
      const fullAgent = agentDetails.find(a => a.id === agent.id);
      
      if (fullAgent) {
        // 设置表单初始值
        setTimeout(() => {
          editForm.setFieldsValue({
            agent_id: agent.id,
            agent_name: agent.displayName,
            description: agent.description,
            capabilities: agent.capabilities,
            // LLM配置 - 从智能体配置中获取，否则使用默认值
            model_name: (fullAgent as any).llm_info?.model_name || 'gpt-4',
            temperature: (fullAgent as any).llm_info?.temperature || 0.7,
            max_tokens: (fullAgent as any).llm_info?.max_tokens || 2000,
            top_p: (fullAgent as any).llm_info?.top_p || 1.0,
            frequency_penalty: (fullAgent as any).llm_info?.frequency_penalty || 0.0,
            presence_penalty: (fullAgent as any).llm_info?.presence_penalty || 0.0,
            // 提示词配置 - 从智能体配置中获取，否则使用默认值
            system_prompt: (fullAgent as any).prompt_info?.system_prompt || `你是${agent.displayName}，请根据用户需求提供专业的帮助。`,
            user_prompt_template: (fullAgent as any).prompt_info?.user_prompt_template || '',
            assistant_prompt_template: (fullAgent as any).prompt_info?.assistant_prompt_template || ''
          });
        }, 100); // 稍微延迟以确保模态框已经打开
      }
    } catch (error) {
      console.error('获取智能体详细配置失败:', error);
    }
    
    setAgentEditModal(true);
  };

  // 删除智能体
  const handleDeleteAgent = async (agent: LocalAgent) => {
    console.log('删除智能体被调用:', agent.id, 'is_builtin:', agent.is_builtin);
    
    if (agent.is_builtin) {
      message.warning('不能删除内置智能体');
      return;
    }

    Modal.confirm({
      title: '确认删除',
      content: `确定要删除智能体 "${agent.displayName}" 吗？此操作不可撤销。`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        console.log('开始删除智能体:', agent.id);
        try {
          await agentApi.deleteAgent(agent.id);
          setAgents(prevAgents => prevAgents.filter(a => a.id !== agent.id));
          message.success('智能体已删除');
          console.log('智能体删除成功:', agent.id);
        } catch (error) {
          console.error('删除智能体失败:', error);
          message.error('删除智能体失败，请重试');
        }
      }
    });
  };

  // 保存智能体（新建或编辑）
  const handleSaveAgent = async (values: any) => {
    setFormSubmitting(true);
    try {
      // 构建工具配置
      const toolsConfig = {
        system_tools: editSystemTools,
        mcp_tools: mcpServers
          .filter(server => server.status === 'connected')
          .map(server => ({
            server_id: server.id,
            server_name: server.name,
            tools: server.tools
              .filter(tool => editMCPTools.includes(tool.name))
              .map(tool => tool.name)
          }))
          .filter(server => server.tools.length > 0)
      };

      // 构建LLM配置
      const llmConfig = {
        model_name: values.model_name || 'gpt-4',
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

      if (isCreating) {
        // 新建智能体
        const newAgentData: CreateAgentRequest = {
          agent_id: values.agent_id,
          agent_name: values.agent_name,
          description: values.description || '',
          capabilities: values.capabilities || [],
          tools_info: toolsConfig,
          llm_info: llmConfig,
          prompt_info: promptConfig
        };

        const newAgent = await agentApi.createAgent(newAgentData);
        setAgents(prevAgents => [...prevAgents, transformAgentToLocal(newAgent)]);
        message.success('智能体创建成功');
      } else if (editingAgent) {
        // 编辑智能体
        const updateData: UpdateAgentRequest = {
          agent_name: values.agent_name,
          description: values.description,
          capabilities: values.capabilities,
          tools_info: toolsConfig,
          llm_info: llmConfig,
          prompt_info: promptConfig
        };

        const updatedAgent = await agentApi.updateAgent(editingAgent.id, updateData);
        setAgents(prevAgents =>
          prevAgents.map(agent => 
            agent.id === editingAgent.id ? transformAgentToLocal(updatedAgent) : agent
          )
        );
        message.success('智能体更新成功');
      }

      setAgentEditModal(false);
      editForm.resetFields();
      // 重置工具选择状态
      setEditSystemTools([]);
      setEditMCPTools([]);
      setEditSystemCheckedKeys([]);
      setEditCheckedKeys([]);
    } catch (error) {
      console.error('保存智能体失败:', error);
      message.error('保存智能体失败，请重试');
    } finally {
      setFormSubmitting(false);
    }
  };



  return (
    <div>

      {/* 智能体管理 */}
      <Card title="智能体管理">
        <div className="mb-4">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索智能体名称、描述"
                allowClear
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="状态筛选"
                allowClear
                style={{ width: '100%' }}
                value={statusFilter}
                onChange={setStatusFilter}
              >
                <Option value="running">运行中</Option>
                <Option value="stopped">已停止</Option>
                <Option value="error">错误</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={12}>
              <Space>
                <Button 
                  type="primary"
                  icon={<RobotOutlined />}
                  onClick={handleCreateAgent}
                >
                  新建智能体
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  loading={loading}
                  onClick={loadData}
                >
                  刷新
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {/* 智能体卡片列表 */}
        <Row gutter={[16, 16]}>
          {filteredAgents.map(agent => (
            <Col xs={24} lg={12} xl={8} key={agent.id}>
              <Card
                className="h-full"
                actions={[
                  <Button 
                    key="detail"
                    type="text" 
                    icon={<EyeOutlined />}
                    onClick={() => handleViewAgent(agent)}
                  >
                    详情
                  </Button>,
                  <Button 
                    key="edit"
                    type="text" 
                    icon={<SettingOutlined />}
                    onClick={() => handleEditAgent(agent)}
                  >
                    编辑
                  </Button>,
                  ...(!agent.is_builtin ? [
                    <Button 
                      key="delete"
                      type="text" 
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('删除按钮被点击:', agent.id);
                        handleDeleteAgent(agent);
                      }}
                    >
                      删除
                    </Button>
                  ] : [])
                ]}
              >
                <Card.Meta
                  avatar={null}
                  title={
                    <div className="flex items-center justify-between">
                      <div className="text-base font-medium text-gray-900">{agent.displayName}</div>
                      <Switch
                        size="small"
                        checked={agent.enabled}
                        onChange={() => toggleAgentEnabled(agent.id)}
                      />
                    </div>
                  }
                  description={
                    <div className="space-y-2 mt-1">
                      {/* 运行统计和MCP工具统计合并 */}
                      <div className="text-sm space-y-1">
                        <div><span className="text-gray-500">运行次数: </span><span className="font-semibold text-gray-800">{agent.totalRuns}</span></div>
                        <div className="flex flex-wrap gap-x-4">
                          <span><span className="text-gray-500">服务器: </span><span className="font-semibold text-gray-800">{agent.mcpConfig.enabledServers.length}</span></span>
                          <span><span className="text-gray-500">工具: </span><span className="font-semibold text-gray-800">{agent.mcpConfig.selectedTools.length}</span></span>
                        </div>
                      </div>

                      {/* 核心能力 */}
                      <div className="flex flex-wrap gap-1">
                        {agent.capabilities.slice(0, 3).map(capability => (
                          <Tag key={capability} size="small" color="blue" className="text-xs">{capability}</Tag>
                        ))}
                      </div>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
        </Row>

        {/* 空状态 */}
        {filteredAgents.length === 0 && (
          <div className="text-center py-8">
            <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
            <div className="mt-2 text-gray-500">暂无智能体</div>
          </div>
        )}
      </Card>

      {/* 智能体详情模态框 */}
      <Modal
        title="智能体详情"
        open={agentDetailModal}
        onCancel={() => setAgentDetailModal(false)}
        footer={null}
        width={900}
      >
        {selectedAgent && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="智能体名称" span={2}>
                <Space>
                  <Avatar 
                    icon={<RobotOutlined />} 
                    style={{ 
                      backgroundColor: selectedAgent.status === 'running' ? '#52c41a' : 
                                     selectedAgent.status === 'error' ? '#ff4d4f' : '#faad14'
                    }} 
                  />
                  {selectedAgent.displayName}
                  <Badge 
                    status={selectedAgent.status === 'running' ? 'success' : 
                           selectedAgent.status === 'error' ? 'error' : 'warning'} 
                    text={getStatusText(selectedAgent.status)}
                  />
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="标识符">{selectedAgent.name}</Descriptions.Item>
              <Descriptions.Item label="版本">{selectedAgent.version}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedAgent.description}
              </Descriptions.Item>
            </Descriptions>
            
            <Divider>运行统计</Divider>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Statistic title="总运行次数" value={selectedAgent.totalRuns} />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="成功率" 
                  value={selectedAgent.successRate} 
                  precision={1}
                  suffix="%" 
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic 
                  title="平均响应时间" 
                  value={selectedAgent.avgResponseTime} 
                  precision={1}
                  suffix="s" 
                />
              </Col>
              <Col span={6}>
                <Statistic title="最后使用时间" value={selectedAgent.lastUsed || '-'} />
              </Col>
            </Row>

            <Divider>核心能力</Divider>
            <Space wrap>
              {selectedAgent.capabilities.map(capability => (
                <Tag key={capability} color="blue">{capability}</Tag>
              ))}
            </Space>

            <Divider>MCP工具配置</Divider>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic title="启用服务器" value={selectedAgent.mcpConfig.enabledServers.length} />
              </Col>
              <Col span={8}>
                <Statistic title="选中工具" value={selectedAgent.mcpConfig.selectedTools.length} />
              </Col>
              <Col span={8}>
                <Statistic title="总可用工具" value={selectedAgent.mcpConfig.totalTools} />
              </Col>
            </Row>
            
            <div className="mt-4">
              <strong>当前工具:</strong>
              <div className="mt-2 space-y-1">
                {selectedAgent.mcpConfig.selectedTools.map(tool => {
                  const mcpTool = mcpServers.flatMap(s => s.tools).find(t => t.name === tool);
                  return mcpTool ? (
                    <Tag key={tool} color={getCategoryColor(mcpTool.category)}>
                      {getCategoryIcon(mcpTool.category)} {tool}
                    </Tag>
                  ) : (
                    <Tag key={tool}>{tool}</Tag>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </Modal>


      {/* 智能体编辑模态框 */}
      <Modal
        title={isCreating ? "新建智能体" : "编辑智能体"}
        open={agentEditModal}
        onCancel={() => {
          setAgentEditModal(false);
          editForm.resetFields();
          setEditSystemTools([]);
          setEditMCPTools([]);
          setEditSystemCheckedKeys([]);
          setEditCheckedKeys([]);
        }}
        width={900}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleSaveAgent}
          initialValues={editingAgent ? {
            agent_id: editingAgent.id,
            agent_name: editingAgent.displayName,
            description: editingAgent.description,
            capabilities: editingAgent.capabilities,
            // LLM配置默认值
            model_name: 'gpt-4',
            temperature: 0.7,
            max_tokens: 2000,
            top_p: 1.0,
            frequency_penalty: 0.0,
            presence_penalty: 0.0,
            // 提示词配置默认值
            system_prompt: `你是${editingAgent.displayName}，请根据用户需求提供专业的帮助。`,
            user_prompt_template: '',
            assistant_prompt_template: ''
          } : {
            capabilities: [],
            // LLM配置默认值
            model_name: 'gpt-4',
            temperature: 0.7,
            max_tokens: 2000,
            top_p: 1.0,
            frequency_penalty: 0.0,
            presence_penalty: 0.0,
            // 提示词配置默认值
            system_prompt: '',
            user_prompt_template: '',
            assistant_prompt_template: ''
          }}
        >
          <Tabs defaultActiveKey="basic" type="card">
            {/* 基本信息 */}
            <TabPane tab="基本信息" key="basic">
              {isCreating && (
                <Form.Item
                  label="智能体ID"
                  name="agent_id"
                  rules={[
                    { required: true, message: '请输入智能体ID' },
                    { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '智能体ID必须以字母开头，只能包含字母、数字和下划线' }
                  ]}
                >
                  <Input placeholder="例如: my_custom_agent" />
                </Form.Item>
              )}

              <Form.Item
                label="智能体名称"
                name="agent_name"
                rules={[{ required: true, message: '请输入智能体名称' }]}
              >
                <Input placeholder="例如: 我的自定义智能体" />
              </Form.Item>

              <Form.Item
                label="描述"
                name="description"
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
                name="capabilities"
              >
                <Select
                  mode="tags"
                  placeholder="添加智能体的核心能力标签，按回车确认"
                  style={{ width: '100%' }}
                  tokenSeparators={[',']}
                />
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
                            // 全选系统工具
                            const allSystemToolNames = systemTools.map(t => t.name);
                            setEditSystemTools(allSystemToolNames);
                            setEditSystemCheckedKeys(allSystemToolNames.map(name => `system-${name}`));
                            
                            // 全选MCP工具
                            const allConnectedMCPKeys: string[] = [];
                            const allMCPToolNames: string[] = [];
                            mcpServers
                              .filter(s => s.status === 'connected')
                              .forEach(server => {
                                allConnectedMCPKeys.push(`server-${server.id}`);
                                server.tools.forEach(tool => {
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
                            // 清空系统工具选择
                            setEditSystemTools([]);
                            setEditSystemCheckedKeys([]);
                            
                            // 清空MCP工具选择
                            setEditCheckedKeys([]);
                            setEditMCPTools([]);
                          }}
                        >
                          清空选择
                        </Button>
                        <Button 
                          size="small"
                          onClick={() => {
                            // 展开系统工具树
                            setEditSystemExpandedKeys(['system-root']);
                            // 展开MCP工具树
                            setEditExpandedKeys(mcpServers.map(s => `server-${s.id}`));
                          }}
                        >
                          展开全部
                        </Button>
                        <Button 
                          size="small"
                          onClick={() => {
                            // 收起系统工具树
                            setEditSystemExpandedKeys([]);
                            // 收起MCP工具树
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
                          总工具数: {systemTools.length + mcpServers.reduce((sum, s) => sum + s.tools.length, 0)}
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
                <Col span={12}>
                  <Form.Item
                    label="模型名称"
                    name="model_name"
                    rules={[{ required: true, message: '请选择模型' }]}
                  >
                    <Select placeholder="选择模型">
                      <Option value="gpt-4">GPT-4</Option>
                      <Option value="gpt-4-turbo">GPT-4 Turbo</Option>
                      <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
                      <Option value="claude-3-opus">Claude-3 Opus</Option>
                      <Option value="claude-3-sonnet">Claude-3 Sonnet</Option>
                      <Option value="claude-3-haiku">Claude-3 Haiku</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="最大Token数"
                    name="max_tokens"
                    rules={[{ required: true, message: '请输入最大Token数' }]}
                  >
                    <Input type="number" min={100} max={8000} placeholder="2000" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="温度 (Temperature)"
                    name="temperature"
                    rules={[{ required: true, message: '请输入温度值' }]}
                  >
                    <Input type="number" min={0} max={2} step={0.1} placeholder="0.7" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="Top P"
                    name="top_p"
                  >
                    <Input type="number" min={0} max={1} step={0.1} placeholder="1.0" />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    label="频率惩罚 (Frequency Penalty)"
                    name="frequency_penalty"
                  >
                    <Input type="number" min={-2} max={2} step={0.1} placeholder="0.0" />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    label="存在惩罚 (Presence Penalty)"
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
          </Tabs>

          <div className="flex justify-end space-x-2 mt-4 pt-4 border-t">
            <Button 
              onClick={() => {
                setAgentEditModal(false);
                editForm.resetFields();
                setEditSystemTools([]);
                setEditMCPTools([]);
                setEditSystemCheckedKeys([]);
                setEditCheckedKeys([]);
              }}
            >
              取消
            </Button>
            <Button 
              type="primary" 
              htmlType="submit"
              loading={formSubmitting}
            >
              {isCreating ? '创建智能体' : '保存修改'}
            </Button>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default AgentManagement;