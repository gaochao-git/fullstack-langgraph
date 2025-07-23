import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  Select, 
  Space, 
  Tag, 
  App, 
  Row,
  Col,
  Switch,
  Checkbox,
  Modal,
  Descriptions,
  Badge,
  Divider,
  Alert,
  Progress,
  Statistic,
  List,
  Avatar,
  Tabs,
  Collapse,
  Tree
} from 'antd';
import { 
  RobotOutlined,
  SettingOutlined,
  EyeOutlined,
  ToolOutlined,
  ApiOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  LinkOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  CloudOutlined,
  GlobalOutlined,
  CaretRightOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { DataNode } from 'antd/es/tree';
import { agentApi, type Agent, type MCPServer, type MCPTool, type UpdateMCPConfigRequest } from '../services/agentApi';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

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
  const [mcpConfigModal, setMCPConfigModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<LocalAgent | null>(null);
  const [tempMCPConfig, setTempMCPConfig] = useState<{enabledServers: string[], selectedTools: string[]}>({
    enabledServers: [],
    selectedTools: []
  });
  const [checkedKeys, setCheckedKeys] = useState<string[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [selectedSystemTools, setSelectedSystemTools] = useState<string[]>([]);
  const [systemCheckedKeys, setSystemCheckedKeys] = useState<string[]>([]);
  const [systemExpandedKeys, setSystemExpandedKeys] = useState<string[]>([]);
  
  const { message } = App.useApp();

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
            title: `${tool.name} [${tool.category}]`,
            key: `system-${tool.name}`,
            children: [
              {
                title: (
                  <div className="space-y-3 p-2">
                    <div>
                      <div className="text-sm font-medium text-gray-800 mb-2">工具描述</div>
                      <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                        {summary}
                      </div>
                    </div>
                    
                    {args && (
                      <div>
                        <div className="text-sm font-medium text-gray-800 mb-2">参数说明</div>
                        <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs">{args}</pre>
                        </div>
                      </div>
                    )}
                    
                    {returns && (
                      <div>
                        <div className="text-sm font-medium text-gray-800 mb-2">返回值说明</div>
                        <div className="text-sm text-gray-600 bg-green-50 p-3 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs">{returns}</pre>
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

  // 处理系统工具选择
  const handleSystemTreeCheck = (checked: string[] | { checked: string[]; halfChecked: string[] }) => {
    const checkedKeyArray = Array.isArray(checked) ? checked : checked.checked;
    setSystemCheckedKeys(checkedKeyArray);
    
    // 从选中的keys中提取工具名
    const selectedTools = checkedKeyArray
      .filter(key => key.startsWith('system-') && !key.endsWith('-detail'))
      .map(key => key.replace('system-', ''));
    
    setSelectedSystemTools(selectedTools);
  };

  // 处理系统工具复选框切换
  const handleSystemToolToggle = (toolName: string, checked: boolean) => {
    if (checked) {
      setSelectedSystemTools(prev => [...prev, toolName]);
    } else {
      setSelectedSystemTools(prev => prev.filter(name => name !== toolName));
    }
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
        title: `${server.name} (${server.status}) - ${server.tools?.length || 0}工具`,
        key: `server-${server.id}`,
        disabled: server.status !== 'connected',
        children: (server.tools || []).map(tool => {
          const { summary, args, returns } = formatToolDescription(tool.description);
          
          return {
            title: `${tool.name} [${tool.category}]`,
            key: `tool-${tool.name}`,
            disabled: server.status !== 'connected',
            isLeaf: true,
            children: [
              {
                title: (
                  <div className="space-y-3 p-2">
                    <div>
                      <div className="text-sm font-medium text-gray-800 mb-2">工具描述</div>
                      <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                        {tool.description}
                      </div>
                    </div>
                    
                    {args && (
                      <div>
                        <div className="text-sm font-medium text-gray-800 mb-2">参数说明</div>
                        <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs">{args}</pre>
                        </div>
                      </div>
                    )}
                    
                    {returns && (
                      <div>
                        <div className="text-sm font-medium text-gray-800 mb-2">返回值说明</div>
                        <div className="text-sm text-gray-600 bg-green-50 p-3 rounded">
                          <pre className="whitespace-pre-wrap font-mono text-xs">{returns}</pre>
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

  // 配置MCP工具
  const handleConfigureMCP = (agent: LocalAgent) => {
    setSelectedAgent(agent);
    setTempMCPConfig({
      enabledServers: [...agent.mcpConfig.enabledServers],
      selectedTools: [...agent.mcpConfig.selectedTools]
    });
    
    // 初始化系统工具选择状态 - 分离系统工具和MCP工具
    const mcpToolNames = mcpServers.flatMap(s => s.tools.map(t => t.name));
    const systemToolNames = agent.mcpConfig.selectedTools.filter(tool => 
      systemTools.some(st => st.name === tool)
    );
    const mcpSelectedTools = agent.mcpConfig.selectedTools.filter(tool => 
      mcpToolNames.includes(tool)
    );
    
    setSelectedSystemTools(systemToolNames);
    
    // 初始化系统工具树状态
    const systemInitialCheckedKeys = systemToolNames.map(name => `system-${name}`);
    setSystemCheckedKeys(systemInitialCheckedKeys);
    setSystemExpandedKeys(['system-root']); // 默认展开根节点
    
    // 初始化MCP工具树形选择状态
    const initialCheckedKeys: string[] = [];
    
    // 添加已选择的服务器
    agent.mcpConfig.enabledServers.forEach(serverId => {
      initialCheckedKeys.push(`server-${serverId}`);
    });
    
    // 添加已选择的MCP工具
    mcpSelectedTools.forEach(toolName => {
      initialCheckedKeys.push(`tool-${toolName}`);
    });
    
    console.log('初始化系统工具:', systemToolNames);
    console.log('初始化MCP工具:', mcpSelectedTools);
    
    setCheckedKeys(initialCheckedKeys);
    
    // 默认展开已启用的服务器
    setExpandedKeys(agent.mcpConfig.enabledServers.map(id => `server-${id}`));
    
    setMCPConfigModal(true);
  };

  // 处理树形选择变化
  const handleTreeCheck = (checked: string[] | { checked: string[]; halfChecked: string[] }) => {
    const checkedKeyArray = Array.isArray(checked) ? checked : checked.checked;
    setCheckedKeys(checkedKeyArray);
    
    // 从选中的keys中提取服务器和工具
    const enabledServers: string[] = [];
    const selectedTools: string[] = [];
    
    checkedKeyArray.forEach(key => {
      if (key.startsWith('server-')) {
        const serverId = key.replace('server-', '');
        enabledServers.push(serverId);
      } else if (key.startsWith('tool-')) {
        const toolName = key.replace('tool-', '');
        selectedTools.push(toolName);
      }
    });
    
    setTempMCPConfig({
      enabledServers,
      selectedTools
    });
  };

  // 保存MCP配置
  const handleSaveMCPConfig = async () => {
    if (selectedAgent) {
      try {
        // 合并系统工具和MCP工具
        const allSelectedTools = [...selectedSystemTools, ...tempMCPConfig.selectedTools];
        
        await agentApi.updateAgentMCPConfig(selectedAgent.id, {
          enabled_servers: tempMCPConfig.enabledServers,
          selected_tools: allSelectedTools
        });
        
        setAgents(prevAgents =>
          prevAgents.map(agent => {
            if (agent.id === selectedAgent.id) {
              return {
                ...agent,
                mcpConfig: {
                  ...agent.mcpConfig,
                  enabledServers: tempMCPConfig.enabledServers,
                  selectedTools: allSelectedTools
                }
              };
            }
            return agent;
          })
        );
        setMCPConfigModal(false);
        message.success('工具配置已保存');
      } catch (error) {
        console.error('保存工具配置失败:', error);
        message.error('保存工具配置失败，请重试');
      }
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
                    key="mcp"
                    type="text" 
                    icon={<ApiOutlined />}
                    onClick={() => handleConfigureMCP(agent)}
                  >
                    MCP配置
                  </Button>,
                  <Button 
                    key="setting"
                    type="text" 
                    icon={<SettingOutlined />}
                    onClick={() => message.info('智能体配置功能开发中...')}
                  >
                    设置
                  </Button>
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

      {/* MCP工具配置模态框 */}
      <Modal
        title={
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ApiOutlined className="mr-2" />
              为 {selectedAgent?.displayName} 配置MCP工具
            </div>
            <div className="text-sm text-gray-500">
              已选: {tempMCPConfig.enabledServers.length}服务器 / {selectedSystemTools.length + tempMCPConfig.selectedTools.length}工具
            </div>
          </div>
        }
        open={mcpConfigModal}
        onCancel={() => setMCPConfigModal(false)}
        onOk={handleSaveMCPConfig}
        width={800}
        okText="保存配置"
        cancelText="取消"
      >
        {selectedAgent && (
          <div>
            {/* 顶部操作栏 */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <Row gutter={16} align="middle">
                <Col span={12}>
                  <Space>
                    <Button 
                      size="small"
                      onClick={() => {
                        // 全选系统工具
                        const systemToolNames = systemTools.map(t => t.name);
                        setSelectedSystemTools(systemToolNames);
                        setSystemCheckedKeys(systemToolNames.map(name => `system-${name}`));
                        
                        // 全选MCP工具
                        const allConnectedKeys: string[] = [];
                        mcpServers
                          .filter(s => s.status === 'connected')
                          .forEach(server => {
                            allConnectedKeys.push(`server-${server.id}`);
                            server.tools.forEach(tool => {
                              allConnectedKeys.push(`tool-${tool.name}`);
                            });
                          });
                        setCheckedKeys(allConnectedKeys);
                        handleTreeCheck(allConnectedKeys);
                      }}
                    >
                      全选可用
                    </Button>
                    <Button 
                      size="small"
                      onClick={() => {
                        // 清空系统工具选择
                        setSelectedSystemTools([]);
                        setSystemCheckedKeys([]);
                        
                        // 清空MCP工具选择
                        setCheckedKeys([]);
                        setTempMCPConfig({ enabledServers: [], selectedTools: [] });
                      }}
                    >
                      清空选择
                    </Button>
                    <Button 
                      size="small"
                      onClick={() => {
                        // 展开系统工具树
                        setSystemExpandedKeys(['system-root']);
                        // 展开MCP工具树
                        setExpandedKeys(mcpServers.map(s => `server-${s.id}`));
                      }}
                    >
                      展开全部
                    </Button>
                    <Button 
                      size="small"
                      onClick={() => {
                        // 收起系统工具树
                        setSystemExpandedKeys([]);
                        // 收起MCP工具树
                        setExpandedKeys([]);
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
                      总工具数: {mcpServers.reduce((sum, s) => sum + s.tools.length, 0)}
                    </span>
                  </Space>
                </Col>
              </Row>
            </div>

            {/* 系统工具选择 */}
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-800 mb-2 flex items-center justify-between">
                <div className="flex items-center">
                  <ToolOutlined className="mr-2" />
                  系统工具 (可选择)
                </div>
                <div className="text-xs text-gray-500">
                  已选: {selectedSystemTools.length}/{systemTools.length}
                </div>
              </div>
              <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
                <Tree
                  checkable
                  checkedKeys={systemCheckedKeys}
                  expandedKeys={systemExpandedKeys}
                  onCheck={handleSystemTreeCheck}
                  onExpand={setSystemExpandedKeys}
                  treeData={buildSystemTreeData()}
                  showLine
                  showIcon={false}
                  className="w-full"
                />
              </div>
            </div>

            {/* MCP工具选择器 */}
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-800 mb-2 flex items-center justify-between">
                <div className="flex items-center">
                  <ApiOutlined className="mr-2" />
                  MCP工具 (可选择)
                </div>
                <div className="text-xs text-gray-500">
                  已选: {tempMCPConfig.enabledServers.length}服务器 / {tempMCPConfig.selectedTools.length}工具
                </div>
              </div>
              <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
                {mcpServers.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <div>加载中...</div>
                  </div>
                ) : (
                  <Tree
                    checkable
                    checkedKeys={checkedKeys}
                    expandedKeys={expandedKeys}
                    onCheck={handleTreeCheck}
                    onExpand={setExpandedKeys}
                    treeData={buildTreeData()}
                    showLine
                    showIcon={false}
                    className="w-full"
                    height={300}
                  />
                )}
              </div>
            </div>


          </div>
        )}
      </Modal>
    </div>
  );
};

export default AgentManagement;