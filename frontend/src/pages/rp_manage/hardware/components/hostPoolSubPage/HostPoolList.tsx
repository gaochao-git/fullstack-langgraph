// @ts-nocheck
// 主机资源池列表页
import React, { useState, useEffect, useCallback } from 'react';
import { Table, Input, Select, Button, Card, Typography } from 'antd';
import { getTextColumnSearchProps, getNumberRangeFilterProps, getColumnSorter } from '../../utils/tableUtils';
import apiClient from '../../services/apiClient';
import HostDetail from './HostDetail';
import './HostPoolStyles.css';

const { Option } = Select;

// 获取IDC名称，优先使用服务端返回的IDC信息
const getIDCName = (host) => {
  if (host.idc_info && host.idc_info.idc_name) {
    return host.idc_info.idc_name;
  }
  return '未知机房';
};

const HostList = () => {
  const [hosts, setHosts] = useState([]);
  const [filteredHosts, setFilteredHosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ipFilter, setIpFilter] = useState('');
  const [datacenterFilter, setDatacenterFilter] = useState([]);
  const [appTypeFilter, setAppTypeFilter] = useState([]);
  const [departmentFilter, setDepartmentFilter] = useState([]);
  const [selectedHost, setSelectedHost] = useState(null);
  const [isCustomModalVisible, setIsCustomModalVisible] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiClient.get('cmdb/v1/get_hosts_pool_detail')
      .then(response => {
        // 判断数据格式：如果是 {list: []} 格式则取 list，否则直接使用数组
        const hostsList = Array.isArray(response.data) 
          ? response.data 
          : (response.data.list || []);
        setHosts(hostsList);
        setFilteredHosts(hostsList);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching hosts:', error);
        setError('Failed to fetch hosts data');
        setLoading(false);
      });
  }, []);

  const applyFilters = useCallback(() => {
    let filtered = hosts;

    if (ipFilter) {
      filtered = filtered.filter(host => host.host_ip.includes(ipFilter));
    }

    if (datacenterFilter.length > 0) {
      filtered = filtered.filter(host => {
        const idcName = getIDCName(host);
        return datacenterFilter.includes(idcName);
      });
    }

    if (appTypeFilter.length > 0) {
      filtered = filtered.filter(host => 
        host.host_applications.some(app => appTypeFilter.includes(app.server_type))
      );
    }

    if (departmentFilter.length > 0) {
      filtered = filtered.filter(host => 
        host.host_applications.some(app => departmentFilter.includes(app.department_name))
      );
    }

    setFilteredHosts(filtered);
  }, [hosts, ipFilter, datacenterFilter, appTypeFilter, departmentFilter]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const showHostDetail = (host) => {
    setSelectedHost(host);
    setIsCustomModalVisible(true);
  };

  const handleCloseModal = () => {
    setIsCustomModalVisible(false);
  };

  const handleRefreshData = () => {
    setLoading(true);
    apiClient.get('cmdb/v1/get_hosts_pool_detail')
      .then(response => {
        const hostsList = Array.isArray(response.data) 
          ? response.data 
          : (response.data.list || []);
        setHosts(hostsList);
        setFilteredHosts(hostsList);
        
        // 如果当前有选中的主机，更新其数据
        if (selectedHost) {
          const updatedHost = hostsList.find(host => host.id === selectedHost.id);
          if (updatedHost) {
            setSelectedHost(updatedHost);
          }
        }
        
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching hosts:', error);
        setError('Failed to fetch hosts data');
        setLoading(false);
      });
  };

  const columns = [
    {
      title: '主机名',
      dataIndex: 'host_name',
      key: 'host_name',
      ...getTextColumnSearchProps('host_name', '主机名'),
      ...getColumnSorter('host_name'),
      render: (text, record) => (
        <Button type="link" onClick={() => showHostDetail(record)}>
          {text}
        </Button>
      ),
    },
    {
      title: 'IP地址',
      dataIndex: 'host_ip',
      key: 'host_ip',
      ...getTextColumnSearchProps('host_ip', 'IP地址'),
      ...getColumnSorter('host_ip'),
    },
    {
      title: 'CPU核数',
      dataIndex: 'vcpus',
      key: 'vcpus',
      ...getNumberRangeFilterProps('vcpus', '核'),
      ...getColumnSorter('vcpus'),
      render: (value) => `${value || 0} 核`,
    },
    {
      title: '内存大小(GB)',
      dataIndex: 'ram',
      key: 'ram',
      ...getNumberRangeFilterProps('ram', 'GB'),
      ...getColumnSorter('ram'),
      render: (value) => `${value || 0} GB`,
    },
    {
      title: '硬盘空间(GB)',
      dataIndex: 'disk_size',
      key: 'disk_size',
      ...getNumberRangeFilterProps('disk_size', 'GB'),
      ...getColumnSorter('disk_size'),
      render: (value) => `${value || 0} GB`,
    },
    {
      title: 'IDC机房',
      key: 'idc_name',
      ...getColumnSorter('idc_name'),
      render: (text, record) => {
        const idcName = getIDCName(record);
        return idcName !== '未知机房' ? (
          <span style={{ color: '#1890ff' }}>{idcName}</span>
        ) : (
          <span style={{ color: '#999' }}>{idcName}</span>
        );
      },
    },
    {
      title: '主机类型',
      dataIndex: 'host_type',
      key: 'host_type',
      ...getTextColumnSearchProps('host_type', '主机类型'),
      ...getColumnSorter('host_type'),
      render: (text) => text === '0' ? '云主机' : '裸金属',
    },
  ];

  return (
    <div className="host-pool-container">
      <div className="host-pool-header">
        <Typography.Title level={3} className="host-pool-title">主机资源池</Typography.Title>
        <div className="filter-section">
          <div className="filter-item">
            <span className="filter-label">IP地址</span>
            <Input
              placeholder="搜索IP"
              value={ipFilter}
              onChange={(e) => setIpFilter(e.target.value)}
              className="filter-input"
            />
          </div>
          <div className="filter-item">
            <span className="filter-label">机房</span>
            <Select
              placeholder="选择机房"
              mode="multiple"
              value={datacenterFilter}
              onChange={(value) => setDatacenterFilter(value)}
              className="filter-select"
            >
              {Array.from(new Set(hosts.map(host => getIDCName(host)))).map((idcName) => (
                <Option key={idcName} value={idcName}>{idcName}</Option>
              ))}
            </Select>
          </div>
          <div className="filter-item">
            <span className="filter-label">应用类型</span>
            <Select
              placeholder="选择应用类型"
              mode="multiple"
              value={appTypeFilter}
              onChange={(value) => setAppTypeFilter(value)}
              className="filter-select"
            >
              {Array.from(new Set(hosts.flatMap(host => 
                host.host_applications ? host.host_applications.map((app) => app.server_type) : []
              ))).map((type) => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </div>
          <div className="filter-item">
            <span className="filter-label">所属部门</span>
            <Select
              placeholder="选择部门"
              mode="multiple"
              value={departmentFilter}
              onChange={(value) => setDepartmentFilter(value)}
              className="filter-select"
            >
              {Array.from(new Set(hosts.flatMap(host => 
                host.host_applications ? host.host_applications.map((app) => app.department_name) : []
              ))).map((dept) => (
                <Option key={dept} value={dept}>{dept}</Option>
              ))}
            </Select>
          </div>
          <Button 
            onClick={() => {
              setIpFilter('');
              setDatacenterFilter([]);
              setAppTypeFilter([]);
              setDepartmentFilter([]);
            }}
            className="reset-button"
          >
            重置
          </Button>
        </div>
      </div>
      <Table
        columns={columns}
        dataSource={filteredHosts}
        rowKey="id"
        loading={loading}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100', '500'],
          defaultPageSize: 10,
        }}
      />
      {isCustomModalVisible && (
        <div className="custom-modal" onClick={handleCloseModal}>
          <div className="custom-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">主机详情</h2>
              <button className="close" onClick={handleCloseModal}>&times;</button>
            </div>
            {selectedHost ? <HostDetail host={selectedHost} onRefresh={handleRefreshData} /> : <div>Loading...</div>}
          </div>
        </div>
      )}
    </div>
  );
};

export default HostList;