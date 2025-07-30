import React from 'react';
import { 
  Modal, 
  Descriptions, 
  Badge, 
  Divider, 
  Statistic, 
  Avatar, 
  Row, 
  Col, 
  Space, 
  Tag 
} from 'antd';
import { 
  RobotOutlined,
  SettingOutlined,
  EyeOutlined,
  ToolOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  CloudOutlined,
  GlobalOutlined
} from '@ant-design/icons';

interface LocalAgent {
  id: string;
  agent_id: string;
  name: string;
  version: string;
  displayName: string;
  agent_description: string;
  status: string;
  lastUsed?: string;
  totalRuns: number;
  successRate: number;
  avgResponseTime: number;
  is_builtin: string;
  capabilities: string[];
  mcpConfig: {
    enabledServers: string[];
    selectedTools: string[];
    totalTools: number;
  };
}

interface LocalMCPServer {
  id: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  tools: Array<{
    name: string;
    category: string;
    description: string;
  }>;
}

interface AgentDetailModalProps {
  visible: boolean;
  onCancel: () => void;
  agent: LocalAgent | null;
  mcpServers: LocalMCPServer[];
}

const AgentDetailModal: React.FC<AgentDetailModalProps> = ({
  visible,
  onCancel,
  agent,
  mcpServers
}) => {
  // 获取状态文本
  const getStatusText = (status: string): string => {
    const texts: Record<string, string> = {
      running: '运行中',
      stopped: '已停止',
      error: '错误'
    };
    return texts[status] || status;
  };

  // 获取工具类别图标
  const getCategoryIcon = (category: string) => {
    const icons: Record<string, React.ReactNode> = {
      database: <DatabaseOutlined />,
      monitoring: <MonitorOutlined />,
      analysis: <EyeOutlined />,
      network: <GlobalOutlined />,
      cloud: <CloudOutlined />,
      sop: <SettingOutlined />,
      general: <ToolOutlined />
    };
    return icons[category] || <ToolOutlined />;
  };

  // 获取工具类别颜色
  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      database: 'blue',
      monitoring: 'green',
      analysis: 'purple',
      network: 'orange',
      cloud: 'cyan',
      sop: 'gold',
      general: 'gray'
    };
    return colors[category] || 'default';
  };

  return (
    <Modal
      title="智能体详情"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={900}
    >
      {agent && (
        <div>
          <Descriptions column={2} bordered>
            <Descriptions.Item label="智能体名称" span={2}>
              <Space>
                <Avatar 
                  icon={<RobotOutlined />} 
                  style={{ 
                    backgroundColor: agent.status === 'running' ? '#52c41a' : 
                                   agent.status === 'error' ? '#ff4d4f' : '#faad14'
                  }} 
                />
                <span style={{ color: agent.is_builtin === 'yes' ? '#faad14' : undefined }}>
                  {agent.displayName}
                </span>
                <Badge 
                  status={agent.status === 'running' ? 'success' : 
                         agent.status === 'error' ? 'error' : 'warning'} 
                  text={getStatusText(agent.status)}
                />
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="标识符">{agent.name}</Descriptions.Item>
            <Descriptions.Item label="版本">{agent.version}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {agent.agent_description}
            </Descriptions.Item>
          </Descriptions>
          
          <Divider>运行统计</Divider>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Statistic title="总运行次数" value={agent.totalRuns} />
            </Col>
            <Col span={6}>
              <Statistic 
                title="成功率" 
                value={agent.successRate} 
                precision={1}
                suffix="%" 
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="平均响应时间" 
                value={agent.avgResponseTime} 
                precision={1}
                suffix="s" 
              />
            </Col>
            <Col span={6}>
              <Statistic title="最后使用时间" value={agent.lastUsed || '-'} />
            </Col>
          </Row>

          <Divider>核心能力</Divider>
          <Space wrap>
            {agent.capabilities.map(capability => (
              <Tag key={capability} color="blue">{capability}</Tag>
            ))}
          </Space>

          <Divider>MCP工具配置</Divider>
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Statistic title="启用服务器" value={agent.mcpConfig.enabledServers.length} />
            </Col>
            <Col span={8}>
              <Statistic title="选中工具" value={agent.mcpConfig.selectedTools.length} />
            </Col>
            <Col span={8}>
              <Statistic title="总可用工具" value={agent.mcpConfig.totalTools} />
            </Col>
          </Row>
          
          <div className="mt-4">
            <strong>当前工具:</strong>
            <div className="mt-2 space-y-1">
              {agent.mcpConfig.selectedTools.map(tool => {
                const mcpTool = mcpServers.flatMap(s => s.tools).find(t => t.name === tool);
                return mcpTool ? (
                  <Tag key={tool} color={getCategoryColor(mcpTool.category)}>
                    {getCategoryIcon(mcpTool.category)} {tool}
                  </Tag>
                ) : (
                  <Tag key={tool}>{tool}</Tag>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
};

export default AgentDetailModal;