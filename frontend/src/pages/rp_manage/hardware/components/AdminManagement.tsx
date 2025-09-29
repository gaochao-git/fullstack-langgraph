// @ts-nocheck
import React, { useState } from 'react';
import { Typography, Menu, Layout, MenuProps } from 'antd';
import {
  SyncOutlined,
  BarChartOutlined,
  EyeOutlined,
  HddOutlined,
  AppstoreOutlined,
  CloudSyncOutlined,
  PlusCircleOutlined,
  SettingOutlined
} from '@ant-design/icons';
import ClusterGroupSync from './adminManagmentSubPage/ClusterGroupSync';
import ServerMetricsLoader from './adminManagmentSubPage/ServerMetricsLoader';
import MonitoringVerification from './adminManagmentSubPage/MonitoringVerification';
import HardwareInfoSync from './adminManagmentSubPage/HardwareInfoSync';
import BatchApplicationManagement from './adminManagmentSubPage/BatchApplicationManagement';
import ExternalCmdbSync from './adminManagmentSubPage/ExternalCmdbSync';
import ManualAddHost from './adminManagmentSubPage/ManualAddHost';

const { Title } = Typography;
const { Sider, Content } = Layout;

const AdminManagement: React.FC = () => {
  const [selectedMenu, setSelectedMenu] = useState('cluster-sync');

  const menuItems: MenuProps['items'] = [
    {
      key: 'cluster-sync',
      icon: <SyncOutlined />,
      label: '集群组数据同步',
    },
    {
      key: 'server-metrics',
      icon: <BarChartOutlined />,
      label: '监控指标数据加载',
    },
    {
      key: 'monitoring-verification',
      icon: <EyeOutlined />,
      label: '监控数据核对',
    },
    {
      key: 'hardware-info-sync',
      icon: <HddOutlined />,
      label: '硬件信息获取',
    },
    {
      key: 'batch-application-management',
      icon: <AppstoreOutlined />,
      label: '批量应用管理',
    },
    {
      key: 'external-cmdb-sync',
      icon: <CloudSyncOutlined />,
      label: '外部CMDB同步',
    },
    {
      key: 'manual-add-host',
      icon: <PlusCircleOutlined />,
      label: '手动添加主机',
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
            <SettingOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            系统管理
          </Title>
        </div>

        {selectedMenu === 'cluster-sync' && <ClusterGroupSync />}
        {selectedMenu === 'server-metrics' && <ServerMetricsLoader />}
        {selectedMenu === 'monitoring-verification' && <MonitoringVerification />}
        {selectedMenu === 'hardware-info-sync' && <HardwareInfoSync />}
        {selectedMenu === 'batch-application-management' && <BatchApplicationManagement />}
        {selectedMenu === 'external-cmdb-sync' && <ExternalCmdbSync />}
        {selectedMenu === 'manual-add-host' && <ManualAddHost />}
      </Content>
    </Layout>
  );
};

export default AdminManagement;