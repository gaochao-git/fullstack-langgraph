import { useState, useEffect } from "react";
import { Card, Row, Col, Typography, Tag, Avatar, Space, Spin, message, Tabs } from "antd";
import { 
  DatabaseOutlined, 
  RobotOutlined, 
  SettingOutlined, 
  UserOutlined,
  ToolOutlined
} from "@ant-design/icons";
import { 
  categoryColors,
  renderIcon,
  getIconBackgroundColor
} from './components/AgentIconSystem';
import { useNavigate } from "react-router-dom";
import { agentApi } from "../../services/agentApi";
import { useTheme } from "../../hooks/ThemeContext";

const { Title, Text, Paragraph } = Typography;
import { Agent as ApiAgent } from '../../services/agentApi';

type Agent = ApiAgent;

// 智能体分类选项
const AGENT_TYPES = [
  { value: 'all', label: '全部', color: 'default' },
  { value: '日志分析', label: '日志分析', color: 'blue' },
  { value: '监控告警', label: '监控告警', color: 'orange' },
  { value: '故障诊断', label: '故障诊断', color: 'red' },
  { value: '性能优化', label: '性能优化', color: 'green' },
  { value: '资源管理', label: '资源管理', color: 'purple' },
  { value: '运维部署', label: '运维部署', color: 'cyan' },
  { value: '安全防护', label: '安全防护', color: 'volcano' },
  { value: '合规审计', label: '合规审计', color: 'magenta' },
  { value: '合同履约', label: '合同履约', color: 'gold' },
  { value: '变更管理', label: '变更管理', color: 'lime' },
  { value: '其他', label: '其他', color: 'default' },
];

const AgentMarketplace = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  
  // 根据类型过滤智能体
  const filteredAgents = selectedType === 'all' 
    ? agents 
    : agents.filter(agent => agent.agent_type === selectedType);

  // 获取智能体数据
  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await agentApi.getAgents({ include_builtin: true });
      
      // 处理业务逻辑错误
      if (response.status === 'error') {
        message.error(response.msg || '加载智能体列表失败');
        return;
      }
      
      // 处理成功响应
      const data = response.data || response;
      console.log('API Response:', response);
      console.log('Items:', data.items);
      // 显示所有智能体，不再过滤启用状态
      const activeAgents = data.items || [];
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
    navigate(`/service/agents/${agentId}`);
  };


  // 获取智能体背景色（根据图标分类）
  const getAgentBackgroundColor = (agent: Agent) => {
    if (agent.agent_icon) {
      return getIconBackgroundColor(agent.agent_icon, '20');
    }
    
    // 回退到基于名称的颜色匹配
    const name = agent.agent_name?.toLowerCase() || '';
    if (name.includes('诊断') || name.includes('故障') || name.includes('监控')) {
      return categoryColors['专业'] + '20';
    }
    if (name.includes('安全') || name.includes('防护') || name.includes('检测')) {
      return categoryColors['专业'] + '20';
    }
    if (name.includes('故事') || name.includes('笑话') || name.includes('娱乐')) {
      return categoryColors['娱乐'] + '20';
    }
    if (name.includes('研究') || name.includes('分析') || name.includes('数据')) {
      return categoryColors['专业'] + '20';
    }
    
    return categoryColors['基础'] + '20'; // 默认蓝色背景
  };

  // 获取智能体图标（优先使用配置的图标，回退到基于名称匹配）
  const getAgentIcon = (agent: Agent) => {
    // 如果有配置的图标，直接使用（基于agent_id获取的配置）
    if (agent.agent_icon) {
      return renderIcon(agent.agent_icon, 20); // 稍微大一点的图标
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
      style={{ 
        height: "100%", 
        cursor: "pointer",
        borderRadius: 12,
        overflow: 'hidden'
      }}
      onClick={() => handleAgentClick(agent.agent_id)}
      bodyStyle={{ padding: 20 }}
    >
      <Card.Meta
        title={
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <Avatar 
                size={42} 
                style={{ 
                  backgroundColor: getAgentBackgroundColor(agent),
                  boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                }} 
                icon={getAgentIcon(agent)} 
              />
              <div style={{ flex: 1 }}>
                <div style={{ 
                  fontWeight: 600, 
                  fontSize: 18, 
                  color: isDark ? '#ffffff' : '#262626',
                  marginBottom: 4
                }}>
                  {agent.agent_name}
                </div>
                <Tag 
                  color={AGENT_TYPES.find(t => t.value === agent.agent_type)?.color || 'default'}
                  style={{ fontSize: 12 }}
                >
                  {agent.agent_type || '未分类'}
                </Tag>
              </div>
            </div>
          </div>
        }
        description={
          <div>
            <Paragraph 
              ellipsis={{ rows: 2, expandable: false }} 
              style={{ 
                marginBottom: 12,
                fontSize: 14,
                lineHeight: 1.6,
                color: isDark ? 'rgba(255,255,255,0.65)' : 'rgba(0,0,0,0.65)'
              }}
            >
              {agent.agent_description || '智能助手，能够帮助您完成各种任务'}
            </Paragraph>
            <div style={{ marginBottom: 12 }}>
              {getAgentTags(agent).slice(0, 3).map((tag: string) => (
                <Tag 
                  key={tag} 
                  style={{ 
                    marginBottom: 4,
                    marginRight: 4,
                    fontSize: 12,
                    borderRadius: 4
                  }}
                >
                  {tag}
                </Tag>
              ))}
              {getAgentTags(agent).length > 3 && (
                <Tag style={{ fontSize: 12, borderRadius: 4 }}>+{getAgentTags(agent).length - 3}</Tag>
              )}
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                paddingTop: 12,
                borderTop: '1px solid rgba(0,0,0,0.06)',
              }}
            >
              <Space size={16}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <ToolOutlined style={{ marginRight: 4 }} />
                  {agent.mcp_config?.total_tools || 0} 个工具
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {agent.llm_info?.model_name || '默认模型'}
                </Text>
              </Space>
              <Tag 
                color={agent.is_builtin === 'yes' ? 'gold' : 'default'} 
                style={{ fontSize: 11, margin: 0 }}
              >
                {agent.is_builtin === 'yes' ? '内置' : '自定义'}
              </Tag>
            </div>
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
      <div style={{ marginBottom: 24 }}>
        {/* 分类选择器 */}
        <Tabs 
          activeKey={selectedType}
          onChange={setSelectedType}
          size="large"
          items={AGENT_TYPES.map(type => ({
            key: type.value,
            label: type.label
          }))}
        />
      </div>
      
      {filteredAgents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">
              {selectedType === 'all' 
                ? '暂无可用的智能体' 
                : `暂无${selectedType}类型的智能体`}
            </Text>
          </div>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">
              {selectedType === 'all'
                ? '请在智能体管理中创建并启用智能体'
                : '请尝试查看其他分类或创建新的智能体'}
            </Text>
          </div>
        </div>
      ) : (
        <Row gutter={[24, 24]}>
          {filteredAgents.map((agent) => (
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