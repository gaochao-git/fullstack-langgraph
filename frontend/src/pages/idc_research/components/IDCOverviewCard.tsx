import React from 'react';
import { Card, Badge, Progress } from 'antd';
import { CloudServerOutlined, ExperimentOutlined, ThunderboltOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { IDCData } from '../types/idc';

interface IDCOverviewCardProps {
  idc: IDCData;
  isSelected?: boolean;
  onSelect?: () => void;
}

export function IDCOverviewCard({ idc, isSelected, onSelect }: IDCOverviewCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return '正常';
      case 'warning':
        return '警告';
      case 'critical':
        return '严重';
      default:
        return '未知';
    }
  };

  const getProgressColor = (value: number) => {
    if (value >= 80) return '#ff4d4f';
    if (value >= 60) return '#faad14';
    return '#52c41a';
  };

  return (
    <Card
      hoverable
      onClick={onSelect}
      style={{
        cursor: 'pointer',
        border: isSelected ? '2px solid #1890ff' : '1px solid #d9d9d9',
        boxShadow: isSelected ? '0 4px 12px rgba(24, 144, 255, 0.15)' : undefined,
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>{idc.name}</h3>
          <Badge
            status={getStatusColor(idc.status) as any}
            text={getStatusText(idc.status)}
          />
        </div>
        <p style={{ margin: 0, color: '#666', fontSize: 14 }}>{idc.location}</p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 16,
        marginBottom: 16,
        fontSize: 14
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CloudServerOutlined style={{ color: '#666' }} />
          <span>{idc.serverCount} 台服务器</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ClockCircleOutlined style={{ color: '#666' }} />
          <span>{idc.uptime}% 可用性</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ExperimentOutlined style={{ color: '#666' }} />
          <span>{idc.temperature}°C</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ThunderboltOutlined style={{ color: '#666' }} />
          <span>{idc.powerUsage}kW</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 14 }}>
            <span>CPU使用率</span>
            <span>{idc.cpuUsage}%</span>
          </div>
          <Progress
            percent={idc.cpuUsage}
            strokeColor={getProgressColor(idc.cpuUsage)}
            showInfo={false}
            size="small"
          />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 14 }}>
            <span>内存使用率</span>
            <span>{idc.memoryUsage}%</span>
          </div>
          <Progress
            percent={idc.memoryUsage}
            strokeColor={getProgressColor(idc.memoryUsage)}
            showInfo={false}
            size="small"
          />
        </div>

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 14 }}>
            <span>网络负载</span>
            <span>{idc.networkLoad}%</span>
          </div>
          <Progress
            percent={idc.networkLoad}
            strokeColor={getProgressColor(idc.networkLoad)}
            showInfo={false}
            size="small"
          />
        </div>
      </div>

      <div style={{
        paddingTop: 16,
        marginTop: 16,
        borderTop: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ fontSize: 14 }}>稳定性评分</span>
        <span style={{ fontWeight: 600, color: idc.stabilityScore >= 95 ? '#52c41a' : '#faad14' }}>
          {idc.stabilityScore}
        </span>
      </div>
    </Card>
  );
}