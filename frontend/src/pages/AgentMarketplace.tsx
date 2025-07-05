import { useState } from "react";
import { Card, Row, Col, Typography, Tag, Avatar, Statistic, Space } from "antd";
import { DatabaseOutlined, RobotOutlined, SettingOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Title, Text, Paragraph } = Typography;

// 模拟智能体数据
const mockAgents = [
  {
    id: "research_agent",
    name: "研究助手",
    description: "强大的研究助手，可以帮助你进行网络搜索、信息整理和深度分析。支持多轮对话和上下文理解。",
    icon: <RobotOutlined />,
    status: "active",
    creator: "系统管理员",
    createTime: "2024-01-15",
    tags: ["研究", "搜索", "分析"],
    usageCount: 1256,
    rating: 4.8,
  },
  {
    id: "diagnostic_agent",
    name: "故障诊断助手",
    description: "智能系统监控与故障诊断，实时分析系统性能指标，快速定位问题根因。",
    icon: <SettingOutlined />,
    status: "active",
    creator: "DevOps团队",
    createTime: "2024-01-10",
    tags: ["监控", "诊断", "性能分析"],
    usageCount: 892,
    rating: 4.6,
  },
];

const AgentMarketplace = () => {
  const navigate = useNavigate();

  const handleAgentClick = (agentId: string) => {
    navigate(`/agents/${agentId}`);
  };

  const renderAgentCard = (agent: any) => (
    <Card
      key={agent.id}
      hoverable
      style={{ height: "100%", cursor: "pointer" }}
      onClick={() => handleAgentClick(agent.id)}
    >
      <Card.Meta
        avatar={
          <Avatar size={48} style={{ backgroundColor: "#1677ff" }} icon={agent.icon} />
        }
        title={
          <Space>
            {agent.name}
            <Tag color={agent.status === "active" ? "success" : "default"}>
              {agent.status === "active" ? "运行中" : "已停止"}
            </Tag>
          </Space>
        }
        description={
          <div>
            <Paragraph ellipsis={{ rows: 2, expandable: false }} style={{ marginBottom: 12 }}>
              {agent.description}
            </Paragraph>
            <div style={{ marginBottom: 8 }}>
              {agent.tags.map((tag: string) => (
                <Tag key={tag} color="blue" style={{ marginBottom: 4 }}>
                  {tag}
                </Tag>
              ))}
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 8,
              }}
            >
              <Text type="secondary" style={{ fontSize: 12 }}>
                创建者: {agent.creator}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {agent.createTime}
              </Text>
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic title="使用次数" value={agent.usageCount} valueStyle={{ fontSize: 14 }} />
              </Col>
              <Col span={12}>
                <Statistic title="评分" value={agent.rating} precision={1} valueStyle={{ fontSize: 14 }} />
              </Col>
            </Row>
          </div>
        }
      />
    </Card>
  );

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
            智能体广场
          </Title>
          <Text type="secondary">发现和使用各种智能助手</Text>
        </div>
      </div>
      <Row gutter={[24, 24]}>
        {mockAgents.map((agent) => (
          <Col key={agent.id} xs={24} sm={12} lg={8} xl={6}>
            {renderAgentCard(agent)}
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default AgentMarketplace; 