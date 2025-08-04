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
  message
} from 'antd';
import { 
  RobotOutlined,
  SettingOutlined,
  EyeOutlined,
  ReloadOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import AgentDetailModal from './components/AgentDetailModal';
import AgentEditModal from './components/AgentEditModal';
import { agentApi, type Agent, type MCPServer, type MCPTool, type CreateAgentRequest, type UpdateAgentRequest } from '../../services/agentApi';
import { renderIcon, getIconBackgroundColor } from './components/AgentIconSystem';

const { Search } = Input;
const { Option } = Select;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';


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
  const toolsInfo = agent.tools_info || {};
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
    lastUsed: agent.last_used,
    totalRuns: agent.total_runs,
    successRate: agent.success_rate,
    avgResponseTime: agent.avg_response_time,
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
  status: server.connection_status === 'connected' ? 'connected' : 'disconnected',
  // 后端返回的是 server_tools，需要映射到 tools
  tools: Array.isArray(server.server_tools) ? server.server_tools : []
});

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<LocalAgent[]>([]);
  const [mcpServers, setMcpServers] = useState<LocalMCPServer[]>([]);
  const [availableModels, setAvailableModels] = useState<any[]>([]);
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
  const [formSubmitting, setFormSubmitting] = useState(false);
  
  // 1. 新增 state
  const [deleteModalVisible, setDeleteModalVisible] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<LocalAgent | null>(null);
  
  
  
  const { message, modal } = App.useApp();

  // 加载可用模型
  const loadAvailableModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ai-models`);
      const data = await response.json();
      if (data.code === 200) {
        const activeModels = data.data.items.filter((model: any) => model.status === 'active');
        setAvailableModels(activeModels);
      }
    } catch (error) {
      console.error('加载可用模型失败:', error);
      // 如果加载失败，使用默认模型
      setAvailableModels([]);
    }
  };

  // 数据加载 - 只加载智能体列表
  const loadData = async () => {
    setLoading(true);
    try {
      const agentsData = await agentApi.getAllAgents();
      console.log('Agents data loaded:', agentsData);
      setAgents(agentsData.map(transformAgentToLocal));
    } catch (error) {
      console.error('加载智能体数据失败:', error);
      message.error('加载智能体数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载辅助数据 - 在需要时调用（创建/编辑时）
  const loadAuxiliaryData = async () => {
    try {
      // 加载MCP服务器
      try {
        const mcpServersData = await agentApi.getMCPServers();
        console.log('MCP servers data loaded:', mcpServersData);
        
        if (Array.isArray(mcpServersData)) {
          setMcpServers(mcpServersData.map(transformMCPServerToLocal));
        } else {
          console.warn('MCP服务器数据不是数组格式:', mcpServersData);
          setMcpServers([]);
        }
      } catch (error) {
        console.error('加载MCP服务器数据失败:', error);
        setMcpServers([]);
      }
      
      // 加载可用模型
      await loadAvailableModels();
      
    } catch (error) {
      console.error('加载辅助数据失败:', error);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadData();
  }, []);


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
      return matchSearch && matchStatus;
    })
    // 内置智能体排前面
    .sort((a, b) => {
      if (a.is_builtin === 'yes' && b.is_builtin !== 'yes') return -1;
      if (a.is_builtin !== 'yes' && b.is_builtin === 'yes') return 1;
      return 0;
    });

  // 切换智能体启用状态
  const toggleAgentEnabled = async (agentId: string) => {
    try {
      await agentApi.toggleAgentStatus(agentId);
      
      // 重新从后端获取最新数据
      await loadData();
      
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
    if (agent.is_builtin === 'yes') {
      message.warning('不能删除内置智能体');
      return;
    }
    setAgentToDelete(agent);
    setDeleteModalVisible(true);
  };


  // 保存智能体（新建或编辑）
  const handleSaveAgent = async (values: any) => {
    setFormSubmitting(true);
    try {
      if (isCreating) {
        // 新建智能体
        const newAgentData: CreateAgentRequest = {
          agent_name: values.agent_name,
          agent_description: values.agent_description || '',
          agent_capabilities: values.agent_capabilities || [],
          agent_icon: values.agent_icon || 'Bot',
          tools_info: values.tools_info,
          llm_info: values.llm_info,
          prompt_info: values.prompt_info
        };

        const newAgent = await agentApi.createAgent(newAgentData);
        setAgents(prevAgents => [...prevAgents, transformAgentToLocal(newAgent)]);
        message.success('智能体创建成功');
      } else if (editingAgent) {
        // 编辑智能体
        const updateData: UpdateAgentRequest = {
          agent_name: values.agent_name,
          agent_description: values.agent_description,
          agent_capabilities: values.agent_capabilities,
          agent_icon: values.agent_icon,
          tools_info: values.tools_info,
          llm_info: values.llm_info,
          prompt_info: values.prompt_info
        };

        const updatedAgent = await agentApi.updateAgent(editingAgent.agent_id, updateData);
        setAgents(prevAgents =>
          prevAgents.map(agent => 
            agent.agent_id === editingAgent.agent_id ? transformAgentToLocal(updatedAgent) : agent
          )
        );
        message.success('智能体更新成功');
      }

      setAgentEditModal(false);
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
                <Option value="enabled">已启用</Option>
                <Option value="disabled">已禁用</Option>
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
                  ...(agent.is_builtin !== 'yes' ? [
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
                  avatar={
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        backgroundColor: agent.agent_icon ? getIconBackgroundColor(agent.agent_icon, '20') : '#1677ff20',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {agent.agent_icon ? renderIcon(agent.agent_icon, 18) : <RobotOutlined style={{ fontSize: 18 }} />}
                    </div>
                  }
                  title={
                    <div className="flex items-center justify-between">
                      <div className="text-base font-medium flex items-center gap-2" style={{ color: agent.is_builtin === 'yes' ? '#faad14' : undefined }}>
                        {agent.displayName}
                      </div>
                      <Switch
                        size="small"
                        checked={agent.agent_enabled === 'yes'}
                        onChange={() => toggleAgentEnabled(agent.agent_id)}
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
                        {(agent.agent_capabilities || []).slice(0, 3).map(capability => (
                          <Tag key={capability} color="blue" className="text-xs">{capability}</Tag>
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
      <AgentDetailModal
        visible={agentDetailModal}
        onCancel={() => setAgentDetailModal(false)}
        agent={selectedAgent}
        mcpServers={mcpServers}
      />


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
      />

      {/* 确认删除模态框 */}
      <Modal
        title="确认删除"
        open={deleteModalVisible}
        onOk={async () => {
          if (!agentToDelete) return;
          try {
            await agentApi.deleteAgent(agentToDelete.agent_id);
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
          <div>确定要删除智能体 "{agentToDelete.displayName}" 吗？此操作不可撤销。</div>
        )}
      </Modal>


    </div>
  );
};

export default AgentManagement;