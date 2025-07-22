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
  Alert
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
  enabled: boolean;
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
        enabled: true,
        category: 'database'
      },
      {
        name: 'postgres_query', 
        description: 'Execute PostgreSQL queries and return results',
        enabled: true,
        category: 'database'
      },
      {
        name: 'db_health_check',
        description: 'Check database connection and performance metrics',
        enabled: false,
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
        enabled: true,
        category: 'monitoring'
      },
      {
        name: 'log_analyzer',
        description: 'Analyze system logs for errors and patterns',
        enabled: true,
        category: 'analysis'
      },
      {
        name: 'process_monitor',
        description: 'Monitor running processes and resource usage',
        enabled: false,
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
        enabled: false,
        category: 'network'
      },
      {
        name: 'port_scan',
        description: 'Scan open ports on target hosts',
        enabled: false,
        category: 'network'
      },
      {
        name: 'traceroute',
        description: 'Trace network path to destination',
        enabled: false,
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
        enabled: false,
        category: 'cloud'
      },
      {
        name: 'azure_resource_monitor',
        description: 'Monitor Azure resources and costs',
        enabled: false,
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
  const [selectedServer, setSelectedServer] = useState<MCPServer | null>(null);
  
  const { message } = App.useApp();

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


  // 切换工具状态
  const toggleToolEnabled = (serverId: string, toolName: string) => {
    setServers(prevServers =>
      prevServers.map(server => {
        if (server.id === serverId) {
          return {
            ...server,
            tools: server.tools.map(tool =>
              tool.name === toolName 
                ? { ...tool, enabled: !tool.enabled }
                : tool
            )
          };
        }
        return server;
      })
    );
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
        const enabledCount = record.tools.filter(tool => tool.enabled).length;
        const totalCount = record.tools.length;
        return (
          <Space>
            <ToolOutlined />
            <span>{enabledCount}/{totalCount}</span>
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
      width: 150,
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
            onClick={() => message.info('连接测试功能开发中...')}
            title="测试连接"
          />
          <Button 
            type="text" 
            size="small" 
            icon={<SettingOutlined />}
            onClick={() => message.info('服务器配置功能开发中...')}
            title="配置"
          />
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
                  onClick={() => message.info('添加服务器功能开发中...')}
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
            
            <Divider>可用工具 ({selectedServer.tools.length})</Divider>
            
            <div className="space-y-3">
              {selectedServer.tools.map(tool => (
                <Card key={tool.name} size="small">
                  <Row align="middle" justify="space-between">
                    <Col span={18}>
                      <Space direction="vertical" size="small">
                        <Space>
                          <span className="font-medium">{tool.name}</span>
                          <Tag color={getCategoryColor(tool.category)}>{tool.category}</Tag>
                        </Space>
                        <span className="text-gray-600 text-sm">{tool.description}</span>
                      </Space>
                    </Col>
                    <Col span={6} className="text-right">
                      <Switch
                        checked={tool.enabled}
                        onChange={() => toggleToolEnabled(selectedServer.id, tool.name)}
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

    </div>
  );
};

export default MCPManagement;