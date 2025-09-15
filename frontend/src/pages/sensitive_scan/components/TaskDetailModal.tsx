import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Space,
  Tag,
  Progress,
  Spin,
  Alert,
  Button,
  message
} from 'antd';
import {
  ReloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { TaskDetail, TaskResult, ScanFile } from '../types/scanTask';
import { ScanApi } from '../services/scanApi';
import ScanResultViewer from './ScanResultViewer';

interface TaskDetailModalProps {
  visible: boolean;
  taskId: string | null;
  onClose: () => void;
}

const TaskDetailModal: React.FC<TaskDetailModalProps> = ({ visible, taskId, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [taskDetail, setTaskDetail] = useState<TaskDetail | null>(null);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timer | null>(null);
  const [resultViewerVisible, setResultViewerVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<{ taskId: string; fileId: string } | null>(null);
  const [htmlModalVisible, setHtmlModalVisible] = useState(false);
  const [htmlReportUrl, setHtmlReportUrl] = useState<string>('');
  const [htmlLoading, setHtmlLoading] = useState(false);

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
  const viewJsonlContent = (fileId: string) => {
    if (!taskId) return;
    setSelectedFile({ taskId, fileId });
    setResultViewerVisible(true);
  };

  // 查看HTML报告
  const viewHtmlReport = async (fileId: string) => {
    if (!taskId) return;
    
    setHtmlModalVisible(true);
    setHtmlLoading(true);
    
    try {
      // 下载HTML文件为blob
      const response = await ScanApi.downloadHtmlReport(taskId, fileId);
      
      // 创建blob URL
      const blob = new Blob([response.data], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      setHtmlReportUrl(url);
    } catch (error) {
      message.error('加载HTML报告失败');
      setHtmlModalVisible(false);
    } finally {
      setHtmlLoading(false);
    }
  };

  // 监听visible变化
  useEffect(() => {
    if (visible && taskId) {
      setLoading(true);
      fetchTaskDetail();
      
      // 如果任务未完成，启动轮询
      const startPolling = () => {
        const interval = setInterval(() => {
          fetchTaskDetail();
        }, 3000); // 每3秒刷新一次
        setPollingInterval(interval);
      };
      
      if (taskDetail && ['pending', 'processing'].includes(taskDetail.status)) {
        startPolling();
      }
    } else {
      // 关闭时清理
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
    
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [visible, taskId]);

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
      width: 150,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN', { hour12: false }) : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 150,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN', { hour12: false }) : '-',
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
              查看结果
            </Button>
            <Button
              type="link"
              size="small"
              icon={<FilePdfOutlined />}
              onClick={() => viewHtmlReport(record.file_id)}
            >
              HTML
            </Button>
          </Space>
        );
      },
    },
  ];

  return (
    <>
      <Modal
        title={`任务详情 - ${taskId}`}
        open={visible}
        onCancel={onClose}
        width={1000}
        footer={[
          <Button key="close" onClick={onClose}>
            关闭
          </Button>,
          <Button
            key="refresh"
            icon={<ReloadOutlined />}
            onClick={() => {
              setRefreshing(true);
              fetchTaskDetail();
            }}
            loading={refreshing}
          >
            刷新
          </Button>
        ]}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" />
          </div>
        ) : taskDetail ? (
          <div>
            {/* 进度条 - 只在处理中时显示 */}
            {['pending', 'processing'].includes(taskDetail.status) && (
              <div style={{ marginBottom: 16 }}>
                <Progress
                  percent={Math.round((taskDetail.progress.current / taskDetail.progress.total) * 100)}
                  status={taskDetail.status === 'processing' ? 'active' : 'normal'}
                />
                <p style={{ marginTop: 8, color: '#666' }}>
                  {taskDetail.progress.message}
                </p>
              </div>
            )}

            {/* 错误信息 */}
            {taskDetail.errors && taskDetail.errors.length > 0 && (
              <Alert
                style={{ marginBottom: 16 }}
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

            {/* 文件扫描结果列表 */}
            {taskResult && (
              <Table
                dataSource={taskResult.files}
                columns={fileColumns}
                rowKey="file_id"
                pagination={false}
                size="small"
              />
            )}
          </div>
        ) : (
          <Alert
            message="任务不存在"
            description="未找到指定的扫描任务"
            type="error"
            showIcon
          />
        )}
      </Modal>

      {/* 结果查看器 */}
      {selectedFile && (
        <ScanResultViewer
          visible={resultViewerVisible}
          taskId={selectedFile.taskId}
          fileId={selectedFile.fileId}
          onClose={() => {
            setResultViewerVisible(false);
            setSelectedFile(null);
          }}
        />
      )}

      {/* HTML报告预览弹窗 */}
      <Modal
        title="HTML扫描报告"
        open={htmlModalVisible}
        onCancel={() => {
          setHtmlModalVisible(false);
          if (htmlReportUrl) {
            URL.revokeObjectURL(htmlReportUrl);
            setHtmlReportUrl('');
          }
        }}
        width={1000}
        bodyStyle={{ padding: 0, height: '70vh' }}
        footer={[
          <Button key="close" onClick={() => {
            setHtmlModalVisible(false);
            if (htmlReportUrl) {
              URL.revokeObjectURL(htmlReportUrl);
              setHtmlReportUrl('');
            }
          }}>
            关闭
          </Button>
        ]}
      >
        {htmlLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh' }}>
            <Spin size="large" tip="加载中..." />
          </div>
        ) : htmlReportUrl ? (
          <iframe
            src={htmlReportUrl}
            style={{ width: '100%', height: '70vh', border: 'none' }}
            title="扫描报告"
          />
        ) : null}
      </Modal>
    </>
  );
};

export default TaskDetailModal;