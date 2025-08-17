import { Card, Row, Col, Typography, Tag, Avatar, Button, Space, Progress } from "antd";
import { BookOutlined, PlusOutlined, FileTextOutlined } from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;

const mockKnowledgeBases = [
  {
    id: "docs",
    name: "产品文档库",
    description: "包含产品使用手册、API文档和最佳实践指南",
    icon: <BookOutlined />,
    status: "active",
    backgroundColor: "#1677ff",
    documentCount: 156,
    lastUpdated: "2024-01-20",
    usageRate: 85,
  },
  {
    id: "tech",
    name: "技术知识库",
    description: "技术架构文档、故障处理手册和运维指南",
    icon: <FileTextOutlined />,
    status: "active",
    backgroundColor: "#52c41a",
    documentCount: 89,
    lastUpdated: "2024-01-18",
    usageRate: 92,
  },
];

const KnowledgeManagement = () => {
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
            知识库管理
          </Title>
          <Text type="secondary">管理和维护智能体的知识库</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />}>
          创建知识库
        </Button>
      </div>

      <Row gutter={[24, 24]}>
        {mockKnowledgeBases.map((kb) => (
          <Col key={kb.id} xs={24} sm={12} lg={8} xl={6}>
            <Card hoverable>
              <Card.Meta
                avatar={
                  <Avatar size={48} style={{ backgroundColor: kb.backgroundColor }} icon={kb.icon} />
                }
                title={
                  <Space>
                    {kb.name} <Tag color="success">已同步</Tag>
                  </Space>
                }
                description={
                  <div>
                    <Paragraph ellipsis={{ rows: 2 }} style={{ fontSize: 12, marginBottom: 12 }}>
                      {kb.description}
                    </Paragraph>
                    <div style={{ marginBottom: 12 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        文档数量: {kb.documentCount}
                      </Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        最后更新: {kb.lastUpdated}
                      </Text>
                    </div>
                    <div>
                      <Text type="secondary" style={{ fontSize: 12, marginBottom: 4, display: "block" }}>
                        知识利用率
                      </Text>
                      <Progress percent={kb.usageRate} size="small" />
                    </div>
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

export default KnowledgeManagement;