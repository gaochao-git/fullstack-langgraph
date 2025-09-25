import React, { useState, useEffect } from 'react';
import { Card, Badge, Alert, Row, Col, Statistic } from 'antd';
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';

interface SystemAlert {
  id: string;
  level: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  idcName: string;
}

export function RealTimeStatus() {
  const [alerts, setAlerts] = useState<SystemAlert[]>([
    {
      id: '1',
      level: 'critical',
      message: '成都数据中心CPU使用率超过85%阈值',
      timestamp: new Date().toISOString(),
      idcName: '成都数据中心',
    },
    {
      id: '2',
      level: 'warning',
      message: '广州数据中心温度偏高，当前26°C',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      idcName: '广州数据中心',
    },
    {
      id: '3',
      level: 'info',
      message: '北京数据中心完成定期维护，所有服务恢复正常',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      idcName: '北京数据中心',
    },
  ]);

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const getAlertType = (level: string) => {
    switch (level) {
      case 'critical':
        return 'error' as const;
      case 'warning':
        return 'warning' as const;
      case 'info':
        return 'info' as const;
      default:
        return 'info' as const;
    }
  };

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <CloseCircleOutlined style={{ color: 'var(--color-destructive)' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: 'var(--color-warning)' }} />;
      case 'info':
        return <CheckCircleOutlined style={{ color: 'var(--color-success)' }} />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  const formatRelativeTime = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}小时前`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}天前`;
  };

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>实时状态监控</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-muted-foreground)', fontSize: 14 }}>
          <ClockCircleOutlined />
          <span>
            {currentTime.toLocaleString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </span>
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Card size="small" style={{ backgroundColor: 'var(--success-soft-bg)', border: '1px solid var(--success-soft-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <CheckCircleOutlined style={{ fontSize: 20, color: 'var(--color-success)' }} />
                <div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 500 }}>正常运行</p>
                  <p style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>3 个数据中心</p>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small" style={{ backgroundColor: 'var(--warning-soft-bg)', border: '1px solid var(--warning-soft-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <ExclamationCircleOutlined style={{ fontSize: 20, color: 'var(--color-warning)' }} />
                <div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 500 }}>警告状态</p>
                  <p style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>1 个数据中心</p>
                </div>
              </div>
            </Card>
          </Col>
          <Col span={8}>
            <Card size="small" style={{ backgroundColor: 'var(--destructive-soft-bg)', border: '1px solid var(--destructive-soft-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <CloseCircleOutlined style={{ fontSize: 20, color: 'var(--color-destructive)' }} />
                <div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 500 }}>严重警告</p>
                  <p style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>1 个数据中心</p>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </div>

      <div>
        <h4 style={{ marginBottom: 16, fontSize: 16, fontWeight: 500 }}>最新告警</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {alerts.map((alert) => (
            <Alert
              key={alert.id}
              type={getAlertType(alert.level)}
              message={
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <Badge
                      color={alert.level === 'critical' ? 'red' : alert.level === 'warning' ? 'orange' : 'green'}
                      text={alert.idcName}
                    />
                    <span style={{ fontSize: 12, color: 'var(--color-muted-foreground)' }}>
                      {formatRelativeTime(alert.timestamp)}
                    </span>
                  </div>
                  <div style={{ fontSize: 14 }}>
                    {alert.message}
                  </div>
                </div>
              }
              showIcon
              icon={getAlertIcon(alert.level)}
            />
          ))}
        </div>
      </div>
    </Card>
  );
}
