import { useState, useEffect } from "react";
import { Card, Row, Col, Typography, Tag,  message, Select, Input, Button, Tooltip } from "antd";
import { RobotOutlined, ToolOutlined,SearchOutlined,StarOutlined,StarFilled,PlayCircleOutlined,LikeOutlined} from "@ant-design/icons";
import { categoryColors,renderIcon,getIconBackgroundColor} from './components/AgentIconSystem';
import { useNavigate } from "react-router-dom";
import { agentApi } from "@/services/agentApi";
import { useTheme } from "@/hooks/ThemeContext";
import { useAuth } from "@/hooks/useAuth";
import { Agent as ApiAgent } from '@/services/agentApi';
const { Text } = Typography;
type Agent = ApiAgent;

// 智能体分类选项
const AGENT_TYPES = [
  { value: '日志分析', label: '日志分析' },
  { value: '监控告警', label: '监控告警' },
  { value: '故障诊断', label: '故障诊断' },
  { value: '性能优化', label: '性能优化' },
  { value: '资源管理', label: '资源管理' },
  { value: '运维部署', label: '运维部署' },
  { value: '安全防护', label: '安全防护' },
  { value: '合规审计', label: '合规审计' },
  { value: '合同履约', label: '合同履约' },
  { value: '变更管理', label: '变更管理' },
  { value: '其他', label: '其他' },
];

// 归属过滤选项
const OWNER_FILTERS = [
  { value: 'mine', label: '我的' },
  { value: 'team', label: '我的团队' },
  { value: 'department', label: '我的部门' },
];

const AgentMarketplace = () => {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const { user } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedType, setSelectedType] = useState<string | undefined>(undefined);
  const [ownerFilter, setOwnerFilter] = useState<string | undefined>(undefined);
  const [searchText, setSearchText] = useState<string>('');
  const [showFavorites, setShowFavorites] = useState<boolean>(false);
  
  // 根据类型、所有者和搜索关键词过滤智能体
  const filteredAgents = agents
    .filter(agent => {
      // 类型过滤
      const matchType = !selectedType || agent.agent_type === selectedType;
      
      // 归属过滤
      let matchOwner = true;
      if (showFavorites) {
        // 如果选中了"我的收藏"，只显示收藏的智能体
        matchOwner = agent.is_favorited === true;
      } else if (ownerFilter) {
        switch (ownerFilter) {
          case 'mine':
            matchOwner = agent.create_by === user?.username;
            break;
          case 'team':
            // TODO: 需要后端支持团队信息
            matchOwner = true; // 暂时显示所有
            break;
          case 'department':
            // TODO: 需要后端支持部门信息
            matchOwner = true; // 暂时显示所有
            break;
        }
      }
      
      // 搜索过滤
      const matchSearch = !searchText || 
        agent.agent_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        agent.agent_description?.toLowerCase().includes(searchText.toLowerCase());
      
      return matchType && matchOwner && matchSearch;
    })
    // 按调用次数排序（从多到少）
    .sort((a, b) => {
      // 获取调用次数
      const usageA = a.total_runs || 0;
      const usageB = b.total_runs || 0;
      
      // 按调用次数降序排列
      if (usageA !== usageB) return usageB - usageA;
      
      // 调用次数相同时，按名称字母顺序
      return (a.agent_name || '').localeCompare(b.agent_name || '');
    });

  // 获取智能体数据
  const loadAgents = async () => {
    try {
      const response = await agentApi.getAgents();
      
      // 处理业务逻辑错误
      if (response.status === 'error') {
        message.error(response.msg || '加载智能体列表失败');
        return;
      }
      
      // 处理成功响应
      const data = response.data || response;
      // 显示所有智能体，不再过滤启用状态
      const activeAgents = data.items || [];
      setAgents(activeAgents);
    } catch (error) {
      console.error('加载智能体失败:', error);
      message.error('加载智能体列表失败');
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleAgentClick = (agentId: string) => {
    navigate(`/service/agents/${agentId}`);
  };

  const handleToggleFavorite = async (e: React.MouseEvent, agent: Agent) => {
    e.stopPropagation(); // 阻止卡片点击事件
    
    try {
      const newFavoriteStatus = !agent.is_favorited;
      const response = await agentApi.toggleFavorite(agent.agent_id, newFavoriteStatus);
      
      if (response.status === 'error') {
        message.error(response.msg || '操作失败');
        return;
      }
      
      // 更新本地状态
      setAgents(prevAgents => 
        prevAgents.map(a => 
          a.agent_id === agent.agent_id 
            ? { ...a, is_favorited: newFavoriteStatus }
            : a
        )
      );
      
      message.success(newFavoriteStatus ? '收藏成功' : '取消收藏成功');
    } catch (error) {
      console.error('切换收藏状态失败:', error);
      message.error('操作失败，请重试');
    }
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
        borderRadius: 8,
        overflow: 'hidden'
      }}
      onClick={() => handleAgentClick(agent.agent_id)}
      styles={{ body: { padding: 16 } }}
    >
      <Card.Meta
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  backgroundColor: getAgentBackgroundColor(agent),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}
              >
                {renderIcon(agent.agent_icon || 'Bot', 16)}
              </div>
              <div style={{ 
                fontWeight: 500, 
                fontSize: 16,
                color: isDark ? '#ffffff' : '#262626'
              }}>
                {agent.agent_name}
              </div>
            </div>
            {/* 收藏按钮 */}
            <Button
              type="text"
              size="small"
              icon={agent.is_favorited ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={(e) => handleToggleFavorite(e, agent)}
            />
          </div>
        }
        description={
          <div className="space-y-2">
            {/* 描述文本 */}
            <div 
              style={{ 
                marginBottom: 8,
                fontSize: 13,
                lineHeight: 1.5,
                color: isDark ? 'rgba(255,255,255,0.65)' : 'rgba(0,0,0,0.65)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
              title={agent.agent_description || '智能助手，能够帮助您完成各种任务'}
            >
              {agent.agent_description || '智能助手，能够帮助您完成各种任务'}
            </div>
            
            {/* 标签行 */}
            <div className="flex items-center gap-2" style={{ overflow: 'hidden' }}>
              <Tag 
                color="blue" 
                className="text-xs"
                style={{ margin: 0 }}
              >
                {agent.agent_type || '未分类'}
              </Tag>
              {agent.is_builtin === 'yes' ? (
                <Tag color="gold" className="text-xs" style={{ margin: 0 }}>内置</Tag>
              ) : (
                <Tag color="cyan" className="text-xs" style={{ margin: 0 }}>模版</Tag>
              )}
              <Tag className="text-xs" style={{ margin: 0 }}>
                {agent.agent_owner || agent.create_by || 'system'}
              </Tag>
            </div>

            {/* 统计信息 */}
            <div className="flex items-center gap-3 text-gray-500" style={{ fontSize: 11 }}>
              <span>
                <ToolOutlined style={{ fontSize: 11, marginRight: 2 }} />
                {(() => {
                  const toolsInfo = agent.tools_info || { mcp_tools: [], system_tools: [] };
                  const mcpTools = toolsInfo.mcp_tools || [];
                  const systemTools = toolsInfo.system_tools || [];
                  const allMcpToolNames = mcpTools.flatMap((tool: any) => tool.tools || []);
                  const totalTools = [...systemTools, ...allMcpToolNames].length;
                  return totalTools;
                })()} 个工具
              </span>
              <span>
                <PlayCircleOutlined style={{ fontSize: 11, marginRight: 2 }} />
                {agent.total_runs || 0}
              </span>
              {/* 满意度显示 */}
              {(() => {
                const thumbsUp = agent.thumbs_up_count || 0;
                const thumbsDown = agent.thumbs_down_count || 0;
                const totalFeedback = thumbsUp + thumbsDown;
                if (totalFeedback > 0) {
                  const satisfactionRate = (thumbsUp / totalFeedback) * 100;
                  return (
                    <Tooltip 
                      title={
                        <div style={{ fontSize: 12 }}>
                          <div>满意度: {satisfactionRate.toFixed(1)}%</div>
                          <div>👍 {thumbsUp} / 👎 {thumbsDown}</div>
                          <div>总反馈: {totalFeedback}</div>
                        </div>
                      }
                    >
                      <span style={{ 
                        color: satisfactionRate >= 80 ? '#52c41a' : satisfactionRate >= 60 ? '#faad14' : '#ff4d4f',
                        cursor: 'help' 
                      }}>
                        <LikeOutlined style={{ fontSize: 11, marginRight: 2 }} />
                        {satisfactionRate.toFixed(0)}%
                      </span>
                    </Tooltip>
                  );
                }
                return null;
              })()}
            </div>

            {/* 能力标签 */}
            {getAgentTags(agent).length > 0 && (
              <div className="flex gap-1" style={{ overflow: 'hidden' }}>
                {getAgentTags(agent).slice(0, 3).map((tag: string) => (
                  <Tag key={tag} color="blue" className="text-xs" style={{ margin: 0 }}>
                    {tag.length > 4 ? tag.slice(0, 4) : tag}
                  </Tag>
                ))}
              </div>
            )}
          </div>
        }
      />
    </Card>
  );


  return (
    <div>
      {/* 头部过滤卡片 */}
      <Card 
        style={{ 
          marginBottom: 24,
          borderRadius: 8,
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)'
        }}
        styles={{ body: { padding: '16px 20px' } }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          {/* 我的收藏按钮 */}
          <Button
            type={showFavorites ? "primary" : "default"}
            icon={showFavorites ? <StarFilled /> : <StarOutlined />}
            onClick={() => {
              setShowFavorites(!showFavorites);
              // 切换收藏时清除归属过滤
              if (!showFavorites) {
                setOwnerFilter(undefined);
              }
            }}
          >
            我的收藏
          </Button>
          
          {/* 归属过滤下拉 */}
          <Select
            value={ownerFilter}
            onChange={(value) => {
              setOwnerFilter(value);
              // 选择归属过滤时取消收藏过滤
              if (value) {
                setShowFavorites(false);
              }
            }}
            style={{ width: 120 }}
            placeholder="归属筛选"
            allowClear
            disabled={showFavorites}
            options={OWNER_FILTERS.map(filter => ({
              value: filter.value,
              label: filter.label
            }))}
          />
          
          {/* 类型筛选下拉 */}
          <Select
            value={selectedType}
            onChange={setSelectedType}
            style={{ width: 120 }}
            placeholder="类型筛选"
            allowClear
            options={AGENT_TYPES.map(type => ({
              value: type.value,
              label: type.label
            }))}
          />
          
          {/* 搜索框 */}
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索智能体名称、描述"
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
        </div>
      </Card>
      
      {filteredAgents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">
              {(() => {
                if (showFavorites) {
                  return '暂无收藏的智能体';
                }
                const ownerLabel = OWNER_FILTERS.find(f => f.value === ownerFilter)?.label || '';
                const typeLabel = AGENT_TYPES.find(t => t.value === selectedType)?.label || '';
                
                if (ownerFilter && selectedType) {
                  return `暂无${ownerLabel}的${typeLabel}智能体`;
                } else if (ownerFilter) {
                  return `暂无${ownerLabel}的智能体`;
                } else if (selectedType) {
                  return `暂无${typeLabel}的智能体`;
                } else {
                  return '暂无可用的智能体';
                }
              })()}
            </Text>
          </div>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">
              {showFavorites
                ? '点击智能体卡片上的星星图标收藏智能体'
                : ownerFilter === 'mine'
                ? '请前往智能体管理创建您的智能体'
                : '请调整筛选条件或前往智能体管理创建新的智能体'}
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