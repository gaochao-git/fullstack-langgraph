import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Tabs, Typography, Card } from 'antd';
import {
  DatabaseOutlined,
  HddOutlined,
  ClusterOutlined,
  ExperimentOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import HostPoolList from './components/HostPoolList';
import HostResourceUsageAnalysis from './components/HostResourceUsageAnalysis';
import ClusterResourceUsageReport from './components/ClusterResourceUsageReport';
import HardwareResourceVerification from './components/HardwareResourceVerification';
import AdminManagement from './components/AdminManagement';

const { Title } = Typography;

const tabItems = [
  {
    key: 'pool',
    path: '/rp/hardware/pool',
    label: (
      <span>
        <DatabaseOutlined style={{ marginRight: 8 }} />
        资源池总览
      </span>
    ),
    children: <HostPoolList />,
  },
  {
    key: 'host-usage',
    path: '/rp/hardware/host-usage',
    label: (
      <span>
        <HddOutlined style={{ marginRight: 8 }} />
        主机资源用量分析
      </span>
    ),
    children: <HostResourceUsageAnalysis />,
  },
  {
    key: 'cluster-usage',
    path: '/rp/hardware/cluster-usage',
    label: (
      <span>
        <ClusterOutlined style={{ marginRight: 8 }} />
        集群资源用量报告
      </span>
    ),
    children: <ClusterResourceUsageReport onShowValidityReport={() => {}} />,
  },
  {
    key: 'verification',
    path: '/rp/hardware/verification',
    label: (
      <span>
        <ExperimentOutlined style={{ marginRight: 8 }} />
        硬件资源验证
      </span>
    ),
    children: <HardwareResourceVerification />,
  },
  {
    key: 'admin',
    path: '/rp/hardware/admin',
    label: (
      <span>
        <SettingOutlined style={{ marginRight: 8 }} />
        系统管理
      </span>
    ),
    children: <AdminManagement />,
  },
];

const HardwareResourceManagement: React.FC = () => {
  const location = useLocation();
  const [activeKey, setActiveKey] = useState('pool');

  // 根据当前路径设置活动标签
  useEffect(() => {
    const currentPath = location.pathname;
    const matchedTab = tabItems.find(tab => tab.path === currentPath);
    if (matchedTab) {
      setActiveKey(matchedTab.key);
    } else if (currentPath === '/rp/hardware') {
      // 如果是主路径，默认显示第一个标签
      setActiveKey('pool');
    }
  }, [location.pathname]);

  // 获取当前要显示的内容
  const getCurrentContent = () => {
    const currentTab = tabItems.find(tab => tab.key === activeKey);
    return currentTab?.children || tabItems[0].children;
  };

  return (
    <Card
      bordered={false}
      style={{
        boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)',
        borderRadius: '8px',
        height: '100%',
      }}
    >
      <Title level={3} style={{ marginBottom: 24 }}>
        硬件资源管理
      </Title>

      <Tabs
        activeKey={activeKey}
        onChange={setActiveKey}
        items={tabItems.map(tab => ({
          key: tab.key,
          label: tab.label,
          children: tab.children
        }))}
        size="large"
        style={{
          marginTop: -12,
        }}
      />
    </Card>
  );
};

export default HardwareResourceManagement;
export { HardwareResourceManagement };
