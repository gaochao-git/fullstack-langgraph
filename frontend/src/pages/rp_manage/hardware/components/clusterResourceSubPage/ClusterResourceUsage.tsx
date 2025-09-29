// @ts-nocheck
// 集群资源使用情况组件
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, message, Modal, Button } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getTextColumnSearchProps, getNumberRangeFilterProps, getColumnSorter, getPercentageValue } from '../../utils/tableUtils';
import apiClient from '../../services/apiClient';
import moment from '../../vendor/moment';

// 集群详细数据弹出界面组件
const ClusterDetailsModal = ({ visible, onCancel, clusterName, dateRange }) => {
  const [loading, setLoading] = useState(false);
  const [clusterData, setClusterData] = useState([]);
  const [originalData, setOriginalData] = useState([]);
  const [sortedInfo, setSortedInfo] = useState({});
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';

  const fetchClusterDetails = async (page = 1, pageSize = 10) => {
    if (!clusterName) return;
    
    setLoading(true);
    try {
      const params = {
        page,
        pageSize,
      };
      
      // 处理集群名称参数
      if (clusterName === '未分配集群') {
        // 对于未分配集群，传递空字符串让后端进行正确的过滤
        params.clusterName = '';
      } else {
        params.clusterName = clusterName;
      }

      // 设置时间范围参数 - 尝试多种可能的参数名以确保后端能正确接收
      if (dateRange && dateRange[0] && dateRange[1]) {
        params.beginTime = dateRange[0].format('YYYY-MM-DD');
        params.endTime = dateRange[1].format('YYYY-MM-DD');
        params.startDate = dateRange[0].format('YYYY-MM-DD');
        params.endDate = dateRange[1].format('YYYY-MM-DD');
        params.start_time = dateRange[0].format('YYYY-MM-DD 00:00:00');
        params.end_time = dateRange[1].format('YYYY-MM-DD 23:59:59');
      } else {
        const defaultStart = moment().subtract(3, 'months');
        const defaultEnd = moment();
        params.beginTime = defaultStart.format('YYYY-MM-DD');
        params.endTime = defaultEnd.format('YYYY-MM-DD');
        params.startDate = defaultStart.format('YYYY-MM-DD');
        params.endDate = defaultEnd.format('YYYY-MM-DD');
        params.start_time = defaultStart.format('YYYY-MM-DD 00:00:00');
        params.end_time = defaultEnd.format('YYYY-MM-DD 23:59:59');
      }

      // 获取集群主机资源使用率详细数据
      const response = await apiClient.axiosGet('/api/cmdb/v1/cluster-resources', { params });

      // 调试：检查API返回数据的字段结构
      if (response.data.list && response.data.list.length > 0) {
        const firstRecord = response.data.list[0];
      }
      
      const data = Array.isArray(response.data) ? response.data : (response.data.list || []);
      
      // 检查是否包含异常数据
      const hasAnomalousData = data.some(item => {
        if (!item) return false;
        const memoryUsage = (Number(item.used_memory) || 0) / (Number(item.total_memory) || 1) * 100;
        const diskUsage = (Number(item.used_disk) || 0) / (Number(item.total_disk) || 1) * 100;
        return memoryUsage > 100 || diskUsage > 100;
      });

      // 新的cluster-resources接口已经按集群名称过滤了数据，无需额外过滤
      const filteredData = data;

      // 使用后端提供的序列号进行排序（如果有的话）
      const sortedData = filteredData.sort((a, b) => {
        // 优先使用后端提供的序列号
        if (a.sequence_number && b.sequence_number) {
          return a.sequence_number - b.sequence_number;
        }
        
        // 备用排序方案：模拟后端排序逻辑
        const aCluster = a.cluster_name || '';
        const bCluster = b.cluster_name || '';
        if (aCluster !== bCluster) {
          return aCluster.localeCompare(bCluster);
        }
        
        const aIp = a.ip || a.ip_address || '';
        const bIp = b.ip || b.ip_address || '';
        if (aIp !== bIp) {
          return aIp.localeCompare(bIp);
        }
        
        const aHostName = a.host_name || '';
        const bHostName = b.host_name || '';
        if (aHostName !== bHostName) {
          return aHostName.localeCompare(bHostName);
        }
        
        const aDateTime = a.datetime || '';
        const bDateTime = b.datetime || '';
        if (aDateTime !== bDateTime) {
          return aDateTime.localeCompare(bDateTime);
        }
        
        return (a.id || 0) - (b.id || 0);
      });

      setOriginalData(sortedData);
      
      // 实现客户端分页 - 使用排序后的数据
      const startIndex = (page - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      const paginatedData = sortedData.slice(startIndex, endIndex);
      
      setClusterData(paginatedData);
      setSortedInfo({}); // 重置排序状态
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: sortedData.length,
      }));
    } catch (error) {
      console.error('获取集群详细数据失败:', error);
      message.error('获取集群详细数据失败');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (visible && clusterName) {
      fetchClusterDetails(pagination.current, pagination.pageSize);
    }
  }, [visible, clusterName, dateRange]);

  // 生成唯一的 rowKey
  const generateRowKey = (record, index) => {
    // 优先使用后端提供的序列号
    if (record.sequence_number) {
      return `seq-${record.sequence_number}`;
    }
    
    // 备用方案：使用数据库ID
    if (record.id) return `id-${record.id}`;
    
    // 最后的备用方案：基于内容生成唯一ID
    const parts = [
      record.cluster_name || 'cluster',
      record.ip || record.ip_address || 'ip',
      record.host_name || 'host',
      record.datetime || new Date().toISOString(),
      String(index)
    ];
    
    // 创建一个基于内容的哈希码
    const hashCode = parts.join('-').split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    
    return `cluster-${Math.abs(hashCode)}-${index}`;
  };

  const columns = [
    {
      title: '集群名称',
      dataIndex: 'cluster_name',
      key: 'cluster_name',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'cluster_name' && sortedInfo.order,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'ip' && sortedInfo.order,
      render: (value, record) => value || record.ip_address,
    },
    {
      title: '主机名',
      dataIndex: 'host_name',
      key: 'host_name',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'host_name' && sortedInfo.order,
    },
    {
      title: 'CPU负载 (%)',
      dataIndex: 'cpu_load',
      key: 'cpu_load',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'cpu_load' && sortedInfo.order,
      render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
    },
    {
      title: '已用内存 (GB)',
      dataIndex: 'used_memory',
      key: 'used_memory',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'used_memory' && sortedInfo.order,
      render: (value) => `${(Number(value) || 0).toFixed(2)} GB`,
    },
    {
      title: '总内存 (GB)',
      dataIndex: 'total_memory',
      key: 'total_memory',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'total_memory' && sortedInfo.order,
      render: (value) => `${(Number(value) || 0).toFixed(2)} GB`,
    },
    {
      title: '内存使用率 (%)',
      key: 'memory_usage',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'memory_usage' && sortedInfo.order,
      render: (_, record) => {
        const usedMemory = Number(record.used_memory) || 0;
        const totalMemory = Number(record.total_memory) || 1;
        const usage = (usedMemory / totalMemory) * 100;
        return `${usage.toFixed(2)}%`;
      },
    },
    {
      title: '已用磁盘 (GB)',
      dataIndex: 'used_disk',
      key: 'used_disk',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'used_disk' && sortedInfo.order,
      render: (value) => `${(Number(value) || 0).toFixed(2)} GB`,
    },
    {
      title: '总磁盘 (GB)',
      dataIndex: 'total_disk',
      key: 'total_disk',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'total_disk' && sortedInfo.order,
      render: (value) => `${(Number(value) || 0).toFixed(2)} GB`,
    },
    {
      title: '磁盘使用率 (%)',
      key: 'disk_usage',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'disk_usage' && sortedInfo.order,
      render: (_, record) => {
        const usedDisk = Number(record.used_disk) || 0;
        const totalDisk = Number(record.total_disk) || 1;
        const usage = (usedDisk / totalDisk) * 100;
        return `${usage.toFixed(2)}%`;
      },
    },
    {
      title: '时间戳',
      dataIndex: 'date_time',
      key: 'date_time',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'date_time' && sortedInfo.order,
      render: (value, record) => {
        // 尝试多种可能的时间字段，优先使用date_time
        const timeValue = value || record.datetime || record.create_time || record.update_time || record.timestamp || record.collected_at;
        if (!timeValue) return 'N/A';

        const date = new Date(timeValue);
        if (isNaN(date.getTime())) {
          // 如果日期解析失败，返回原始值
          return timeValue;
        }

        // 格式化为本地时间字符串
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      },
    },
  ];

  // 客户端排序函数
  const sortData = (data, sorter) => {
    // 如果没有排序器、没有列键或没有排序方向，返回原始数据
    if (!sorter || !sorter.columnKey || !sorter.order) {
      console.log('No sorting applied, returning original data');
      return [...data]; // 返回数组副本避免引用问题
    }

    return [...data].sort((a, b) => {
      let aVal, bVal;
      
      // 根据不同的列类型处理排序值
      switch (sorter.columnKey) {
        case 'memory_usage':
          aVal = (Number(a.used_memory) || 0) / (Number(a.total_memory) || 1) * 100;
          bVal = (Number(b.used_memory) || 0) / (Number(b.total_memory) || 1) * 100;
          break;
        case 'disk_usage':
          aVal = (Number(a.used_disk) || 0) / (Number(a.total_disk) || 1) * 100;
          bVal = (Number(b.used_disk) || 0) / (Number(b.total_disk) || 1) * 100;
          break;
        case 'date_time':
          aVal = new Date(a.date_time || a.datetime || 0).getTime();
          bVal = new Date(b.date_time || b.datetime || 0).getTime();
          break;
        case 'cluster_name':
        case 'host_name':
        case 'ip':
          // 文本字段
          aVal = String(a[sorter.columnKey] || '').toLowerCase();
          bVal = String(b[sorter.columnKey] || '').toLowerCase();
          return sorter.order === 'ascend' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        case 'cpu_load':
          aVal = Number(a.cpu_load) || 0;
          bVal = Number(b.cpu_load) || 0;
          break;
        case 'used_memory':
          aVal = Number(a.used_memory) || 0;
          bVal = Number(b.used_memory) || 0;
          break;
        case 'used_disk':
          aVal = Number(a.used_disk) || 0;
          bVal = Number(b.used_disk) || 0;
          break;
        default:
          // 其他数值字段
          aVal = Number(a[sorter.columnKey]) || 0;
          bVal = Number(b[sorter.columnKey]) || 0;
          break;
      }

      if (sorter.order === 'ascend') {
        return aVal - bVal;
      } else {
        return bVal - aVal;
      }
    });
  };

  const handleTableChange = (paginationConfig, filters, sorter) => {
    
    // 更新排序状态
    setSortedInfo(sorter || {});
    
    // 应用排序
    const sortedData = sortData(originalData, sorter);

    // 应用客户端分页
    const { current, pageSize } = paginationConfig;
    const startIndex = (current - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedData = sortedData.slice(startIndex, endIndex);

    setClusterData(paginatedData);
    
    // 更新分页信息
    setPagination(prev => ({
      ...prev,
      current: current,
      pageSize: pageSize,
      total: sortedData.length,
    }));
  };

  return (
    <Modal
      title={`集群 ${clusterName} 的详细数据源`}
      visible={visible}
      onCancel={onCancel}
      footer={[
        <Button key="close" onClick={onCancel}>
          关闭
        </Button>
      ]}
      width={1400}
      destroyOnClose
    >
      <Table
        columns={columns}
        dataSource={clusterData}
        loading={loading}
        sortDirections={['ascend', 'descend']}
        showSorterTooltip={false}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
        }}
        onChange={handleTableChange}
        rowKey={generateRowKey}
        scroll={{ x: 1200 }}
      />
    </Modal>
  );
};

// 添加列定义导出函数
export const getClusterResourceColumns = (onClusterClick) => [
  {
    title: '集群名称',
    dataIndex: 'clusterName',
    ...getTextColumnSearchProps('clusterName', '集群名称'),
    ...getColumnSorter('clusterName'),
    render: (value) => (
      <Button 
        type="link" 
        style={{ padding: 0, height: 'auto' }}
        onClick={() => onClusterClick && onClusterClick(value)}
      >
        {value}
      </Button>
    ),
  },
  {
    title: '集群组名称',
    dataIndex: 'groupName',
    ...getTextColumnSearchProps('groupName', '集群组名称'),
    ...getColumnSorter('groupName'),
  },
  {
    title: 'CPU使用率(平均)',
    dataIndex: 'cpu',
    ...getNumberRangeFilterProps('cpu', '%', (record) => {
      const value = Number(record.cpu);
      return isNaN(value) ? 0 : value;
    }),
    ...getColumnSorter('cpu', (record) => {
      const value = Number(record.cpu);
      return isNaN(value) ? 0 : value;
    }),
    render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
  },
  {
    title: 'CPU使用率(最大)',
    dataIndex: 'maxCPU',
    ...getNumberRangeFilterProps('maxCPU', '%', (record) => {
      const value = Number(record.maxCPU);
      return isNaN(value) ? 0 : value;
    }),
    ...getColumnSorter('maxCPU', (record) => {
      const value = Number(record.maxCPU);
      return isNaN(value) ? 0 : value;
    }),
    render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
  },
  {
    title: '内存使用率(平均)',
    dataIndex: 'memory',
    ...getNumberRangeFilterProps('memory', '%', (record) => {
      const value = Number(record.memory);
      return isNaN(value) ? 0 : value;
    }),
    ...getColumnSorter('memory', (record) => {
      const value = Number(record.memory);
      return isNaN(value) ? 0 : value;
    }),
    render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
  },
  {
    title: '内存使用率(最大)',
    dataIndex: 'maxMemory',
    ...getNumberRangeFilterProps('maxMemory', '%', (record) => {
      const value = Number(record.maxMemory);
      return isNaN(value) ? 0 : value;
    }),
    ...getColumnSorter('maxMemory', (record) => {
      const value = Number(record.maxMemory);
      return isNaN(value) ? 0 : value;
    }),
    render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
  },
  {
    title: '磁盘使用率(平均)',
    dataIndex: 'disk',
    ...getNumberRangeFilterProps('disk', '%', (record) => {
      const value = Number(record.disk);
      return isNaN(value) ? 0 : value;
    }),
    ...getColumnSorter('disk', (record) => {
      const value = Number(record.disk);
      return isNaN(value) ? 0 : value;
    }),
    render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
  },
  {
    title: '磁盘使用率(最大)',
    dataIndex: 'maxDisk',
    ...getNumberRangeFilterProps('maxDisk', '%', (record) => {
      const value = Number(record.maxDisk);
      return isNaN(value) ? 0 : value;
    }),
    ...getColumnSorter('maxDisk', (record) => {
      const value = Number(record.maxDisk);
      return isNaN(value) ? 0 : value;
    }),
    render: (value) => `${(Number(value) || 0).toFixed(2)}%`,
  }
];

const ClusterResourceUsage = ({ dateRange, data: externalData }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const data = externalData || [];

  const handleClusterClick = (clusterName) => {
    setSelectedCluster(clusterName);
    setModalVisible(true);
  };

  const handleModalClose = () => {
    setModalVisible(false);
    setSelectedCluster(null);
  };




  const renderClusterChart = (cluster, index) => {
    const roundToTwoDecimals = (value) => Math.round(value * 100) / 100;

    const chartData = [
      { 
        name: 'CPU', 
        平均: roundToTwoDecimals(cluster.cpu),
        最大: roundToTwoDecimals(cluster.maxCPU),
        最小: roundToTwoDecimals(cluster.minCPU)
      },
      { 
        name: '内存', 
        平均: roundToTwoDecimals(cluster.memory),
        最大: roundToTwoDecimals(cluster.maxMemory),
        最小: roundToTwoDecimals(cluster.minMemory)
      },
      { 
        name: '磁盘', 
        平均: roundToTwoDecimals(cluster.disk),
        最大: roundToTwoDecimals(cluster.maxDisk),
        最小: roundToTwoDecimals(cluster.minDisk)
      },
    ];

    return (
      <Col 
        key={`${cluster.groupName}-${cluster.clusterName}`}
        xs={24} 
        sm={12} 
        md={8} 
        lg={6} 
        xl={4} 
        xxl={4} 
        style={{ marginBottom: '20px' }}
      >
        <Card title={`${cluster.groupName}-${cluster.clusterName}`} style={{ height: 400 }}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} barSize={30}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
              <Tooltip formatter={(value) => `${value}%`} />
              <Legend />
              <Bar dataKey="平均" fill="#8884d8" name="平均使用率 (%)" />
              <Bar dataKey="最大" fill="#82ca9d" name="最大使用率 (%)" />
              <Bar dataKey="最小" fill="#ffc658" name="最小使用率 (%)" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    );
  };

  const sortedData = [...data].sort((a, b) => {
    const aKey = `${a.groupName}-${a.clusterName}`;
    const bKey = `${b.groupName}-${b.clusterName}`;
    return aKey.localeCompare(bKey);
  });

  const currentPageData = sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleTableChange = (pagination) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        {currentPageData.map((cluster, index) => renderClusterChart(cluster, index))}
      </Row>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Table
            columns={getClusterResourceColumns(handleClusterClick)}
            dataSource={sortedData}
            rowKey={(record) => `${record.groupName}-${record.clusterName}`}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: sortedData.length,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ['5', '10', '20', '50'],
              onChange: (page, pageSize) => {
                setCurrentPage(page);
                setPageSize(pageSize || 5);
              },
            }}
            onChange={handleTableChange}
            loading={false}
          />
        </Col>
      </Row>

      <ClusterDetailsModal
        visible={modalVisible}
        onCancel={handleModalClose}
        clusterName={selectedCluster}
        dateRange={dateRange}
      />
    </div>
  );
};

export default ClusterResourceUsage;
