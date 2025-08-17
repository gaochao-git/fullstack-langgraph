import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Tag,
  App,
  Popconfirm,
  Row,
  Col,
  Modal,
  Form,
  Upload,
  message as antdMessage,
  Descriptions,
  Badge,
  Collapse,
  Select,
  Divider
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  UploadOutlined,
  ApiOutlined,
  ToolOutlined,
  CopyOutlined,
  InfoCircleOutlined,
  RobotOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { useTheme } from '@/hooks/ThemeContext';
import { omind_get, omind_post, omind_put, omind_patch, omind_del } from '@/utils/base_api';
import type { ColumnsType } from 'antd/es/table';

const { Search } = Input;
const { TextArea } = Input;
const { Panel } = Collapse;
const { Option } = Select;

interface OpenAPIConfig {
  id: number;
  mcp_server_prefix: string;
  mcp_tool_name: string;
  mcp_tool_enabled: number;
  openapi_schema: string | object;
  auth_config: string | object;
  extra_config: string | object;
  is_deleted: number;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

interface OpenAPIConfigTableProps {
  onSuccess?: (config: any) => void;
}

const OpenAPIConfigTable: React.FC<OpenAPIConfigTableProps> = ({ onSuccess }) => {
  const { isDark } = useTheme();
  const { message } = App.useApp();
  const [form] = Form.useForm();

  // 表格状态
  const [configs, setConfigs] = useState<OpenAPIConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');

  // 模态框状态
  const [formModal, setFormModal] = useState(false);
  const [detailModal, setDetailModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<OpenAPIConfig | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<OpenAPIConfig | null>(null);
  const [openApiSpec, setOpenApiSpec] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [authConfig, setAuthConfig] = useState<any>({});
  const [timeoutConfig, setTimeoutConfig] = useState<any>({});

  // 加载配置列表
  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await omind_get('/api/v1/mcp/openapi/configs');
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok' && result.data && result.data.items) {
          setConfigs(result.data.items);
        } else {
          message.error(result.msg || '获取配置列表失败');
        }
      } else {
        message.error('获取配置列表失败，请检查网络连接');
      }
    } catch (error: any) {
      message.error('获取配置列表失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取数据
  useEffect(() => {
    fetchConfigs();
  }, []);

  // OpenAPI 模板
  const openapiTemplates = {
    'rest_api': {
      name: 'REST API 服务',
      description: '通用 REST API 服务模板',
      template: {
        "openapi": "3.0.0",
        "info": {
          "title": "API 服务",
          "description": "通用 API 服务接口",
          "version": "1.0.0"
        },
        "servers": [
          {
            "url": "https://api.example.com",
            "description": "生产环境"
          }
        ],
        "paths": {
          "/items": {
            "get": {
              "summary": "获取项目列表",
              "operationId": "getItems",
              "parameters": [
                {
                  "name": "page",
                  "in": "query",
                  "description": "页码",
                  "schema": {
                    "type": "integer",
                    "default": 1
                  }
                },
                {
                  "name": "limit",
                  "in": "query",
                  "description": "每页数量",
                  "schema": {
                    "type": "integer",
                    "default": 10
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "成功",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "object",
                        "properties": {
                          "items": {
                            "type": "array",
                            "items": {
                              "type": "object"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            },
            "post": {
              "summary": "创建项目",
              "operationId": "createItem",
              "requestBody": {
                "required": true,
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "object",
                      "properties": {
                        "name": {
                          "type": "string",
                          "description": "项目名称"
                        },
                        "description": {
                          "type": "string",
                          "description": "项目描述"
                        }
                      },
                      "required": ["name"]
                    }
                  }
                }
              },
              "responses": {
                "201": {
                  "description": "创建成功"
                }
              }
            }
          }
        }
      }
    },
    'weather_api': {
      name: '天气 API',
      description: '天气查询 API 模板',
      template: {
        "openapi": "3.0.0",
        "info": {
          "title": "天气 API",
          "description": "天气信息查询接口",
          "version": "1.0.0"
        },
        "servers": [
          {
            "url": "https://api.weather.com",
            "description": "天气服务"
          }
        ],
        "paths": {
          "/weather/current": {
            "get": {
              "summary": "获取当前天气",
              "operationId": "getCurrentWeather",
              "parameters": [
                {
                  "name": "city",
                  "in": "query",
                  "required": true,
                  "description": "城市名称",
                  "schema": {
                    "type": "string"
                  }
                },
                {
                  "name": "units",
                  "in": "query",
                  "description": "温度单位",
                  "schema": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "成功",
                  "content": {
                    "application/json": {
                      "schema": {
                        "type": "object",
                        "properties": {
                          "temperature": {
                            "type": "number",
                            "description": "温度"
                          },
                          "humidity": {
                            "type": "number",
                            "description": "湿度"
                          },
                          "description": {
                            "type": "string",
                            "description": "天气描述"
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          },
          "/weather/forecast": {
            "get": {
              "summary": "获取天气预报",
              "operationId": "getWeatherForecast",
              "parameters": [
                {
                  "name": "city",
                  "in": "query",
                  "required": true,
                  "description": "城市名称",
                  "schema": {
                    "type": "string"
                  }
                },
                {
                  "name": "days",
                  "in": "query",
                  "description": "预报天数",
                  "schema": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 7,
                    "default": 3
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "成功"
                }
              }
            }
          }
        }
      }
    },
    'user_management': {
      name: '用户管理 API',
      description: '用户管理系统 API 模板',
      template: {
        "openapi": "3.0.0",
        "info": {
          "title": "用户管理 API",
          "description": "用户管理系统接口",
          "version": "1.0.0"
        },
        "servers": [
          {
            "url": "https://api.example.com/v1",
            "description": "用户管理服务"
          }
        ],
        "paths": {
          "/users": {
            "get": {
              "summary": "获取用户列表",
              "operationId": "getUsers",
              "parameters": [
                {
                  "name": "page",
                  "in": "query",
                  "schema": {
                    "type": "integer",
                    "default": 1
                  }
                },
                {
                  "name": "status",
                  "in": "query",
                  "schema": {
                    "type": "string",
                    "enum": ["active", "inactive"]
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "成功"
                }
              }
            },
            "post": {
              "summary": "创建用户",
              "operationId": "createUser",
              "requestBody": {
                "required": true,
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "object",
                      "properties": {
                        "username": {
                          "type": "string",
                          "description": "用户名"
                        },
                        "email": {
                          "type": "string",
                          "format": "email",
                          "description": "邮箱"
                        },
                        "role": {
                          "type": "string",
                          "enum": ["admin", "user"],
                          "description": "角色"
                        }
                      },
                      "required": ["username", "email"]
                    }
                  }
                }
              },
              "responses": {
                "201": {
                  "description": "创建成功"
                }
              }
            }
          },
          "/users/{userId}": {
            "get": {
              "summary": "获取用户详情",
              "operationId": "getUserById",
              "parameters": [
                {
                  "name": "userId",
                  "in": "path",
                  "required": true,
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "responses": {
                "200": {
                  "description": "成功"
                }
              }
            },
            "put": {
              "summary": "更新用户",
              "operationId": "updateUser",
              "parameters": [
                {
                  "name": "userId",
                  "in": "path",
                  "required": true,
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "requestBody": {
                "required": true,
                "content": {
                  "application/json": {
                    "schema": {
                      "type": "object",
                      "properties": {
                        "username": {
                          "type": "string"
                        },
                        "email": {
                          "type": "string",
                          "format": "email"
                        },
                        "status": {
                          "type": "string",
                          "enum": ["active", "inactive"]
                        }
                      }
                    }
                  }
                }
              },
              "responses": {
                "200": {
                  "description": "更新成功"
                }
              }
            },
            "delete": {
              "summary": "删除用户",
              "operationId": "deleteUser",
              "parameters": [
                {
                  "name": "userId",
                  "in": "path",
                  "required": true,
                  "schema": {
                    "type": "integer"
                  }
                }
              ],
              "responses": {
                "204": {
                  "description": "删除成功"
                }
              }
            }
          }
        }
      }
    }
  };

  // 认证配置案例
  const authExamples = {
    'none': {},
    'api_key': {
      "api_key": "your-api-key-here",
      "header_name": "X-API-Key"
    },
    'bearer': {
      "token": "your-bearer-token-here",
      "token_prefix": "Bearer"
    },
    'basic': {
      "username": "your-username",
      "password": "your-password"
    },
    'oauth2': {
      "client_id": "your-client-id",
      "client_secret": "your-client-secret",
      "token_url": "https://api.example.com/oauth/token",
      "scope": "read write"
    }
  };

  // 超时配置案例
  const timeoutExamples = {
    "connect_timeout": 5,
    "read_timeout": 30,
    "write_timeout": 10,
    "total_timeout": 60,
    "retry_count": 3,
    "retry_delay": 1,
    "retry_backoff": 2.0,
    "max_retry_delay": 30
  };

  // 过滤数据
  const filteredConfigs = configs.filter(config =>
    (config.mcp_server_prefix || '').toLowerCase().includes(searchText.toLowerCase()) ||
    (config.mcp_tool_name || '').toLowerCase().includes(searchText.toLowerCase())
  );

  // 处理文件上传
  const handleFileUpload = (file: any) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setOpenApiSpec(content);
      form.setFieldsValue({ openapi_spec: content });
    };
    reader.readAsText(file);
    return false; // 阻止自动上传
  };

  // 选择模板
  const handleTemplateSelect = (templateKey: string) => {
    if (templateKey && openapiTemplates[templateKey]) {
      const template = openapiTemplates[templateKey];
      const specJson = JSON.stringify(template.template, null, 2);
      setOpenApiSpec(specJson);
      form.setFieldsValue({ 
        openapi_spec: specJson
      });
    }
  };

  // 新增配置
  const handleAddConfig = () => {
    setEditingConfig(null);
    form.resetFields();
    setOpenApiSpec('');
    setSelectedTemplate('');
    setAuthConfig({});
    setTimeoutConfig(timeoutExamples);
    setFormModal(true);
  };

  // 编辑配置
  const handleEditConfig = async (config: OpenAPIConfig) => {
    try {
      const response = await omind_get(`/api/v1/mcp/openapi/configs/${config.id}`);
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok') {
          const fullConfig = result.data;
          setEditingConfig(fullConfig);
          form.setFieldsValue({
            mcp_server_prefix: fullConfig.mcp_server_prefix,
            mcp_tool_name: fullConfig.mcp_tool_name,
            mcp_tool_enabled: fullConfig.mcp_tool_enabled,
            openapi_spec: typeof fullConfig.openapi_schema === 'string' 
              ? fullConfig.openapi_schema 
              : JSON.stringify(fullConfig.openapi_schema, null, 2)
          });
          setOpenApiSpec(typeof fullConfig.openapi_schema === 'string' 
            ? fullConfig.openapi_schema 
            : JSON.stringify(fullConfig.openapi_schema, null, 2));
          setAuthConfig(fullConfig.auth_config || {});
          setTimeoutConfig(fullConfig.extra_config || timeoutExamples);
          setFormModal(true);
        } else {
          message.error(result.msg || '获取配置详情失败');
        }
      }
    } catch (error: any) {
      message.error('获取配置详情失败: ' + (error.message || '未知错误'));
    }
  };

  // 查看配置详情
  const handleViewConfig = async (config: OpenAPIConfig) => {
    try {
      const response = await omind_get(`/api/v1/mcp/openapi/configs/${config.id}`);
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok') {
          setSelectedConfig(result.data);
          setDetailModal(true);
        } else {
          message.error(result.msg || '获取配置详情失败');
        }
      }
    } catch (error: any) {
      message.error('获取配置详情失败: ' + (error.message || '未知错误'));
    }
  };

  // 删除配置
  const handleDeleteConfig = async (configId: number) => {
    try {
      const response = await omind_del(`/api/v1/mcp/openapi/configs/${configId}`);
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok') {
          message.success('配置删除成功');
          fetchConfigs(); // 重新加载列表
        } else {
          message.error(result.msg || '删除配置失败');
        }
      } else {
        message.error('删除配置失败，请检查网络连接');
      }
    } catch (error: any) {
      message.error('删除配置失败: ' + (error.message || '未知错误'));
    }
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    try {
      const requestData = {
        mcp_server_prefix: values.mcp_server_prefix,
        mcp_tool_name: values.mcp_tool_name,
        mcp_tool_enabled: values.mcp_tool_enabled || 0,
        openapi_schema: values.openapi_spec,
        auth_config: JSON.stringify(authConfig),
        extra_config: JSON.stringify(timeoutConfig),
        create_by: 'frontend_user'
      };

      let response;
      if (editingConfig) {
        // 更新配置
        const updateData = {
          ...requestData,
          update_by: 'frontend_user'
        };
        delete updateData.create_by;
        response = await omind_put(`/api/v1/mcp/openapi/configs/${editingConfig.id}`, updateData);
      } else {
        // 创建配置
        response = await omind_post('/api/v1/mcp/openapi/configs', requestData);
      }

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') {
          message.success(`${editingConfig ? '更新' : '创建'}成功！`);
          setFormModal(false);
          form.resetFields();
          setOpenApiSpec('');
          fetchConfigs(); // 重新加载列表
          onSuccess?.(data.data);
        } else {
          message.error(data.msg || `${editingConfig ? '更新' : '创建'}失败`);
        }
      } else {
        message.error(`${editingConfig ? '更新' : '创建'}失败，请检查网络连接`);
      }
    } catch (error: any) {
      message.error(`${editingConfig ? '更新' : '创建'}失败: ` + (error.message || '未知错误'));
    }
  };

  // 启用/禁用配置
  const handleToggleEnable = async (config: OpenAPIConfig) => {
    try {
      const newEnabled = config.mcp_tool_enabled === 1 ? false : true;
      const response = await omind_patch(`/api/v1/mcp/openapi/configs/${config.id}/enable?enabled=${newEnabled}`, {});
      
      if (response.ok) {
        const result = await response.json();
        if (result.status === 'ok') {
          message.success(`配置已${newEnabled ? '启用' : '禁用'}`);
          fetchConfigs(); // 重新加载列表
        } else {
          message.error(result.msg || '切换状态失败');
        }
      } else {
        message.error('切换状态失败，请检查网络连接');
      }
    } catch (error: any) {
      message.error('切换状态失败: ' + (error.message || '未知错误'));
    }
  };



  // 复制配置到剪贴板
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  // 表格列定义
  const columns: ColumnsType<OpenAPIConfig> = [
    {
      title: 'MCP服务前缀',
      dataIndex: 'mcp_server_prefix',
      key: 'mcp_server_prefix',
      width: 150,
      render: (prefix: string) => (
        <span>{prefix}</span>
      )
    },
    {
      title: '工具名称',
      dataIndex: 'mcp_tool_name',
      key: 'mcp_tool_name',
      width: 200,
      render: (name: string) => (
        <span className="font-medium">{name}</span>
      )
    },
    {
      title: '状态',
      dataIndex: 'mcp_tool_enabled',
      key: 'mcp_tool_enabled',
      width: 100,
      align: 'center',
      render: (enabled: number) => (
        <Badge
          status={enabled === 1 ? 'success' : 'default'}
          text={enabled === 1 ? '启用' : '禁用'}
        />
      )
    },
    {
      title: '创建者',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 120,
      render: (creator: string) => (
        <div className="text-sm text-gray-600">{creator}</div>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      render: (time: string) => (
        <div className="text-sm text-gray-500">
          {time?.replace('T', ' ').slice(0, 16) || '-'}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record: OpenAPIConfig) => (
        <Space size="small">
          <Button
            type="primary"
            icon={<EyeOutlined />}
            onClick={() => handleViewConfig(record)}
            title="查看详情"
            style={{ backgroundColor: '#1890ff' }}
          />
          <Button
            type="default"
            icon={<EditOutlined />}
            onClick={() => handleEditConfig(record)}
            title="编辑"
            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a', color: 'white' }}
          />
          <Button
            type="default"
            onClick={() => handleToggleEnable(record)}
            title={record.mcp_tool_enabled === 1 ? '禁用' : '启用'}
            style={{ 
              backgroundColor: record.mcp_tool_enabled === 1 ? '#fa8c16' : '#722ed1', 
              borderColor: record.mcp_tool_enabled === 1 ? '#fa8c16' : '#722ed1', 
              color: 'white' 
            }}
          >
            {record.mcp_tool_enabled === 1 ? '禁用' : '启用'}
          </Button>
          <Popconfirm
            title="删除工具"
            description="确定要删除这个工具吗？删除后无法恢复。"
            onConfirm={() => handleDeleteConfig(record.id)}
            okText="确定"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="primary"
              icon={<DeleteOutlined />}
              danger
              title="删除"
              style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' }}
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card title="OpenAPI MCP 工具管理">
        <div className="mb-4">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索MCP服务前缀、工具名称"
                allowClear
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={24} sm={12} md={16}>
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
                  新增工具
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
          scroll={{ x: 1200 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个工具`,
            pageSizeOptions: ['10', '20', '50'],
            defaultPageSize: 10
          }}
        />
      </Card>

      {/* 新增/编辑工具模态框 */}
      <Modal
        title={editingConfig ? '编辑工具配置' : '新增工具配置'}
        open={formModal}
        onCancel={() => setFormModal(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="mcp_server_prefix"
                label="MCP服务前缀"
                rules={[
                  { required: true, message: '请输入MCP服务前缀' },
                  { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线' }
                ]}
              >
                <Input placeholder="例如: jsonplaceholder_api" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="mcp_tool_name"
                label="工具名称"
                rules={[
                  { required: true, message: '请输入工具名称' },
                  { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和连字符' }
                ]}
              >
                <Input placeholder="例如: get_users" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="mcp_tool_enabled"
            label="是否启用"
          >
            <Select placeholder="选择是否启用" defaultValue={0}>
              <Option value={0}>禁用</Option>
              <Option value={1}>启用</Option>
            </Select>
          </Form.Item>

          <Form.Item label="OpenAPI 模板">
            <Select
              placeholder="选择模板快速开始"
              value={selectedTemplate}
              onChange={(value) => {
                setSelectedTemplate(value);
                handleTemplateSelect(value);
              }}
              allowClear
            >
              {Object.entries(openapiTemplates).map(([key, template]) => (
                <Option key={key} value={key}>
                  <div style={{ lineHeight: 1.4 }}>
                    <div style={{ fontWeight: 500, marginBottom: '2px' }}>{template.name}</div>
                    <div style={{ fontSize: '12px', color: '#666', opacity: 0.8 }}>{template.description}</div>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="openapi_spec"
            label="OpenAPI 规范"
            rules={[{ required: true, message: '请输入 OpenAPI 规范' }]}
          >
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ marginBottom: '8px', padding: '8px', background: '#f0f9ff', borderRadius: '4px', border: '1px solid #bae6fd' }}>
                  <div style={{ fontSize: '12px', color: '#0369a1', lineHeight: 1.4 }}>
                    <InfoCircleOutlined style={{ marginRight: '4px' }} />
                    <strong>说明：</strong> OpenAPI规范中包含API基础地址和描述信息，无需单独填写
                  </div>
                </div>
                <Space>
                  <Upload
                    accept=".json,.yaml,.yml"
                    beforeUpload={handleFileUpload}
                    showUploadList={false}
                  >
                    <Button icon={<UploadOutlined />}>上传 OpenAPI 文件</Button>
                  </Upload>
                  <Button 
                    type="link" 
                    icon={<InfoCircleOutlined />}
                    onClick={() => message.info('选择上方模板或直接粘贴 OpenAPI 3.0 规范 JSON')}
                  >
                    帮助
                  </Button>
                </Space>
                <TextArea
                  rows={12}
                  placeholder="粘贴 OpenAPI JSON 规范，或选择上方模板..."
                  value={openApiSpec}
                  onChange={(e) => {
                    setOpenApiSpec(e.target.value);
                    form.setFieldsValue({ openapi_spec: e.target.value });
                  }}
                />
              </Space>
            </div>
          </Form.Item>

          <Divider>高级配置（可选）</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="auth_type"
                label="认证类型"
              >
                <Select
                  placeholder="选择认证类型"
                  onChange={(value) => {
                    setAuthConfig(authExamples[value] || {});
                  }}
                >
                  <Option value="none">无认证</Option>
                  <Option value="api_key">API Key</Option>
                  <Option value="bearer">Bearer Token</Option>
                  <Option value="basic">Basic Auth</Option>
                  <Option value="oauth2">OAuth2</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="认证配置案例">
                <TextArea
                  rows={4}
                  value={JSON.stringify(authConfig, null, 2)}
                  onChange={(e) => {
                    try {
                      setAuthConfig(JSON.parse(e.target.value));
                    } catch (e) {
                      // 忽略解析错误，用户输入过程中可能不完整
                    }
                  }}
                  placeholder="认证参数配置 JSON"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="超时配置案例">
            <TextArea
              rows={3}
              value={JSON.stringify(timeoutConfig, null, 2)}
              onChange={(e) => {
                try {
                  setTimeoutConfig(JSON.parse(e.target.value));
                } catch (e) {
                  // 忽略解析错误
                }
              }}
              placeholder="超时和重试配置 JSON"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingConfig ? '更新工具' : '创建工具'}
              </Button>
              <Button onClick={() => setFormModal(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 工具详情模态框 */}
      <Modal
        title="工具详情"
        open={detailModal}
        onCancel={() => setDetailModal(false)}
        footer={null}
        width={900}
      >
        {selectedConfig && (
          <div>
            <Descriptions column={2} bordered>
              <Descriptions.Item label="MCP服务前缀" span={1}>
                <Tag color="blue">{selectedConfig.mcp_server_prefix}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="工具名称" span={1}>
                <span className="font-medium">{selectedConfig.mcp_tool_name}</span>
              </Descriptions.Item>
              <Descriptions.Item label="状态" span={1}>
                <Badge
                  status={selectedConfig.mcp_tool_enabled === 1 ? 'success' : 'default'}
                  text={selectedConfig.mcp_tool_enabled === 1 ? '启用' : '禁用'}
                />
              </Descriptions.Item>
              <Descriptions.Item label="创建者" span={1}>
                {selectedConfig.create_by}
              </Descriptions.Item>
              <Descriptions.Item label="创建时间" span={1}>
                {selectedConfig.create_time}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间" span={1}>
                {selectedConfig.update_time || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="OpenAPI规范" span={2}>
                <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                  <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '8px', borderRadius: '4px', margin: 0 }}>
                    {typeof selectedConfig.openapi_schema === 'string' 
                      ? selectedConfig.openapi_schema 
                      : JSON.stringify(selectedConfig.openapi_schema, null, 2)}
                  </pre>
                </div>
              </Descriptions.Item>
            </Descriptions>

            {selectedConfig.tools && selectedConfig.tools.length > 0 && (
              <div className="mt-4">
                <Collapse size="small">
                  <Panel
                    header={
                      <Space>
                        <ToolOutlined />
                        工具列表 ({selectedConfig.tools.length})
                      </Space>
                    }
                    key="tools"
                    extra={
                      <Button
                        type="link"
                        icon={<CopyOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          copyToClipboard(JSON.stringify(selectedConfig.tools, null, 2));
                        }}
                      >
                        复制
                      </Button>
                    }
                  >
                    <div className="space-y-3">
                      {selectedConfig.tools.map((tool: any, index: number) => (
                        <div
                          key={index}
                          className={`p-3 rounded border ${
                            isDark ? 'border-gray-600 bg-gray-700' : 'border-gray-200 bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <Space>
                              <Tag color="blue">{tool.method}</Tag>
                              <span className="font-mono text-sm">{tool.name}</span>
                            </Space>
                            <span className="text-xs text-gray-500">{tool.path}</span>
                          </div>
                          {tool.description && (
                            <div className="text-sm text-gray-600 mb-2">{tool.description}</div>
                          )}
                          {tool.parameters && tool.parameters.length > 0 && (
                            <div className="text-xs">
                              <span className="text-gray-500">参数: </span>
                              <Space size={4}>
                                {tool.parameters.map((param: any, idx: number) => (
                                  <Tag key={idx} size="small">
                                    {param.name} ({param.type})
                                  </Tag>
                                ))}
                              </Space>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </Panel>
                </Collapse>
              </div>
            )}
          </div>
        )}
      </Modal>


    </div>
  );
};

export default OpenAPIConfigTable;