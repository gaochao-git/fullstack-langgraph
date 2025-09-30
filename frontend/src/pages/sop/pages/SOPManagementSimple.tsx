import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Input, 
  Select, 
  Space, 
  Tag, 
  message, 
  Popconfirm,
  Tooltip,
  Modal
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { SOPTemplate, SOPQueryParams } from '../types/sop';
import { SOPApi } from '@/services/sopApi';
import SOPFormModal from '../components/SOPFormModal';

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
  const [editingSOP, setEditingSOP] = useState<SOPTemplate | null>(null);

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
      
      const response = await SOPApi.querySOPTemplates(queryParams);
      if (response.status === 'success' && response.data) {
        setSOPs(response.data.data || []);
        setTotal(response.data.total || 0);
      } else {
        message.error(response.msg || '获取SOP数据失败');
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
    const params = { ...searchParams, [key]: value === 'all' ? undefined : value };
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
    Modal.info({
      title: `SOP详情 - ${sop.sop_title}`,
      width: 800,
      content: (
        <div>
          <p><strong>SOP ID:</strong> {sop.sop_id}</p>
          <p><strong>创建人:</strong> {sop.create_by}</p>
          <p><strong>创建时间:</strong> {sop.create_time}</p>
          <p><strong>更新时间:</strong> {sop.update_time}</p>
          <div style={{ marginTop: 16 }}>
            <strong>详细内容:</strong>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              backgroundColor: '#f5f5f5', 
              padding: 12,
              borderRadius: 4,
              marginTop: 8,
              maxHeight: 400,
              overflow: 'auto'
            }}>
              {sop.sop_description || '暂无详细描述'}
            </pre>
          </div>
        </div>
      ),
      okText: '关闭'
    });
  };

  // 删除SOP
  const handleDelete = async (sopId: string) => {
    try {
      const response = await SOPApi.deleteSOP(sopId);
      
      if (response.status === 'error') {
        message.error(response.msg || '删除失败');
        return;
      }
      
      message.success('删除成功');
      fetchSOPs();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 表单提交成功
  const handleFormSuccess = () => {
    setFormModalVisible(false);
    fetchSOPs();
  };

  // 表格列定义
  const columns: ColumnsType<SOPTemplate> = [
    {
      title: 'SOP ID',
      dataIndex: 'sop_id',
      key: 'sop_id',
      width: 150
    },
    {
      title: 'SOP标题',
      dataIndex: 'sop_title',
      key: 'sop_title',
      ellipsis: true,
      width: 250
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time: string) => time.replace('T', ' ').slice(0, 19)
    },
    {
      title: '更新人',
      dataIndex: 'update_by',
      key: 'update_by',
      width: 100,
      render: (text: string | undefined) => text || '-'
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 180,
      render: (time: string) => time.replace('T', ' ').slice(0, 19)
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个SOP吗？"
            onConfirm={() => handleDelete(record.sop_id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button 
                type="text" 
                size="small" 
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <Card title="SOP管理">
      {/* 搜索和筛选栏 */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Search
          placeholder="搜索SOP标题或ID"
          allowClear
          onSearch={handleSearch}
          style={{ width: 300 }}
        />
        
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
        
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleCreate}
        >
          创建SOP
        </Button>
      </Space>

      {/* 数据表格 */}
      <Table
        columns={columns}
        dataSource={sops}
        loading={loading}
        rowKey="id"
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showTotal: (total) => `共 ${total} 条`,
          showSizeChanger: true,
          onChange: (page, size) => {
            setCurrentPage(page);
            setPageSize(size);
          }
        }}
      />

      {/* 表单弹窗 */}
      <SOPFormModal
        visible={formModalVisible}
        onCancel={() => setFormModalVisible(false)}
        onSuccess={handleFormSuccess}
        editData={editingSOP}
      />
    </Card>
  );
};

export default SOPManagementSimple;