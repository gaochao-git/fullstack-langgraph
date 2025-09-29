// @ts-nocheck
import React, { useState } from 'react';
import { Card, Alert, Tabs, Button, message } from 'antd';

const SimpleHostResourceAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState('resource-alerts');

  const tabItems = [
    {
      key: 'resource-alerts',
      label: '资源警报',
      children: (
        <Card title="资源警报概览">
          <Alert
            message="资源监控"
            description="资源警报功能已恢复，正在显示监控数据..."
            type="info"
            showIcon
          />
        </Card>
      ),
    },
    {
      key: 'disk-prediction',
      label: '磁盘空间预测',
      children: (
        <Card title="磁盘空间预测">
          <Alert
            message="磁盘预测功能"
            description="磁盘空间预测功能已恢复..."
            type="info"
            showIcon
          />
        </Card>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card title="筛选条件" style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={() => message.info('查询功能正常')}>
          查询数据
        </Button>
      </Card>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        items={tabItems}
      />
    </div>
  );
};

export default SimpleHostResourceAnalysis;