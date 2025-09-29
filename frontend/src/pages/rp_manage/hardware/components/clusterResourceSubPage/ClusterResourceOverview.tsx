// @ts-nocheck
// 集群资源概览组件
import React, { useMemo, useEffect } from 'react';
import { Table, Button } from 'antd';
import { getTextColumnSearchProps, getNumberRangeFilterProps, getColumnSorter } from '../../utils/tableUtils';

export const getClusterOverviewColumns = (cpuThresholds, memoryThresholds, diskThresholds, handleShowValidityReport) => [
  {
    title: '集群组名',
    dataIndex: 'team',
    ...getTextColumnSearchProps('team', '集群组名'),
    ...getColumnSorter('team'),
  },
  {
    title: '集群名',
    dataIndex: 'cluster_name',
    ...getTextColumnSearchProps('cluster_name', '集群名'),
    ...getColumnSorter('cluster_name'),
  },
  {
    title: '所属部门',
    dataIndex: 'department',
    ...getTextColumnSearchProps('department', '所属部门'),
    ...getColumnSorter('department'),
  },
  {
    title: 'CPU峰值利用率',
    dataIndex: 'max_cpu',
    ...getNumberRangeFilterProps('max_cpu', '%'),
    ...getColumnSorter('max_cpu'),
    render: (value) => {
      const isCompliant = value >= cpuThresholds.min && value <= cpuThresholds.max;
      return (
        <span style={{ color: isCompliant ? 'green' : 'red' }}>
          {value.toFixed(2)}%
        </span>
      );
    }
  },
  {
    title: '内存峰值利用率',
    dataIndex: 'max_memory',
    ...getNumberRangeFilterProps('max_memory', '%'),
    ...getColumnSorter('max_memory'),
    render: (value) => {
      const isCompliant = value >= memoryThresholds.min && value <= memoryThresholds.max;
      return (
        <span style={{ color: isCompliant ? 'green' : 'red' }}>
          {value.toFixed(2)}%
        </span>
      );
    }
  },
  {
    title: '磁盘峰值利用率',
    dataIndex: 'max_disk',
    ...getNumberRangeFilterProps('max_disk', '%'),
    ...getColumnSorter('max_disk'),
    render: (value) => {
      const isCompliant = value >= diskThresholds.min && value <= diskThresholds.max;
      return (
        <span style={{ color: isCompliant ? 'green' : 'red' }}>
          {value.toFixed(2)}%
        </span>
      );
    }
  },
  {
    title: '集群有效性报告',
    key: 'report',
    render: (_, record) => (
      <Button 
        type="primary" 
        onClick={() => handleShowValidityReport(record.cluster_name)}
      >
        查看报告
      </Button>
    )
  }
];

const ClusterResourceOverview = ({ 
  data, 
  cpuThresholds, 
  memoryThresholds, 
  diskThresholds, 
  handleShowValidityReport,
  pagination = true 
}) => {
  // 确保 data 是数组，添加数据验证
  const validData = useMemo(() => {
    if (!data) {
      console.warn('ClusterResourceOverview: data is null or undefined');
      return [];
    }
    if (!Array.isArray(data)) {
      console.warn('ClusterResourceOverview: data is not an array:', typeof data, data);
      return [];
    }
    return data;
  }, [data]);


  return (
    <Table
      columns={getClusterOverviewColumns(cpuThresholds, memoryThresholds, diskThresholds, handleShowValidityReport)}
      dataSource={validData}
      rowKey={(record, index) => {
        // 安全的 rowKey 生成
        if (record && record.id) {
          return record.id;
        }
        if (record && record.cluster_name) {
          return record.cluster_name;
        }
        return `row-${index}`;
      }}
      pagination={{
        showSizeChanger: true,
        showQuickJumper: true,
        pageSizeOptions: ['10', '20', '50', '100'],
        defaultPageSize: 10,
      }}
      locale={{
        emptyText: validData.length === 0 ? '暂无集群数据' : '数据加载中...'
      }}
    />
  );
};

export default ClusterResourceOverview;