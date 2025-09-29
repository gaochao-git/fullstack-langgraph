// @ts-nocheck
// 资源警报详情组件
import React, { useMemo } from 'react';
import { Table, Button, Modal } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getTextColumnSearchProps, getNumberRangeFilterProps, getColumnSorter, getPercentageValue } from '../../utils/tableUtils';

interface IdcInfo {
  idc_name?: string;
  idc_code?: string;
}

interface ClusterInfo {
  cluster_name?: string;
  cluster_group_name?: string;
}

interface ResourceData {
  id: string;
  ip: string;
  idc_info?: IdcInfo;
  max_cpu_load?: number;
  max_used_memory?: number;
  total_memory?: number;
  max_used_disk?: number;
  total_disk?: number;
  clusters?: ClusterInfo[];
}

interface ThresholdConfig {
  min: number;
  max: number;
}

interface ResourceAlertsProps {
  data: ResourceData[];
  cpuThresholds: ThresholdConfig;
  memoryThresholds: ThresholdConfig;
  diskThresholds: ThresholdConfig;
  triggerUpdate: number;
  pagination?: boolean;
}

export const getResourceAlertsColumns = (cpuMin: number, cpuMax: number, memoryMin: number, memoryMax: number, diskMin: number, diskMax: number): ColumnsType<ResourceData> => [
  {
    title: 'ID',
    dataIndex: 'id',
    ...getTextColumnSearchProps('id', 'ID'),
    ...getColumnSorter('id'),
  },
  {
    title: 'IP地址',
    dataIndex: 'ip',
    ...getTextColumnSearchProps('ip', 'IP地址'),
    ...getColumnSorter('ip'),
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
    title: 'CPU Usage',
    dataIndex: 'max_cpu_load',
    ...getNumberRangeFilterProps('max_cpu_load', '%'),
    ...getColumnSorter('max_cpu_load'),
    render: (value) => {
      if (value === undefined || value === null) return '0.00%';
      const text = `${value.toFixed(2)}%`;
      const color = value < cpuMin ? 'green' : value > cpuMax ? 'red' : 'inherit';
      return <span style={{ color }}>{text}</span>;
    },
  },
  {
    title: 'Memory Usage',
    dataIndex: 'memory_usage',
    ...getNumberRangeFilterProps('memory_usage', '%', (record) => {
      const usage = getPercentageValue(record, 'max_used_memory', 'total_memory');
      return isNaN(usage) ? 0 : usage;
    }),
    sorter: (a, b) => {
      const aUsage = getPercentageValue(a, 'max_used_memory', 'total_memory');
      const bUsage = getPercentageValue(b, 'max_used_memory', 'total_memory');
      return aUsage - bUsage;
    },
    sortDirections: ['descend', 'ascend'],
    render: (_, record) => {
      const usage = getPercentageValue(record, 'max_used_memory', 'total_memory');
      if (isNaN(usage)) return '0.00%';
      const text = `${usage.toFixed(2)}%`;
      const color = usage < memoryMin ? 'green' : usage > memoryMax ? 'red' : 'inherit';
      return <span style={{ color }}>{text}</span>;
    },
  },
  {
    title: 'Disk Usage',
    dataIndex: 'disk_usage',
    ...getNumberRangeFilterProps('disk_usage', '%', (record) => {
      const usage = getPercentageValue(record, 'max_used_disk', 'total_disk');
      return isNaN(usage) ? 0 : usage;
    }),
    sorter: (a, b) => {
      const aUsage = getPercentageValue(a, 'max_used_disk', 'total_disk');
      const bUsage = getPercentageValue(b, 'max_used_disk', 'total_disk');
      return aUsage - bUsage;
    },
    sortDirections: ['descend', 'ascend'],
    render: (_, record) => {
      const usage = getPercentageValue(record, 'max_used_disk', 'total_disk');
      if (isNaN(usage)) return '0.00%';
      const text = `${usage.toFixed(2)}%`;
      const color = usage < diskMin ? 'green' : usage > diskMax ? 'red' : 'inherit';
      return <span style={{ color }}>{text}</span>;
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
                  title: `${record.ip} 的集群信息`,
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

const ResourceAlerts: React.FC<ResourceAlertsProps> = ({ data, cpuThresholds, memoryThresholds, diskThresholds, triggerUpdate, pagination = true }) => {
  const filteredData = useMemo(() => {
    return data.filter(item => {
      const cpuUsage = item.max_cpu_load || 0;
      const memoryUsage = item.max_used_memory && item.total_memory ? (item.max_used_memory / item.total_memory) * 100 : 0;
      const diskUsage = item.max_used_disk && item.total_disk ? (item.max_used_disk / item.total_disk) * 100 : 0;
      
      const cpuCompliant = cpuUsage >= cpuThresholds.min && cpuUsage <= cpuThresholds.max;
      const memoryCompliant = memoryUsage >= memoryThresholds.min && memoryUsage <= memoryThresholds.max;
      const diskCompliant = diskUsage >= diskThresholds.min && diskUsage <= diskThresholds.max;
      
      return !cpuCompliant || !memoryCompliant || !diskCompliant;
    });
  }, [data, cpuThresholds, memoryThresholds, diskThresholds]);

  return (
    <Table
      columns={getResourceAlertsColumns(
        cpuThresholds.min, 
        cpuThresholds.max, 
        memoryThresholds.min, 
        memoryThresholds.max, 
        diskThresholds.min, 
        diskThresholds.max
      )}
      dataSource={filteredData}
      rowKey={(record) => `${record.id}-${record.ip}`}
      pagination={{
        showSizeChanger: true,
        showQuickJumper: true,
        pageSizeOptions: ['5', '20', '50', '100', '500'],
        defaultPageSize: 5,
      }}
    />
  );
}

export default ResourceAlerts;
