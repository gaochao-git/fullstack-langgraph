import { Card, Row, Col, Typography, Tag, Avatar, Button, Space } from "antd";
import { ToolOutlined, DatabaseOutlined, PlusOutlined } from "@ant-design/icons";

const { Title, Text, Paragraph } = Typography;

const mockTools = [
  {
    id: "file_tools",
    name: "文件操作工具",
    description: "提供文件读写、目录管理等基础操作",
    icon: <ToolOutlined />,
    status: "active",
  },
  {
    id: "db_tools",
    name: "数据库工具",
    description: "数据库连接、查询执行等操作",
    icon: <DatabaseOutlined />,
    status: "active",
  },
];

const ToolsManagement = () => {
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
            工具管理
          </Title>
          <Text type="secondary">注册和管理MCP工具服务器</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large">
          注册工具
        </Button>
      </div>

      <Row gutter={[24, 24]}>
        {mockTools.map((tool) => (
          <Col key={tool.id} xs={24} sm={12} lg={8} xl={6}>
            <Card hoverable>
              <Card.Meta
                avatar={
                  <Avatar
                    size={48}
                    style={{ backgroundColor: tool.id === "file_tools" ? "#52c41a" : "#1677ff" }}
                    icon={tool.icon}
                  />
                }
                title={
                  <Space>
                    {tool.name} <Tag color="success">运行中</Tag>
                  </Space>
                }
                description={
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {tool.description}
                    </Text>
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

export default ToolsManagement; 