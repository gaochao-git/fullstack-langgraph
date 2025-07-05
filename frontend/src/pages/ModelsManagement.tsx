import { Card, Row, Col, Typography, Tag, Avatar, Button, Space, Statistic } from "antd";
import { ApiOutlined, PlusOutlined } from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;

const mockModels = [
  {
    id: "gpt4",
    name: "GPT-4",
    description: "OpenAI GPT-4 模型，支持复杂推理和代码生成",
    icon: <ApiOutlined />,
    status: "active",
    backgroundColor: "#722ed1",
    latency: "200ms",
    successRate: "99.9%",
  },
  {
    id: "claude",
    name: "Claude-3.5",
    description: "Anthropic Claude-3.5 模型，擅长分析和代码编写",
    icon: <ApiOutlined />,
    status: "active",
    backgroundColor: "#fa8c16",
    latency: "180ms",
    successRate: "99.8%",
  },
];

const ModelsManagement = () => {
  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <div>
          <Title level={3} style={{ margin: 0 }}>
            模型管理
          </Title>
          <Text type="secondary">注册和管理AI模型服务</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large">
          注册模型
        </Button>
      </div>

      <Row gutter={[24, 24]}>
        {mockModels.map((model) => (
          <Col key={model.id} xs={24} sm={12} lg={8} xl={6}>
            <Card hoverable>
              <Card.Meta
                avatar={
                  <Avatar size={48} style={{ backgroundColor: model.backgroundColor }} icon={model.icon} />
                }
                title={
                  <Space>
                    {model.name} <Tag color="success">可用</Tag>
                  </Space>
                }
                description={
                  <div>
                    <Paragraph ellipsis={{ rows: 2 }} style={{ fontSize: 12, marginBottom: 8 }}>
                      {model.description}
                    </Paragraph>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Statistic title="延迟" value={model.latency} valueStyle={{ fontSize: 12 }} />
                      </Col>
                      <Col span={12}>
                        <Statistic title="成功率" value={model.successRate} valueStyle={{ fontSize: 12 }} />
                      </Col>
                    </Row>
                  </div>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ModelsManagement; 