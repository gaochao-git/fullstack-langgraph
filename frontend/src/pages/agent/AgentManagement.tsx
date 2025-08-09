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
  Modal
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
import { agentApi, type Agent, type MCPServer, type CreateAgentRequest, type UpdateAgentRequest } from '../../services/agentApi';
import { renderIcon, getIconBackgroundColor } from './components/AgentIconSystem';

const { Search } = Input;
const { Option } = Select;
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
    totalRuns: agent.total_queries || 0,
    successRate: agent.success_queries && agent.total_queries ? 
      Number((agent.success_queries / agent.total_queries * 100).toFixed(1)) : 0,
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
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  
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
  
  
  
  const { message } = App.useApp();

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
        console.warn('加载可用模型响应格式异常:', data);
        setAvailableModels([]);
      }
    } catch (error) {
      console.error('加载可用模型失败:', error);
      // 如果加载失败，使用默认模型
      setAvailableModels([]);
    }
  };

  // 数据加载 - 只加载智能体列表
  const loadData = async () => {
    try {
      const response = await agentApi.getAllAgents();
      
      // 处理业务逻辑错误
      if (response.status === 'error') {
        message.error(response.msg || '加载智能体数据失败');
        return;
      }
      
      // 处理成功响应
      const data = response.data || response;
      const agentsData = data.items || data;
      console.log('Agents data loaded:', agentsData);
      setAgents(Array.isArray(agentsData) ? agentsData.map(transformAgentToLocal) : []);
    } catch (error) {
      console.error('加载智能体数据失败:', error);
      message.error('加载智能体数据失败');
    }
  };

  // 加载辅助数据 - 在需要时调用（创建/编辑时）
  const loadAuxiliaryData = async () => {
    try {
      // 加载MCP服务器
      try {
        const response = await agentApi.getMCPServers();
        console.log('MCP servers response:', response);
        
        // 处理统一响应格式
        if (response.status === 'ok' && response.data && response.data.items) {
          const mcpServersData = response.data.items;
          console.log('MCP servers data:', mcpServersData);
          setMcpServers(mcpServersData.map(transformMCPServerToLocal));
        } else if (response.status === 'error') {
          console.error('加载MCP服务器失败:', response.msg);
          message.error(response.msg || '加载MCP服务器失败');
          setMcpServers([]);
        } else {
          console.warn('MCP服务器响应格式异常:', response);
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
      // 分类筛选
      let matchType = true;
      if (typeFilter) matchType = agent.agent_type === typeFilter;
      return matchSearch && matchStatus && matchType;
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
          agent_type: values.agent_type,
          agent_description: values.agent_description || '',
          agent_capabilities: values.agent_capabilities || [],
          agent_icon: values.agent_icon || 'Bot',
          tools_info: values.tools_info,
          llm_info: values.llm_info,
          prompt_info: values.prompt_info
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
          prompt_info: values.prompt_info
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
      console.error('保存智能体失败:', error);
      message.error('保存智能体失败，请重试');
    } finally {
      setFormSubmitting(false);
    }
  };



  return (
    <div>
      <Card 
        title="智能体管理"
        extra={
          <Space>
            <Search
              placeholder="搜索智能体名称、描述"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 240 }}
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
              <Option value="enabled">已启用</Option>
              <Option value="disabled">已禁用</Option>
            </Select>
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
                      {/* 分类标签 */}
                      <div>
                        <Tag 
                          color={AGENT_TYPES.find(t => t.value === agent.agent_type)?.color || 'default'} 
                          className="text-xs"
                        >
                          {agent.agent_type || '未分类'}
                        </Tag>
                      </div>

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
          <div>确定要删除智能体 "{agentToDelete.displayName}" 吗？此操作不可撤销。</div>
        )}
      </Modal>


    </div>
  );
};

export default AgentManagement;