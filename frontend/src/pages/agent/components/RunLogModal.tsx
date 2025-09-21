import React, { useState, useEffect } from 'react';
import { Modal, Table, Tag, Tabs, Space, DatePicker, Select, Statistic, Row, Col, Card, message } from 'antd';
import { UserOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, TeamOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { runLogApi, type RunLog, type UserRunSummary } from '@/services/runLogApi';
import { useTheme } from '@/hooks/ThemeContext';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

interface RunLogModalProps {
  visible: boolean;
  onClose: () => void;
  agentId: string;
  agentName: string;
}

const RunLogModal: React.FC<RunLogModalProps> = ({ visible, onClose, agentId, agentName }) => {
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<RunLog[]>([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<any>(null);
  const [userStats, setUserStats] = useState<UserRunSummary[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedUser, setSelectedUser] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [activeTab, setActiveTab] = useState('logs');

  // 加载运行日志
  const loadRunLogs = async () => {
    setLoading(true);
    try {
      const response = await runLogApi.getRunLogs(agentId, {
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
        user_name: selectedUser,
        start_date: dateRange?.[0]?.toISOString(),
        end_date: dateRange?.[1]?.toISOString(),
      });

      if (response.status === 'ok' && response.data) {
        setLogs(response.data.logs);
        setTotal(response.data.total);
        setStats(response.data.stats);
      }
    } catch (error) {
      message.error('加载运行日志失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载用户统计
  const loadUserSummary = async () => {
    setLoading(true);
    try {
      const response = await runLogApi.getRunSummary(agentId, 7);
      if (response.status === 'ok' && response.data) {
        setUserStats(response.data.user_stats);
      }
    } catch (error) {
      message.error('加载用户统计失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      if (activeTab === 'logs') {
        loadRunLogs();
      } else {
        loadUserSummary();
      }
    }
  }, [visible, currentPage, pageSize, selectedUser, dateRange, activeTab]);

  // 运行日志表格列
  const logColumns: ColumnsType<RunLog> = [
    {
      title: '用户',
      dataIndex: 'user_display_name',
      key: 'user',
      width: 120,
      render: (text, record) => (
        <Space>
          <UserOutlined />
          <span>{text || record.user_name}</span>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'run_status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = {
          running: { color: 'processing', icon: <ClockCircleOutlined />, text: '运行中' },
          success: { color: 'success', icon: <CheckCircleOutlined />, text: '成功' },
          failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
        };
        const { color, icon, text } = config[status as keyof typeof config] || config.running;
        return (
          <Tag color={color} icon={icon}>
            {text}
          </Tag>
        );
      },
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '运行时长',
      dataIndex: 'duration_ms',
      key: 'duration',
      width: 120,
      render: (duration: any) => {
        const durationValue = typeof duration === 'number' && !isNaN(duration) ? duration : 0;
        if (!durationValue) return '-';
        if (durationValue < 1000) return `${Math.round(durationValue)}ms`;
        if (durationValue < 60000) return `${(durationValue / 1000).toFixed(1)}s`;
        return `${(durationValue / 60000).toFixed(1)}min`;
      },
    },
    {
      title: 'Token用量',
      dataIndex: 'token_usage',
      key: 'tokens',
      width: 100,
      render: (tokens?: number) => tokens || '-',
    },
    {
      title: '消息数',
      dataIndex: 'message_count',
      key: 'messages',
      width: 80,
      render: (count: number) => count || 0,
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error',
      ellipsis: true,
      render: (error?: string) => error ? (
        <span style={{ color: '#ff4d4f' }}>{error}</span>
      ) : '-',
    },
  ];

  // 用户统计表格列
  const userColumns: ColumnsType<UserRunSummary> = [
    {
      title: '用户',
      dataIndex: 'user_display_name',
      key: 'user',
      render: (text, record) => (
        <Space>
          <UserOutlined />
          <span>{text || record.user_name}</span>
        </Space>
      ),
    },
    {
      title: '运行次数',
      dataIndex: 'total_runs',
      key: 'total_runs',
      sorter: (a, b) => a.total_runs - b.total_runs,
      defaultSortOrder: 'descend',
    },
    {
      title: '成功率',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (rate: any) => {
        // Ensure rate is a valid number
        const rateValue = typeof rate === 'number' && !isNaN(rate) ? rate : 0;
        return (
          <Tag color={rateValue >= 90 ? 'success' : rateValue >= 70 ? 'warning' : 'error'}>
            {rateValue.toFixed(1)}%
          </Tag>
        );
      },
    },
    {
      title: '平均耗时',
      dataIndex: 'avg_duration_ms',
      key: 'avg_duration',
      render: (duration: any) => {
        const durationValue = typeof duration === 'number' && !isNaN(duration) ? duration : 0;
        if (!durationValue) return '-';
        if (durationValue < 1000) return `${Math.round(durationValue)}ms`;
        if (durationValue < 60000) return `${(durationValue / 1000).toFixed(1)}s`;
        return `${(durationValue / 60000).toFixed(1)}min`;
      },
    },
    {
      title: 'Token总量',
      dataIndex: 'total_tokens',
      key: 'total_tokens',
      render: (tokens: number) => tokens || 0,
    },
    {
      title: '最后运行',
      dataIndex: 'last_run_time',
      key: 'last_run',
      render: (time?: string) => time ? dayjs(time).format('MM-DD HH:mm') : '-',
    },
  ];

  return (
    <Modal
      title={`${agentName} - 运行记录`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1200}
      bodyStyle={{
        padding: '16px 24px',
        maxHeight: '80vh',
        overflow: 'auto',
      }}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="运行日志" key="logs">
          {/* 统计卡片 */}
          {stats && (
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="总运行次数"
                    value={stats.total_runs}
                    prefix={<TeamOutlined />}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="独立用户数"
                    value={stats.unique_users}
                    prefix={<UserOutlined />}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="成功率"
                    value={stats.success_rate}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: stats.success_rate >= 90 ? '#3f8600' : '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="平均耗时"
                    value={stats.avg_duration_ms}
                    precision={0}
                    suffix="ms"
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="成功次数"
                    value={stats.success_runs}
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col span={4}>
                <Card size="small">
                  <Statistic
                    title="失败次数"
                    value={stats.failed_runs}
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
            </Row>
          )}

          {/* 筛选条件 */}
          <Space style={{ marginBottom: 16 }}>
            <Select
              placeholder="选择用户"
              style={{ width: 200 }}
              value={selectedUser}
              onChange={setSelectedUser}
              allowClear
              options={stats?.user_stats?.map((u: any) => ({
                label: `${u.user_display_name} (${u.run_count}次)`,
                value: u.user_name,
              })) || []}
            />
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates)}
              showTime
              format="YYYY-MM-DD HH:mm"
            />
          </Space>

          {/* 日志表格 */}
          <Table
            columns={logColumns}
            dataSource={logs}
            rowKey="id"
            loading={loading}
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              onChange: (page, size) => {
                setCurrentPage(page);
                setPageSize(size || 20);
              },
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
          />
        </TabPane>

        <TabPane tab="用户统计" key="users">
          <Table
            columns={userColumns}
            dataSource={userStats}
            rowKey="user_name"
            loading={loading}
            pagination={false}
          />
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default RunLogModal;