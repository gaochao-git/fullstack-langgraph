import React, { useState, useEffect } from 'react';
import { getBaseUrl } from '@/utils/base_api';
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
  Modal,
  Form,
  message as antdMessage,
  Tabs,
  Collapse,
  Divider,
  Switch,
  InputNumber
} from 'antd';
import { dump } from 'js-yaml';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  SettingOutlined,
  ApiOutlined,
  MinusCircleOutlined,
  GlobalOutlined,
  ToolOutlined,
  CloudServerOutlined,
  BulbOutlined,
  DownOutlined,
  UpOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useTheme } from '@/hooks/ThemeContext';

const { Search } = Input;
const { Option } = Select;
const { TextArea } = Input;

// API基础URL
const API_BASE_URL = getBaseUrl();

// MCP Gateway配置类型定义
interface MCPGatewayConfig {
  id: number;
  config_id: string;
  name: string;
  tenant: string;
  routers: any[];
  servers: any[];
  tools: any[];
  prompts: any[];
  mcp_servers: any[];
  is_deleted: number;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

interface MCPGatewayManagementProps {
  onSuccess?: (config: MCPGatewayConfig) => void;
}

const MCPGatewayManagement: React.FC<MCPGatewayManagementProps> = ({ onSuccess }) => {
  const { isDark } = useTheme();
  const [configs, setConfigs] = useState<MCPGatewayConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [tenantFilter, setTenantFilter] = useState<string>('');
  
  // 模态框状态
  const [configDetailModal, setConfigDetailModal] = useState(false);
  const [configFormModal, setConfigFormModal] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<MCPGatewayConfig | null>(null);
  const [editingConfig, setEditingConfig] = useState<MCPGatewayConfig | null>(null);
  
  // 工具展开状态
  const [expandedTools, setExpandedTools] = useState<Record<number, boolean>>({});
  
  const { message } = App.useApp();
  const [form] = Form.useForm();

  // API调用函数
  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/gateway/configs`);
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok' && result.data && result.data.items) {
          setConfigs(result.data.items);
        } else {
          message.error(result.msg || '获取配置列表失败');
        }
      } else {
        message.error('获取配置列表失败');
      }
    } catch (error) {
      console.error('获取配置列表错误:', error);
      message.error('获取配置列表失败');
    } finally {
      setLoading(false);
    }
  };

  const createConfig = async (configData: any) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/gateway/configs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...configData,
          create_by: 'frontend_user'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        message.success('配置创建成功');
        await fetchConfigs();
        onSuccess?.(result.data);
        return true;
      } else {
        const errorData = await response.json();
        message.error(`创建配置失败: ${errorData.detail || '未知错误'}`);
        return false;
      }
    } catch (error) {
      console.error('创建配置错误:', error);
      message.error('创建配置失败');
      return false;
    }
  };

  const updateConfig = async (configId: number, configData: any) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/gateway/configs/${configId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...configData,
          update_by: 'frontend_user'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        message.success('配置更新成功');
        await fetchConfigs();
        onSuccess?.(result.data);
        return true;
      } else {
        const errorData = await response.json();
        message.error(`更新配置失败: ${errorData.detail || '未知错误'}`);
        return false;
      }
    } catch (error) {
      console.error('更新配置错误:', error);
      message.error('更新配置失败');
      return false;
    }
  };

  const deleteConfig = async (configId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/mcp/gateway/configs/${configId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        message.success('配置删除成功');
        await fetchConfigs();
        return true;
      } else {
        const errorData = await response.json();
        message.error(`删除配置失败: ${errorData.detail || '未知错误'}`);
        return false;
      }
    } catch (error) {
      console.error('删除配置错误:', error);
      message.error('删除配置失败');
      return false;
    }
  };


  // 初始化数据
  useEffect(() => {
    fetchConfigs();
  }, []);

  // 过滤配置
  const filteredConfigs = configs.filter(config => {
    const matchSearch = !searchText || 
      config.name.toLowerCase().includes(searchText.toLowerCase()) ||
      config.tenant.toLowerCase().includes(searchText.toLowerCase());
    const matchTenant = !tenantFilter || config.tenant === tenantFilter;
    return matchSearch && matchTenant;
  });

  // 转换为YAML格式
  const toYaml = (data: any) => {
    try {
      return dump(data, { 
        indent: 2, 
        lineWidth: -1, 
        noRefs: true, 
        sortKeys: false 
      });
    } catch (error) {
      return JSON.stringify(data, null, 2);
    }
  };

  // 查看配置详情
  const handleViewConfig = (config: MCPGatewayConfig) => {
    setSelectedConfig(config);
    setConfigDetailModal(true);
  };

  // 删除配置
  const handleDeleteConfig = async (configId: number) => {
    await deleteConfig(configId);
  };

  // 添加配置
  const handleAddConfig = () => {
    setEditingConfig(null);
    form.resetFields();
    setConfigFormModal(true);
  };

  // 编辑配置
  const handleEditConfig = (config: MCPGatewayConfig) => {
    setEditingConfig(config);
    
    // 处理工具配置中的headers字段，确保它们是字符串格式
    const processedTools = (config.tools || []).map(tool => ({
      ...tool,
      headers: typeof tool.headers === 'object' && tool.headers !== null 
        ? JSON.stringify(tool.headers, null, 2) 
        : tool.headers
    }));
    
    form.setFieldsValue({
      name: config.name,
      tenant: config.tenant,
      routers: config.routers || [],
      servers: config.servers || [],
      tools: processedTools,
      prompts: config.prompts || [],
      mcp_servers: config.mcp_servers || []
    });
    setConfigFormModal(true);
  };

  // 保存配置（新增或编辑）
  const handleSaveConfig = async (values: any) => {
    try {
      // 处理工具配置中的headers字段，将字符串转换为对象
      const processedTools = (values.tools || []).map(tool => ({
        ...tool,
        headers: tool.headers && typeof tool.headers === 'string' 
          ? (() => {
              try {
                return JSON.parse(tool.headers);
              } catch {
                return {};
              }
            })()
          : tool.headers
      }));
      
      const configData = {
        name: values.name,
        tenant: values.tenant || 'default',
        routers: values.routers || [],
        servers: values.servers || [],
        tools: processedTools,
        prompts: values.prompts || [],
        mcp_servers: values.mcp_servers || []
      };

      let success = false;
      if (editingConfig) {
        success = await updateConfig(editingConfig.id, configData);
      } else {
        success = await createConfig(configData);
      }

      if (success) {
        setConfigFormModal(false);
        form.resetFields();
      }
    } catch (error) {
      message.error('配置保存失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<MCPGatewayConfig> = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string) => (
        <Space>
          <SettingOutlined />
          <span className="font-medium">{name}</span>
        </Space>
      )
    },
    {
      title: '租户',
      dataIndex: 'tenant',
      key: 'tenant',
      width: 100,
      render: (tenant: string) => (
        <Tag color="blue">{tenant}</Tag>
      )
    },
    {
      title: '路由数量',
      key: 'routersCount',
      width: 100,
      render: (_, record: MCPGatewayConfig) => (
        <span>{record.routers?.length || 0}</span>
      )
    },
    {
      title: '服务器数量',
      key: 'serversCount',
      width: 100,
      render: (_, record: MCPGatewayConfig) => (
        <span>{record.servers?.length || 0}</span>
      )
    },
    {
      title: '工具数量',
      key: 'toolsCount',
      width: 100,
      render: (_, record: MCPGatewayConfig) => (
        <span>{record.tools?.length || 0}</span>
      )
    },
    {
      title: '创建者',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 120
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      render: (time: string) => time?.replace('T', ' ').slice(0, 16) || '-'
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 150,
      render: (time: string) => time?.replace('T', ' ').slice(0, 16) || '-'
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_, record: MCPGatewayConfig) => (
        <Space size="small">
          <Button 
            type="text" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewConfig(record)}
            title="查看详情"
          />
          <Button 
            type="text" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEditConfig(record)}
            title="编辑"
          />
          <Popconfirm
            title="删除配置"
            description="确定要删除这个MCP Gateway配置吗？删除后无法恢复。"
            onConfirm={() => handleDeleteConfig(record.id)}
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
    <Card title="MCP Gateway配置管理">
      <div className="mb-4">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索配置名称、租户"
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Select
              placeholder="租户筛选"
              allowClear
              style={{ width: '100%' }}
              value={tenantFilter}
              onChange={setTenantFilter}
            >
              <Option value="default">default</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={12}>
            <Space>
              <Button 
                icon={<ReloadOutlined />}
                onClick={fetchConfigs}
                loading={loading}
              >
                刷新
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleAddConfig}
              >
                添加配置
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      <Table
        columns={columns}
        dataSource={filteredConfigs}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1000 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 个配置`,
          pageSizeOptions: ['10', '20', '50'],
          defaultPageSize: 10
        }}
      />

      {/* 配置详情模态框 */}
      <Modal
        title="MCP Gateway配置详情"
        open={configDetailModal}
        onCancel={() => setConfigDetailModal(false)}
        footer={null}
        width={900}
      >
        {selectedConfig && (
          <div>
            <div style={{ marginBottom: 12 }}>
              <Space>
                <Tag color="blue">配置名称: {selectedConfig.name}</Tag>
                <Tag color="green">租户: {selectedConfig.tenant}</Tag>
                <Tag color="purple">配置ID: {selectedConfig.config_id}</Tag>
                <Tag>创建者: {selectedConfig.create_by}</Tag>
              </Space>
            </div>
            <pre style={{ 
              background: isDark ? '#374151' : '#f5f5f5',
              padding: 16,
              borderRadius: 4,
              maxHeight: 500,
              overflow: 'auto',
              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
              border: isDark ? '1px solid #4b5563' : '1px solid #d1d5db'
            }}>
              {toYaml({
                name: selectedConfig.name,
                tenant: selectedConfig.tenant,
                routers: selectedConfig.routers || [],
                servers: selectedConfig.servers || [], 
                tools: selectedConfig.tools || [],
                prompts: selectedConfig.prompts || [],
                mcpServers: selectedConfig.mcp_servers || [],
                createdAt: selectedConfig.create_time,
                updatedAt: selectedConfig.update_time,
                metadata: {
                  id: selectedConfig.id,
                  config_id: selectedConfig.config_id,
                  create_by: selectedConfig.create_by,
                  update_by: selectedConfig.update_by
                }
              })}
            </pre>
          </div>
        )}
      </Modal>

      {/* 配置表单模态框 */}
      <Modal
        title={editingConfig ? "编辑MCP Gateway配置" : "添加MCP Gateway配置"}
        open={configFormModal}
        onCancel={() => setConfigFormModal(false)}
        footer={null}
        width={1000}
        style={{ top: 20 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveConfig}
          scrollToFirstError
        >
          {/* 使用说明 */}
          <Card title="使用说明" size="small" style={{ marginBottom: 16 }}>
            <Collapse
              ghost
              items={[
                {
                  key: 'instructions',
                  label: '📖 如何配置MCP Gateway？点击展开查看详细说明',
                  children: (
                    <div style={{ color: isDark ? '#d1d5db' : '#374151', lineHeight: 1.6 }}>
                      <div style={{ marginBottom: 16 }}>
                        <h4 style={{ margin: '0 0 8px 0', color: isDark ? '#f3f4f6' : '#1f2937' }}>🔧 配置步骤：</h4>
                        <ol style={{ paddingLeft: 20, margin: 0 }}>
                          <li><strong>工具配置</strong> - 首先定义全局工具库，包含工具名称、HTTP方法、端点地址等</li>
                          <li><strong>HTTP服务</strong> - 创建HTTP服务器，并从工具库中选择绑定的工具</li>
                          <li><strong>MCP服务</strong> - 配置MCP服务器连接（可选）</li>
                          <li><strong>路由配置</strong> - 设置访问路径和前缀</li>
                          <li><strong>提示词配置</strong> - 添加提示词模板（可选）</li>
                        </ol>
                      </div>
                      
                      <div style={{ marginBottom: 16 }}>
                        <h4 style={{ margin: '0 0 8px 0', color: isDark ? '#f3f4f6' : '#1f2937' }}>💡 重要提示：</h4>
                        <ul style={{ paddingLeft: 20, margin: 0 }}>
                          <li>工具配置是基础，其他服务会引用这些工具</li>
                          <li>HTTP服务的"允许的工具"字段会自动从工具配置中获取选项</li>
                          <li>路由配置中的"服务器名称"需要与HTTP服务或MCP服务的名称对应</li>
                          <li>响应体模板和请求头有默认值，通常无需修改</li>
                        </ul>
                      </div>
                      
                      <div>
                        <h4 style={{ margin: '0 0 8px 0', color: isDark ? '#f3f4f6' : '#1f2937' }}>📋 配置示例：</h4>
                        <div style={{ 
                          background: isDark ? '#374151' : '#f9fafb', 
                          padding: 12, 
                          borderRadius: 6,
                          fontSize: '13px',
                          fontFamily: 'Monaco, Consolas, monospace'
                        }}>
                          <div>1. 工具配置：systeminfo (POST) → http://localhost:8000/api/v1/tools/system</div>
                          <div>2. HTTP服务：nn (绑定systeminfo工具)</div>
                          <div>3. 路由配置：nn → /gateway/9xuv</div>
                        </div>
                      </div>
                    </div>
                  )
                }
              ]}
            />
          </Card>

          {/* 基本信息 */}
          <Card title="基本信息" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="配置名称"
                  name="name"
                  rules={[
                    { required: true, message: '请输入配置名称' },
                    { max: 50, message: '配置名称不能超过50个字符' }
                  ]}
                >
                  <Input placeholder="例如：systemhaha" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label="租户名称"
                  name="tenant"
                  rules={[
                    { required: true, message: '请输入租户名称' },
                    { max: 50, message: '租户名称不能超过50个字符' }
                  ]}
                >
                  <Input placeholder="default" />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* Tab配置区域 */}
          <Card title="配置管理" size="small" style={{ marginBottom: 16 }}>
            <Tabs
              type="card"
              items={[
                {
                  key: 'tools',
                  label: <Space><ToolOutlined />工具配置</Space>,
                  children: (
                    <Form.List name="tools">
                      {(fields, { add, remove }) => (
                        <>
                          {fields.map(({ key, name, ...restField }) => {
                            const toggleExpand = (toolKey: number) => {
                              setExpandedTools(prev => ({
                                ...prev,
                                [toolKey]: !prev[toolKey]
                              }));
                            };
                            
                            const isExpanded = expandedTools[key] || false;
                            
                            return (
                              <Card key={key} size="small" style={{ marginBottom: 8, background: isDark ? '#374151' : '#fafafa' }}>
                                <Row gutter={16} align="middle">
                                  <Col span={6}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'name']}
                                      label="工具名称"
                                      rules={[{ required: true, message: '请输入工具名称' }]}
                                      style={{ marginBottom: isExpanded ? 24 : 0 }}
                                    >
                                      <Input placeholder="systeminfo" />
                                    </Form.Item>
                                  </Col>
                                  <Col span={4}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'method']}
                                      label="HTTP方法"
                                      rules={[{ required: true, message: '请选择HTTP方法' }]}
                                      style={{ marginBottom: isExpanded ? 24 : 0 }}
                                    >
                                      <Select placeholder="POST">
                                        <Select.Option value="GET">GET</Select.Option>
                                        <Select.Option value="POST">POST</Select.Option>
                                        <Select.Option value="PUT">PUT</Select.Option>
                                        <Select.Option value="DELETE">DELETE</Select.Option>
                                      </Select>
                                    </Form.Item>
                                  </Col>
                                  <Col span={10}>
                                    <Form.Item
                                      {...restField}
                                      name={[name, 'endpoint']}
                                      label="端点地址"
                                      rules={[{ required: true, message: '请输入端点地址' }]}
                                      style={{ marginBottom: isExpanded ? 24 : 0 }}
                                    >
                                      <Input placeholder="http://localhost:8000/api/v1/mcp/tools/system_info" />
                                    </Form.Item>
                                  </Col>
                                  <Col span={2}>
                                    <Button 
                                      type="text" 
                                      icon={isExpanded ? <UpOutlined /> : <DownOutlined />}
                                      onClick={() => toggleExpand(key)}
                                      title={isExpanded ? "收起详细配置" : "展开详细配置"}
                                    />
                                  </Col>
                                  <Col span={2}>
                                    <Button 
                                      type="text" 
                                      danger 
                                      icon={<DeleteOutlined />} 
                                      onClick={() => remove(name)}
                                      title="删除工具"
                                    />
                                  </Col>
                                </Row>
                                {isExpanded && (
                                  <Row gutter={16}>
                                    <Col span={6}>
                                      <Form.Item
                                        {...restField}
                                        name={[name, 'description']}
                                        label="描述"
                                      >
                                        <Input placeholder="工具功能描述" />
                                      </Form.Item>
                                    </Col>
                                    <Col span={6}>
                                      <Form.Item
                                        {...restField}
                                        name={[name, 'requestBody']}
                                        label="请求体"
                                      >
                                        <TextArea 
                                          rows={1} 
                                          placeholder='{"key": "value"}' 
                                        />
                                      </Form.Item>
                                    </Col>
                                    <Col span={6}>
                                      <Form.Item
                                        {...restField}
                                        name={[name, 'headers']}
                                        label="请求头"
                                        initialValue='{"Content-Type": "application/json"}'
                                        normalize={(value) => {
                                          // 如果是对象，转换为字符串
                                          if (typeof value === 'object' && value !== null) {
                                            return JSON.stringify(value, null, 2);
                                          }
                                          return value;
                                        }}
                                        getValueFromEvent={(e) => {
                                          // 确保始终返回字符串
                                          const value = e.target.value;
                                          return value;
                                        }}
                                      >
                                        <TextArea 
                                          rows={1} 
                                          placeholder='{"Content-Type": "application/json"}' 
                                        />
                                      </Form.Item>
                                    </Col>
                                    <Col span={6}>
                                      <Form.Item
                                        {...restField}
                                        name={[name, 'responseBody']}
                                        label="响应体模板"
                                        initialValue="{{.Response.Body}}"
                                      >
                                        <Input placeholder="{{.Response.Body}}" />
                                      </Form.Item>
                                    </Col>
                                  </Row>
                                )}
                              </Card>
                            );
                          })}
                          <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />} block>
                            添加工具
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )
                },
                {
                  key: 'servers',
                  label: <Space><CloudServerOutlined />HTTP服务</Space>,
                  children: (
                    <Form.List name="servers">
                      {(fields, { add, remove }) => (
                        <>
                          {fields.map(({ key, name, ...restField }) => (
                            <Card key={key} size="small" style={{ marginBottom: 8, background: isDark ? '#374151' : '#fafafa' }}>
                              <Row gutter={16} align="middle">
                                <Col span={8}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'name']}
                                    label="服务器名称"
                                    rules={[{ required: true, message: '请输入服务器名称' }]}
                                  >
                                    <Input placeholder="nn" />
                                  </Form.Item>
                                </Col>
                                <Col span={10}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'description']}
                                    label="描述"
                                  >
                                    <Input placeholder="服务器描述" />
                                  </Form.Item>
                                </Col>
                                <Col span={4}>
                                  <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => 
                                    JSON.stringify(prevValues.tools) !== JSON.stringify(currentValues.tools)
                                  }>
                                    {({ getFieldValue }) => {
                                      const tools = getFieldValue('tools') || [];
                                      const toolOptions = tools.map((tool: any, index: number) => ({
                                        label: tool?.name || `工具${index + 1}`,
                                        value: tool?.name || `tool${index + 1}`
                                      }));
                                      
                                      return (
                                        <Form.Item
                                          {...restField}
                                          name={[name, 'allowedTools']}
                                          label="允许的工具"
                                        >
                                          <Select
                                            mode="multiple"
                                            placeholder="从工具列表中选择"
                                            style={{ width: '100%' }}
                                            options={toolOptions}
                                            allowClear
                                          />
                                        </Form.Item>
                                      );
                                    }}
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Button 
                                    type="text" 
                                    danger 
                                    icon={<MinusCircleOutlined />} 
                                    onClick={() => remove(name)}
                                    title="删除服务器"
                                  />
                                </Col>
                              </Row>
                            </Card>
                          ))}
                          <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />} block>
                            添加HTTP服务
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )
                },
                {
                  key: 'mcp_servers',
                  label: <Space><ApiOutlined />MCP服务</Space>,
                  children: (
                    <Form.List name="mcp_servers">
                      {(fields, { add, remove }) => (
                        <>
                          {fields.map(({ key, name, ...restField }) => (
                            <Card key={key} size="small" style={{ marginBottom: 8, background: isDark ? '#374151' : '#fafafa' }}>
                              <Row gutter={16} align="middle">
                                <Col span={4}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'type']}
                                    label="类型"
                                    rules={[{ required: true, message: '请选择类型' }]}
                                  >
                                    <Select placeholder="stdio">
                                      <Select.Option value="stdio">stdio</Select.Option>
                                      <Select.Option value="sse">sse</Select.Option>
                                      <Select.Option value="streamable-http">streamable-http</Select.Option>
                                    </Select>
                                  </Form.Item>
                                </Col>
                                <Col span={6}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'name']}
                                    label="服务器名称"
                                    rules={[{ required: true, message: '请输入服务器名称' }]}
                                  >
                                    <Input placeholder="server-name" />
                                  </Form.Item>
                                </Col>
                                <Col span={4}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'policy']}
                                    label="策略"
                                  >
                                    <Select placeholder="onStart">
                                      <Select.Option value="onStart">onStart</Select.Option>
                                      <Select.Option value="onDemand">onDemand</Select.Option>
                                    </Select>
                                  </Form.Item>
                                </Col>
                                <Col span={6}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'url']}
                                    label="URL/命令"
                                  >
                                    <Input placeholder="http://localhost:8000" />
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'preinstalled']}
                                    label="预装"
                                    valuePropName="checked"
                                  >
                                    <Switch />
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Button 
                                    type="text" 
                                    danger 
                                    icon={<MinusCircleOutlined />} 
                                    onClick={() => remove(name)}
                                    title="删除MCP服务器"
                                  />
                                </Col>
                              </Row>
                            </Card>
                          ))}
                          <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />} block>
                            添加MCP服务
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )
                },
                {
                  key: 'routes',
                  label: <Space><GlobalOutlined />路由配置</Space>,
                  children: (
                    <Form.List name="routers">
                      {(fields, { add, remove }) => (
                        <>
                          {fields.map(({ key, name, ...restField }) => (
                            <Card key={key} size="small" style={{ marginBottom: 8, background: isDark ? '#374151' : '#fafafa' }}>
                              <Row gutter={16} align="middle">
                                <Col span={8}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'server']}
                                    label="服务器名称"
                                    rules={[{ required: true, message: '请输入服务器名称' }]}
                                  >
                                    <Input placeholder="nn" />
                                  </Form.Item>
                                </Col>
                                <Col span={7}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'prefix']}
                                    label="路由前缀"
                                    rules={[{ required: true, message: '请输入路由前缀' }]}
                                  >
                                    <Input placeholder="/gateway/9xuv" />
                                  </Form.Item>
                                </Col>
                                <Col span={7}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'ssePrefix']}
                                    label="SSE前缀"
                                  >
                                    <Input placeholder="/gateway/9xuv" />
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Button 
                                    type="text" 
                                    danger 
                                    icon={<MinusCircleOutlined />} 
                                    onClick={() => remove(name)}
                                    title="删除路由"
                                  />
                                </Col>
                              </Row>
                            </Card>
                          ))}
                          <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />} block>
                            添加路由
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )
                },
                {
                  key: 'prompts',
                  label: <Space><BulbOutlined />提示词配置</Space>,
                  children: (
                    <Form.List name="prompts">
                      {(fields, { add, remove }) => (
                        <>
                          {fields.map(({ key, name, ...restField }) => (
                            <Card key={key} size="small" style={{ marginBottom: 8, background: isDark ? '#374151' : '#fafafa' }}>
                              <Row gutter={16} align="middle">
                                <Col span={6}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'name']}
                                    label="提示词名称"
                                    rules={[{ required: true, message: '请输入提示词名称' }]}
                                  >
                                    <Input placeholder="prompt_name" />
                                  </Form.Item>
                                </Col>
                                <Col span={14}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'content']}
                                    label="提示词内容"
                                    rules={[{ required: true, message: '请输入提示词内容' }]}
                                  >
                                    <TextArea rows={2} placeholder="提示词模板内容" />
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Form.Item
                                    {...restField}
                                    name={[name, 'enabled']}
                                    label="启用"
                                    valuePropName="checked"
                                  >
                                    <Switch />
                                  </Form.Item>
                                </Col>
                                <Col span={2}>
                                  <Button 
                                    type="text" 
                                    danger 
                                    icon={<MinusCircleOutlined />} 
                                    onClick={() => remove(name)}
                                    title="删除提示词"
                                  />
                                </Col>
                              </Row>
                            </Card>
                          ))}
                          <Button type="dashed" onClick={() => add()} icon={<PlusOutlined />} block>
                            添加提示词
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )
                }
              ]}
            />
          </Card>

          <Form.Item>
            <div className="flex justify-end gap-2">
              <Button onClick={() => setConfigFormModal(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingConfig ? '更新' : '添加'}
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default MCPGatewayManagement;