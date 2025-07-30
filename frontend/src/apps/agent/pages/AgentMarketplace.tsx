import { useState, useEffect } from "react";
import { Card, Row, Col, Typography, Tag, Avatar, Statistic, Space, Spin, message } from "antd";
import { 
  DatabaseOutlined, 
  RobotOutlined, 
  SettingOutlined, 
  UserOutlined,
  BulbOutlined,
  HeartOutlined,
  BookOutlined,
  CodeOutlined,
  CustomerServiceOutlined
} from "@ant-design/icons";
import { 
  Bot, 
  Settings, 
  User, 
  Database, 
  Lightbulb, 
  Heart, 
  Book, 
  Code, 
  Headphones,
  Brain,
  Sparkles,
  Shield,
  Search,
  MessageCircle,
  Zap,
  Target,
  TrendingUp,
  FileText,
  Globe,
  Music,
  Gamepad2,
  Camera,
  Palette,
  Calculator
} from 'lucide-react';
import { useNavigate } from "react-router-dom";
import { agentApi } from "../services/agentApi";
import { useTheme } from "../../../contexts/ThemeContext";

const { Title, Text, Paragraph } = Typography;
interface Agent {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_description: string;
  agent_status: string;
  agent_enabled: string; // 'yes' | 'no'
  agent_icon?: string;
  agent_capabilities: string[];
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

  // 定义分类颜色（与配置页面保持一致）
  const categoryColors = {
    '基础': '#1677ff',    // 蓝色 - 基础功能
    '专业': '#722ed1',    // 紫色 - 专业技术
    '服务': '#13c2c2',    // 青色 - 服务类型
    '教育': '#52c41a',    // 绿色 - 教育知识
    '娱乐': '#fa8c16',    // 橙色 - 娱乐休闲
    '工具': '#eb2f96'     // 粉色 - 工具类型
  };

  // 图标分类映射
  const iconCategoryMap: { [key: string]: string } = {
    'Bot': '基础', 'Brain': '基础', 'Sparkles': '基础',
    'Settings': '专业', 'Database': '专业', 'Code': '专业', 'Shield': '专业', 'Search': '专业', 'TrendingUp': '专业',
    'User': '服务', 'Headphones': '服务', 'MessageCircle': '服务', 'Heart': '服务',
    'Book': '教育', 'FileText': '教育', 'Lightbulb': '教育', 'Target': '教育',
    'Music': '娱乐', 'Gamepad2': '娱乐', 'Camera': '娱乐', 'Palette': '娱乐',
    'Calculator': '工具', 'Globe': '工具', 'Zap': '工具'
  };

  // 根据图标名称渲染图标组件（带颜色）
  const renderIcon = (iconName: string, size: number = 18) => {
    // 获取图标对应的分类颜色
    const category = iconCategoryMap[iconName];
    const iconColor = category ? categoryColors[category as keyof typeof categoryColors] : '#666666';
    
    const iconMap: { [key: string]: React.ReactNode } = {
      // Lucide React 图标（带颜色）
      'Bot': <Bot size={size} color={iconColor} />,
      'Brain': <Brain size={size} color={iconColor} />,
      'Sparkles': <Sparkles size={size} color={iconColor} />,
      'Settings': <Settings size={size} color={iconColor} />,
      'Database': <Database size={size} color={iconColor} />,
      'Code': <Code size={size} color={iconColor} />,
      'Shield': <Shield size={size} color={iconColor} />,
      'Search': <Search size={size} color={iconColor} />,
      'TrendingUp': <TrendingUp size={size} color={iconColor} />,
      'User': <User size={size} color={iconColor} />,
      'Headphones': <Headphones size={size} color={iconColor} />,
      'MessageCircle': <MessageCircle size={size} color={iconColor} />,
      'Heart': <Heart size={size} color={iconColor} />,
      'Book': <Book size={size} color={iconColor} />,
      'FileText': <FileText size={size} color={iconColor} />,
      'Lightbulb': <Lightbulb size={size} color={iconColor} />,
      'Target': <Target size={size} color={iconColor} />,
      'Music': <Music size={size} color={iconColor} />,
      'Gamepad2': <Gamepad2 size={size} color={iconColor} />,
      'Camera': <Camera size={size} color={iconColor} />,
      'Palette': <Palette size={size} color={iconColor} />,
      'Calculator': <Calculator size={size} color={iconColor} />,
      'Globe': <Globe size={size} color={iconColor} />,
      'Zap': <Zap size={size} color={iconColor} />,
      
      // 向后兼容 Ant Design 图标
      'RobotOutlined': <RobotOutlined />,
      'SettingOutlined': <SettingOutlined />,
      'UserOutlined': <UserOutlined />,
      'DatabaseOutlined': <DatabaseOutlined />,
      'BulbOutlined': <BulbOutlined />,
      'HeartOutlined': <HeartOutlined />,
      'BookOutlined': <BookOutlined />,
      'CodeOutlined': <CodeOutlined />,
      'CustomerServiceOutlined': <CustomerServiceOutlined />
    };
    return iconMap[iconName] || <Bot size={size} color={iconColor} />;
  };

  // 获取智能体图标（优先使用配置的图标，回退到基于名称匹配）
  const getAgentIcon = (agent: Agent) => {
    // 如果有配置的图标，直接使用（基于agent_id获取的配置）
    if (agent.agent_icon) {
      return renderIcon(agent.agent_icon);
    }
    
    // 回退到基于名称的匹配（向后兼容）
    const name = agent.agent_name?.toLowerCase() || '';
    
    // 故障诊断相关
    if (name.includes('诊断') || name.includes('故障') || name.includes('监控')) {
      return <SettingOutlined />;
    }
    
    // 安全防护相关
    if (name.includes('安全') || name.includes('防护') || name.includes('检测')) {
      return <UserOutlined />;
    }
    
    // 故事、娱乐相关
    if (name.includes('故事') || name.includes('笑话') || name.includes('娱乐')) {
      return <RobotOutlined style={{ color: '#52c41a' }} />;
    }
    
    // 研究分析相关
    if (name.includes('研究') || name.includes('分析') || name.includes('数据')) {
      return <DatabaseOutlined />;
    }
    
    // 默认通用智能体图标
    return <RobotOutlined />;
  };

  // 获取智能体标签（基于agent_name和capabilities）
  const getAgentTags = (agent: Agent) => {
    const tags = [];
    const name = agent.agent_name?.toLowerCase() || '';
    
    // 优先使用agent_capabilities作为标签
    if (agent.agent_capabilities && agent.agent_capabilities.length > 0) {
      tags.push(...agent.agent_capabilities);
    } else {
      // 如果没有capabilities，基于名称添加标签
      if (name.includes('诊断') || name.includes('故障') || name.includes('监控')) {
        tags.push('监控', '诊断', '性能分析');
      } else if (name.includes('安全') || name.includes('防护') || name.includes('检测')) {
        tags.push('安全', '防护', '检测');
      } else if (name.includes('故事') || name.includes('笑话') || name.includes('娱乐')) {
        tags.push('娱乐', '故事', '笑话');
      } else if (name.includes('研究') || name.includes('分析') || name.includes('数据')) {
        tags.push('研究', '分析', '数据');
      } else {
        tags.push('智能助手');
      }
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
                icon={getAgentIcon(agent)} 
              />
              <span style={{ fontWeight: 600, fontSize: 18, color: isDark ? '#ffffff' : '#262626' }}>
                {agent.agent_name}
              </span>
            </div>
          </div>
        }
        description={
          <div>
            <Paragraph ellipsis={{ rows: 2, expandable: false }} style={{ marginBottom: 12 }}>
              {agent.agent_description || '智能助手，能够帮助您完成各种任务'}
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