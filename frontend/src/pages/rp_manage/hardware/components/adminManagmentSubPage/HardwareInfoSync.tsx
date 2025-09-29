// @ts-nocheck
import React, { useState } from 'react';
import { Card, Button, Table, Typography, notification, Input, Select, Tag } from 'antd';
import apiClient from '../../services/apiClient';
import { getTextColumnSearchProps } from '../../utils/tableUtils';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

const HardwareInfoSync = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [syncResult, setSyncResult] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // 获取主机硬件信息
  const fetchHardwareInfo = async (hostIpList = []) => {
    setLoading(true);
    try {
      const response = await apiClient.post('/api/cmdb/v1/fetch-hosts-hardware-info', {
        host_ip_list: hostIpList
      });
      const result = response.data;
      
      if (result.success) {
        setSyncResult({
          totalHosts: result.total_hosts,
          updatedHosts: result.updated_hosts,
          failedHosts: result.failed_hosts,
          message: result.message
        });
        
        // 转换数据格式用于表格显示
        const tableData = result.hardware_info_list.map((item, index) => ({
          key: index,
          hostIp: item.host_ip,
          hostName: item.host_name,
          disk: item.disk,
          ram: item.ram,
          vcpus: item.vcpus,
          status: item.success ? 'success' : 'failed',
          message: item.message,
        }));
        
        setData(tableData);
        
        notification.success({
          message: '硬件信息获取完成（模拟模式）',
          description: `总计: ${result.total_hosts}, 成功: ${result.updated_hosts}, 失败: ${result.failed_hosts}`,
          duration: 4,
        });
      } else {
        notification.error({
          message: '硬件信息获取失败',
          description: result.message || '未知错误',
          duration: 4,
        });
      }
    } catch (error) {
      console.error('硬件信息获取错误:', error);
      notification.error({
        message: '硬件信息获取失败',
        description: '网络连接错误或服务不可用',
        duration: 4,
      });
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '主机IP',
      dataIndex: 'hostIp',
      key: 'hostIp',
      width: 120,
      ...getTextColumnSearchProps('hostIp', '搜索主机IP'),
    },
    {
      title: '主机名',
      dataIndex: 'hostName',
      key: 'hostName',
      width: 150,
      ...getTextColumnSearchProps('hostName', '搜索主机名'),
    },
    {
      title: '磁盘大小(GB)',
      dataIndex: 'disk',
      key: 'disk',
      width: 100,
      sorter: (a, b) => a.disk - b.disk,
      render: (value) => value > 0 ? value : '-',
    },
    {
      title: '内存大小(GB)',
      dataIndex: 'ram',
      key: 'ram',
      width: 100,
      sorter: (a, b) => a.ram - b.ram,
      render: (value) => value > 0 ? value : '-',
    },
    {
      title: 'CPU核数',
      dataIndex: 'vcpus',
      key: 'vcpus',
      width: 80,
      sorter: (a, b) => a.vcpus - b.vcpus,
      render: (value) => value > 0 ? value : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      filters: [
        { text: '成功', value: 'success' },
        { text: '失败', value: 'failed' },
      ],
      onFilter: (value, record) => record.status === value,
      render: (status) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '结果信息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (text) => (
        <Text style={{ fontSize: '12px' }} title={text}>
          {text}
        </Text>
      ),
    },
  ];

  // 筛选后的数据
  const filteredData = data.filter(item => {
    const matchesSearch = !searchText || 
      item.hostIp.toLowerCase().includes(searchText.toLowerCase()) ||
      item.hostName.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      <Card 
        title={
          <div>
            <Title level={4} style={{ margin: 0, display: 'inline-block', marginRight: 8 }}>硬件信息获取</Title>
            <Text type="secondary" style={{ marginRight: 8 }}>从外部CMDB系统获取主机硬件信息并更新到hosts_pool表</Text>
            <Tag color="orange">当前为模拟模式</Tag>
          </div>
        }
        style={{ marginBottom: '16px' }}
      >
        <div style={{ width: '100%' }}>
          <div style={{ marginBottom: 16 }}>
            <Button 
              type="primary" 
              onClick={() => fetchHardwareInfo()}
              loading={loading}
              size="large"
              style={{ marginRight: 8 }}
            >
              获取所有主机硬件信息
            </Button>
            <Search
              placeholder="输入主机IP（多个用逗号分隔）"
              allowClear
              style={{ width: 300 }}
              onSearch={(value) => {
                const hostIpList = value.split(',').map(ip => ip.trim()).filter(ip => ip);
                fetchHardwareInfo(hostIpList);
              }}
              loading={loading}
            />
          </div>
          
          {syncResult && (
            <Card size="small" style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
              <div>
                <Text strong>同步结果：</Text>
                <div style={{ margin: '8px 0' }}>
                  <Tag color="blue">总计: {syncResult.totalHosts}</Tag>
                  <Tag color="green">成功: {syncResult.updatedHosts}</Tag>
                  <Tag color="red">失败: {syncResult.failedHosts}</Tag>
                </div>
                <Text type="secondary">{syncResult.message}</Text>
              </div>
            </Card>
          )}
        </div>
      </Card>

      {data.length > 0 && (
        <Card title="硬件信息详情">
          <div style={{ marginBottom: 16 }}>
            <Search
              placeholder="搜索主机IP或主机名"
              allowClear
              style={{ width: 200, marginRight: 8 }}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <Select
              placeholder="筛选状态"
              style={{ width: 120, marginRight: 8 }}
              value={statusFilter}
              onChange={setStatusFilter}
            >
              <Option value="all">全部状态</Option>
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
            </Select>
            <Text type="secondary">
              显示 {filteredData.length} / {data.length} 条记录
            </Text>
          </div>
          
          <Table
            columns={columns}
            dataSource={filteredData}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            }}
            scroll={{ x: 800 }}
            size="small"
          />
        </Card>
      )}
    </div>
  );
};

export default HardwareInfoSync;
