import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  message,
  Modal,
  Tabs
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  UploadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { ScanTask } from '../types/scanTask';
import { ScanApi } from '../services/scanApi';
import TaskDetailModal from '../components/TaskDetailModal';
import DocumentUploadScan from '../components/DocumentUploadScan';
import ScanConfigManagement from '../components/ScanConfigManagement';
import { useIsMobile } from '@/hooks';

const { Search } = Input;

const ScanTaskList: React.FC = () => {
  const isMobile = useIsMobile();
  const [tasks, setTasks] = useState<ScanTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchCreateBy, setSearchCreateBy] = useState<string>('');
  const [searchTaskId, setSearchTaskId] = useState<string>('');
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTaskStatus, setSelectedTaskStatus] = useState<string | null>(null);
  // 实际用于查询的参数
  const [queryCreateBy, setQueryCreateBy] = useState<string>('');
  const [queryTaskId, setQueryTaskId] = useState<string>('');
  // 上传扫描模态框
  const [uploadModalVisible, setUploadModalVisible] = useState(false);

  // 获取任务列表
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await ScanApi.listTasks({
        page: currentPage,
        size: pageSize,
        create_by: queryCreateBy || undefined,
        task_id: queryTaskId || undefined
      });
      
      if (response.data.status === 'ok') {
        setTasks(response.data.data.items);
        setTotal(response.data.data.pagination.total);
      } else {
        message.error(response.data.msg || '获取任务列表失败');
      }
    } catch (error) {
      message.error('获取任务列表失败');
    } finally {
      setLoading(false);
    }
  };


  // 初始化和查询参数变化时重新获取数据
  useEffect(() => {
    fetchTasks();
  }, [currentPage, pageSize, queryTaskId, queryCreateBy]);

  // 处理任务创建成功
  const handleTaskCreated = (taskId: string) => {
    setUploadModalVisible(false);
    message.success(`扫描任务已创建: ${taskId}`);
    // 刷新任务列表
    fetchTasks();
  };

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
            setSelectedTaskStatus(record.status);
            setDetailModalVisible(true);
          }}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div className="scan-task-list-container">
      <style>{`
        @media (max-width: 768px) {
          .scan-task-list-card .ant-card-head {
            flex-direction: column;
            align-items: flex-start;
          }
          .scan-task-list-card .ant-card-head-title {
            margin-bottom: 8px;
          }
          .scan-task-list-card .ant-card-extra {
            width: 100%;
            margin-left: 0;
          }
        }
      `}</style>
      <Card
        title="敏感数据扫描任务"
        className="scan-task-list-card"
        styles={{
          body: { padding: isMobile ? '12px' : '24px' },
          header: isMobile ? { padding: '12px 16px' } : undefined
        }}
        extra={
          <div style={{
            width: isMobile ? '100%' : 'auto',
            marginTop: isMobile ? '12px' : 0
          }}>
            {isMobile ? (
              // 移动端布局 - 多行显示
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <Search
                  placeholder="搜索任务ID"
                  allowClear
                  style={{ flex: 1, minWidth: '120px' }}
                  value={searchTaskId}
                  onChange={(e) => {
                    setSearchTaskId(e.target.value);
                    if (!e.target.value && searchTaskId) {
                      setCurrentPage(1);
                      setQueryTaskId('');
                    }
                  }}
                  onSearch={(value) => {
                    setCurrentPage(1);
                    setQueryTaskId(value);
                  }}
                />
                <Search
                  placeholder="搜索创建人"
                  allowClear
                  style={{ flex: 1, minWidth: '120px' }}
                  value={searchCreateBy}
                  onChange={(e) => {
                    setSearchCreateBy(e.target.value);
                    if (!e.target.value && searchCreateBy) {
                      setCurrentPage(1);
                      setQueryCreateBy('');
                    }
                  }}
                  onSearch={(value) => {
                    setCurrentPage(1);
                    setQueryCreateBy(value);
                  }}
                />
                <Button
                  icon={<ReloadOutlined />}
                  onClick={fetchTasks}
                />
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                >
                  上传
                </Button>
              </div>
            ) : (
              // 桌面端布局 - 单行显示
              <Space>
                <Search
                  placeholder="搜索任务ID"
                  allowClear
                  style={{ width: 200 }}
                  value={searchTaskId}
                  onChange={(e) => {
                    setSearchTaskId(e.target.value);
                    if (!e.target.value && searchTaskId) {
                      setCurrentPage(1);
                      setQueryTaskId('');
                    }
                  }}
                  onSearch={(value) => {
                    setCurrentPage(1);
                    setQueryTaskId(value);
                  }}
                />
                <Search
                  placeholder="搜索创建人"
                  allowClear
                  style={{ width: 200 }}
                  value={searchCreateBy}
                  onChange={(e) => {
                    setSearchCreateBy(e.target.value);
                    if (!e.target.value && searchCreateBy) {
                      setCurrentPage(1);
                      setQueryCreateBy('');
                    }
                  }}
                  onSearch={(value) => {
                    setCurrentPage(1);
                    setQueryCreateBy(value);
                  }}
                />
                <Button
                  icon={<ReloadOutlined />}
                  onClick={fetchTasks}
                >
                  刷新
                </Button>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={() => setUploadModalVisible(true)}
                >
                  上传文件
                </Button>
              </Space>
            )}
          </div>
        }
      >

        {/* 任务列表 */}
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          loading={loading}
          scroll={{ x: 1200 }}
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
      </Card>

      {/* 任务详情弹窗 */}
      <TaskDetailModal
        visible={detailModalVisible}
        taskId={selectedTaskId}
        taskStatus={selectedTaskStatus || undefined}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedTaskId(null);
          setSelectedTaskStatus(null);
        }}
      />

      {/* 上传文件扫描模态框 - 支持配置管理 */}
      <Modal
        title="文件扫描与配置管理"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={isMobile ? '95%' : 1000}
        destroyOnClose
        styles={{
          body: { padding: isMobile ? '12px' : '24px' }
        }}
      >
        <Tabs
          defaultActiveKey="upload"
          items={[
            {
              key: 'upload',
              label: '上传文件',
              children: <DocumentUploadScan onTaskCreated={handleTaskCreated} />
            },
            {
              key: 'config',
              label: '配置管理',
              children: <ScanConfigManagement />
            }
          ]}
        />
      </Modal>
    </div>
  );
};

export default ScanTaskList;