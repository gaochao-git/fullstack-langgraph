import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  message
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { ScanTask } from '../types/scanTask';
import { ScanApi } from '../services/scanApi';
import TaskDetailModal from '../components/TaskDetailModal';

const { Search } = Input;

const ScanTaskList: React.FC = () => {
  
  const [tasks, setTasks] = useState<ScanTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchCreateBy, setSearchCreateBy] = useState<string>('');
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  // 获取任务列表
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await ScanApi.listTasks({
        page: currentPage,
        size: pageSize,
        create_by: searchCreateBy || undefined
      });
      
      if (response.data.status === 'ok') {
        setTasks(response.data.data.items);
        setTotal(response.data.data.total);
      } else {
        message.error(response.data.msg || '获取任务列表失败');
      }
    } catch (error) {
      message.error('获取任务列表失败');
    } finally {
      setLoading(false);
    }
  };


  // 初始化
  useEffect(() => {
    fetchTasks();
  }, [currentPage, pageSize]);

  // 状态标签
  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '等待中' },
      processing: { color: 'processing', text: '处理中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' }
    };
    
    const config = statusMap[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 表格列定义
  const columns: ColumnsType<ScanTask> = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    {
      title: '总文件数',
      dataIndex: 'total_files',
      key: 'total_files',
      width: 90,
      align: 'center' as const,
    },
    {
      title: '完成数',
      dataIndex: 'completed_files',
      key: 'completed_files',
      width: 80,
      align: 'center' as const,
      render: (value) => (
        <span style={{ color: '#52c41a' }}>
          {value || 0}
        </span>
      ),
    },
    {
      title: '失败数',
      dataIndex: 'failed_files',
      key: 'failed_files',
      width: 80,
      align: 'center' as const,
      render: (value) => (
        <span style={{ color: value > 0 ? '#ff4d4f' : '#999' }}>
          {value || 0}
        </span>
      ),
    },
    {
      title: '敏感项数',
      dataIndex: 'sensitive_items',
      key: 'sensitive_items',
      width: 100,
      render: (count) => (
        <span style={{ 
          color: count > 0 ? '#ff4d4f' : '#52c41a',
          fontWeight: count > 0 ? 'bold' : 'normal'
        }}>
          {count || 0}
        </span>
      ),
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 120,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN', { hour12: false }),
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN', { hour12: false }) : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN', { hour12: false }) : '-',
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => {
            setSelectedTaskId(record.task_id);
            setDetailModalVisible(true);
          }}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <Card>
      {/* 搜索栏 */}
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索创建人"
            allowClear
            enterButton={<SearchOutlined />}
            style={{ width: 200 }}
            value={searchCreateBy}
            onChange={(e) => setSearchCreateBy(e.target.value)}
            onSearch={() => {
              setCurrentPage(1);
              fetchTasks();
            }}
          />
          
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchTasks}
          >
            刷新
          </Button>
        </Space>
      </div>

      {/* 任务列表 */}
      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="task_id"
        loading={loading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (page, size) => {
            setCurrentPage(page);
            setPageSize(size || 10);
          },
        }}
      />

      {/* 任务详情弹窗 */}
      <TaskDetailModal
        visible={detailModalVisible}
        taskId={selectedTaskId}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedTaskId(null);
        }}
      />
    </Card>
  );
};

export default ScanTaskList;