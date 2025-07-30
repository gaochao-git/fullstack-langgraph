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
  ClockCircleOutlined 
} from '@ant-design/icons';
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
  }, [visible, isCreating, agent, mcpServers, availableModels]);

  const loadAgentDetails = async () => {
    if (!agent) return;
    
    try {
      // 使用具体的智能体ID接口，而不是获取全部后过滤
      const fullAgent = await agentApi.getAgent(agent.agent_id);
      
      if (fullAgent) {
        setTimeout(() => {
          form.setFieldsValue({
            agent_id: fullAgent.agent_id,
            agent_name: fullAgent.agent_name,
            agent_description: fullAgent.agent_description,
            agent_capabilities: fullAgent.agent_capabilities,
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
        }, 100);
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