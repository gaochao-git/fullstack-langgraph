import React, { useState, useEffect } from 'react';
import { useTheme } from '@/hooks/ThemeContext';
import { getBaseUrl } from '@/utils/base_api';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  InputNumber,
  Select, 
  Space, 
  Tag, 
  App, 
  Popconfirm,
  Row,
  Col,
  Switch,
  Checkbox,
  Modal,
  Descriptions,
  Badge,
  Divider,
  Form,
  Collapse,
  Tabs,
  message as antdMessage
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  SettingOutlined,
  ApiOutlined,
  ToolOutlined,
  LinkOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import MCPGatewayManagement from '../components/MCPGatewayManagement';

const { Search } = Input;
const { Option } = Select;

// MCP相关类型定义
interface MCPTool {
  name: string;
  description: string;
  globalEnabled: boolean;  // 保留用于兼容性，但所有工具默认可用
  category: string;
  parameters?: any;
}

interface MCPServer {
  id: string;
  name: string;
  uri: string;
  transportType?: string;
  status: 'connected' | 'disconnected' | 'error';
  description: string;
  tools: MCPTool[];
  enabled: boolean;
  lastConnected?: string;
  version?: string;
  authType?: 'none' | 'bearer' | 'basic' | 'api_key';
  authToken?: string;
  apiKeyHeader?: string;
  readTimeoutSeconds?: number;
}


// API基础URL
const API_BASE_URL = getBaseUrl();

// 将后端数据转换为前端格式
const transformServerFromAPI = (apiServer: any): MCPServer => {
  // server_tools现在已经是数组对象，不需要JSON.parse
  const tools = Array.isArray(apiServer.server_tools) ? apiServer.server_tools : [];
  return {
    id: apiServer.server_id,
    name: apiServer.server_name,
    uri: apiServer.server_uri,
    transportType: apiServer.transport_type,
    status: apiServer.connection_status as 'connected' | 'disconnected' | 'error',
    description: apiServer.server_description || '',
    enabled: apiServer.is_enabled === 'on',
    lastConnected: apiServer.update_time,
    authType: apiServer.auth_type || 'none',
    authToken: apiServer.auth_token,
    apiKeyHeader: apiServer.api_key_header,
    readTimeoutSeconds: apiServer.read_timeout_seconds || 5,
    tools: tools.map((tool: any) => ({
      name: tool.name,
      description: tool.description,
      globalEnabled: true, // 所有工具默认可用
      category: tool.category || 'unknown',
      parameters: tool.inputSchema || tool.parameters // 兼容两种格式
    }))
  };
};

// 将前端数据转换为后端格式
const transformServerToAPI = (server: Partial<MCPServer>, createBy: string = 'frontend_user') => {
  return {
    server_id: server.id,
    server_name: server.name,
    server_uri: server.uri,
    transport_type: server.transportType || 'streamable-http',
    server_description: server.description,
    is_enabled: server.enabled ? 'on' : 'off',
    connection_status: server.status || 'disconnected',
    auth_type: server.authType || '',
    auth_token: server.authToken,
    api_key_header: server.apiKeyHeader,
    read_timeout_seconds: server.readTimeoutSeconds || 5,
    server_tools: server.tools || [],
    server_config: {},
    team_name: 'default_team',
    create_by: createBy
  };
};


const MCPManagement: React.FC = () => {
  const { isDark } = useTheme();
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  
  // 模态框状态
  const [serverDetailModal, setServerDetailModal] = useState(false);
  const [serverFormModal, setServerFormModal] = useState(false);
  const [selectedServer, setSelectedServer] = useState<MCPServer | null>(null);
  const [editingServer, setEditingServer] = useState<MCPServer | null>(null);
  const [formConnectionStatus, setFormConnectionStatus] = useState<'idle' | 'testing' | 'connected' | 'error'>('idle');
  const [formDiscoveredTools, setFormDiscoveredTools] = useState<MCPTool[]>([]);
  
  const { message } = App.useApp();
  const [form] = Form.useForm();

  // API调用函数
  const fetchServers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers?size=100`);
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok' && result.data && result.data.items) {
          const transformedServers = result.data.items.map(transformServerFromAPI);
          setServers(transformedServers);
        } else {
          message.error(result.msg || '获取服务器列表失败');
        }
      } else {
        message.error('获取服务器列表失败');
      }
    } catch (error) {
      console.error('获取服务器列表错误:', error);
      message.error('获取服务器列表失败');
    }
  };

  const createServer = async (serverData: Partial<MCPServer>) => {
    try {
      const apiData = transformServerToAPI(serverData);
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiData)
      });
      
      if (response.ok) {
        message.success('服务器创建成功');
        await fetchServers();
        return true;
      } else {
        const errorData = await response.json();
        message.error(`创建服务器失败: ${errorData.detail || '未知错误'}`);
        return false;
      }
    } catch (error) {
      console.error('创建服务器错误:', error);
      message.error('创建服务器失败');
      return false;
    }
  };

  const updateServer = async (serverId: string, serverData: Partial<MCPServer>) => {
    try {
      const apiData = { ...transformServerToAPI(serverData), update_by: 'frontend_user' };
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers/${serverId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiData)
      });
      
      if (response.ok) {
        message.success('服务器更新成功');
        await fetchServers();
        return true;
      } else {
        const errorData = await response.json();
        message.error(`更新服务器失败: ${errorData.detail || '未知错误'}`);
        return false;
      }
    } catch (error) {
      console.error('更新服务器错误:', error);
      message.error('更新服务器失败');
      return false;
    }
  };

  const deleteServer = async (serverId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers/${serverId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        message.success('服务器删除成功');
        await fetchServers();
        return true;
      } else {
        const errorData = await response.json();
        message.error(`删除服务器失败: ${errorData.detail || '未知错误'}`);
        return false;
      }
    } catch (error) {
      console.error('删除服务器错误:', error);
      message.error('删除服务器失败');
      return false;
    }
  };

  const testServerConnection = async (serverId: string) => {
    try {
      // 获取服务器信息
      const server = servers.find(s => s.id === serverId);
      if (!server) {
        message.error('找不到服务器信息');
        return { healthy: false, tools: [], error: '服务器不存在' };
      }

      // 构建测试请求体，包含认证信息
      const requestBody = {
        url: server.uri,
        auth_type: server.authType || 'none',
        auth_token: server.authToken || null,
        api_key_header: server.apiKeyHeader || null
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      if (response.ok) {
        const result = await response.json();
        const data = result.data; // 解析统一响应格式
        if (data) {
          message.success('服务器连接测试成功');
          await fetchServers(); // 刷新状态
        } else {
          message.error(`连接测试失败: ${result.msg || '未知错误'}`);
        }
        return data;
      } else {
        message.error('连接测试失败');
        return { healthy: false, tools: [], error: '请求失败' };
      }
    } catch (error) {
      console.error('测试连接错误:', error);
      message.error('连接测试失败');
      return { healthy: false, tools: [], error: String(error) };
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchServers();
  }, []);

  // 获取状态颜色
  const getStatusColor = (status: MCPServer['status']): string => {
    const colors = {
      connected: 'green',
      disconnected: 'orange',
      error: 'red'
    };
    return colors[status];
  };

  // 获取状态文本
  const getStatusText = (status: MCPServer['status']): string => {
    const texts = {
      connected: '已连接',
      disconnected: '已断开', 
      error: '连接错误'
    };
    return texts[status];
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

  // 过滤服务器
  const filteredServers = servers.filter(server => {
    const matchSearch = !searchText || 
      server.name.toLowerCase().includes(searchText.toLowerCase()) ||
      server.description.toLowerCase().includes(searchText.toLowerCase());
    const matchStatus = !statusFilter || server.status === statusFilter;
    return matchSearch && matchStatus;
  });

  // 切换服务器启用状态
  const toggleServerEnabled = async (serverId: string) => {
    const server = servers.find(s => s.id === serverId);
    if (!server) return;
    
    const newEnabled = !server.enabled;
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/servers/${serverId}/enable`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newEnabled ? 'on' : 'off' })
      });
      
      if (response.ok) {
        await fetchServers(); // 刷新数据
        message.success(`服务器已${newEnabled ? '启用' : '禁用'}`);
      } else {
        message.error('更新服务器状态失败');
      }
    } catch (error) {
      console.error('更新服务器状态错误:', error);
      message.error('更新服务器状态失败');
    }
  };

  // 查看服务器详情
  const handleViewServer = (server: MCPServer) => {
    setSelectedServer(server);
    setServerDetailModal(true);
  };

  // 删除服务器
  const handleDeleteServer = async (serverId: string) => {
    await deleteServer(serverId);
  };

  // 添加服务器
  const handleAddServer = () => {
    setEditingServer(null);
    setFormConnectionStatus('idle');
    setFormDiscoveredTools([]);
    form.resetFields();
    // 设置新建时的默认值
    form.setFieldsValue({
      authType: 'none',
      transportType: 'streamable-http',
      readTimeoutSeconds: 5,
      apiKeyHeader: 'X-API-Key'
    });
    setServerFormModal(true);
  };

  // 编辑服务器
  const handleEditServer = (server: MCPServer) => {
    setEditingServer(server);
    setFormConnectionStatus('idle');
    setFormDiscoveredTools(server.tools);
    // 重置表单并设置编辑的服务器数据
    form.setFieldsValue({
      name: server.name,
      uri: server.uri,
      transportType: server.transportType || 'streamable-http',
      description: server.description,
      readTimeoutSeconds: server.readTimeoutSeconds || 5,
      authType: server.authType || 'none',
      authToken: server.authToken || '',
      apiKeyHeader: server.apiKeyHeader || 'X-API-Key'
    });
    setServerFormModal(true);
  };

  // 测试连接
  const handleTestConnection = async (serverId: string) => {
    await testServerConnection(serverId);
  };

  // 保存服务器（新增或编辑）
  const handleSaveServer = async (values: any) => {
    const serverData: Partial<MCPServer> = {
      id: editingServer?.id || `server-${Date.now()}`,
      name: values.name,
      uri: values.uri,
      transportType: values.transportType,
      description: values.description,
      readTimeoutSeconds: values.readTimeoutSeconds,
      authType: values.authType,
      authToken: values.authToken,
      apiKeyHeader: values.apiKeyHeader,
      enabled: true,
      status: 'disconnected',
      tools: formDiscoveredTools
    };

    let success = false;
    if (editingServer) {
      success = await updateServer(editingServer.id, serverData);
    } else {
      success = await createServer(serverData);
    }

    if (success) {
      setServerFormModal(false);
      form.resetFields();
      setFormConnectionStatus('idle');
      setFormDiscoveredTools([]);
    }
  };



  // 批量启用/禁用服务器的所有工具
  const toggleAllServerTools = (serverId: string, enableAll: boolean) => {
    setServers(prevServers =>
      prevServers.map(server => {
        if (server.id === serverId) {
          return {
            ...server,
            tools: server.tools.map(tool => ({
              ...tool,
              globalEnabled: enableAll
            }))
          };
        }
        return server;
      })
    );
    
    const serverName = servers.find(s => s.id === serverId)?.name;
    message.success(`${serverName} 的所有工具已${enableAll ? '全局启用' : '全局禁用'}`);
  };


  // 表单中测试连接并发现工具
  const handleFormTestConnection = async (formValues: any) => {
    console.log('测试连接参数 formValues:', formValues);
    console.log('测试连接参数 formValues.uri:', formValues.uri);
    if (!formValues.uri) {
      message.warning('请先填写连接地址');
      return;
    }

    // 检查认证配置
    if (formValues.authType !== 'none' && !formValues.authToken) {
      message.warning('请填写认证信息');
      return;
    }

    if (formValues.authType === 'api_key' && !formValues.apiKeyHeader) {
      message.warning('请填写 API Key Header');
      return;
    }

    setFormConnectionStatus('testing');
    try {
      // 构建请求体，包含认证信息
      const requestBody = {
        url: formValues.uri,
        auth_type: formValues.authType || '',
        auth_token: formValues.authToken || null,
        api_key_header: formValues.apiKeyHeader || null
      };
      
      console.log('发送测试连接请求:', requestBody);
      
      // 对于表单中的测试，我们创建一个临时服务器来测试
      // 这里先简化处理，只检查URL格式
      const resp = await fetch(`${API_BASE_URL}/api/v1/mcp/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      const response = await resp.json();
      const tools = response.data; // 解析统一响应格式
      const msg = response.msg; // 解析统一响应格式
      if (tools) {
        // 转换后端返回的工具为前端MCPTool结构
        const discoveredTools = (tools || []).map((tool: any) => ({
          name: tool.name,
          description: tool.description,
          globalEnabled: true, // 默认全局启用，可根据需要调整
          category: 'unknown', // 后端未返回类别，前端可自定义
          parameters: tool.inputSchema || tool.parameters // 统一参数字段
        }));
        setFormConnectionStatus('connected');
        setFormDiscoveredTools(discoveredTools);
        message.success('连接测试成功，已发现工具');
      } else {
        setFormConnectionStatus('error');
        setFormDiscoveredTools([]);
        message.error('连接测试失败: ' + (msg || '未知错误'));
      }
    } catch (error: any) {
      setFormConnectionStatus('error');
      setFormDiscoveredTools([]);
      message.error('连接测试失败: ' + (error?.msg || '未知错误'));
    }
  };


  // 格式化工具描述
  const formatToolDescription = (description: string) => {
    if (!description) return { summary: '', args: '', returns: '' };
    
    // 分离主要描述和参数信息
    const lines = description.split('\n');
    let summary = '';
    let args = '';
    let returns = '';
    let currentSection = 'summary';
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.startsWith('Args:')) {
        currentSection = 'args';
        continue;
      } else if (trimmedLine.startsWith('Returns:')) {
        currentSection = 'returns';
        continue;
      }
      
      if (currentSection === 'summary' && trimmedLine) {
        summary += (summary ? ' ' : '') + trimmedLine;
      } else if (currentSection === 'args' && trimmedLine) {
        args += (args ? '\n' : '') + trimmedLine;
      } else if (currentSection === 'returns' && trimmedLine) {
        returns += (returns ? ' ' : '') + trimmedLine;
      }
    }
    
    return { summary, args, returns };
  };

  // 表格列定义
  const columns: ColumnsType<MCPServer> = [
    {
      title: '服务器名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: MCPServer) => (
        <Space>
          <ApiOutlined />
          <span className="font-medium">{name}</span>
          <Badge 
            status={record.status === 'connected' ? 'success' : record.status === 'error' ? 'error' : 'warning'} 
          />
        </Space>
      )
    },
    {
      title: '连接地址',
      dataIndex: 'uri',
      key: 'uri',
      render: (uri: string) => (
        <code 
          className="px-2 py-1 rounded block overflow-x-auto whitespace-nowrap"
          style={{ 
            fontSize: '11px',
            scrollbarWidth: 'thin',
            backgroundColor: isDark ? '#374151' : '#f3f4f6',
            color: isDark ? '#e5e7eb' : '#374151',
            border: `1px solid ${isDark ? '#4b5563' : '#d1d5db'}`
          }}
        >
          {uri}
        </code>
      )
    },
    {
      title: '传输类型',
      dataIndex: 'transportType',
      key: 'transportType',
      render: (transportType: string) => {
        const getTransportColor = (type: string) => {
          switch(type) {
            case 'sse': return 'blue';
            case 'streamable-http': return 'green';
            case 'stdio': return 'orange';
            default: return 'default';
          }
        };
        
        const getTransportText = (type: string) => {
          switch(type) {
            case 'sse': return 'sse';
            case 'streamable-http': return 'streamable-http';
            case 'stdio': return 'stdio';
            default: return type || 'streamable-http';
          }
        };
        
        return (
          <Tag color={getTransportColor(transportType)}>
            {getTransportText(transportType)}
          </Tag>
        );
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: MCPServer['status']) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      )
    },
    {
      title: '工具数量',
      key: 'toolsCount',
      render: (_, record: MCPServer) => {
        const enabledCount = record.tools.filter(tool => tool.globalEnabled).length;
        const totalCount = record.tools.length;
        return (
          <Space>
            <ToolOutlined />
            <span style={{ color: enabledCount > 0 ? '#52c41a' : '#8c8c8c' }}>
              {enabledCount}/{totalCount}
            </span>
          </Space>
        );
      }
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => (
        <Tag color="default">{version || '-'}</Tag>
      )
    },
    {
      title: '最后连接时间',
      dataIndex: 'lastConnected',
      key: 'lastConnected',
      render: (time: string) => time?.replace('T', ' ').slice(0, 16) || '-'
    },
    {
      title: '启用状态',
      key: 'enabled',
      render: (_, record: MCPServer) => (
        <Switch
          checked={record.enabled}
          onChange={() => toggleServerEnabled(record.id)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          size="small"
        />
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record: MCPServer) => (
        <Space size="small">
          <Button 
            type="text" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewServer(record)}
            title="查看详情"
          />
          <Button 
            type="text" 
            size="small" 
            icon={<LinkOutlined />}
            onClick={() => handleTestConnection(record.id)}
            title="测试连接"
          />
          <Button 
            type="text" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEditServer(record)}
            title="编辑"
          />
          <Popconfirm
            title="删除服务器"
            description="确定要删除这个MCP服务器吗？删除后无法恢复。"
            onConfirm={() => handleDeleteServer(record.id)}
            okText="确定"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button 
              type="text" 
              size="small" 
              icon={<DeleteOutlined />}
              danger
              title="删除"
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  const handleGatewayConfigSuccess = (config: any) => {
    message.success('MCP Gateway配置操作成功！');
    // 可以在这里处理成功后的逻辑
    fetchServers();
  };

  return (
    <div>
      <Tabs
        defaultActiveKey="management"
        items={[
          {
            key: 'management',
            label: (
              <Space>
                <SettingOutlined />
                服务器管理
              </Space>
            ),
            children: (
              <Card 
                title="MCP服务器管理"
                extra={
                  <Space>
                    <Search
                      placeholder="搜索服务器名称、描述"
                      allowClear
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      style={{ width: 240 }}
                    />
                    <Select
                      placeholder="状态筛选"
                      allowClear
                      style={{ width: 120 }}
                      value={statusFilter}
                      onChange={setStatusFilter}
                    >
                      <Option value="connected">已连接</Option>
                      <Option value="disconnected">已断开</Option>
                      <Option value="error">连接错误</Option>
                    </Select>
                    <Button 
                      icon={<ReloadOutlined />}
                      onClick={fetchServers}
                    >
                      刷新
                    </Button>
                    <Button 
                      type="primary" 
                      icon={<PlusOutlined />}
                      onClick={handleAddServer}
                    >
                      添加服务器
                    </Button>
                  </Space>
                }
              >
                <Table
                  columns={columns}
                  dataSource={filteredServers}
                  rowKey="id"
                  scroll={{ x: 'max-content' }}
                  pagination={{
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 个服务器`,
                    pageSizeOptions: ['10', '20', '50'],
                    defaultPageSize: 10
                  }}
                />
              </Card>
            )
          },
          {
            key: 'gateway-management',
            label: (
              <Space>
                <ApiOutlined />
                MCP Gateway管理
              </Space>
            ),
            children: (
              <MCPGatewayManagement onSuccess={handleGatewayConfigSuccess} />
            )
          }
        ]}
      />
      <Modal
        title="MCP服务器详情"
        open={serverDetailModal}
        onCancel={() => setServerDetailModal(false)}
        footer={null}
        width={800}
      >
        {selectedServer && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="服务器名称" span={2}>
                {selectedServer.name}
              </Descriptions.Item>
              <Descriptions.Item label="连接地址" span={2}>
                <code>{selectedServer.uri}</code>
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedServer.description}
              </Descriptions.Item>
            </Descriptions>
            
            <Divider>
              可用工具 ({selectedServer.tools.length})
            </Divider>
            
            <Collapse
              size="small"
              items={selectedServer.tools.map(tool => {
                const { summary, args, returns } = formatToolDescription(tool.description);
                // 处理参数显示：tool.parameters 可能是 inputSchema 格式
                let parameters = {};
                if (tool.parameters?.properties) {
                  // 标准的 inputSchema 格式
                  parameters = tool.parameters.properties;
                } else if (tool.parameters && typeof tool.parameters === 'object') {
                  // 直接的参数对象
                  parameters = tool.parameters;
                }
                
                return {
                  key: tool.name,
                  label: (
                    <Row align="middle" style={{ width: '100%' }}>
                      <Col span={24}>
                        <Space>
                          <span className="font-medium text-gray-900">
                            {tool.name}
                          </span>
                          {Object.keys(parameters).length > 0 && (
                            <Tag color="blue" size="small">{Object.keys(parameters).length} 参数</Tag>
                          )}
                        </Space>
                      </Col>
                    </Row>
                  ),
                  children: (
                    <div className="space-y-2 pt-1">
                      {/* 工具描述 */}
                      {summary && (
                        <div style={{ marginBottom: 12 }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: isDark ? '#9ca3af' : '#8c8c8c', marginBottom: 8 }}>描述:</div>
                          <div style={{ 
                            fontSize: 12, 
                            color: isDark ? '#d1d5db' : '#595959',
                            backgroundColor: isDark ? '#374151' : '#fff',
                            padding: '8px 12px',
                            border: `1px solid ${isDark ? '#4b5563' : '#f0f0f0'}`,
                            borderRadius: 4,
                            lineHeight: '1.5'
                          }}>
                            {summary}
                          </div>
                        </div>
                      )}
                      
                      {/* 参数信息 */}
                      {Object.keys(parameters).length > 0 && (
                        <div style={{ marginBottom: 12 }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: isDark ? '#9ca3af' : '#8c8c8c', marginBottom: 8 }}>参数:</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {Object.entries(parameters).map(([paramName, paramInfo]: [string, any]) => (
                              <div key={paramName} style={{ 
                                display: 'flex', 
                                alignItems: 'flex-start', 
                                gap: 8, 
                                fontSize: 12, 
                                backgroundColor: isDark ? '#374151' : '#fafafa', 
                                padding: '8px 12px', 
                                borderRadius: 4, 
                                border: `1px solid ${isDark ? '#4b5563' : '#f0f0f0'}`,
                                flexWrap: 'wrap'
                              }}>
                                <span style={{ fontFamily: 'monospace', color: isDark ? '#60a5fa' : '#1890ff', fontWeight: 600, minWidth: 80 }}>
                                  {paramName}
                                </span>
                                <Tag size="small" color="blue">{paramInfo.type || 'unknown'}</Tag>
                                {paramInfo.description && (
                                  <span style={{ color: isDark ? '#9ca3af' : '#666666', flex: 1, marginLeft: 8 }}>
                                    {paramInfo.description}
                                  </span>
                                )}
                                {paramInfo.default !== undefined && (
                                  <Tag size="small" color="orange">默认: {String(paramInfo.default)}</Tag>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* 返回值信息 */}
                      {returns && (
                        <div style={{ marginBottom: 8 }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: isDark ? '#9ca3af' : '#8c8c8c', marginBottom: 8 }}>返回:</div>
                          <div style={{ 
                            fontSize: 12, 
                            backgroundColor: isDark ? '#065f46' : '#f6ffed', 
                            padding: '8px 12px', 
                            borderRadius: 4, 
                            border: `1px solid ${isDark ? '#059669' : '#b7eb8f'}`,
                            color: isDark ? '#10b981' : '#52c41a',
                            lineHeight: '1.4'
                          }}>
                            {returns}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                };
              })}
              style={{ maxHeight: '400px', overflowY: 'auto' }}
            />
          </div>
        )}
      </Modal>

      {/* 服务器表单模态框 */}
      <Modal
        title={editingServer ? "编辑MCP服务器" : "添加MCP服务器"}
        open={serverFormModal}
        onCancel={() => {
          setServerFormModal(false);
          form.resetFields();
          setEditingServer(null);
          setFormConnectionStatus('idle');
          setFormDiscoveredTools([]);
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveServer}
        >
          <Form.Item
            label="服务器名称"
            name="name"
            rules={[
              { required: true, message: '请输入服务器名称' },
              { max: 50, message: '服务器名称不能超过50个字符' }
            ]}
          >
            <Input placeholder="例如：Database Tools Server" />
          </Form.Item>

          <Form.Item label="连接地址" required>
            <Row gutter={8} align="middle" wrap={false}>
              <Col flex="auto">
                <Form.Item
                  name="uri"
                  noStyle
                  rules={[{ required: true, message: '请输入连接地址' }]}
                >
                  <Input 
                    placeholder="http://localhost:8080/sse" 
                  />
                </Form.Item>
              </Col>
              <Col>
                <Button 
                  type="primary"
                  loading={formConnectionStatus === 'testing'}
                  onClick={async () => {
                    const values = await form.validateFields();
                    handleFormTestConnection(values);
                  }}
                >
                  {formConnectionStatus === 'testing' ? '测试中' : '测试连接'}
                </Button>
              </Col>
            </Row>
          </Form.Item>

          {/* 传输类型选择 */}
          <Form.Item
            label="传输类型"
            name="transportType"
          >
            <Select>
              <Option value="streamable-http">streamable-http</Option>
              <Option value="sse">sse</Option>
              <Option value="stdio">stdio</Option>
            </Select>
          </Form.Item>

          {/* 认证类型选择 */}
          <Form.Item
            label="认证类型"
            name="authType"
          >
            <Select>
              <Option value="none">无认证</Option>
              <Option value="bearer">Bearer</Option>
              <Option value="basic">Basic</Option>
              <Option value="api_key">API Key</Option>
            </Select>
          </Form.Item>

          {/* 认证信息输入，根据类型动态渲染 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => 
              prevValues.authType !== currentValues.authType
            }
          >
            {({ getFieldValue }) => {
              const authType = getFieldValue('authType');
              
              if (authType === 'bearer') {
                return (
                  <Form.Item
                    label="Bearer Token"
                    name="authToken"
                    rules={[{ required: true, message: '请输入 Bearer Token' }]}
                  >
                    <Input.Password placeholder="输入 Bearer Token" />
                  </Form.Item>
                );
              }
              
              if (authType === 'basic') {
                return (
                  <Form.Item
                    label="Basic Auth Token"
                    name="authToken"
                    rules={[{ required: true, message: '请输入 Basic Auth Token (base64编码)' }]}
                    extra="格式: base64(username:password)"
                  >
                    <Input.Password placeholder="输入 Basic Auth Token" />
                  </Form.Item>
                );
              }
              
              if (authType === 'api_key') {
                return (
                  <>
                    <Form.Item
                      label="API Key Header"
                      name="apiKeyHeader"
                      rules={[{ required: true, message: '请输入 API Key Header 名称' }]}
                    >
                      <Input placeholder="例如: X-API-Key, Authorization, etc." />
                    </Form.Item>
                    <Form.Item
                      label="API Key"
                      name="authToken"
                      rules={[{ required: true, message: '请输入 API Key' }]}
                    >
                      <Input.Password placeholder="输入 API Key" />
                    </Form.Item>
                  </>
                );
              }
              
              return null;
            }}
          </Form.Item>

          {/* 超时时间配置 */}
          <Form.Item
            label="读取超时时间"
            name="readTimeoutSeconds"
            rules={[
              { required: true, message: '请设置超时时间' },
              { type: 'number', min: 1, max: 300, message: '超时时间必须在1-300秒之间' }
            ]}
          >
            <InputNumber 
              min={1}
              max={300}
              addonAfter="秒"
              placeholder="1-300秒之间"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
            rules={[
              { max: 200, message: '描述不能超过200个字符' }
            ]}
          >
            <Input 
              placeholder="描述该MCP服务器提供的功能和用途"
            />
          </Form.Item>


          {/* 工具配置 */}
          {formDiscoveredTools.length > 0 && (
            <Form.Item label={`发现的工具 (${formDiscoveredTools.length})`}>
              <Collapse
                size="small"
                items={formDiscoveredTools.map(tool => {
                  const { summary, args, returns } = formatToolDescription(tool.description);
                  // 处理参数显示：tool.parameters 可能是 inputSchema 格式
                  let parameters = {};
                  if (tool.parameters?.properties) {
                    // 标准的 inputSchema 格式
                    parameters = tool.parameters.properties;
                  } else if (tool.parameters && typeof tool.parameters === 'object') {
                    // 直接的参数对象
                    parameters = tool.parameters;
                  }
                  
                  
                  return {
                    key: tool.name,
                    label: (
                      <Row align="middle" style={{ width: '100%' }}>
                        <Col span={24}>
                          <Space>
                            <span className="font-medium text-gray-900">
                              {tool.name}
                            </span>
                            {Object.keys(parameters).length > 0 && (
                              <Tag color="blue" size="small">{Object.keys(parameters).length} 参数</Tag>
                            )}
                          </Space>
                        </Col>
                      </Row>
                    ),
                    children: (
                      <div className="space-y-2 pt-1">
                        {/* 工具描述 */}
                        {summary && (
                          <div style={{ marginBottom: 12 }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: isDark ? '#9ca3af' : '#8c8c8c', marginBottom: 8 }}>描述:</div>
                            <div style={{ 
                              fontSize: 12, 
                              color: isDark ? '#d1d5db' : '#595959',
                              backgroundColor: isDark ? '#374151' : '#fff',
                              padding: '8px 12px',
                              border: `1px solid ${isDark ? '#4b5563' : '#f0f0f0'}`,
                              borderRadius: 4,
                              lineHeight: '1.5'
                            }}>
                              {summary}
                            </div>
                          </div>
                        )}
                        
                        {/* 参数信息 */}
                        {Object.keys(parameters).length > 0 && (
                          <div style={{ marginBottom: 12 }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: isDark ? '#9ca3af' : '#8c8c8c', marginBottom: 8 }}>参数:</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {Object.entries(parameters).map(([paramName, paramInfo]: [string, any]) => (
                                <div key={paramName} style={{ 
                                  display: 'flex', 
                                  alignItems: 'flex-start', 
                                  gap: 8, 
                                  fontSize: 12, 
                                  backgroundColor: isDark ? '#374151' : '#fafafa', 
                                  padding: '8px 12px', 
                                  borderRadius: 4, 
                                  border: `1px solid ${isDark ? '#4b5563' : '#f0f0f0'}`,
                                  flexWrap: 'wrap'
                                }}>
                                  <span style={{ fontFamily: 'monospace', color: isDark ? '#60a5fa' : '#1890ff', fontWeight: 600, minWidth: 80 }}>
                                    {paramName}
                                  </span>
                                  <Tag size="small" color="blue">{paramInfo.type || 'unknown'}</Tag>
                                  {paramInfo.description && (
                                    <span style={{ color: isDark ? '#9ca3af' : '#666666', flex: 1, marginLeft: 8 }}>
                                      {paramInfo.description}
                                    </span>
                                  )}
                                  {paramInfo.default !== undefined && (
                                    <Tag size="small" color="orange">默认: {String(paramInfo.default)}</Tag>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* 返回值信息 */}
                        {returns && (
                          <div style={{ marginBottom: 8 }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: isDark ? '#9ca3af' : '#8c8c8c', marginBottom: 8 }}>返回:</div>
                            <div style={{ 
                              fontSize: 12, 
                              backgroundColor: isDark ? '#065f46' : '#f6ffed', 
                              padding: '8px 12px', 
                              borderRadius: 4, 
                              border: `1px solid ${isDark ? '#059669' : '#b7eb8f'}`,
                              color: isDark ? '#10b981' : '#52c41a',
                              lineHeight: '1.4'
                            }}>
                              {returns}
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  };
                })}
                style={{ maxHeight: '400px', overflowY: 'auto' }}
              />
            </Form.Item>
          )}

          <Form.Item>
            <div className="flex justify-end gap-2">
              <Button onClick={() => {
                setServerFormModal(false);
                form.resetFields();
                setEditingServer(null);
                setFormConnectionStatus('idle');
                setFormDiscoveredTools([]);
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingServer ? '更新' : '添加'}
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>

    </div>
  );
};

export default MCPManagement;