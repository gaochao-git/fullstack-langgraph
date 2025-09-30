// @ts-nocheck
// 主机资源详情组件
import React, { useState } from 'react';
import { Table, Button, DatePicker, Alert, Spin, Modal, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getTextColumnSearchProps, getNumberRangeFilterProps, getColumnSorter, getPercentageValue, getDateRangeFilterProps } from '../../utils/tableUtils';
import moment from '../../vendor/moment';
import apiClient from '../../services/apiClient';

interface IdcInfo {
  idc_name?: string;
  idc_code?: string;
}

interface ClusterInfo {
  cluster_name?: string;
  cluster_group_name?: string;
}

interface HostResourceData {
  id?: string | number;
  cluster_name?: string;
  group_name?: string;
  ip?: string;
  ip_address?: string;
  host_name?: string;
  port?: string;
  instance_role?: string;
  total_memory?: number;
  max_used_memory?: number;
  used_memory?: number;
  total_disk?: number;
  max_used_disk?: number;
  used_disk?: number;
  cpu_cores?: number;
  max_cpu_load?: number;
  cpu_load?: number;
  max_date_time?: string;
  date_time?: string;
  clusters?: ClusterInfo[];
  idc_info?: IdcInfo;
}

interface HostMetricsModalProps {
  visible: boolean;
  onCancel: () => void;
  hostIp: string | null;
  dateRange: [Moment, Moment] | null;
}

interface HostResourceDetailProps {
  data: HostResourceData[];
  pagination?: boolean;
  dateRange?: [Moment, Moment] | null;
  onDateChange?: (dates: [Moment, Moment] | null) => void;
  refreshData?: () => void;
  error?: string;
  loading?: boolean;
}

// 主机详细指标数据弹出界面组件
const HostMetricsModal: React.FC<HostMetricsModalProps> = ({ visible, onCancel, hostIp, dateRange }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [metricsData, setMetricsData] = useState<HostResourceData[]>([]);
  const [originalData, setOriginalData] = useState<HostResourceData[]>([]);
  const [sortedInfo, setSortedInfo] = useState<any>({});
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';

  const fetchHostMetrics = async (page: number = 1, pageSize: number = 10) => {
    if (!hostIp) return;

    setLoading(true);
    try {
      // 清空之前的数据
      setOriginalData([]);
      setMetricsData([]);
      setSortedInfo({}); // 重置排序状态

      const params = {
        ip: hostIp,
        page,
        pageSize,
      };

      if (dateRange && dateRange[0] && dateRange[1]) {
        params.startDate = dateRange[0].format('YYYY-MM-DD');
        params.endDate = dateRange[1].format('YYYY-MM-DD');
      } else {
        params.startDate = moment().subtract(3, 'months').format('YYYY-MM-DD');
        params.endDate = moment().format('YYYY-MM-DD');
      }

      const response = await apiClient.axiosGet('cmdb/v1/server-resources', { params });
      const data = Array.isArray(response.data) ? response.data : (response.data.list || []);

      // 直接使用后端返回的数据，无需客户端过滤
      setOriginalData(data);
      setMetricsData(data);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: data.length,
      }));
    } catch (error) {
      console.error('获取主机指标数据失败:', error);
      message.error('获取主机指标数据失败');
      // 出错时也要清空数据
      setOriginalData([]);
      setMetricsData([]);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    if (visible && hostIp) {
      fetchHostMetrics(pagination.current, pagination.pageSize);
    }
  }, [visible, hostIp, dateRange]);

  // 生成唯一的 rowKey
  const generateRowKey = (record: HostResourceData, index: number): string => {
    // 尝试多种方式生成唯一ID
    if (record.id) return String(record.id);
    
    const parts = [
      record.ip || record.ip_address || 'ip',
      record.host_name || 'host',
      record.date_time || new Date().toISOString(),
      String(record.cpu_load || 0),
      String(record.used_memory || 0),
      String(index)
    ];
    
    // 创建一个基于内容的哈希码
    const hashCode = parts.join('-').split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    
    return `host-${Math.abs(hashCode)}-${index}`;
  };

  const columns = [
    {
      title: 'IP地址',
      dataIndex: 'ip',
      key: 'ip',
      render: (value, record) => value || record.ip_address,
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
        const usage = getPercentageValue(record, 'used_memory', 'total_memory');
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
        const usage = getPercentageValue(record, 'used_disk', 'total_disk');
        return `${usage.toFixed(2)}%`;
      },
    },
    {
      title: '时间戳',
      dataIndex: 'date_time',
      key: 'date_time',
      sorter: true,
      sortOrder: sortedInfo.columnKey === 'date_time' && sortedInfo.order,
      render: (value) => {
        if (!value) return 'N/A';
        const date = new Date(value);
        return isNaN(date.getTime()) ? value : date.toLocaleString();
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
          aVal = getPercentageValue(a, 'used_memory', 'total_memory');
          bVal = getPercentageValue(b, 'used_memory', 'total_memory');
          break;
        case 'disk_usage':
          aVal = getPercentageValue(a, 'used_disk', 'total_disk');
          bVal = getPercentageValue(b, 'used_disk', 'total_disk');
          break;
        case 'date_time':
          aVal = new Date(a.date_time || 0).getTime();
          bVal = new Date(b.date_time || 0).getTime();
          break;
        default:
          // 数值字段
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
    console.log('=== HostMetricsModal Table Change Event ===');
    console.log('Pagination:', paginationConfig);
    console.log('Filters:', filters);
    console.log('Sorter:', sorter);
    console.log('Original data length:', originalData.length);
    console.log('Current metrics data length:', metricsData.length);
    
    // 检查排序参数
    if (sorter && sorter.columnKey) {
      console.log('Sorting by:', sorter.columnKey, 'Order:', sorter.order);
      
      // 显示前几条数据用于调试
      console.log('Sample original data:', originalData.slice(0, 3).map(item => ({
        [sorter.columnKey]: item[sorter.columnKey],
        ip: item.ip || item.ip_address
      })));
    }
    
    // 更新排序状态
    setSortedInfo(sorter || {});
    
    // 应用排序
    const sortedData = sortData(originalData, sorter);
    console.log('Sorted data length:', sortedData.length);
    
    if (sorter && sorter.columnKey && sortedData.length > 0) {
      console.log('Sample sorted data:', sortedData.slice(0, 3).map(item => ({
        [sorter.columnKey]: item[sorter.columnKey],
        ip: item.ip || item.ip_address
      })));
    }
    
    setMetricsData(sortedData);
    
    // 更新分页信息
    setPagination(prev => ({
      ...prev,
      current: paginationConfig.current,
      pageSize: paginationConfig.pageSize,
    }));
    
    console.log('=== End Table Change Event ===');
  };

  return (
    <Modal
      title={`主机 ${hostIp} 的详细监控数据`}
      visible={visible}
      onCancel={onCancel}
      footer={[
        <Button key="close" onClick={onCancel}>
          关闭
        </Button>
      ]}
      width={1200}
      destroyOnClose
    >
      <Table
        columns={columns}
        dataSource={metricsData}
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
        scroll={{ x: 1000 }}
      />
    </Modal>
  );
};

export const getHostResourceDetailColumns = (onIpClick?: (ip: string) => void): ColumnsType<HostResourceData> => [
  { 
    title: '主机IP', 
    dataIndex: 'ip',
    key: 'ip',
    ...getTextColumnSearchProps('ip', 'IP地址'),
    ...getColumnSorter('ip'),
    render: (value, record) => {
      const ip = value || record.ip_address;
      return (
        <Button 
          type="link" 
          style={{ padding: 0, height: 'auto' }}
          onClick={() => onIpClick && onIpClick(ip)}
        >
          {ip}
        </Button>
      );
    },
  },
  {
    title: 'IDC机房',
    dataIndex: 'idc_info',
    key: 'idc_info',
    ...getTextColumnSearchProps('idc_name', 'IDC机房', (record) => {
      return record.idc_info && record.idc_info.idc_name ? record.idc_info.idc_name : '';
    }),
    render: (idcInfo) => {
      if (idcInfo && idcInfo.idc_name) {
        return (
          <div>
            <div style={{ fontWeight: 'bold', color: '#1890ff' }}>
              {idcInfo.idc_name}
            </div>
            {idcInfo.idc_code && (
              <div style={{ fontSize: '12px', color: '#666' }}>
                ({idcInfo.idc_code})
              </div>
            )}
          </div>
        );
      }
      return <span style={{ color: '#ccc', fontStyle: 'italic' }}>未分配IDC</span>;
    },
  },
  { 
    title: '主机名', 
    dataIndex: 'host_name',
    key: 'host_name',
    ...getTextColumnSearchProps('host_name', '主机名'),
    ...getColumnSorter('host_name'),
  },
  {
    title: 'CPU最大利用率(%)',
    dataIndex: 'max_cpu_load',
    key: 'max_cpu_load',
    ...getNumberRangeFilterProps('max_cpu_load', '%'),
    ...getColumnSorter('max_cpu_load'),
    render: (value) => parseFloat(value || 0).toFixed(2)
  },
  {
    title: '内存最大利用率(%)',
    key: 'memory_usage',
    ...getNumberRangeFilterProps('memory_usage', '%', (record) => getPercentageValue(record, 'max_used_memory', 'total_memory')),
    sorter: (a, b) => getPercentageValue(a, 'max_used_memory', 'total_memory') - getPercentageValue(b, 'max_used_memory', 'total_memory'),
    sortDirections: ['descend', 'ascend'],
    render: (_, record) => {
      const usage = getPercentageValue(record, 'max_used_memory', 'total_memory');
      return parseFloat(usage || 0).toFixed(2) + '%';
    }
  },
  {
    title: '磁盘最大利用率(%)',
    key: 'disk_usage', 
    ...getNumberRangeFilterProps('disk_usage', '%', (record) => getPercentageValue(record, 'max_used_disk', 'total_disk')),
    sorter: (a, b) => getPercentageValue(a, 'max_used_disk', 'total_disk') - getPercentageValue(b, 'max_used_disk', 'total_disk'),
    sortDirections: ['descend', 'ascend'],
    render: (_, record) => {
      const usage = getPercentageValue(record, 'max_used_disk', 'total_disk');
      return parseFloat(usage || 0).toFixed(2) + '%';
    }
  },
  { 
    title: 'CPU Cores', 
    dataIndex: 'cpu_cores',
    ...getNumberRangeFilterProps('cpu_cores'),
    ...getColumnSorter('cpu_cores'),
  },
  {
    title: '总内存大小(GB)',
    dataIndex: 'total_memory',
    key: 'total_memory',
    ...getNumberRangeFilterProps('total_memory', 'GB'),
    ...getColumnSorter('total_memory'),
    render: (value) => parseFloat(value || 0).toFixed(2)
  },
  {
    title: '总磁盘大小(GB)',
    dataIndex: 'total_disk',
    key: 'total_disk',
    ...getNumberRangeFilterProps('total_disk', 'GB'),
    ...getColumnSorter('total_disk'),
    render: (value) => parseFloat(value || 0).toFixed(2)
  },
  { 
    title: 'Date Time', 
    dataIndex: 'max_date_time',
    key: 'max_date_time',
    ...getDateRangeFilterProps('max_date_time', (record) => {
      // 处理日期时间字段，支持多种格式
      const dateValue = record.max_date_time;
      if (!dateValue) return null;
      
      if (dateValue instanceof Date) {
        return dateValue;
      }
      
      if (typeof dateValue === 'string') {
        return new Date(dateValue);
      }
      
      return null;
    }),
    ...getColumnSorter('max_date_time', (record) => {
      const dateValue = record.max_date_time;
      if (!dateValue) return new Date(0);
      
      if (dateValue instanceof Date) {
        return dateValue;
      }
      
      if (typeof dateValue === 'string') {
        const date = new Date(dateValue);
        return isNaN(date.getTime()) ? new Date(0) : date;
      }
      
      return new Date(0);
    }),
    render: (value) => {
      if (!value) return 'N/A';
      
      if (value instanceof Date) {
        return value.toLocaleString();
      }
      
      if (typeof value === 'string') {
        const date = new Date(value);
        return isNaN(date.getTime()) ? value : date.toLocaleString();
      }
      
      return String(value);
    },
  },
  {
    title: '集群归属',
    dataIndex: 'clusters',
    render: (clusters, record) => {
      const clusterList = clusters || [];
      return (
        <div>
          {clusterList.length > 0 ? (
            <Button 
              type="link" 
              size="small"
              onClick={() => {
                Modal.info({
                  title: `${record.host_name || record.ip} 的集群信息`,
                  content: (
                    <div>
                      {clusterList.map((cluster, index) => (
                        <div key={index} style={{ marginBottom: '8px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                          <div><strong>集群名称：</strong>{cluster.cluster_name || '未知集群'}</div>
                          <div><strong>集群组：</strong>{cluster.cluster_group_name || '未知集群组'}</div>
                        </div>
                      ))}
                    </div>
                  ),
                  width: 500,
                });
              }}
            >
              查看集群({clusterList.length})
            </Button>
          ) : (
            <span style={{ color: '#999', fontSize: '12px' }}>(未分配集群)</span>
          )}
        </div>
      );
    }
  },
];

const HostResourceDetail: React.FC<HostResourceDetailProps> = ({
  data,
  pagination = true,
  dateRange,
  onDateChange,
  refreshData,
  error,
  loading
}) => {
  const { RangePicker } = DatePicker;
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [selectedHostIp, setSelectedHostIp] = useState<string | null>(null);

  // 按 IP 聚合数据，取各指标的最大值
  const aggregateDataByIP = (rawData: HostResourceData[]): HostResourceData[] => {
    if (!rawData || !Array.isArray(rawData)) {
      return [];
    }

    const aggregatedMap = new Map();

    rawData.forEach(record => {
      const ip = record.ip || record.ip_address;
      if (!ip) return;

      if (!aggregatedMap.has(ip)) {
        // 初始化该 IP 的记录，使用正确的最大值字段
        aggregatedMap.set(ip, {
          id: record.id,
          cluster_name: record.cluster_name,
          group_name: record.group_name,
          ip: ip,
          ip_address: ip,
          host_name: record.host_name,
          port: record.port,
          instance_role: record.instance_role,
          total_memory: record.total_memory || 0,
          max_used_memory: record.max_used_memory || 0,
          total_disk: record.total_disk || 0,
          max_used_disk: record.max_used_disk || 0,
          cpu_cores: record.cpu_cores || 0,
          max_cpu_load: record.max_cpu_load || 0,
          max_date_time: record.max_date_time,
          clusters: record.clusters || [],
          idc_info: record.idc_info,
        });
      } else {
        // 更新该 IP 的最大值
        const existing = aggregatedMap.get(ip);
        aggregatedMap.set(ip, {
          ...existing,
          total_memory: Math.max(existing.total_memory, record.total_memory || 0),
          max_used_memory: Math.max(existing.max_used_memory, record.max_used_memory || 0),
          total_disk: Math.max(existing.total_disk, record.total_disk || 0),
          max_used_disk: Math.max(existing.max_used_disk, record.max_used_disk || 0),
          cpu_cores: Math.max(existing.cpu_cores, record.cpu_cores || 0),
          max_cpu_load: Math.max(existing.max_cpu_load, record.max_cpu_load || 0),
          // 保持最新的时间戳
          max_date_time: record.max_date_time > existing.max_date_time 
            ? record.max_date_time 
            : existing.max_date_time,
          // 合并集群信息
          clusters: [...(existing.clusters || []), ...(record.clusters || [])],
        });
      }
    });

    return Array.from(aggregatedMap.values());
  };

  // 处理聚合后的数据
  const aggregatedData = aggregateDataByIP(data);

  const handleIpClick = (ip: string): void => {
    setSelectedHostIp(ip);
    setModalVisible(true);
  };

  const handleModalClose = (): void => {
    setModalVisible(false);
    setSelectedHostIp(null);
  };
  
  return (
    <div>
      {onDateChange && (
        <div style={{ marginBottom: 16 }}>
          <RangePicker 
            value={dateRange}
            onChange={onDateChange}
            style={{ marginRight: 16 }}
          />
          <Button 
            type="primary" 
            onClick={refreshData}
            loading={loading}
          >
            刷新数据
          </Button>
        </div>
      )}
      
      {error && (
        <Alert
          message="数据加载错误"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Spin spinning={loading}>
        <Table 
          columns={getHostResourceDetailColumns(handleIpClick)} 
          dataSource={aggregatedData} 
          rowKey={(record) => `${record.id || record.ip}-aggregated`} 
          pagination={pagination ? {
            showSizeChanger: true,
            showQuickJumper: true,
            pageSizeOptions: ['5', '20', '50', '100', '500'],
            defaultPageSize: 5,
          } : false}
          locale={{
            emptyText: error ? '加载失败' : (loading ? '加载中...' : '暂无数据')
          }}
        />
      </Spin>

      <HostMetricsModal
        visible={modalVisible}
        onCancel={handleModalClose}
        hostIp={selectedHostIp}
        dateRange={dateRange}
      />
    </div>
  );
};

export default HostResourceDetail;
