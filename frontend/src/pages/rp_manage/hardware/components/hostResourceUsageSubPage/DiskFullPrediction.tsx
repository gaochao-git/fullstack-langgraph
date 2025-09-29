// @ts-nocheck
// 磁盘空间预测组件
import React from 'react';
import { Table, Button, Modal } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { getTextColumnSearchProps, getNumberRangeFilterProps, getColumnSorter, getPercentageValue, getDateRangeFilterProps } from '../../utils/tableUtils';

interface IdcInfo {
  idc_name?: string;
  idc_code?: string;
}

interface ClusterInfo {
  cluster_name?: string;
  cluster_group_name?: string;
}

interface DiskPredictionData {
  id: string | number;
  ip: string;
  idc_info?: IdcInfo;
  current_disk_usage_percent?: number;
  total_disk?: number;
  used_disk?: number;
  daily_growth_rate?: number;
  predicted_full_date?: string;
  days_until_full?: number;
  is_high_risk?: boolean;
  clusters?: ClusterInfo[];
}

interface DiskFullPredictionProps {
  data: DiskPredictionData[];
  pagination?: boolean;
}

export const getDiskPredictionColumns = (): ColumnsType<DiskPredictionData> => [
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
    title: 'Current Disk Usage',
    dataIndex: 'current_disk_usage_percent',
    ...getNumberRangeFilterProps('current_disk_usage_percent', '%', (record) => {
      if (!record) return 0;
      return typeof record.current_disk_usage_percent === 'number' ? record.current_disk_usage_percent : 0;
    }),
    sorter: (a, b) => {
      const aValue = a && typeof a.current_disk_usage_percent === 'number' ? a.current_disk_usage_percent : 0;
      const bValue = b && typeof b.current_disk_usage_percent === 'number' ? b.current_disk_usage_percent : 0;
      return aValue - bValue;
    },
    sortDirections: ['descend', 'ascend'],
    render: (value, record) => {
      if (!record) return '0.00%';
      const usage = typeof record.current_disk_usage_percent === 'number' ? record.current_disk_usage_percent : 0;
      return `${Number(usage).toFixed(2)}%`;
    },
  },
  {
    title: 'Total Disk (GB)',
    dataIndex: 'total_disk',
    ...getNumberRangeFilterProps('total_disk', 'GB', (record) => {
      if (!record) return 0;
      return typeof record.total_disk === 'number' ? record.total_disk : 0;
    }),
    sorter: (a, b) => {
      const aValue = a && typeof a.total_disk === 'number' ? a.total_disk : 0;
      const bValue = b && typeof b.total_disk === 'number' ? b.total_disk : 0;
      return aValue - bValue;
    },
    sortDirections: ['descend', 'ascend'],
    render: (value, record) => {
      if (!record) return '0 GB';
      const total = typeof record.total_disk === 'number' ? record.total_disk : 0;
      return `${total} GB`;
    },
  },
  {
    title: 'Used Disk (GB)',
    dataIndex: 'used_disk',
    ...getNumberRangeFilterProps('used_disk', 'GB', (record) => {
      if (!record) return 0;
      return typeof record.used_disk === 'number' ? record.used_disk : 0;
    }),
    sorter: (a, b) => {
      const aValue = a && typeof a.used_disk === 'number' ? a.used_disk : 0;
      const bValue = b && typeof b.used_disk === 'number' ? b.used_disk : 0;
      return aValue - bValue;
    },
    sortDirections: ['descend', 'ascend'],
    render: (value, record) => {
      if (!record) return '0 GB';
      const used = typeof record.used_disk === 'number' ? record.used_disk : 0;
      return `${used} GB`;
    },
  },
  {
    title: 'Daily Growth Rate',
    dataIndex: 'daily_growth_rate',
    ...getNumberRangeFilterProps('daily_growth_rate', 'GB/天', (record) => {
      if (!record) return 0;
      return typeof record.daily_growth_rate === 'number' ? record.daily_growth_rate : 0;
    }),
    sorter: (a, b) => {
      const aValue = a && typeof a.daily_growth_rate === 'number' ? a.daily_growth_rate : 0;
      const bValue = b && typeof b.daily_growth_rate === 'number' ? b.daily_growth_rate : 0;
      return aValue - bValue;
    },
    sortDirections: ['descend', 'ascend'],
    render: (value, record) => {
      if (!record) return '无增长';
      const rate = typeof record.daily_growth_rate === 'number' ? record.daily_growth_rate : 0;
      if (rate <= 0) return '无增长';
      return `${Number(rate).toFixed(3)} GB/天`;
    },
  },
  {
    title: 'Predicted Full Date',
    dataIndex: 'predicted_full_date',
    ...getDateRangeFilterProps('predicted_full_date', (record) => {
      // 确保 record 和 predicted_full_date 存在且有效
      if (!record || !record.predicted_full_date) {
        return null;
      }
      const date = record.predicted_full_date;
      if (typeof date !== 'string' || date.includes('无法预测') || date.includes('长期内不会满')) {
        return null;
      }
      try {
        return new Date(date);
      } catch (e) {
        return null;
      }
    }),
    sorter: (a, b) => {
      if (!a || !b) {
        return 0;
      }

      const dateA = a.predicted_full_date;
      const dateB = b.predicted_full_date;

      // 处理特殊情况
      if (!dateA && !dateB) {
        return 0;
      }
      if (!dateA) {
        return 1;
      }
      if (!dateB) {
        return -1;
      }

      // 处理特殊字符串
      const specialStrings = ['无法预测', '长期内不会满', '增长缓慢', '增长缓慢，长期内不会满'];

      const isSpecialA = typeof dateA === 'string' && specialStrings.some(str => dateA.includes(str));
      const isSpecialB = typeof dateB === 'string' && specialStrings.some(str => dateB.includes(str));

      if (isSpecialA && isSpecialB) {
        return 0;
      }
      if (isSpecialA) {
        return 1;
      }
      if (isSpecialB) {
        return -1;
      }

      // 正常日期比较
      try {
        const dateObjA = new Date(dateA);
        const dateObjB = new Date(dateB);

        if (isNaN(dateObjA.getTime()) && isNaN(dateObjB.getTime())) {
          return 0;
        }
        if (isNaN(dateObjA.getTime())) {
          return 1;
        }
        if (isNaN(dateObjB.getTime())) {
          return -1;
        }

        return dateObjA.getTime() - dateObjB.getTime();
      } catch (error) {
        return 0;
      }
    },
    sortDirections: ['ascend', 'descend'],
    render: (value, record) => {
      if (!record) {
        return <span style={{ color: '#52c41a' }}>无风险</span>;
      }

      const date = record.predicted_full_date;

      if (!date || typeof date !== 'string') {
        return <span style={{ color: '#52c41a' }}>无风险</span>;
      }

      const specialStrings = ['无法预测', '长期内不会满', '增长缓慢', '增长缓慢，长期内不会满'];
      for (const specialStr of specialStrings) {
        if (date.includes(specialStr)) {
          return <span style={{ color: '#52c41a' }}>无风险</span>;
        }
      }

      const isHighRisk = record.is_high_risk === true;
      const color = isHighRisk ? '#ff4d4f' : '#faad14';
      const days = typeof record.days_until_full === 'number' ? record.days_until_full : 0;

      return (
        <span style={{ color }}>
          {date}
          {days > 0 && <div style={{ fontSize: '12px', color: '#666' }}>({days}天后)</div>}
        </span>
      );
    },
  },
  {
    title: 'Days Until Full',
    dataIndex: 'days_until_full',
    ...getNumberRangeFilterProps('days_until_full', '天', (record) => {
      if (!record) return 0;
      return typeof record.days_until_full === 'number' ? record.days_until_full : 0;
    }),
    sorter: (a, b) => {
      const getDays = (record: DiskPredictionData | null) => {
        if (!record) return Number.MAX_SAFE_INTEGER;
        const days = typeof record.days_until_full === 'number' ? record.days_until_full : 0;
        if (days <= 0) return Number.MAX_SAFE_INTEGER; // 无法预测的放最后
        return days;
      };
      return getDays(a) - getDays(b);
    },
    sortDirections: ['ascend', 'descend'],
    render: (value, record) => {
      if (!record) return '无法预测';
      const days = typeof record.days_until_full === 'number' ? record.days_until_full : 0;
      if (days <= 0) return '无法预测';
      return `${days} 天`;
    },
  },
  {
    title: '风险等级',
    dataIndex: 'is_high_risk',
    filters: [
      { text: '高风险', value: true },
      { text: '中风险', value: false },
      { text: '无风险', value: 'no_risk' as any }, // 使用字符串而不是 null
    ],
    onFilter: (value, record) => {
      if (!record) {
        return value === 'no_risk';
      }

      if (value === 'no_risk') {
        const days = typeof record.days_until_full === 'number' ? record.days_until_full : 0;
        const date = typeof record.predicted_full_date === 'string' ? record.predicted_full_date : '';
        const specialStrings = ['无法预测', '长期内不会满', '增长缓慢', '增长缓慢，长期内不会满'];
        const isSpecialString = typeof date === 'string' && specialStrings.some(str => date.includes(str));
        const isNoRisk = days <= 0 || !date || isSpecialString;
        return isNoRisk;
      }

      return record.is_high_risk === value;
    },
    sorter: (a, b) => {
      const getLevel = (record: DiskPredictionData | null) => {
        if (!record) return 0;

        const days = typeof record.days_until_full === 'number' ? record.days_until_full : 0;
        const date = typeof record.predicted_full_date === 'string' ? record.predicted_full_date : '';

        if (days <= 0 || !date || date.includes('无法预测') || date.includes('长期内不会满')) {
          return 0; // 无风险
        }

        return record.is_high_risk === true ? 2 : 1; // 高风险:2, 中风险:1
      };
      return getLevel(b) - getLevel(a);
    },
    render: (value, record) => {
      if (!record) return <span style={{ color: '#52c41a' }}>无风险</span>;

      const days = typeof record.days_until_full === 'number' ? record.days_until_full : 0;
      const date = typeof record.predicted_full_date === 'string' ? record.predicted_full_date : '';

      const specialStrings = ['无法预测', '长期内不会满', '增长缓慢', '增长缓慢，长期内不会满'];
      if (days <= 0 || !date || specialStrings.some(str => date.includes(str))) {
        return <span style={{ color: '#52c41a' }}>无风险</span>;
      }

      if (record.is_high_risk === true) {
        return <span style={{ color: '#ff4d4f' }}>高风险</span>;
      }

      return <span style={{ color: '#faad14' }}>中风险</span>;
    },
  },
  {
    title: '集群归属',
    dataIndex: 'clusters',
    render: (clusters, record) => {
      console.log('🔍 集群归属渲染调试:', { clusters, record, ip: record?.ip });
      const clusterList = clusters || [];
      return (
        <div>
          {clusterList.length > 0 ? (
            <Button
              type="link"
              size="small"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🖱️ 点击查看集群按钮:', { clusterList, record });
                Modal.info({
                  title: `${record?.ip || '未知IP'} 的集群信息`,
                  content: (
                    <div>
                      {clusterList.map((cluster: ClusterInfo, index: number) => (
                        <div key={index} style={{ marginBottom: '8px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                          <div><strong>集群名称：</strong>{cluster.cluster_name || '未知集群'}</div>
                          <div><strong>集群组：</strong>{cluster.cluster_group_name || '未知集群组'}</div>
                        </div>
                      ))}
                    </div>
                  ),
                  width: 500,
                  onOk() {
                    console.log('📝 Modal确认关闭');
                  },
                });
                console.log('📋 Modal.info 已调用');
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

const DiskFullPrediction: React.FC<DiskFullPredictionProps> = ({ data, pagination = true }) => {
  // 确保数据是数组且不为空
  const safeData = Array.isArray(data) ? data.filter(item => item != null) : [];

  return (
    <Table
      columns={getDiskPredictionColumns()}
      dataSource={safeData}
      rowKey={(record) => {
        if (!record) return 'unknown';
        const id = typeof record.id === 'string' || typeof record.id === 'number' ? record.id : '';
        const ip = typeof record.ip === 'string' ? record.ip : '';
        return `${id}-${ip}`;
      }}
      pagination={pagination ? {
        showSizeChanger: true,
        showQuickJumper: true,
        pageSizeOptions: ['5', '20', '50', '100', '500'],
        defaultPageSize: 5,
      } : false}
    />
  );
}

export default DiskFullPrediction;