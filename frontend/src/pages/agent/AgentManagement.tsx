import React, { useState, useEffect } from 'react';
import { useIsMobile } from '@/hooks';
import { getBaseUrl } from '@/utils/base_api';
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
  Form
} from 'antd';
import { 
  RobotOutlined,
  SettingOutlined,
  EyeOutlined,
  ReloadOutlined,
  DeleteOutlined,
  LockOutlined,
  TeamOutlined,
  GlobalOutlined,
  UserOutlined,
  SwapOutlined,
  InfoCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import AgentEditModal from './components/AgentEditModal';
import RunLogModal from './components/RunLogModal';
import { agentApi, type Agent, type MCPServer, type CreateAgentRequest, type UpdateAgentRequest } from '@/services/agentApi';
import { renderIcon, getIconBackgroundColor } from './components/AgentIconSystem';
import { useAuth } from '@/hooks/useAuth';

const { Search } = Input;
const { Option } = Select;
const API_BASE_URL = getBaseUrl();

// 智能体分类选项
const AGENT_TYPES = [
  { value: '日志分析', label: '日志分析', color: 'blue' },
  { value: '监控告警', label: '监控告警', color: 'orange' },
  { value: '故障诊断', label: '故障诊断', color: 'red' },
  { value: '性能优化', label: '性能优化', color: 'green' },
  { value: '资源管理', label: '资源管理', color: 'purple' },
  { value: '运维部署', label: '运维部署', color: 'cyan' },
  { value: '安全防护', label: '安全防护', color: 'volcano' },
  { value: '合规审计', label: '合规审计', color: 'magenta' },
  { value: '合同履约', label: '合同履约', color: 'gold' },
  { value: '变更管理', label: '变更管理', color: 'lime' },
  { value: '其他', label: '其他', color: 'default' },
];

// 状态过滤选项
const STATUS_FILTERS = [
  { value: 'enabled', label: '已启用' },
  { value: 'disabled', label: '已禁用' },
];

// 归属过滤选项
const OWNER_FILTERS = [
  { value: 'mine', label: '我的' },
  { value: 'favorites', label: '我的收藏' },
  { value: 'team', label: '我的团队' },
  { value: 'department', label: '我的部门' },
];


// 本地状态类型（为了向前兼容，保持一些驼峰命名）
interface LocalAgent extends Agent {
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

interface LocalMCPServer extends MCPServer {
  status: 'connected' | 'disconnected' | 'error';
  // tools: LocalMCPTool[]; // 改为 MCPTool[]
}

// 数据转换工具函数
const transformAgentToLocal = (agent: Agent): LocalAgent => {
  // 从 tools_info 中提取 MCP 配置，后端BaseModel会自动解析JSON字段为对象
  const toolsInfo = agent.tools_info || { mcp_tools: [], system_tools: [] };
  const mcpTools = toolsInfo.mcp_tools || [];
  const systemTools = toolsInfo.system_tools || [];
  
  // 计算唯一的服务器ID列表
  const enabledServers = mcpTools
    .map((tool: any) => tool.server_id)
    .filter((id: string, index: number, self: string[]) => 
      id && self.indexOf(id) === index
    );
  
  // 计算所有选中的工具
  const allMcpToolNames = mcpTools.flatMap((tool: any) => tool.tools || []);
  const selectedTools = [...systemTools, ...allMcpToolNames];
  
  return {
    ...agent,
    displayName: agent.agent_name,
    lastUsed: agent.last_used_at || '',
    totalRuns: agent.total_runs || 0,
    successRate: agent.success_rate || 0,
    avgResponseTime: 0, // 这个字段在 Agent 接口中不存在
    mcpConfig: {
      enabledServers,
      selectedTools,
      totalTools: selectedTools.length
    }
  };
};

const transformMCPServerToLocal = (server: any): LocalMCPServer => ({
  ...server,
  id: server.server_id,
  name: server.server_name,
  status: 'connected', // 默认所有服务器都是连接状态，让用户可以勾选
  // 后端返回的是 server_tools，需要映射到 tools
  tools: Array.isArray(server.server_tools) ? server.server_tools : []
});

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<LocalAgent[]>([]);
  const [mcpServers, setMcpServers] = useState<LocalMCPServer[]>([]);
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [ownerFilter, setOwnerFilter] = useState<string | undefined>(undefined); // 归属过滤：我的/我的团队/我的部门
  const isMobile = useIsMobile();
  
  // 模态框状态
  const [agentEditModal, setAgentEditModal] = useState(false);
  const [editingAgent, setEditingAgent] = useState<LocalAgent | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  
  // 表单相关状态
  const [formSubmitting, setFormSubmitting] = useState(false);
  
  // 1. 新增 state
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<LocalAgent | null>(null);
  
  // 转移所有权相关状态
  const [transferModalVisible, setTransferModalVisible] = useState(false);
  const [agentToTransfer, setAgentToTransfer] = useState<LocalAgent | null>(null);
  
  // 运行日志相关状态
  const [runLogModalVisible, setRunLogModalVisible] = useState(false);
  const [runLogAgent, setRunLogAgent] = useState<LocalAgent | null>(null);
  const [transferForm] = Form.useForm();
  
  
  
  const { message } = App.useApp();
  const { user } = useAuth(); // 获取当前用户信息

  // 加载可用模型
  const loadAvailableModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai-models`);
      const data = await response.json();
      
      // 处理统一响应格式
      if (data.status === 'ok' && data.data && data.data.items) {
        const activeModels = data.data.items.filter((model: any) => model.status === 'active');
        setAvailableModels(activeModels);
      } else if (data.code === 200 && data.data && data.data.items) {
        // 兼容旧格式
        const activeModels = data.data.items.filter((model: any) => model.status === 'active');
        setAvailableModels(activeModels);
      } else {
        // 加载可用模型响应格式异常
        setAvailableModels([]);
      }
    } catch (error) {
      // 加载可用模型失败，使用默认模型
      // 如果加载失败，使用默认模型
      setAvailableModels([]);
    }
  };

  // 数据加载 - 只加载智能体列表
  const loadData = async () => {
    try {
      // 根据筛选条件构建参数
      const params: any = { size: 100 };
      
      // 设置归属过滤参数
      if (ownerFilter === 'favorites') {
        // 获取收藏列表
        const favResponse = await agentApi.getFavoriteAgents({ size: 100 });
        
        // 处理业务逻辑错误
        if (favResponse.status === 'error') {
          message.error(favResponse.msg || '加载收藏列表失败');
          return;
        }
        
        // 处理成功响应
        const favData = favResponse.data || favResponse;
        const favAgentsData = favData.items || favData;
        setAgents(Array.isArray(favAgentsData) ? favAgentsData.map(transformAgentToLocal) : []);
        return;
      } else if (ownerFilter) {
        params.owner_filter = ownerFilter;
      }
      
      const response = await agentApi.getAgents(params);
      
      // 处理业务逻辑错误
      if (response.status === 'error') {
        message.error(response.msg || '加载智能体数据失败');
        return;
      }
      
      // 处理成功响应
      const data = response.data || response;
      const agentsData = data.items || data;
      // 智能体数据加载成功
      setAgents(Array.isArray(agentsData) ? agentsData.map(transformAgentToLocal) : []);
    } catch (error) {
      // 加载智能体数据失败
      message.error('加载智能体数据失败');
    }
  };

  // 加载辅助数据 - 在需要时调用（创建/编辑时）
  const loadAuxiliaryData = async () => {
    try {
      // 加载MCP服务器
      try {
        const response = await agentApi.getMCPServers();
        // MCP服务器响应
        
        // 处理统一响应格式
        if (response.status === 'ok' && response.data && response.data.items) {
          const mcpServersData = response.data.items;
          // MCP服务器数据
          setMcpServers(mcpServersData.map(transformMCPServerToLocal));
        } else if (response.status === 'error') {
          // 加载MCP服务器失败
          message.error(response.msg || '加载MCP服务器失败');
          setMcpServers([]);
        } else {
          // MCP服务器响应格式异常
          setMcpServers([]);
        }
      } catch (error) {
        // 加载MCP服务器数据失败
        setMcpServers([]);
      }
      
      // 加载可用模型
      await loadAvailableModels();
      
    } catch (error) {
      // 加载辅助数据失败
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadData();
  }, []);
  
  // 当筛选条件变化时重新加载数据
  useEffect(() => {
    loadData();
  }, [ownerFilter]);
  


  // 过滤智能体
  const filteredAgents = agents
    .filter(agent => {
      const matchSearch = !searchText || 
        agent.displayName?.toLowerCase().includes(searchText.toLowerCase()) ||
        (agent.agent_description || '').toLowerCase().includes(searchText.toLowerCase());
      // 状态筛选用 agent.agent_enabled
      let matchStatus = true;
      if (statusFilter === 'enabled') matchStatus = agent.agent_enabled === 'yes';
      if (statusFilter === 'disabled') matchStatus = agent.agent_enabled === 'no';
      // 分类筛选
      let matchType = true;
      if (typeFilter) matchType = agent.agent_type === typeFilter;
      return matchSearch && matchStatus && matchType;
    })
    // 按调用次数排序（从多到少）
    .sort((a, b) => {
      // 获取调用次数
      const usageA = a.total_runs || 0;
      const usageB = b.total_runs || 0;
      
      // 按调用次数降序排列
      if (usageA !== usageB) return usageB - usageA;
      
      // 调用次数相同时，按名称字母顺序
      return (a.agent_name || '').localeCompare(b.agent_name || '');
    });

  // 切换智能体启用状态
  const toggleAgentEnabled = async (agentId: string) => {
    try {
      // 找到当前智能体
      const agent = agents.find(a => a.agent_id === agentId);
      if (agent) {
        // 切换状态
        const newStatus = agent.agent_enabled === 'yes' ? 'no' : 'yes';
        const response = await agentApi.updateAgent(agentId, { agent_enabled: newStatus });
        
        // 处理业务逻辑错误
        if (response.status === 'error') {
          message.error(response.msg || '更新智能体状态失败');
          return;
        }
      }
      
      // 重新从后端获取最新数据
      await loadData();
      
      message.success('智能体状态已更新');
    } catch (error) {
      // 切换智能体状态失败
      message.error('切换智能体状态失败，请重试');
    }
  };

  // 查看智能体详情 - 已删除，改为统计功能



  // 新建智能体
  const handleCreateAgent = async () => {
    setEditingAgent(null);
    setIsCreating(true);
    
    // 在打开创建模态框之前加载辅助数据
    await loadAuxiliaryData();
    
    setAgentEditModal(true);
  };

  // 编辑智能体
  const handleEditAgent = async (agent: LocalAgent) => {
    setEditingAgent(agent);
    setIsCreating(false);
    
    // 在打开编辑模态框之前加载辅助数据
    await loadAuxiliaryData();
    
    setAgentEditModal(true);
  };


  // 删除智能体
  const handleDeleteAgent = (agent: LocalAgent) => {
    // 内置智能体也可以删除，会在服务重启时自动注册
    setAgentToDelete(agent);
    setDeleteModalVisible(true);
  };

  // 转移所有权
  const handleTransferOwnership = (agent: LocalAgent) => {
    setAgentToTransfer(agent);
    setTransferModalVisible(true);
    transferForm.resetFields();
  };

  // 确认转移所有权
  const confirmTransferOwnership = async () => {
    try {
      const values = await transferForm.validateFields();
      if (!agentToTransfer) return;

      console.log('Transfer form values:', values);
      console.log('Transfer data:', {
        new_owner: values.new_owner,
        reason: values.reason
      });

      const response = await agentApi.transferOwnership(agentToTransfer.agent_id, {
        new_owner: values.new_owner,
        reason: values.reason
      });

      if (response.status === 'error') {
        message.error(response.msg || '转移所有权失败');
        return;
      }

      message.success('所有权转移成功');
      setTransferModalVisible(false);
      setAgentToTransfer(null);
      // 重新加载列表
      await loadData();
    } catch (error) {
      message.error('转移所有权失败，请重试');
    }
  };


  // 保存智能体（新建或编辑）
  const handleSaveAgent = async (values: any) => {
    setFormSubmitting(true);
    try {
      if (isCreating) {
        // 新建智能体
        const newAgentData: CreateAgentRequest = {
          agent_name: values.agent_name,
          agent_type: values.agent_type,
          agent_description: values.agent_description || '',
          agent_capabilities: values.agent_capabilities || [],
          agent_icon: values.agent_icon || 'Bot',
          tools_info: values.tools_info,
          llm_info: values.llm_info,
          prompt_info: values.prompt_info,
          visibility_type: values.visibility_type || 'private',
          visibility_additional_users: values.visibility_additional_users || []
        };

        const response = await agentApi.createAgent(newAgentData);
        
        // 处理业务逻辑错误
        if (response.status === 'error') {
          message.error(response.msg || '创建智能体失败');
          return;
        }
        
        const newAgent = response.data || response;
        setAgents(prevAgents => [...prevAgents, transformAgentToLocal(newAgent)]);
        message.success('智能体创建成功');
      } else if (editingAgent) {
        // 编辑智能体
        const updateData: UpdateAgentRequest = {
          agent_name: values.agent_name,
          agent_type: values.agent_type,
          agent_description: values.agent_description,
          agent_capabilities: values.agent_capabilities,
          agent_icon: values.agent_icon,
          tools_info: values.tools_info,
          llm_info: values.llm_info,
          prompt_info: values.prompt_info,
          visibility_type: values.visibility_type || 'private',
          visibility_additional_users: values.visibility_additional_users || []
        };

        const response = await agentApi.updateAgent(editingAgent.agent_id, updateData);
        
        // 处理业务逻辑错误
        if (response.status === 'error') {
          message.error(response.msg || '更新智能体失败');
          return;
        }
        
        const updatedAgent = response.data || response;
        setAgents(prevAgents =>
          prevAgents.map(agent => 
            agent.agent_id === editingAgent.agent_id ? transformAgentToLocal(updatedAgent) : agent
          )
        );
        message.success('智能体更新成功');
      }

      setAgentEditModal(false);
    } catch (error) {
      // 保存智能体失败
      message.error('保存智能体失败，请重试');
    } finally {
      setFormSubmitting(false);
    }
  };



  return (
    <div className="agent-management-container">
      <style>{`
        @media (max-width: 768px) {
          .agent-management-card .ant-card-head {
            flex-direction: column;
            align-items: flex-start;
          }
          .agent-management-card .ant-card-head-title {
            margin-bottom: 8px;
          }
          .agent-management-card .ant-card-extra {
            width: 100%;
            margin-left: 0;
          }
        }
      `}</style>
      <Card 
        title="智能体管理"
        className="agent-management-card"
        styles={{ 
          body: { padding: isMobile ? '12px' : '24px' },
          header: isMobile ? { padding: '12px 16px' } : undefined
        }}
        extra={
          <div style={{ 
            width: isMobile ? '100%' : 'auto',
            marginTop: isMobile ? '12px' : 0
          }}>
            {isMobile ? (
              // 移动端布局 - 多行显示
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <Select
                    value={ownerFilter}
                    onChange={setOwnerFilter}
                    style={{ width: 100 }}
                    allowClear
                    placeholder="归属"
                    options={OWNER_FILTERS.map(filter => ({
                      value: filter.value,
                      label: filter.label
                    }))}
                  />
                  <Button 
                    type="primary"
                    icon={<RobotOutlined />}
                    onClick={handleCreateAgent}
                  >
                    新建
                  </Button>
                </div>
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  <Search
                    placeholder="搜索"
                    allowClear
                    value={searchText}
                    onChange={(e) => setSearchText(e.target.value)}
                    style={{ flex: 1, minWidth: '100px' }}
                  />
                  <Select
                    placeholder="分类"
                    allowClear
                    style={{ width: '70px' }}
                    value={typeFilter}
                    onChange={setTypeFilter}
                  >
                    {AGENT_TYPES.map(type => (
                      <Option key={type.value} value={type.value}>{type.label}</Option>
                    ))}
                  </Select>
                  <Select
                    placeholder="状态"
                    allowClear
                    style={{ width: '80px' }}
                    value={statusFilter}
                    onChange={setStatusFilter}
                  >
                    {STATUS_FILTERS.map(status => (
                      <Option key={status.value} value={status.value}>{status.label}</Option>
                    ))}
                  </Select>
                  <Button 
                    icon={<ReloadOutlined />}
                    onClick={loadData}
                  />
                </div>
              </>
            ) : (
              // 桌面端布局 - 单行显示
              <Space>
                <Select
                  value={ownerFilter}
                  onChange={setOwnerFilter}
                  style={{ width: 120 }}
                  allowClear
                  placeholder="归属筛选"
                  options={OWNER_FILTERS.map(filter => ({
                    value: filter.value,
                    label: filter.label
                  }))}
                />
                <Select
                  placeholder="分类筛选"
                  allowClear
                  style={{ width: 120 }}
                  value={typeFilter}
                  onChange={setTypeFilter}
                >
                  {AGENT_TYPES.map(type => (
                    <Option key={type.value} value={type.value}>{type.label}</Option>
                  ))}
                </Select>
                <Select
                  placeholder="状态筛选"
                  allowClear
                  style={{ width: 120 }}
                  value={statusFilter}
                  onChange={setStatusFilter}
                >
                  {STATUS_FILTERS.map(status => (
                    <Option key={status.value} value={status.value}>{status.label}</Option>
                  ))}
                </Select>
                <Search
                  placeholder="搜索智能体名称、描述"
                  allowClear
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ width: 240 }}
                />
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={loadData}
                >
                  刷新
                </Button>
                <Button 
                  type="primary"
                  icon={<RobotOutlined />}
                  onClick={handleCreateAgent}
                >
                  新建智能体
                </Button>
              </Space>
            )}
          </div>
        }
      >
        {/* 智能体卡片列表 */}
        <Row gutter={[16, 16]}>
          {filteredAgents.map(agent => (
            <Col xs={24} lg={12} xl={8} key={agent.id}>
              <Card
                className="h-full"
                actions={[
                  <Button 
                    key="stats"
                    type="text" 
                    icon={<BarChartOutlined />}
                    onClick={() => {
                      setRunLogAgent(agent);
                      setRunLogModalVisible(true);
                    }}
                  >
                    统计
                  </Button>,
                  ...(user && agent.agent_owner === user.username ? [
                    // 编辑按钮：只有所有者可以编辑
                    <Button 
                      key="edit"
                      type="text" 
                      icon={<SettingOutlined />}
                      onClick={() => handleEditAgent(agent)}
                    >
                      编辑
                    </Button>,
                    // 转移按钮：只有所有者可以转移
                    <Button 
                      key="transfer"
                      type="text" 
                      icon={<SwapOutlined />}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleTransferOwnership(agent);
                      }}
                    >
                      转移
                    </Button>,
                    // 删除按钮：只有所有者可以删除
                    <Button 
                      key="delete"
                      type="text" 
                      danger
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        // 删除智能体: agent.id
                        handleDeleteAgent(agent);
                      }}
                    >
                      删除
                    </Button>
                  ] : [])
                ]}
              >
                <Card.Meta
                  title={
                    <div className="flex items-center justify-between" style={{ marginBottom: 8 }}>
                      <div className="flex items-center gap-2">
                        <div
                          style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            backgroundColor: agent.agent_icon ? getIconBackgroundColor(agent.agent_icon, '20') : '#1677ff20',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0
                          }}
                        >
                          {agent.agent_icon ? renderIcon(agent.agent_icon, 16) : <RobotOutlined style={{ fontSize: 16 }} />}
                        </div>
                        <div className="text-base font-medium" style={{ color: agent.is_builtin === 'yes' ? '#faad14' : undefined }}>
                          {agent.displayName}
                        </div>
                      </div>
                      <Switch
                        checked={agent.agent_enabled === 'yes'}
                        onChange={() => toggleAgentEnabled(agent.agent_id)}
                      />
                    </div>
                  }
                  description={
                    <div className="space-y-2">
                      {/* 分类标签、权限标签和所有者 */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <Tag 
                          color={AGENT_TYPES.find(t => t.value === agent.agent_type)?.color || 'default'} 
                          className="text-xs"
                        >
                          {agent.agent_type || '未分类'}
                        </Tag>
                        {/* 权限标签 */}
                        {agent.visibility_type === 'private' && (
                          <Tag icon={<LockOutlined />} color="red" className="text-xs">私有</Tag>
                        )}
                        {agent.visibility_type === 'team' && (
                          <Tag icon={<TeamOutlined />} color="orange" className="text-xs">团队</Tag>
                        )}
                        {agent.visibility_type === 'department' && (
                          <Tag icon={<TeamOutlined />} color="blue" className="text-xs">部门</Tag>
                        )}
                        {agent.visibility_type === 'public' && (
                          <Tag icon={<GlobalOutlined />} color="green" className="text-xs">公开</Tag>
                        )}
                        {/* 所有者信息 */}
                        <Tag icon={<UserOutlined />} className="text-xs">
                          {agent.agent_owner || agent.create_by || 'system'}
                        </Tag>
                      </div>

                      {/* 运行统计和MCP工具统计合并为一行 */}
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-gray-500">运行: <span className="font-semibold text-gray-700">{agent.totalRuns}</span></span>
                        <span className="text-gray-500">服务器: <span className="font-semibold text-gray-700">{agent.mcpConfig.enabledServers.length}</span></span>
                        <span className="text-gray-500">工具: <span className="font-semibold text-gray-700">{agent.mcpConfig.selectedTools.length}</span></span>
                      </div>

                      {/* 核心能力 */}
                      {agent.agent_capabilities && agent.agent_capabilities.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {agent.agent_capabilities.slice(0, 3).map(capability => (
                            <Tag key={capability} color="blue" className="text-xs">{capability}</Tag>
                          ))}
                        </div>
                      )}
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



      {/* 智能体编辑模态框 */}
      <AgentEditModal
        visible={agentEditModal}
        onCancel={() => setAgentEditModal(false)}
        onSave={handleSaveAgent}
        agent={editingAgent}
        isCreating={isCreating}
        mcpServers={mcpServers}
        availableModels={availableModels}
        loading={formSubmitting}
        onRefresh={loadData}
        currentUser={user}
      />

      {/* 确认删除模态框 */}
      <Modal
        title="确认删除"
        open={deleteModalVisible}
        onOk={async () => {
          if (!agentToDelete) return;
          try {
            const response = await agentApi.deleteAgent(agentToDelete.agent_id);
            
            // 处理业务逻辑错误
            if (response.status === 'error') {
              message.error(response.msg || '删除智能体失败');
              return;
            }
            
            setAgents(prevAgents => prevAgents.filter(a => a.agent_id !== agentToDelete.agent_id));
            message.success('智能体已删除');
          } catch (error) {
            message.error('删除智能体失败，请重试');
          } finally {
            setDeleteModalVisible(false);
            setAgentToDelete(null);
          }
        }}
        onCancel={() => {
          setDeleteModalVisible(false);
          setAgentToDelete(null);
        }}
        okText="确认删除"
        okType="danger"
        cancelText="取消"
      >
        {agentToDelete && (
          <div>
            <p>确定要删除智能体 "{agentToDelete.displayName}" 吗？此操作不可撤销。</p>
            {agentToDelete.is_builtin === 'yes' && (
              <p style={{ marginTop: 8, color: '#faad14' }}>
                <InfoCircleOutlined /> 提示：这是内置智能体，删除后将在服务重启时自动重新注册。
              </p>
            )}
          </div>
        )}
      </Modal>

      {/* 转移所有权模态框 */}
      <Modal
        title="转移智能体所有权"
        open={transferModalVisible}
        onOk={confirmTransferOwnership}
        onCancel={() => {
          setTransferModalVisible(false);
          setAgentToTransfer(null);
          transferForm.resetFields();
        }}
        okText="确认转移"
        cancelText="取消"
      >
        {agentToTransfer && (
          <div>
            <p style={{ marginBottom: 16 }}>
              将智能体 "{agentToTransfer.displayName}" 的所有权转移给其他用户
            </p>
            <Form
              form={transferForm}
              layout="vertical"
            >
              <Form.Item
                name="new_owner"
                label="新所有者用户名"
                rules={[
                  { required: true, message: '请输入新所有者用户名' },
                  { min: 3, message: '用户名至少3个字符' }
                ]}
              >
                <Input placeholder="请输入新所有者的用户名" />
              </Form.Item>
              <Form.Item
                name="reason"
                label="转移原因（可选）"
              >
                <Input.TextArea 
                  rows={3} 
                  placeholder="请输入转移原因" 
                  maxLength={200}
                />
              </Form.Item>
            </Form>
            <p style={{ color: '#ff4d4f', marginTop: 16 }}>
              注意：转移后您将失去对该智能体的所有权限
            </p>
          </div>
        )}
      </Modal>

      {/* 运行日志弹窗 */}
      {runLogAgent && (
        <RunLogModal
          visible={runLogModalVisible}
          onClose={() => {
            setRunLogModalVisible(false);
            setRunLogAgent(null);
          }}
          agentId={runLogAgent.agent_id}
          agentName={runLogAgent.agent_name}
        />
      )}

    </div>
  );
};

export default AgentManagement;