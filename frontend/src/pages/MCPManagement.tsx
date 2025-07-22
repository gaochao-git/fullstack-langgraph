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
  Popconfirm,
  Row,
  Col,
  Switch,
  Checkbox,
  Modal,
  Descriptions,
  Badge,
  Divider,
  Alert,
  Form,
  Collapse,
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

const { Search } = Input;
const { Option } = Select;

// MCP相关类型定义
interface MCPTool {
  name: string;
  description: string;
  globalEnabled: boolean;  // 全局开关
  category: string;
  parameters?: any;
}

interface MCPServer {
  id: string;
  name: string;
  uri: string;
  status: 'connected' | 'disconnected' | 'error';
  description: string;
  tools: MCPTool[];
  enabled: boolean;
  lastConnected?: string;
  version?: string;
  authType?: 'none' | 'bearer' | 'basic' | 'api_key';
  authToken?: string;
  apiKeyHeader?: string;
}


// Mock数据
const mockMCPServers: MCPServer[] = [
  {
    id: 'server-1',
    name: 'Database Tools Server',
    uri: 'mcp://localhost:3001',
    status: 'connected',
    description: '数据库相关工具集合，支持MySQL、PostgreSQL查询和监控',
    enabled: true,
    lastConnected: '2025-07-22 10:30:00',
    version: '1.0.0',
    tools: [
      {
        name: 'mysql_query',
        description: 'Execute MySQL queries and return results',
        globalEnabled: true,
        category: 'database'
      },
      {
        name: 'postgres_query', 
        description: 'Execute PostgreSQL queries and return results',
        globalEnabled: true,
        category: 'database'
      },
      {
        name: 'db_health_check',
        description: 'Check database connection and performance metrics',
        globalEnabled: false,
        category: 'monitoring'
      }
    ]
  },
  {
    id: 'server-2',
    name: 'System Monitor Server',
    uri: 'mcp://localhost:3002',
    status: 'connected',
    description: '系统监控工具，包含性能分析、日志查看等功能',
    enabled: true,
    lastConnected: '2025-07-22 10:25:00',
    version: '2.1.0',
    tools: [
      {
        name: 'system_metrics',
        description: 'Get system CPU, memory, disk usage metrics',
        globalEnabled: true,
        category: 'monitoring'
      },
      {
        name: 'log_analyzer',
        description: 'Analyze system logs for errors and patterns',
        globalEnabled: true,
        category: 'analysis'
      },
      {
        name: 'process_monitor',
        description: 'Monitor running processes and resource usage',
        globalEnabled: false,
        category: 'monitoring'
      }
    ]
  },
  {
    id: 'server-3',
    name: 'Network Tools Server',
    uri: 'mcp://remote-host:3003',
    status: 'error',
    description: '网络诊断工具集，包含ping、traceroute、端口扫描等',
    enabled: false,
    lastConnected: '2025-07-22 09:15:00',
    version: '1.5.2',
    tools: [
      {
        name: 'ping_test',
        description: 'Test network connectivity to hosts',
        globalEnabled: false,
        category: 'network'
      },
      {
        name: 'port_scan',
        description: 'Scan open ports on target hosts',
        globalEnabled: false,
        category: 'network'
      },
      {
        name: 'traceroute',
        description: 'Trace network path to destination',
        globalEnabled: false,
        category: 'network'
      }
    ]
  },
  {
    id: 'server-4',
    name: 'Cloud API Server',
    uri: 'mcp://api.cloud.com:443',
    status: 'disconnected',
    description: '云服务API集成，支持AWS、Azure、阿里云等',
    enabled: false,
    lastConnected: '2025-07-21 16:45:00',
    version: '3.0.1',
    tools: [
      {
        name: 'aws_ec2_list',
        description: 'List AWS EC2 instances and their status',
        globalEnabled: false,
        category: 'cloud'
      },
      {
        name: 'azure_resource_monitor',
        description: 'Monitor Azure resources and costs',
        globalEnabled: false,
        category: 'cloud'
      }
    ]
  }
];


const MCPManagement: React.FC = () => {
  const [servers, setServers] = useState<MCPServer[]>(mockMCPServers);
  const [loading, setLoading] = useState(false);
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

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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
  const toggleServerEnabled = (serverId: string) => {
    setServers(prevServers =>
      prevServers.map(server =>
        server.id === serverId 
          ? { ...server, enabled: !server.enabled }
          : server
      )
    );
    message.success('服务器状态已更新');
  };

  // 查看服务器详情
  const handleViewServer = (server: MCPServer) => {
    setSelectedServer(server);
    setServerDetailModal(true);
  };


  // 切换工具全局状态
  const toggleToolGlobalEnabled = (serverId: string, toolName: string) => {
    setServers(prevServers =>
      prevServers.map(server => {
        if (server.id === serverId) {
          return {
            ...server,
            tools: server.tools.map(tool =>
              tool.name === toolName 
                ? { ...tool, globalEnabled: !tool.globalEnabled }
                : tool
            )
          };
        }
        return server;
      })
    );
    
    const newState = servers.find(s => s.id === serverId)?.tools.find(t => t.name === toolName)?.globalEnabled;
    message.success(`工具 ${toolName} 已${!newState ? '全局启用' : '全局禁用'}`);
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

  // 新增服务器
  const handleAddServer = () => {
    setEditingServer(null);
    setFormConnectionStatus('idle');
    setFormDiscoveredTools([]);
    setServerFormModal(true);
  };

  // 编辑服务器
  const handleEditServer = (server: MCPServer) => {
    setEditingServer(server);
    setFormConnectionStatus(server.status === 'connected' ? 'connected' : 'idle');
    setFormDiscoveredTools(server.tools || []);
    setServerFormModal(true);
  };

  // 删除服务器
  const handleDeleteServer = (serverId: string) => {
    setServers(prevServers => prevServers.filter(server => server.id !== serverId));
    message.success('服务器已删除');
  };

  // 测试连接
  const handleTestConnection = (serverId: string) => {
    const server = servers.find(s => s.id === serverId);
    if (server) {
      // 模拟连接测试
      setTimeout(() => {
        setServers(prevServers =>
          prevServers.map(s =>
            s.id === serverId
              ? { ...s, status: 'connected', lastConnected: new Date().toISOString().slice(0, 16) }
              : s
          )
        );
        message.success(`${server.name} 连接测试成功`);
      }, 1000);
      message.info('正在测试连接...');
    }
  };

  // 保存服务器
  const handleSaveServer = (values: any) => {
    const serverData = {
      ...values,
      tools: formDiscoveredTools,
      status: formConnectionStatus === 'connected' ? 'connected' as const : 'disconnected' as const,
      lastConnected: formConnectionStatus === 'connected' ? new Date().toISOString().slice(0, 16) : undefined
    };

    if (editingServer) {
      // 编辑模式
      setServers(prevServers =>
        prevServers.map(server =>
          server.id === editingServer.id
            ? { ...server, ...serverData }
            : server
        )
      );
      message.success('服务器信息已更新');
    } else {
      // 新增模式
      const newServer: MCPServer = {
        id: `server-${Date.now()}`,
        ...serverData,
        enabled: true
      };
      setServers(prevServers => [...prevServers, newServer]);
      message.success('服务器已添加');
    }
    setServerFormModal(false);
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
        authType: formValues.authType || 'none',
        authToken: formValues.authToken || null,
        apiKeyHeader: formValues.apiKeyHeader || null
      };
      
      console.log('发送测试连接请求:', requestBody);
      
      // 带baseurl调用后端接口
      const resp = await fetch(`${API_BASE_URL}/api/mcp/test_server`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      const data = await resp.json();
      if (data.healthy) {
        // 转换后端返回的工具为前端MCPTool结构
        const discoveredTools = (data.tools || []).map((tool: any) => ({
          name: tool.name,
          description: tool.description,
          globalEnabled: true, // 默认全局启用，可根据需要调整
          category: 'unknown', // 后端未返回类别，前端可自定义
          parameters: tool.inputSchema
        }));
        setFormConnectionStatus('connected');
        setFormDiscoveredTools(discoveredTools);
        message.success('连接测试成功，已发现工具');
      } else {
        setFormConnectionStatus('error');
        setFormDiscoveredTools([]);
        message.error('连接测试失败: ' + (data.error || '未知错误'));
      }
    } catch (error: any) {
      setFormConnectionStatus('error');
      setFormDiscoveredTools([]);
      message.error('连接测试失败: ' + (error?.message || '未知错误'));
    }
  };

  // 切换表单中工具的状态
  const toggleFormToolEnabled = (toolName: string) => {
    setFormDiscoveredTools(prevTools =>
      prevTools.map(tool =>
        tool.name === toolName
          ? { ...tool, globalEnabled: !tool.globalEnabled }
          : tool
      )
    );
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
      width: 200,
      fixed: 'left',
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
      width: 300,
      render: (uri: string) => (
        <div style={{ minWidth: 200, maxWidth: 300 }}>
          <code 
            className="text-sm bg-gray-100 px-2 py-1 rounded block overflow-x-auto whitespace-nowrap"
            style={{ scrollbarWidth: 'thin' }}
          >
            {uri}
          </code>
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: MCPServer['status']) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      )
    },
    {
      title: '工具数量',
      key: 'toolsCount',
      width: 100,
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
      width: 100,
      render: (version: string) => (
        <Tag color="default">{version}</Tag>
      )
    },
    {
      title: '最后连接时间',
      dataIndex: 'lastConnected',
      key: 'lastConnected',
      width: 150,
      render: (time: string) => time?.replace('T', ' ').slice(0, 16) || '-'
    },
    {
      title: '启用状态',
      key: 'enabled',
      width: 120,
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
      width: 180,
      fixed: 'right',
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

  return (
    <div>
      {/* 提示信息 */}
      <Alert
        message="MCP服务器管理"
        description="管理MCP服务器连接状态和工具配置。添加、测试和配置外部MCP服务器。"
        type="info"
        showIcon
        className="mb-4"
      />

      {/* MCP服务器管理 */}
      <Card title="MCP服务器管理">
        <div className="mb-4">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索服务器名称、描述"
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
                <Option value="connected">已连接</Option>
                <Option value="disconnected">已断开</Option>
                <Option value="error">连接错误</Option>
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
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={handleAddServer}
                >
                  添加服务器
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        <Table
          columns={columns}
          dataSource={filteredServers}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个服务器`,
            pageSizeOptions: ['10', '20', '50'],
            defaultPageSize: 10
          }}
        />
      </Card>

      {/* 服务器详情模态框 */}
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
                <Space>
                  {selectedServer.name}
                  <Badge 
                    status={selectedServer.status === 'connected' ? 'success' : 
                             selectedServer.status === 'error' ? 'error' : 'warning'} 
                    text={getStatusText(selectedServer.status)}
                  />
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="连接地址" span={2}>
                <code>{selectedServer.uri}</code>
              </Descriptions.Item>
              <Descriptions.Item label="版本">{selectedServer.version}</Descriptions.Item>
              <Descriptions.Item label="最后连接时间">{selectedServer.lastConnected}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {selectedServer.description}
              </Descriptions.Item>
            </Descriptions>
            
            <Divider>
              可用工具 ({selectedServer.tools.length})
            </Divider>
            
            <div className="space-y-3">
              {selectedServer.tools.map(tool => (
                <Card key={tool.name} size="small" 
                      style={{ 
                        borderColor: tool.globalEnabled ? '#52c41a' : '#d9d9d9',
                        backgroundColor: tool.globalEnabled ? '#f6ffed' : '#fafafa'
                      }}>
                  <Row align="middle" justify="space-between">
                    <Col span={18}>
                      <Space direction="vertical" size="small">
                        <Space>
                          <span className={`font-medium ${tool.globalEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                            {tool.name}
                          </span>
                          <Tag color={getCategoryColor(tool.category)}>{tool.category}</Tag>
                          {tool.globalEnabled && (
                            <Tag color="green">全局启用</Tag>
                          )}
                          {!tool.globalEnabled && (
                            <Tag color="default">全局禁用</Tag>
                          )}
                        </Space>
                        <span className={`text-sm ${tool.globalEnabled ? 'text-gray-600' : 'text-gray-400'}`}>
                          {tool.description}
                        </span>
                      </Space>
                    </Col>
                    <Col span={6} className="text-right">
                      <Switch
                        checked={tool.globalEnabled}
                        disabled={true}
                        checkedChildren="启用"
                        unCheckedChildren="禁用"
                      />
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* 服务器表单模态框 */}
      <Modal
        title={editingServer ? "编辑MCP服务器" : "添加MCP服务器"}
        open={serverFormModal}
        onCancel={() => setServerFormModal(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveServer}
          key={editingServer?.id || 'new'}
          initialValues={editingServer ? {
            name: editingServer.name,
            uri: editingServer.uri,
            description: editingServer.description,
            version: editingServer.version,
            authType: editingServer.authType || 'none',
            authToken: editingServer.authToken || '',
            apiKeyHeader: editingServer.apiKeyHeader || 'X-API-Key'
          } : {
            authType: 'none'
          }}
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

          <Form.Item label="连接地址" required style={{ marginBottom: 0 }}>
            <Row gutter={8} align="middle" wrap={false}>
              <Col flex="auto">
                <Form.Item
                  name="uri"
                  noStyle
                  rules={[{ required: true, message: '请输入连接地址' }]}
                >
                  <Input 
                    placeholder="例如：mcp://localhost:3001 或 http://localhost:8080" 
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

          {/* 认证类型选择 */}
          <Form.Item
            label="认证类型"
            name="authType"
            initialValue="none"
            style={{ marginBottom: 0 }}
          >
            <Select size="middle">
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
                      initialValue="X-API-Key"
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

          {/* 连接状态提示 */}
          {formConnectionStatus !== 'idle' && (
            <Form.Item>
              <Alert
                message={
                  formConnectionStatus === 'testing' ? '正在测试连接...' :
                  formConnectionStatus === 'connected' ? '连接成功' :
                  '连接失败'
                }
                type={
                  formConnectionStatus === 'testing' ? 'info' :
                  formConnectionStatus === 'connected' ? 'success' :
                  'error'
                }
                showIcon
              />
            </Form.Item>
          )}

          <Form.Item
            label="描述"
            name="description"
            rules={[
              { max: 200, message: '描述不能超过200个字符' }
            ]}
          >
            <Input.TextArea 
              rows={3}
              placeholder="描述该MCP服务器提供的功能和用途"
            />
          </Form.Item>

          <Form.Item
            label="版本"
            name="version"
          >
            <Input placeholder="例如：1.0.0" />
          </Form.Item>

          {/* 工具配置 */}
          {formDiscoveredTools.length > 0 && (
            <Form.Item label={`发现的工具 (${formDiscoveredTools.length})`}>
              <Collapse
                size="small"
                items={formDiscoveredTools.map(tool => {
                  const { summary, args, returns } = formatToolDescription(tool.description);
                  const parameters = tool.parameters?.properties || {};
                  
                  return {
                    key: tool.name,
                    label: (
                      <Row align="middle" style={{ width: '100%' }}>
                        <Col span={20}>
                          <Space>
                            <span className={`font-medium ${tool.globalEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                              {tool.name}
                            </span>
                            {Object.keys(parameters).length > 0 && (
                              <Tag color="blue" size="small">{Object.keys(parameters).length} 参数</Tag>
                            )}
                          </Space>
                        </Col>
                        <Col span={4} className="text-right">
                          <Switch
                            checked={tool.globalEnabled}
                            onChange={(checked) => {
                              toggleFormToolEnabled(tool.name);
                            }}
                            onClick={(checked, e) => e.stopPropagation()}
                            size="small"
                          />
                        </Col>
                      </Row>
                    ),
                    children: (
                      <div className="space-y-2 pt-1">
                        {/* 工具描述 */}
                        {summary && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">描述:</div>
                            <div className={`text-xs ${tool.globalEnabled ? 'text-gray-600' : 'text-gray-400'}`}>
                              {summary}
                            </div>
                          </div>
                        )}
                        
                        {/* 参数信息 */}
                        {Object.keys(parameters).length > 0 && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">参数:</div>
                            <div className="space-y-1">
                              {Object.entries(parameters).map(([paramName, paramInfo]: [string, any]) => (
                                <div key={paramName} className="flex items-center gap-1 text-xs bg-gray-50 px-2 py-1 rounded">
                                  <span className="font-mono text-blue-600 font-medium text-xs">{paramName}</span>
                                  <Tag size="small" color="blue" className="text-xs">{paramInfo.type || 'unknown'}</Tag>
                                  {paramInfo.default !== undefined && (
                                    <Tag size="small" color="orange" className="text-xs">默认: {String(paramInfo.default)}</Tag>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* 返回值信息 */}
                        {returns && (
                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">返回:</div>
                            <div className={`text-xs bg-green-50 px-2 py-1 rounded ${tool.globalEnabled ? 'text-gray-600' : 'text-gray-400'}`}>
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
              <Button onClick={() => setServerFormModal(false)}>
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