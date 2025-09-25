import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  DatePicker,
  Select,
  Input,
  Row,
  Col,
  Statistic,
  Progress,
  Divider,
  message,
  Modal,
  Form
} from 'antd';
import {
  FileTextOutlined,
  DownloadOutlined,
  EyeOutlined,
  ReloadOutlined,
  PlusOutlined,
  SearchOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import IDCReportApi from '@/services/idcReportApi';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Search } = Input;

interface IDCReport {
  id: string;
  reportName: string;
  idcLocation: string;
  reportType: string;
  generateTime: string;
  status: string;
  powerUsage: number;
  energyEfficiency: number;
  availabilityRate: number;
  alertCount: number;
  fileSize: string;
}

const IDCReportManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState<IDCReport[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [filters, setFilters] = useState({
    idcLocation: '',
    reportType: '',
    dateRange: null as any,
    status: '',
    keyword: ''
  });
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 统计卡片
  const [stats, setStats] = useState({
    total: 0,
    monthly: 0,
    avgPue: 0,
    avgAvailability: 0,
  });

  const columns: ColumnsType<IDCReport> = [
    {
      title: '报告名称',
      dataIndex: 'reportName',
      key: 'reportName',
      ellipsis: true,
      render: (text: string, record: IDCReport) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: 'IDC位置',
      dataIndex: 'idcLocation',
      key: 'idcLocation',
      width: 120,
    },
    {
      title: '报告类型',
      dataIndex: 'reportType',
      key: 'reportType',
      width: 100,
      render: (type: string) => (
        <Tag color={type === '月度报告' ? 'blue' : type === '季度报告' ? 'green' : 'orange'}>
          {type}
        </Tag>
      ),
    },
    {
      title: '生成时间',
      dataIndex: 'generateTime',
      key: 'generateTime',
      width: 160,
      sorter: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === '已完成' ? 'success' : status === '生成中' ? 'processing' : 'error'}>
          {status}
        </Tag>
      ),
    },
    {
      title: '电力使用(kWh)',
      dataIndex: 'powerUsage',
      key: 'powerUsage',
      width: 120,
      render: (value: number) => value.toLocaleString(),
    },
    {
      title: 'PUE值',
      dataIndex: 'energyEfficiency',
      key: 'energyEfficiency',
      width: 80,
      render: (value: number) => (
        <span style={{ color: value < 1.5 ? 'var(--color-success)' : value < 2.0 ? 'var(--color-warning)' : 'var(--color-destructive)' }}>
          {value}
        </span>
      ),
    },
    {
      title: '可用性(%)',
      dataIndex: 'availabilityRate',
      key: 'availabilityRate',
      width: 100,
      render: (value: number) => (
        <div>
          <Progress 
            percent={value} 
            size="small" 
            strokeColor={value >= 99.9 ? 'var(--color-success, #22c55e)' : value >= 99.5 ? 'var(--color-warning, #f59e0b)' : 'var(--color-destructive, #ef4444)'}
            trailColor={'var(--color-input-background, var(--input-background))'}
            showInfo={false}
          />
          <span style={{ fontSize: '12px' }}>{value}%</span>
        </div>
      ),
    },
    {
      title: '告警数',
      dataIndex: 'alertCount',
      key: 'alertCount',
      width: 80,
      render: (count: number) => (
        <span style={{ color: count === 0 ? 'var(--color-success)' : count < 5 ? 'var(--color-warning)' : 'var(--color-destructive)' }}>
          {count}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record: IDCReport) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            size="small"
            onClick={() => handleViewReport(record)}
            disabled={record.status !== '已完成'}
          >
            查看
          </Button>
          <Button 
            type="link" 
            icon={<DownloadOutlined />} 
            size="small"
            onClick={() => handleDownloadReport(record)}
            disabled={record.status !== '已完成'}
          >
            下载
          </Button>
        </Space>
      ),
    },
  ];

  const statCards = [
    { title: '总报告数', value: stats.total, color: 'var(--color-primary)' },
    { title: '本月报告', value: stats.monthly, color: 'var(--color-success)' },
    { title: '平均PUE', value: stats.avgPue?.toString(), color: 'var(--color-warning)' },
    { title: '平均可用性', value: `${stats.avgAvailability}%`, color: 'var(--color-accent)' },
  ];

  useEffect(() => {
    fetchReports();
  }, [pagination.current, pagination.pageSize, filters]);

  const mapTypeToCN = (t?: string) => ({ monthly: '月度报告', quarterly: '季度报告', yearly: '年度报告', custom: '自定义报告' } as any)[t || ''] || '自定义报告';
  const mapStatusToCN = (s?: string) => ({ completed: '已完成', generating: '生成中', pending: '生成中', failed: '失败' } as any)[s || ''] || '生成中';
  const toMB = (bytes?: number) => bytes ? `${(bytes / (1024 * 1024)).toFixed(bytes < 10 * 1024 * 1024 ? 1 : 0)}MB` : '';

  const fetchReports = async () => {
    setLoading(true);
    try {
      // 拉取统计
      try {
        const statResp = await IDCReportApi.getReportStats();
        const d = statResp?.data || {};
        const recent = Array.isArray(d.recent_reports) ? d.recent_reports : [];
        // 粗略估计平均PUE、可用性
        const pueVals = recent.map((r: any) => r.pue_value).filter((x: any) => typeof x === 'number');
        const availVals = recent.map((r: any) => r.availability_rate).filter((x: any) => typeof x === 'number');
        setStats({
          total: d.total_reports || 0,
          monthly: d.this_month_reports || 0,
          avgPue: pueVals.length ? Number((pueVals.reduce((a: number, b: number) => a + b, 0) / pueVals.length).toFixed(2)) : 0,
          avgAvailability: availVals.length ? Number((availVals.reduce((a: number, b: number) => a + b, 0) / availVals.length).toFixed(2)) : 0,
        });
      } catch {}

      const params: any = {
        page: pagination.current,
        pageSize: pagination.pageSize,
      };
      if (filters.keyword) params.keyword = filters.keyword;
      if (filters.idcLocation) params.idcLocation = filters.idcLocation;
      if (filters.reportType) {
        const map: any = { '日报告': 'daily', '周报告': 'weekly', '月度报告': 'monthly', '季度报告': 'quarterly', '年度报告': 'yearly' };
        params.reportType = map[filters.reportType] || 'custom';
      }
      if (filters.status) {
        const map: any = { '已完成': 'completed', '生成中': 'generating', '失败': 'failed' };
        params.status = map[filters.status] || '';
      }
      if (filters.dateRange && Array.isArray(filters.dateRange)) {
        params.dateRange = [filters.dateRange[0]?.toISOString(), filters.dateRange[1]?.toISOString()];
      }

      const resp = await IDCReportApi.getReports(params);
      const items: any[] = resp?.data?.items || [];
      const total: number = resp?.data?.pagination?.total || items.length;

      const mapped: IDCReport[] = items.map((it: any) => ({
        id: it.report_id,
        reportName: it.report_name,
        idcLocation: it.idc_location,
        reportType: mapTypeToCN(it.report_type),
        generateTime: (it.generation_time || it.updated_at || it.created_at || '').toString().replace('T', ' ').slice(0, 19),
        status: mapStatusToCN(it.status),
        powerUsage: Number(it.total_power_consumption || 0),
        energyEfficiency: Number(it.pue_value || 0),
        availabilityRate: Number(it.availability_rate || 0),
        alertCount: Number(it.incident_count || 0),
        fileSize: toMB(it.file_size),
      }));

      setReports(mapped);
      setPagination(prev => ({ ...prev, total }));
    } catch (error) {
      message.error('获取报告列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = (record: IDCReport) => {
    // 这里将来实现报告查看功能
    message.info(`查看报告：${record.reportName}`);
  };

  const handleDownloadReport = (record: IDCReport) => {
    // 这里将来实现报告下载功能
    message.success(`开始下载：${record.reportName}`);
  };

  const handleCreateReport = () => {
    setCreateModalVisible(true);
  };

  const handleCreateSubmit = async (values: any) => {
    try {
      const mapType: any = { '日报告': 'daily', '周报告': 'weekly', '月度报告': 'monthly', '季度报告': 'quarterly', '年度报告': 'yearly' };
      const dateRange: [string, string] = [
        values.dateRange?.[0]?.toISOString?.() || dayjs().startOf('month').toISOString(),
        values.dateRange?.[1]?.toISOString?.() || dayjs().toISOString(),
      ];
      await IDCReportApi.createReport({
        reportName: values.reportName,
        idcLocation: values.idcLocation,
        reportType: mapType[values.reportType] || 'custom',
        dateRange,
      });
      message.success('报告生成任务已提交');
      setCreateModalVisible(false);
      form.resetFields();
      fetchReports();
    } catch (error) {
      message.error('提交失败');
    }
  };

  const handleTableChange = (paginationConfig: any, filters: any, sorter: any) => {
    setPagination(prev => ({
      ...prev,
      current: paginationConfig.current,
      pageSize: paginationConfig.pageSize,
    }));
  };

  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, keyword: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleFilterChange = (field: string, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleRefresh = () => {
    fetchReports();
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {statCards.map((card, index) => (
          <Col span={6} key={index}>
            <Card>
              <Statistic
                title={card.title}
                value={card.value}
                valueStyle={{ color: card.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 主要内容区域 */}
      <Card
        title="IDC运行报告管理"
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleCreateReport}
            >
              生成报告
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
              刷新
            </Button>
          </Space>
        }
      >
        {/* 筛选条件 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Search
              placeholder="搜索报告名称或IDC位置"
              allowClear
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && handleSearch('')}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="IDC位置"
              allowClear
              style={{ width: '100%' }}
              value={filters.idcLocation}
              onChange={(value) => handleFilterChange('idcLocation', value)}
            >
              <Option value="北京机房A">北京机房A</Option>
              <Option value="上海机房B">上海机房B</Option>
              <Option value="广州机房C">广州机房C</Option>
              <Option value="全部机房">全部机房</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="报告类型"
              allowClear
              style={{ width: '100%' }}
              value={filters.reportType}
              onChange={(value) => handleFilterChange('reportType', value)}
            >
              <Option value="日报告">日报告</Option>
              <Option value="周报告">周报告</Option>
              <Option value="月度报告">月度报告</Option>
              <Option value="季度报告">季度报告</Option>
              <Option value="年度报告">年度报告</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: '100%' }}
              value={filters.status}
              onChange={(value) => handleFilterChange('status', value)}
            >
              <Option value="已完成">已完成</Option>
              <Option value="生成中">生成中</Option>
              <Option value="失败">失败</Option>
            </Select>
          </Col>
          <Col span={6}>
            <RangePicker
              style={{ width: '100%' }}
              value={filters.dateRange}
              onChange={(dates) => handleFilterChange('dateRange', dates)}
              placeholder={['开始日期', '结束日期']}
            />
          </Col>
        </Row>

        <Divider />

        {/* 表格 */}
        <Table
          columns={columns}
          dataSource={reports}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
          }}
          onChange={handleTableChange}
          size="middle"
        />
      </Card>

      {/* 创建报告模态框 */}
      <Modal
        title="生成IDC运行报告"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateSubmit}
        >
          <Form.Item
            name="reportName"
            label="报告名称"
            rules={[{ required: true, message: '请输入报告名称' }]}
          >
            <Input placeholder="请输入报告名称" />
          </Form.Item>
          
          <Form.Item
            name="idcLocation"
            label="IDC位置"
            rules={[{ required: true, message: '请选择IDC位置' }]}
          >
            <Select placeholder="请选择IDC位置">
              <Option value="北京机房A">北京机房A</Option>
              <Option value="上海机房B">上海机房B</Option>
              <Option value="广州机房C">广州机房C</Option>
              <Option value="全部机房">全部机房</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="reportType"
            label="报告类型"
            rules={[{ required: true, message: '请选择报告类型' }]}
          >
            <Select placeholder="请选择报告类型">
              <Option value="日报告">日报告</Option>
              <Option value="周报告">周报告</Option>
              <Option value="月度报告">月度报告</Option>
              <Option value="季度报告">季度报告</Option>
              <Option value="年度报告">年度报告</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="dateRange"
            label="报告时间范围"
            rules={[{ required: true, message: '请选择时间范围' }]}
          >
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default IDCReportManagement;
