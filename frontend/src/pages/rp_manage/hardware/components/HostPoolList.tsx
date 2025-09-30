// @ts-nocheck
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Input, Select, Button, Card, Typography, Space, Tag, Modal, message, Tooltip } from 'antd';
import { SearchOutlined, ReloadOutlined, EyeOutlined, HddOutlined, DatabaseOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import apiClient from '../services/apiClient';
import HostDetail from './hostPoolSubPage/HostDetail';

const { Option } = Select;
const { Title } = Typography;

interface HostApplication {
  id: number;
  pool_id?: number;
  server_type: string;
  server_version?: string;
  server_subtitle?: string;
  cluster_name?: string;
  server_protocol?: string;
  server_addr?: string;
  department_name?: string;
}

interface IdcInfo {
  idc_name: string;
  idc_code: string;
  idc_location?: string;
}

interface Host {
  id: number;
  host_name: string;
  host_ip: string;
  vcpus: number;
  ram: number;
  disk_size: number;
  host_type: string;
  operating_system?: string;
  idc_info?: IdcInfo;
  host_applications: HostApplication[];
  create_time?: string;
  update_time?: string;
  // 新增字段
  h3c_id?: string;
  h3c_status?: string;
  h3c_img_id?: string;
  h3c_hm_name?: string;
  if_h3c_sync?: string;
  serial_number?: string;
  rack_number?: string;
  rack_height?: number;
  rack_start_number?: number;
  leaf_number?: string;
  from_factor?: number;
  is_deleted?: boolean;
  is_static?: boolean;
  is_delete?: string;
}

const HostPoolList: React.FC = () => {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [filteredHosts, setFilteredHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [selectedIdcs, setSelectedIdcs] = useState<string[]>([]);
  const [selectedAppTypes, setSelectedAppTypes] = useState<string[]>([]);
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([]);
  const [selectedHost, setSelectedHost] = useState<Host | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // 获取IDC名称
  const getIdcName = (host: Host): string => {
    return host.idc_info?.idc_name || '未知机房';
  };

  // 获取主机类型显示名称
  const getHostTypeDisplay = (hostType: string): string => {
    return hostType === '0' ? '云主机' : '裸金属';
  };

  // 获取应用类型列表
  const getAppTypes = (host: Host): string[] => {
    return host.host_applications?.map(app => app.server_type) || [];
  };

  // 获取部门列表
  const getDepartments = (host: Host): string[] => {
    return host.host_applications?.map(app => app.department_name).filter(Boolean) || [];
  };

  // 加载主机数据
  const loadHosts = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('cmdb/v1/get_hosts_pool_detail');
      const hostsList = Array.isArray(response.data)
        ? response.data
        : (response.data.list || []);

      setHosts(hostsList);
      setFilteredHosts(hostsList);
      console.log('加载主机数据成功:', hostsList.length, '台主机');
    } catch (error) {
      console.error('加载主机数据失败:', error);
      message.error('加载主机数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHosts();
  }, []);

  // 应用筛选
  const applyFilters = useCallback(() => {
    let filtered = hosts;

    // 文本搜索
    if (searchText) {
      filtered = filtered.filter(host =>
        host.host_name.toLowerCase().includes(searchText.toLowerCase()) ||
        host.host_ip.includes(searchText)
      );
    }

    // IDC筛选
    if (selectedIdcs.length > 0) {
      filtered = filtered.filter(host =>
        selectedIdcs.includes(getIdcName(host))
      );
    }

    // 应用类型筛选
    if (selectedAppTypes.length > 0) {
      filtered = filtered.filter(host =>
        getAppTypes(host).some(type => selectedAppTypes.includes(type))
      );
    }

    // 部门筛选
    if (selectedDepartments.length > 0) {
      filtered = filtered.filter(host =>
        getDepartments(host).some(dept => selectedDepartments.includes(dept))
      );
    }

    setFilteredHosts(filtered);
  }, [hosts, searchText, selectedIdcs, selectedAppTypes, selectedDepartments]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  // 显示主机详情
  const showHostDetail = (host: Host) => {
    setSelectedHost(host);
    setDetailModalVisible(true);
  };

  // 重置筛选
  const resetFilters = () => {
    setSearchText('');
    setSelectedIdcs([]);
    setSelectedAppTypes([]);
    setSelectedDepartments([]);
  };

  // 获取所有唯一的IDC
  const uniqueIdcs = Array.from(new Set(hosts.map(host => getIdcName(host))));

  // 获取所有唯一的应用类型
  const uniqueAppTypes = Array.from(new Set(
    hosts.flatMap(host => getAppTypes(host))
  )).filter(Boolean);

  // 获取所有唯一的部门
  const uniqueDepartments = Array.from(new Set(
    hosts.flatMap(host => getDepartments(host))
  )).filter(Boolean);

  const columns: ColumnsType<Host> = [
    {
      title: '主机名',
      dataIndex: 'host_name',
      key: 'host_name',
      fixed: 'left',
      width: 150,
      render: (text: string, record: Host) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => showHostDetail(record)}
          style={{ padding: 0 }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: 'IP地址',
      dataIndex: 'host_ip',
      key: 'host_ip',
      width: 130,
      render: (text: string) => (
        <code style={{ background: '#f5f5f5', padding: '2px 4px' }}>{text}</code>
      ),
    },
    {
      title: 'CPU核数',
      dataIndex: 'vcpus',
      key: 'vcpus',
      width: 100,
      align: 'center',
      sorter: (a: Host, b: Host) => (a.vcpus || 0) - (b.vcpus || 0),
      render: (value: number) => (
        <Tag color="blue">{value || 0} 核</Tag>
      ),
    },
    {
      title: '内存(GB)',
      dataIndex: 'ram',
      key: 'ram',
      width: 100,
      align: 'center',
      sorter: (a: Host, b: Host) => (a.ram || 0) - (b.ram || 0),
      render: (value: number) => (
        <Tag color="green">{value || 0} GB</Tag>
      ),
    },
    {
      title: '硬盘(GB)',
      dataIndex: 'disk_size',
      key: 'disk_size',
      width: 100,
      align: 'center',
      sorter: (a: Host, b: Host) => (a.disk_size || 0) - (b.disk_size || 0),
      render: (value: number) => (
        <Tag color="orange">{value || 0} GB</Tag>
      ),
    },
    {
      title: 'IDC机房',
      key: 'idc_name',
      width: 120,
      render: (_, record: Host) => {
        const idcName = getIdcName(record);
        return (
          <Tag color={idcName !== '未知机房' ? 'purple' : 'default'}>
            {idcName}
          </Tag>
        );
      },
    },
    {
      title: '主机类型',
      dataIndex: 'host_type',
      key: 'host_type',
      width: 100,
      render: (text: string) => (
        <Tag color={text === '0' ? 'cyan' : 'geekblue'}>
          {getHostTypeDisplay(text)}
        </Tag>
      ),
    },
    {
      title: '应用类型',
      key: 'app_types',
      width: 150,
      render: (_, record: Host) => {
        const appTypes = getAppTypes(record);
        return (
          <div>
            {appTypes.slice(0, 2).map((type, index) => (
              <Tag key={index} size="small" style={{ marginBottom: 2 }}>
                {type}
              </Tag>
            ))}
            {appTypes.length > 2 && (
              <Tooltip title={appTypes.slice(2).join(', ')}>
                <Tag size="small" color="default">+{appTypes.length - 2}</Tag>
              </Tooltip>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <Card>
      <div style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 16 }}>
          <HddOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          主机资源池
          <span style={{ fontSize: 14, fontWeight: 'normal', marginLeft: 8, color: '#666' }}>
            共 {filteredHosts.length} 台主机
          </span>
        </Title>

        <Space wrap size="middle">
          <Input
            placeholder="搜索主机名或IP地址"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />

          <Select
            placeholder="选择IDC机房"
            mode="multiple"
            value={selectedIdcs}
            onChange={setSelectedIdcs}
            style={{ minWidth: 150 }}
            allowClear
          >
            {uniqueIdcs.map(idc => (
              <Option key={idc} value={idc}>{idc}</Option>
            ))}
          </Select>

          <Select
            placeholder="选择应用类型"
            mode="multiple"
            value={selectedAppTypes}
            onChange={setSelectedAppTypes}
            style={{ minWidth: 150 }}
            allowClear
          >
            {uniqueAppTypes.map(type => (
              <Option key={type} value={type}>{type}</Option>
            ))}
          </Select>

          <Select
            placeholder="选择部门"
            mode="multiple"
            value={selectedDepartments}
            onChange={setSelectedDepartments}
            style={{ minWidth: 150 }}
            allowClear
          >
            {uniqueDepartments.map(dept => (
              <Option key={dept} value={dept}>{dept}</Option>
            ))}
          </Select>

          <Button onClick={resetFilters}>重置筛选</Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadHosts}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredHosts}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) =>
            `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          pageSizeOptions: ['10', '20', '50', '100'],
          defaultPageSize: 20,
        }}
        size="small"
      />

      {/* 主机详情弹窗 */}
      <Modal
        title={
          <span>
            <DatabaseOutlined style={{ marginRight: 8 }} />
            主机详情 - {selectedHost?.host_name}
          </span>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={1200}
        footer={null}
        style={{ top: 20 }}
        bodyStyle={{ maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}
      >
        {selectedHost && <HostDetail host={selectedHost} onRefresh={loadHosts} />}
      </Modal>
    </Card>
  );
};

export default HostPoolList;