import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Table,
  Button,
  Space,
  Tag,
  Progress,
  Spin,
  Alert,
  message,
  Modal,
  Tabs
} from 'antd';
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { TaskDetail, TaskResult, ScanFile } from '../types/scanTask';
import { ScanApi } from '../services/scanApi';

const { TabPane } = Tabs;

const ScanTaskDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [taskDetail, setTaskDetail] = useState<TaskDetail | null>(null);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timer | null>(null);

  // 获取任务详情
  const fetchTaskDetail = async () => {
    if (!taskId) return;
    
    try {
      const response = await ScanApi.getTaskProgress(taskId);
      if (response.data.status === 'ok') {
        setTaskDetail(response.data.data);
        
        // 如果任务已完成，获取结果
        if (['completed', 'failed'].includes(response.data.data.status)) {
          fetchTaskResult();
          // 停止轮询
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
        }
      } else {
        message.error(response.data.msg || '获取任务详情失败');
      }
    } catch (error) {
      message.error('获取任务详情失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // 获取任务结果
  const fetchTaskResult = async () => {
    if (!taskId) return;
    
    try {
      const response = await ScanApi.getTaskResult(taskId);
      if (response.data.status === 'ok') {
        setTaskResult(response.data.data);
      }
    } catch (error) {
      console.error('获取任务结果失败:', error);
    }
  };

  // 查看JSONL内容
  const viewJsonlContent = async (fileId: string) => {
    if (!taskId) return;
    
    try {
      const content = await ScanApi.getJsonlContent(taskId, fileId);
      Modal.info({
        title: 'JSONL 扫描结果',
        width: 800,
        content: (
          <pre style={{ 
            maxHeight: '500px', 
            overflow: 'auto',
            background: '#f5f5f5',
            padding: '10px',
            borderRadius: '4px'
          }}>
            {content}
          </pre>
        ),
      });
    } catch (error) {
      message.error('获取JSONL内容失败');
    }
  };

  // 查看HTML报告
  const viewHtmlReport = (fileId: string) => {
    if (!taskId) return;
    
    const url = ScanApi.getHtmlReportUrl(taskId, fileId);
    window.open(url, '_blank');
  };

  // 初始化
  useEffect(() => {
    fetchTaskDetail();
    
    // 如果任务未完成，启动轮询
    if (taskDetail && ['pending', 'processing'].includes(taskDetail.status)) {
      const interval = setInterval(fetchTaskDetail, 3000); // 每3秒刷新一次
      setPollingInterval(interval);
    }
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [taskId]);

  // 状态标签
  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'default', text: '等待中' },
      processing: { color: 'processing', text: '处理中' },
      reading: { color: 'processing', text: '读取中' },
      scanning: { color: 'processing', text: '扫描中' },
      completed: { color: 'success', text: '已完成' },
      failed: { color: 'error', text: '失败' }
    };
    
    const config = statusMap[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 文件列表列定义
  const fileColumns: ColumnsType<ScanFile> = [
    {
      title: '文件ID',
      dataIndex: 'file_id',
      key: 'file_id',
      ellipsis: true,
      width: 300,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '错误信息',
      dataIndex: 'error',
      key: 'error',
      ellipsis: true,
      render: (error) => error ? (
        <span style={{ color: '#ff4d4f' }}>{error}</span>
      ) : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => {
        if (record.status !== 'completed') {
          return '-';
        }
        
        return (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => viewJsonlContent(record.file_id)}
            >
              JSONL
            </Button>
            <Button
              type="link"
              size="small"
              icon={<FilePdfOutlined />}
              onClick={() => viewHtmlReport(record.file_id)}
            >
              报告
            </Button>
          </Space>
        );
      },
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!taskDetail) {
    return (
      <Alert
        message="任务不存在"
        description="未找到指定的扫描任务"
        type="error"
        showIcon
      />
    );
  }

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
          >
            返回
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              setRefreshing(true);
              fetchTaskDetail();
            }}
            loading={refreshing}
            style={{ marginLeft: 8 }}
          >
            刷新
          </Button>
        </div>

        <Descriptions title="任务详情" bordered column={2}>
          <Descriptions.Item label="任务ID">{taskDetail.task_id}</Descriptions.Item>
          <Descriptions.Item label="状态">
            {getStatusTag(taskDetail.status)}
          </Descriptions.Item>
          <Descriptions.Item label="总文件数">{taskDetail.total_files}</Descriptions.Item>
          <Descriptions.Item label="已处理">{taskDetail.processed_files}</Descriptions.Item>
          <Descriptions.Item label="失败数">{taskDetail.failed_files}</Descriptions.Item>
          <Descriptions.Item label="敏感项数">{taskDetail.statistics.sensitive_items}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(taskDetail.create_time).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="开始时间">
            {taskDetail.start_time ? new Date(taskDetail.start_time).toLocaleString() : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="结束时间" span={2}>
            {taskDetail.end_time ? new Date(taskDetail.end_time).toLocaleString() : '-'}
          </Descriptions.Item>
        </Descriptions>

        {/* 进度条 */}
        {['pending', 'processing'].includes(taskDetail.status) && (
          <Card style={{ marginTop: 16 }} title="扫描进度">
            <Progress
              percent={Math.round((taskDetail.progress.current / taskDetail.progress.total) * 100)}
              status={taskDetail.status === 'processing' ? 'active' : 'normal'}
            />
            <p style={{ marginTop: 8, color: '#666' }}>
              {taskDetail.progress.message}
            </p>
          </Card>
        )}

        {/* 错误信息 */}
        {taskDetail.errors && taskDetail.errors.length > 0 && (
          <Alert
            style={{ marginTop: 16 }}
            message="错误信息"
            description={
              <ul>
                {taskDetail.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            }
            type="error"
            showIcon
            icon={<ExclamationCircleOutlined />}
          />
        )}

        {/* 文件列表 */}
        {taskResult && (
          <Card style={{ marginTop: 16 }} title="文件扫描结果">
            <Table
              dataSource={taskResult.files}
              columns={fileColumns}
              rowKey="file_id"
              pagination={false}
            />
          </Card>
        )}
      </Card>
    </div>
  );
};

export default ScanTaskDetail;