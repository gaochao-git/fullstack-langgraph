/**
 * 记忆统计卡片组件
 */

import React from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Button, 
  Space,
  Tag,
  Tooltip
} from 'antd';
import { 
  UserOutlined,
  DatabaseOutlined,
  HistoryOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  ExperimentOutlined
} from '@ant-design/icons';

import { MemoryStats } from '../../../services/memoryApi';

interface MemoryStatsCardProps {
  stats: MemoryStats | null;
  loading: boolean;
  onRefresh: () => void;
}

/**
 * 记忆统计卡片组件
 */
const MemoryStatsCard: React.FC<MemoryStatsCardProps> = ({
  stats,
  loading,
  onRefresh
}) => {
  return (
    <Card
      title={
        <Space>
          <ExperimentOutlined style={{ color: '#1890ff' }} />
          记忆统计概览
          <Tooltip title="显示当前用户的记忆统计信息">
            <InfoCircleOutlined style={{ color: '#999' }} />
          </Tooltip>
        </Space>
      }
      extra={
        <Button 
          icon={<ReloadOutlined />} 
          onClick={onRefresh}
          loading={loading}
          size="small"
        >
          刷新
        </Button>
      }
      loading={loading}
    >
      <Row gutter={[24, 16]}>
        {/* 当前用户信息 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Statistic
              title="当前用户"
              value={stats?.current_user || '未知'}
              prefix={<UserOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>

        {/* 个人档案记忆 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Statistic
              title="个人档案"
              value={stats?.user_memory_count?.profile || 0}
              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
              suffix="条"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>

        {/* 专业技能记忆 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Statistic
              title="专业技能"
              value={stats?.user_memory_count?.expertise || 0}
              prefix={<DatabaseOutlined style={{ color: '#722ed1' }} />}
              suffix="条"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>

        {/* 个人偏好记忆 */}
        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center' }}>
            <Statistic
              title="个人偏好"
              value={stats?.user_memory_count?.preferences || 0}
              prefix={<HistoryOutlined style={{ color: '#fa541c' }} />}
              suffix="条"
              valueStyle={{ color: '#fa541c' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 状态标签 */}
      <Row style={{ marginTop: '16px' }}>
        <Col span={24} style={{ textAlign: 'center' }}>
          <Space>
            <Tag color="blue">记忆系统状态</Tag>
            <Tag color={stats?.status === 'active' ? 'green' : 'orange'}>
              {stats?.status === 'active' ? '运行正常' : '状态未知'}
            </Tag>
          </Space>
        </Col>
      </Row>
    </Card>
  );
};

export default MemoryStatsCard;