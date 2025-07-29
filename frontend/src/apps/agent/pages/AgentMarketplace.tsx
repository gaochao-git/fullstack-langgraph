import { useState, useEffect } from "react";
import { Card, Row, Col, Typography, Tag, Avatar, Statistic, Space, Spin, message } from "antd";
import { DatabaseOutlined, RobotOutlined, SettingOutlined, UserOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { agentApi } from "../services/agentApi";
import { useTheme } from "../../../contexts/ThemeContext";

const { Title, Text, Paragraph } = Typography;
interface Agent {
  id: string;
  agent_id: string;
  name: string;
  display_name: string;
  description: string;
  status: string;
  enabled: string; // 'yes' | 'no'
  tools_info: {
    system_tools: string[];
    mcp_tools: any[];
  };
  llm_info: {
    model_name: string;
    temperature: number;
    max_tokens: number;
  };
  prompt_info: {
    system_prompt: string;
  };
  mcp_config: {
    total_tools: number;
    selected_tools: string[];
  };
  is_builtin: string; // 'yes' | 'no'
}

const AgentMarketplace = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  // 获取智能体数据
  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await agentApi.getAgents({ include_builtin: true });
      console.log('API Response:', response);
      console.log('Items:', response.items);
      // 显示所有智能体，不再过滤启用状态
      const activeAgents = response.items;
      setAgents(activeAgents);
    } catch (error) {
      console.error('加载智能体失败:', error);
      message.error('加载智能体列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleAgentClick = (agentId: string) => {
    navigate(`/agents/${agentId}`);
  };

  // 获取智能体图标
  const getAgentIcon = (agentId: string) => {
    switch (agentId) {
      case 'diagnostic_agent':
        return <SettingOutlined />;
      case 'security_agent':
        return <UserOutlined />;
      default:
        return <RobotOutlined />;
    }
  };

  // 获取智能体标签
  const getAgentTags = (agent: Agent) => {
    const tags = [];
    
    // 根据智能体类型添加标签
    switch (agent.agent_id) {
      case 'diagnostic_agent':
        tags.push('监控', '诊断', '性能分析');
        break;
      case 'security_agent':
        tags.push('安全', '防护', '检测');
        break;
      default:
        tags.push('智能助手');
    }
    
    // 根据工具配置添加标签
    const totalTools = agent.mcp_config?.total_tools || 0;
    if (totalTools > 0) {
      tags.push(`${totalTools}个工具`);
    }
    
    return tags;
  };

  const renderAgentCard = (agent: Agent) => (
    <Card
      key={agent.id}
      hoverable
      style={{ height: "100%", cursor: "pointer" }}
      onClick={() => handleAgentClick(agent.agent_id)}
    >
      <Card.Meta
        title={
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <Avatar 
                size={36} 
                style={{ backgroundColor: "#1677ff" }} 
                icon={getAgentIcon(agent.agent_id)} 
              />
              <span style={{ fontWeight: 600, fontSize: 18, color: isDark ? '#ffffff' : '#262626' }}>
                {agent.display_name || agent.name}
              </span>
            </div>
          </div>
        }
        description={
          <div>
            <Paragraph ellipsis={{ rows: 2, expandable: false }} style={{ marginBottom: 12 }}>
              {agent.description || '智能助手，能够帮助您完成各种任务'}
            </Paragraph>
            <div style={{ marginBottom: 8 }}>
              {getAgentTags(agent).map((tag: string) => (
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
                模型: {agent.llm_info?.model_name || '默认模型'}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {agent.is_builtin === 'yes' ? '内置智能体' : '自定义'}
              </Text>
            </div>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic 
                  title="工具数量" 
                  value={agent.mcp_config?.total_tools || 0} 
                  valueStyle={{ fontSize: 14 }} 
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="温度" 
                  value={agent.llm_info?.temperature || 0} 
                  precision={1}
                  valueStyle={{ fontSize: 14 }} 
                />
              </Col>
            </Row>
          </div>
        }
      />
    </Card>
  );

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">加载智能体列表中...</Text>
        </div>
      </div>
    );
  }

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
          <Text type="secondary">发现和使用各种智能助手 ({agents.length} 个可用)</Text>
        </div>
      </div>
      
      {agents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">暂无可用的智能体</Text>
          </div>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">请在智能体管理中创建并启用智能体</Text>
          </div>
        </div>
      ) : (
        <Row gutter={[24, 24]}>
          {agents.map((agent) => (
            <Col key={agent.id} xs={24} sm={12} lg={8} xl={6}>
              {renderAgentCard(agent)}
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default AgentMarketplace; 