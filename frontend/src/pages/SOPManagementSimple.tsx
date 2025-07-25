import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  Select, 
  Space, 
  Tag, 
  App, 
  Popconfirm,
  Row,
  Col
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { SOPTemplate, SOPQueryParams, SOPSeverity } from '../types/sop';
import { SOPApi, SOPUtils } from '../services/sopApi.real';
import SOPFormModalSimple from '../components/SOPFormModalSimple';
import SOPDetailModalSimple from '../components/SOPDetailModalSimple';

const { Search } = Input;
const { Option } = Select;

const SOPManagementSimple: React.FC = () => {
  const [sops, setSOPs] = useState<SOPTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchParams, setSearchParams] = useState<SOPQueryParams>({});
  
  // 模态框状态
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editingSOP, setEditingSOP] = useState<SOPTemplate | null>(null);
  const [viewingSOP, setViewingSOP] = useState<SOPTemplate | null>(null);
  
  const { message } = App.useApp();

  // 获取SOP数据
  const fetchSOPs = async (params?: SOPQueryParams) => {
    setLoading(true);
    try {
      const queryParams = {
        ...searchParams,
        ...params,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize
      };
      
      const response = await SOPApi.getSOPs(queryParams);
      if (response.success && response.data) {
        setSOPs(response.data.data);
        setTotal(response.data.total);
      } else {
        message.error(response.error || '获取SOP数据失败');
      }
    } catch (error) {
      message.error('获取SOP数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    fetchSOPs();
  }, [currentPage, pageSize]);

  // 搜索处理
  const handleSearch = (value: string) => {
    const params = { ...searchParams, search: value };
    setSearchParams(params);
    setCurrentPage(1);
    fetchSOPs(params);
  };

  // 筛选处理
  const handleFilter = (key: string, value: any) => {
    const params = { ...searchParams, [key]: value };
    setSearchParams(params);
    setCurrentPage(1);
    fetchSOPs(params);
  };

  // 重置筛选
  const handleReset = () => {
    setSearchParams({});
    setCurrentPage(1);
    fetchSOPs({});
  };

  // 创建SOP
  const handleCreate = () => {
    setEditingSOP(null);
    setFormModalVisible(true);
  };

  // 编辑SOP
  const handleEdit = (sop: SOPTemplate) => {
    setEditingSOP(sop);
    setFormModalVisible(true);
  };

  // 查看SOP详情
  const handleView = (sop: SOPTemplate) => {
    setViewingSOP(sop);
    setDetailModalVisible(true);
  };

  // 表单提交成功
  const handleFormSuccess = () => {
    setFormModalVisible(false);
    fetchSOPs();
  };

  // 删除SOP
  const handleDelete = async (sopId: string) => {
    try {
      const response = await SOPApi.deleteSOP(sopId);
      if (response.success) {
        message.success('删除成功');
        fetchSOPs();
      } else {
        message.error(response.error || '删除失败');
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 严重性颜色映射
  const getSeverityColor = (severity: SOPSeverity): string => {
    const colors = {
      low: 'blue',
      medium: 'orange', 
      high: 'red',
      critical: 'purple'
    };
    return colors[severity];
  };

  // 严重性文本映射
  const getSeverityText = (severity: SOPSeverity): string => {
    const texts = {
      low: '低',
      medium: '中',
      high: '高', 
      critical: '紧急'
    };
    return texts[severity];
  };

  // 表格列定义
  const columns: ColumnsType<SOPTemplate> = [
    {
      title: 'SOP ID',
      dataIndex: 'sop_id',
      key: 'sop_id',
      width: 100
    },
    {
      title: 'SOP标题',
      dataIndex: 'sop_title',
      key: 'sop_title',
      ellipsis: true,
      width: 150
    },
    {
      title: '分类',
      dataIndex: 'sop_category',
      key: 'sop_category',
      width: 100,
      render: (category: string) => (
        <Tag color="blue">{category}</Tag>
      )
    },
    {
      title: '严重性',
      dataIndex: 'sop_severity',
      key: 'sop_severity',
      width: 80,
      render: (severity: SOPSeverity) => (
        <Tag color={getSeverityColor(severity)}>
          {getSeverityText(severity)}
        </Tag>
      )
    },
    {
      title: '步骤数',
      dataIndex: 'sop_steps',
      key: 'steps_count',
      width: 80,
      render: (stepsJson: string) => {
        const steps = SOPUtils.parseSteps(stepsJson);
        return steps.length;
      }
    },
    {
      title: '团队',
      dataIndex: 'team_name',
      key: 'team_name',
      width: 100
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 150,
      render: (time: string) => time.replace('T', ' ').slice(0, 16)
    },
    {
      title: '操作',
      key: 'actions',
      width: 130,
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="text" 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          />
          <Button 
            type="text" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定要删除这个SOP吗？"
            onConfirm={() => handleDelete(record.sop_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="text" 
              size="small" 
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card>
        <div className="mb-4">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Search
                placeholder="搜索SOP标题、描述、ID"
                allowClear
                onSearch={handleSearch}
                style={{ width: '100%' }}
              />
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="分类"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('category', value)}
                value={searchParams.category}
              >
                <Option value="database">数据库</Option>
                <Option value="system">系统</Option>
                <Option value="network">网络</Option>
                <Option value="application">应用</Option>
              </Select>
            </Col>
            <Col xs={12} sm={6} md={4}>
              <Select
                placeholder="严重性"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilter('severity', value)}
                value={searchParams.severity}
              >
                <Option value="low">低</Option>
                <Option value="medium">中</Option>
                <Option value="high">高</Option>
                <Option value="critical">紧急</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Space>
                <Button onClick={handleReset}>
                  重置
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={() => fetchSOPs()}
                >
                  刷新
                </Button>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={handleCreate}
                >
                  新建SOP
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        <Table
          columns={columns}
          dataSource={sops}
          rowKey="id"
          loading={loading}
          scroll={{ x: 800 }}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 10);
            }
          }}
        />
      </Card>

      {/* SOP表单模态框 */}
      <SOPFormModalSimple
        visible={formModalVisible}
        onCancel={() => setFormModalVisible(false)}
        onSuccess={handleFormSuccess}
        editData={editingSOP}
      />

      {/* SOP详情模态框 */}
      <SOPDetailModalSimple
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        sopData={viewingSOP}
      />
    </div>
  );
};

export default SOPManagementSimple;