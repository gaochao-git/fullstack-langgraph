// @ts-nocheck
import React, { useState } from 'react';
import { Typography, Menu, Layout, MenuProps } from 'antd';
import {
  DashboardOutlined,
  RadarChartOutlined,
  HddOutlined,
  ScheduleOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import CpuResourceVerification from './hardwareResourceVerificationSubPage/CpuResourceVerification';
import MemoryResourceVerification from './hardwareResourceVerificationSubPage/MemoryResourceVerification';
import DiskResourceVerification from './hardwareResourceVerificationSubPage/DiskResourceVerification';
import ScheduledTaskManagement from './hardwareResourceVerificationSubPage/ScheduledTaskManagement';

const { Title } = Typography;
const { Sider, Content } = Layout;

const HardwareResourceVerification: React.FC = () => {
  const [selectedMenu, setSelectedMenu] = useState('cpu-verification');

  const menuItems: MenuProps['items'] = [
    {
      key: 'cpu-verification',
      icon: <DashboardOutlined />,
      label: 'CPU资源验证',
    },
    {
      key: 'memory-verification',
      icon: <RadarChartOutlined />,
      label: '内存资源验证',
    },
    {
      key: 'disk-verification',
      icon: <HddOutlined />,
      label: '磁盘资源验证',
    },
    {
      key: 'scheduled-tasks',
      icon: <ScheduleOutlined />,
      label: '定时任务管理',
    },
  ];

  return (
    <Layout style={{ background: '#fff' }}>
      <Sider width={200} style={{ background: '#fff' }}>
        <Menu
          mode="inline"
          selectedKeys={[selectedMenu]}
          style={{ height: '100%' }}
          onSelect={({ key }) => setSelectedMenu(key as string)}
          items={menuItems}
        />
      </Sider>
      <Content style={{ padding: '0 24px', minHeight: 280 }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Title level={2}>
            <ExperimentOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            硬件资源验证
          </Title>
        </div>

        {selectedMenu === 'cpu-verification' && <CpuResourceVerification />}
        {selectedMenu === 'memory-verification' && <MemoryResourceVerification />}
        {selectedMenu === 'disk-verification' && <DiskResourceVerification />}
        {selectedMenu === 'scheduled-tasks' && <ScheduledTaskManagement />}
      </Content>
    </Layout>
  );
};

export default HardwareResourceVerification;