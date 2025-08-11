import { useState, useEffect } from 'react';
import { Modal, Table, Tag, Spin, message, Select, InputNumber, Button, Space } from 'antd';
import { AlertOutlined, ReloadOutlined } from '@ant-design/icons';
import SOPApi from '@/services/sopApi';
import type { ColumnsType } from 'antd/es/table';

interface ZabbixProblem {
  eventid: string;
  hostname: string;
  host?: string;  // 主机标识
  host_ip?: string;  // 主机IP地址
  hostid?: string;
  name: string;
  severity: string;
  severity_name: string;
  clock: string;
  item_name: string;
  item_key: string;
  last_value: string;
  units: string;
  trigger_description: string;
  trigger_priority: string;
}

interface ZabbixProblemsModalProps {
  visible: boolean;
  onClose: () => void;
  onSelectProblem?: (problem: ZabbixProblem) => void;
}

const ZabbixProblemsModal: React.FC<ZabbixProblemsModalProps> = ({
  visible,
  onClose,
  onSelectProblem
}) => {
  const [loading, setLoading] = useState(false);
  const [problems, setProblems] = useState<ZabbixProblem[]>([]);
  const [severityMin, setSeverityMin] = useState(2);
  const [limit, setLimit] = useState(100);

  // 严重级别映射
  const severityColorMap: Record<string, string> = {
    '0': '#8c8c8c',  // 未分类
    '1': '#52c41a',  // 信息
    '2': '#faad14',  // 警告
    '3': '#fa8c16',  // 一般
    '4': '#f5222d',  // 严重
    '5': '#820014',  // 灾难
  };

  // 获取Zabbix问题数据
  const fetchProblems = async () => {
    setLoading(true);
    try {
      const response = await SOPApi.getZabbixProblems({
        severity_min: severityMin,
        recent_only: true,
        limit: limit
      });

      if (response.status === 'ok') {
        setProblems(response.data || []);
      } else {
        message.error(response.msg || '获取Zabbix问题失败');
        setProblems([]);
      }
    } catch (error) {
      console.error('Failed to fetch Zabbix problems:', error);
      message.error('获取Zabbix问题失败');
      setProblems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      fetchProblems();
    }
  }, [visible, severityMin, limit]);

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(parseInt(timestamp) * 1000);
    return date.toLocaleString('zh-CN');
  };

  // 表格列定义
  const columns: ColumnsType<ZabbixProblem> = [
    {
      title: '主机',
      dataIndex: 'hostname',
      key: 'hostname',
      width: 150,
      ellipsis: true,
      render: (text, record) => (
        <div>
          <div className="font-medium">{text || '未知主机'}</div>
          {record.host_ip && (
            <div className="text-xs text-gray-500">IP: {record.host_ip}</div>
          )}
        </div>
      ),
    },
    {
      title: '问题',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (text) => (
        <span className="font-medium">{text}</span>
      ),
    },
    {
      title: '严重级别',
      dataIndex: 'severity_name',
      key: 'severity',
      width: 100,
      render: (text, record) => (
        <Tag color={severityColorMap[record.severity] || '#8c8c8c'}>
          {text}
        </Tag>
      ),
    },
    {
      title: '监控项',
      dataIndex: 'item_name',
      key: 'item_name',
      width: 200,
      ellipsis: true,
      render: (text, record) => (
        <div>
          <div className="text-sm">{text}</div>
          <div className="text-xs text-gray-500">{record.item_key}</div>
        </div>
      ),
    },
    {
      title: '当前值',
      key: 'value',
      width: 120,
      render: (_, record) => (
        <span className="font-mono">
          {record.last_value} {record.units}
        </span>
      ),
    },
    {
      title: '时间',
      dataIndex: 'clock',
      key: 'clock',
      width: 180,
      render: (text) => formatTime(text),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => {
            if (onSelectProblem) {
              onSelectProblem(record);
              onClose();
            }
          }}
        >
          诊断
        </Button>
      ),
    },
  ];

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <AlertOutlined className="text-red-500" />
          <span>Zabbix 异常问题</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={1200}
      footer={null}
      className="zabbix-problems-modal"
    >
      <div className="mb-4">
        <Space>
          <span>最小严重级别：</span>
          <Select
            value={severityMin}
            onChange={setSeverityMin}
            style={{ width: 120 }}
            options={[
              { value: 0, label: '全部' },
              { value: 1, label: '信息' },
              { value: 2, label: '警告' },
              { value: 3, label: '一般' },
              { value: 4, label: '严重' },
              { value: 5, label: '灾难' },
            ]}
          />
          <span className="ml-4">显示数量：</span>
          <InputNumber
            value={limit}
            onChange={(value) => setLimit(value || 100)}
            min={10}
            max={1000}
            step={50}
            style={{ width: 100 }}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchProblems}
            loading={loading}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={problems}
        rowKey="eventid"
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 个问题`,
        }}
        scroll={{ x: 1000 }}
        size="small"
      />
    </Modal>
  );
};

export default ZabbixProblemsModal;