import React, { useState } from 'react';
import {
  Card,
  Button,
  Input,
  Form,
  Upload,
  message,
  Space,
  Divider,
  Tag,
  Collapse,
  Row,
  Col,
  Alert,
  Spin
} from 'antd';
import {
  UploadOutlined,
  ApiOutlined,
  ToolOutlined,
  SendOutlined,
  CopyOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useTheme } from '../../../contexts/ThemeContext';
import { omind_post } from '../../../utils/base_api';

const { TextArea } = Input;
const { Panel } = Collapse;

interface OpenAPIConverterProps {
  onSuccess?: (config: any) => void;
}

interface ConvertedTool {
  name: string;
  description: string;
  method: string;
  path: string;
  parameters: any[];
}

interface ConvertResult {
  id: number;
  config_name: string;
  config_description: string;
  api_base_url: string;
  tools: ConvertedTool[];
  create_time: string;
}

const OpenAPIConverter: React.FC<OpenAPIConverterProps> = ({ onSuccess }) => {
  const { isDark } = useTheme();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [convertResult, setConvertResult] = useState<ConvertResult | null>(null);
  const [openApiSpec, setOpenApiSpec] = useState('');

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

  // 转换 OpenAPI 到 MCP
  const handleConvert = async (values: any) => {
    setLoading(true);
    try {
      let specData;
      try {
        specData = JSON.parse(values.openapi_spec);
      } catch (e) {
        // 尝试解析为 YAML（这里简化处理，实际项目可能需要 yaml 库）
        throw new Error('请提供有效的 JSON 格式的 OpenAPI 规范');
      }

      const response = await omind_post('/api/v1/mcp/openapi/convert', {
        config_name: values.name,
        config_description: values.description,
        api_base_url: values.base_url,
        openapi_spec_content: specData
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') {
          setConvertResult(data.data);
          message.success('OpenAPI 转换成功！');
          form.resetFields();
          setOpenApiSpec('');
          onSuccess?.(data.data);
        } else {
          message.error(data.msg || '转换失败');
        }
      } else {
        message.error('转换失败，请检查网络连接');
      }
    } catch (error: any) {
      message.error('转换失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  // 复制配置到剪贴板
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  return (
    <div className="space-y-4">
      {/* 转换表单 */}
      <Card
        title={
          <Space>
            <ApiOutlined />
            OpenAPI 规范转换
          </Space>
        }
        size="small"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleConvert}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="服务器名称"
                rules={[{ required: true, message: '请输入服务器名称' }]}
              >
                <Input placeholder="输入 MCP 服务器名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="base_url"
                label="API 基础地址"
                rules={[
                  { required: true, message: '请输入 API 基础地址' },
                  { type: 'url', message: '请输入有效的 URL' }
                ]}
              >
                <Input placeholder="https://api.example.com" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input placeholder="描述这个 MCP 服务器的用途" />
          </Form.Item>

          <Form.Item
            name="openapi_spec"
            label="OpenAPI 规范"
            rules={[{ required: true, message: '请输入或上传 OpenAPI 规范' }]}
          >
            <div>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Upload
                  accept=".json,.yaml,.yml"
                  beforeUpload={handleFileUpload}
                  showUploadList={false}
                >
                  <Button icon={<UploadOutlined />}>上传 OpenAPI 文件</Button>
                </Upload>
                <TextArea
                  rows={12}
                  placeholder="粘贴 OpenAPI JSON 规范，或使用上传按钮..."
                  value={openApiSpec}
                  onChange={(e) => setOpenApiSpec(e.target.value)}
                />
              </Space>
            </div>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<SendOutlined />}
              >
                转换为 MCP 服务器
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  setOpenApiSpec('');
                  setConvertResult(null);
                }}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* 转换结果 */}
      {convertResult && (
        <Card
          title={
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              转换结果
            </Space>
          }
          size="small"
          extra={
            <Button
              type="link"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(JSON.stringify(convertResult, null, 2))}
            >
              复制配置
            </Button>
          }
        >
          <Alert
            message="转换成功"
            description={`已成功将 OpenAPI 规范转换为 MCP 服务器配置，发现 ${convertResult.tools.length} 个工具`}
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Row gutter={16}>
            <Col span={8}>
              <div className="text-sm text-gray-500">服务器名称</div>
              <div className="font-medium">{convertResult.config_name}</div>
            </Col>
            <Col span={8}>
              <div className="text-sm text-gray-500">基础地址</div>
              <div className="font-medium">{convertResult.api_base_url}</div>
            </Col>
            <Col span={8}>
              <div className="text-sm text-gray-500">工具数量</div>
              <div className="font-medium">
                <Tag color="blue">{convertResult.tools.length} 个工具</Tag>
              </div>
            </Col>
          </Row>

          <Divider />

          <Collapse size="small">
            <Panel
              header={
                <Space>
                  <ToolOutlined />
                  发现的工具 ({convertResult.tools.length})
                </Space>
              }
              key="tools"
            >
              <div className="space-y-3">
                {convertResult.tools.map((tool, index) => (
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
        </Card>
      )}

      {loading && (
        <div className="text-center py-8">
          <Spin size="large" />
          <div className="mt-2 text-gray-500">正在转换 OpenAPI 规范...</div>
        </div>
      )}
    </div>
  );
};

export default OpenAPIConverter;