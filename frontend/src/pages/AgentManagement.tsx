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
  Tabs
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
  GlobalOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

// 智能体相关类型定义
interface Agent {
  id: string;
  name: string;
  displayName: string;
  description: string;
  status: 'running' | 'stopped' | 'error';
  enabled: boolean;
  version: string;
  lastUsed?: string;
  totalRuns: number;
  successRate: number;
  avgResponseTime: number;
  capabilities: string[];
  mcpConfig: {
    enabledServers: string[];
    selectedTools: string[];
    totalTools: number;
  };
}

interface MCPTool {
  name: string;
  description: string;
  enabled: boolean;
  category: string;
  serverId: string;
  serverName: string;
}

interface MCPServer {
  id: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  tools: MCPTool[];
}

// Mock数据
const mockAgents: Agent[] = [
  {
    id: 'diagnostic_agent',
    name: 'diagnostic_agent',
    displayName: '故障诊断智能体',
    description: '专业的系统故障诊断和问题分析智能体，能够快速定位和解决各类技术问题',
    status: 'running',
    enabled: true,
    version: '2.1.0',
    lastUsed: '2025-07-22 14:30:00',
    totalRuns: 1247,
    successRate: 94.5,
    avgResponseTime: 2.3,
    capabilities: ['数据库诊断', '系统监控', '日志分析', '性能优化'],
    mcpConfig: {
      enabledServers: ['server-1', 'server-2'],
      selectedTools: ['mysql_query', 'postgres_query', 'system_metrics', 'log_analyzer'],
      totalTools: 8
    }
  },
  {
    id: 'research_agent',
    name: 'research_agent',
    displayName: '研究分析智能体',
    description: '强大的信息研究和数据分析智能体，擅长网络搜索、数据整理和深度分析',
    status: 'running',
    enabled: true,
    version: '1.8.2',
    lastUsed: '2025-07-22 13:45:00',
    totalRuns: 892,
    successRate: 96.2,
    avgResponseTime: 3.1,
    capabilities: ['网络搜索', '数据分析', '信息整理', '报告生成'],
    mcpConfig: {
      enabledServers: ['server-2', 'server-4'],
      selectedTools: ['system_metrics', 'log_analyzer', 'aws_ec2_list'],
      totalTools: 5
    }
  },
  {
    id: 'security_agent',
    name: 'security_agent',
    displayName: '安全防护智能体',
    description: '专注于网络安全和系统防护的智能体，能够检测威胁和提供安全建议',
    status: 'stopped',
    enabled: false,
    version: '1.5.1',
    lastUsed: '2025-07-21 09:20:00',
    totalRuns: 456,
    successRate: 91.8,
    avgResponseTime: 1.9,
    capabilities: ['威胁检测', '漏洞扫描', '安全评估', '防护建议'],
    mcpConfig: {
      enabledServers: ['server-3'],
      selectedTools: ['port_scan', 'ping_test'],
      totalTools: 3
    }
  }
];

const mockMCPServers: MCPServer[] = [
  {
    id: 'server-1',
    name: 'Database Tools Server',
    status: 'connected',
    tools: [
      { name: 'mysql_query', description: 'Execute MySQL queries', enabled: false, category: 'database', serverId: 'server-1', serverName: 'Database Tools Server' },
      { name: 'postgres_query', description: 'Execute PostgreSQL queries', enabled: false, category: 'database', serverId: 'server-1', serverName: 'Database Tools Server' },
      { name: 'db_health_check', description: 'Check database health', enabled: false, category: 'monitoring', serverId: 'server-1', serverName: 'Database Tools Server' }
    ]
  },
  {
    id: 'server-2',
    name: 'System Monitor Server',
    status: 'connected',
    tools: [
      { name: 'system_metrics', description: 'Get system metrics', enabled: false, category: 'monitoring', serverId: 'server-2', serverName: 'System Monitor Server' },
      { name: 'log_analyzer', description: 'Analyze system logs', enabled: false, category: 'analysis', serverId: 'server-2', serverName: 'System Monitor Server' },
      { name: 'process_monitor', description: 'Monitor processes', enabled: false, category: 'monitoring', serverId: 'server-2', serverName: 'System Monitor Server' }
    ]
  },
  {
    id: 'server-3',
    name: 'Network Tools Server',
    status: 'error',
    tools: [
      { name: 'ping_test', description: 'Test network connectivity', enabled: false, category: 'network', serverId: 'server-3', serverName: 'Network Tools Server' },
      { name: 'port_scan', description: 'Scan open ports', enabled: false, category: 'network', serverId: 'server-3', serverName: 'Network Tools Server' },
      { name: 'traceroute', description: 'Trace network path', enabled: false, category: 'network', serverId: 'server-3', serverName: 'Network Tools Server' }
    ]
  },
  {
    id: 'server-4',
    name: 'Cloud API Server',
    status: 'connected',
    tools: [
      { name: 'aws_ec2_list', description: 'List AWS EC2 instances', enabled: false, category: 'cloud', serverId: 'server-4', serverName: 'Cloud API Server' },
      { name: 'azure_resource_monitor', description: 'Monitor Azure resources', enabled: false, category: 'cloud', serverId: 'server-4', serverName: 'Cloud API Server' }
    ]
  }
];

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>(mockAgents);
  const [mcpServers] = useState<MCPServer[]>(mockMCPServers);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  // 模态框状态
  const [agentDetailModal, setAgentDetailModal] = useState(false);
  const [mcpConfigModal, setMCPConfigModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [tempMCPConfig, setTempMCPConfig] = useState<{enabledServers: string[], selectedTools: string[]}>({
    enabledServers: [],
    selectedTools: []
  });
  
  const { message } = App.useApp();

  // 获取状态颜色
  const getStatusColor = (status: Agent['status']): string => {
    const colors = {
      running: 'green',
      stopped: 'orange',
      error: 'red'
    };
    return colors[status];
  };

  // 获取状态文本
  const getStatusText = (status: Agent['status']): string => {
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
      cloud: <CloudOutlined />
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
      cloud: 'cyan'
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
  const toggleAgentEnabled = (agentId: string) => {
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
  };

  // 查看智能体详情
  const handleViewAgent = (agent: Agent) => {
    setSelectedAgent(agent);
    setAgentDetailModal(true);
  };

  // 配置MCP工具
  const handleConfigureMCP = (agent: Agent) => {
    setSelectedAgent(agent);
    setTempMCPConfig({
      enabledServers: [...agent.mcpConfig.enabledServers],
      selectedTools: [...agent.mcpConfig.selectedTools]
    });
    setMCPConfigModal(true);
  };

  // 保存MCP配置
  const handleSaveMCPConfig = () => {
    if (selectedAgent) {
      setAgents(prevAgents =>
        prevAgents.map(agent => {
          if (agent.id === selectedAgent.id) {
            return {
              ...agent,
              mcpConfig: {
                ...agent.mcpConfig,
                enabledServers: tempMCPConfig.enabledServers,
                selectedTools: tempMCPConfig.selectedTools
              }
            };
          }
          return agent;
        })
      );
      setMCPConfigModal(false);
      message.success('MCP配置已保存');
    }
  };

  // 切换服务器选择
  const toggleServerSelection = (serverId: string, checked: boolean) => {
    if (checked) {
      setTempMCPConfig(prev => ({
        ...prev,
        enabledServers: [...prev.enabledServers, serverId]
      }));
    } else {
      setTempMCPConfig(prev => ({
        ...prev,
        enabledServers: prev.enabledServers.filter(id => id !== serverId),
        selectedTools: prev.selectedTools.filter(tool => {
          const server = mcpServers.find(s => s.id === serverId);
          return !server?.tools.some(t => t.name === tool);
        })
      }));
    }
  };

  // 切换工具选择
  const toggleToolSelection = (toolName: string, checked: boolean) => {
    if (checked) {
      setTempMCPConfig(prev => ({
        ...prev,
        selectedTools: [...prev.selectedTools, toolName]
      }));
    } else {
      setTempMCPConfig(prev => ({
        ...prev,
        selectedTools: prev.selectedTools.filter(tool => tool !== toolName)
      }));
    }
  };


  return (
    <div>
      {/* 概览统计 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总智能体"
              value={agents.length}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="运行中"
              value={agents.filter(a => a.status === 'running').length}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已停止"
              value={agents.filter(a => a.status === 'stopped').length}
              prefix={<PauseCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均成功率"
              value={agents.reduce((acc, agent) => acc + agent.successRate, 0) / agents.length}
              precision={1}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

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
                  onClick={() => message.success('数据已刷新')}
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
                  avatar={
                    <Avatar 
                      size={48}
                      icon={<RobotOutlined />} 
                      style={{ 
                        backgroundColor: agent.status === 'running' ? '#52c41a' : 
                                       agent.status === 'error' ? '#ff4d4f' : '#faad14'
                      }} 
                    />
                  }
                  title={
                    <Space direction="vertical" size="small">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{agent.displayName}</span>
                        <Switch
                          size="small"
                          checked={agent.enabled}
                          onChange={() => toggleAgentEnabled(agent.id)}
                        />
                      </div>
                      <div className="text-xs text-gray-500">{agent.name}</div>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      {/* 状态和版本 */}
                      <div className="flex justify-between items-center">
                        <Badge 
                          status={agent.status === 'running' ? 'success' : agent.status === 'error' ? 'error' : 'warning'} 
                          text={getStatusText(agent.status)}
                        />
                        <Tag color="blue" size="small">{agent.version}</Tag>
                      </div>
                      
                      {/* 运行统计 */}
                      <div className="space-y-1">
                        <div className="text-sm">
                          <span className="text-gray-600">运行次数: </span>
                          <span className="font-medium">{agent.totalRuns}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">成功率: </span>
                          <span className="font-medium text-green-600">{agent.successRate}%</span>
                        </div>
                      </div>

                      {/* MCP工具统计 */}
                      <div className="space-y-1">
                        <div className="text-sm">
                          <span className="text-gray-600">服务器: </span>
                          <span className="font-medium">{agent.mcpConfig.enabledServers.length}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">工具: </span>
                          <span className="font-medium">{agent.mcpConfig.selectedTools.length}/{agent.mcpConfig.totalTools}</span>
                        </div>
                      </div>

                      {/* 核心能力 */}
                      <div className="mt-2">
                        <Space wrap size="small">
                          {agent.capabilities.slice(0, 3).map(capability => (
                            <Tag key={capability} size="small" color="blue">{capability}</Tag>
                          ))}
                          {agent.capabilities.length > 3 && (
                            <Tag size="small" color="default">+{agent.capabilities.length - 3}</Tag>
                          )}
                        </Space>
                      </div>

                      {/* 最后使用时间 */}
                      <div className="text-xs text-gray-500 mt-2">
                        最后使用: {agent.lastUsed?.replace('T', ' ').slice(0, 16) || '-'}
                      </div>
                    </Space>
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
        title="MCP工具配置"
        open={mcpConfigModal}
        onCancel={() => setMCPConfigModal(false)}
        onOk={handleSaveMCPConfig}
        width={1000}
        okText="保存配置"
        cancelText="取消"
      >
        {selectedAgent && (
          <div>
            <Alert
              message="MCP工具配置"
              description={`为 ${selectedAgent.displayName} 选择需要的MCP服务器和工具。只有启用的工具会被加载到智能体中。`}
              type="info"
              showIcon
              className="mb-4"
            />
            
            {mcpServers.map(server => (
              <Card key={server.id} size="small" className="mb-3">
                <div className="mb-3">
                  <Space>
                    <Checkbox
                      checked={tempMCPConfig.enabledServers.includes(server.id)}
                      onChange={(e) => toggleServerSelection(server.id, e.target.checked)}
                      disabled={server.status !== 'connected'}
                    >
                      <strong>{server.name}</strong>
                    </Checkbox>
                    <Badge 
                      status={server.status === 'connected' ? 'success' : 
                             server.status === 'error' ? 'error' : 'warning'} 
                      text={server.status}
                    />
                  </Space>
                </div>
                
                <div className="pl-6">
                  <Row gutter={[16, 8]}>
                    {server.tools.map(tool => (
                      <Col key={tool.name} span={12}>
                        <Checkbox
                          checked={tempMCPConfig.selectedTools.includes(tool.name)}
                          onChange={(e) => toggleToolSelection(tool.name, e.target.checked)}
                          disabled={
                            !tempMCPConfig.enabledServers.includes(server.id) || 
                            server.status !== 'connected'
                          }
                        >
                          <Space>
                            {getCategoryIcon(tool.category)}
                            <span>{tool.name}</span>
                            <Tag size="small" color={getCategoryColor(tool.category)}>
                              {tool.category}
                            </Tag>
                          </Space>
                        </Checkbox>
                        <div className="text-xs text-gray-500 ml-6">{tool.description}</div>
                      </Col>
                    ))}
                  </Row>
                </div>
              </Card>
            ))}
            
            <div className="mt-4 p-3 bg-gray-50 rounded">
              <strong>配置摘要:</strong>
              <div className="mt-2">
                <span className="text-gray-600">选中服务器: </span>
                <span className="font-medium">{tempMCPConfig.enabledServers.length}</span>
                <span className="mx-4 text-gray-600">选中工具: </span>
                <span className="font-medium">{tempMCPConfig.selectedTools.length}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AgentManagement;