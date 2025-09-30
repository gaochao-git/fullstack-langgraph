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
  Tooltip
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { SOPTemplate, SOPQueryParams } from '../types/sop';
import { SOPApi, SOPUtils } from '@/services/sopApi';
import SOPFormModal from '../components/SOPFormModal';

const { Search } = Input;
const { Option } = Select;

const SOPList: React.FC = () => {
  const [sops, setSOPs] = useState<SOPTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchParams, setSearchParams] = useState<SOPQueryParams>({});
  
  // 模态框状态
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [editingSOP, setEditingSOP] = useState<SOPTemplate | null>(null);
  
  const { message } = App.useApp();

  // 获取SOP数据
  const fetchSOPs = async (params?: SOPQueryParams) => {
    setLoading(true);
    try {
      const queryParams = {
        ...searchParams,
        ...params,
        page: currentPage,
        size: pageSize
      };
      
      const response = await SOPApi.getSOPs(queryParams);
      
      // 处理业务逻辑错误
      if (response.status === 'error') {
        message.error(response.msg || '获取SOP数据失败');
        return;
      }
      
      // 处理成功响应
      const data = response.data || response;
      if (data.items && data.pagination) {
        setSOPs(data.items);
        setTotal(data.pagination.total);
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


  // 删除SOP
  const handleDelete = async (sopId: string) => {
    try {
      const response = await SOPApi.deleteSOP(sopId);
      
      // 处理业务逻辑错误
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
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      render: (time: string) => time.replace('T', ' ').slice(0, 16)
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
      width: 150,
      render: (time: string) => time.replace('T', ' ').slice(0, 16)
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button 
              type="text" 
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个SOP吗？"
              onConfirm={() => handleDelete(record.sop_id)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="text" 
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card
        title="SOP管理"
        extra={
          <Space>
            <Search
              placeholder="搜索SOP标题、描述、ID"
              allowClear
              onSearch={handleSearch}
              style={{ width: 240 }}
            />
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
        }
      >
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
      <SOPFormModal
        visible={formModalVisible}
        onCancel={() => setFormModalVisible(false)}
        onSuccess={handleFormSuccess}
        editData={editingSOP}
      />
    </div>
  );
};

export default SOPList;