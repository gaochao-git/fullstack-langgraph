import { useState } from "react";
import { Card, Row, Col, Typography, Tag, Avatar, Button, Space } from "antd";
import {
  DatabaseOutlined,
  RobotOutlined,
  SettingOutlined,
  EditOutlined,
  EyeOutlined,
  DeleteOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const { Title, Text, Paragraph } = Typography;

// 使用相同的模拟数据
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
  },
];

const AgentManagement = () => {
  const navigate = useNavigate();

  const handlePreview = (agentId: string) => {
    navigate(`/agents/${agentId}`);
  };

  const handleEdit = (agentId: string) => {
    // TODO: 实现编辑功能
    console.log("Edit agent:", agentId);
  };

  const handleDelete = (agentId: string) => {
    // TODO: 实现删除功能
    console.log("Delete agent:", agentId);
  };

  const renderAgentCard = (agent: any) => (
    <Card
      hoverable
      style={{ height: "100%" }}
      actions={[
        <Button key="edit" type="text" icon={<EditOutlined />} onClick={() => handleEdit(agent.id)}>
          编辑
        </Button>,
        <Button
          key="view"
          type="text"
          icon={<EyeOutlined />}
          onClick={() => handlePreview(agent.id)}
        >
          预览
        </Button>,
        <Button
          key="delete"
          type="text"
          icon={<DeleteOutlined />}
          danger
          onClick={() => handleDelete(agent.id)}
        >
          删除
        </Button>,
      ]}
    >
      <Card.Meta
        avatar={<Avatar size={48} style={{ backgroundColor: "#1677ff" }} icon={agent.icon} />}
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
            智能体管理
          </Title>
          <Text type="secondary">创建、编辑和管理您的智能体</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} size="large">
          创建智能体
        </Button>
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

export default AgentManagement; 