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
  FilePdfOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { TaskDetail, TaskResult, ScanFile } from '../types/scanTask';
import { ScanApi } from '../services/scanApi';

interface TaskDetailModalProps {
  visible: boolean;
  taskId: string | null;
  taskStatus?: string;
  onClose: () => void;
}

const TaskDetailModal: React.FC<TaskDetailModalProps> = ({ visible, taskId, taskStatus, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [taskResult, setTaskResult] = useState<TaskResult | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [htmlModalVisible, setHtmlModalVisible] = useState(false);
  const [htmlReportUrl, setHtmlReportUrl] = useState<string>('');
  const [htmlLoading, setHtmlLoading] = useState(false);

  // 获取任务结果
  const fetchTaskResult = async () => {
    if (!taskId) return;
    
    try {
      const response = await ScanApi.getTaskResult(taskId);
      if (response.data.status === 'ok') {
        setTaskResult(response.data.data);
      } else {
        message.error(response.data.msg || '获取任务结果失败');
      }
    } catch (error) {
      message.error('获取任务结果失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  // 查看HTML报告
  const viewHtmlReport = async (fileId: string) => {
    if (!taskId) return;
    
    setHtmlModalVisible(true);
    setHtmlLoading(true);
    
    try {
      // 下载HTML文件
      const response = await ScanApi.downloadHtmlReport(taskId, fileId);
      
      if (response.status === 'ok' && response.data) {
        // 从标准响应格式中获取HTML内容
        const htmlContent = response.data.html;
        
        // 创建blob URL，明确指定UTF-8编码
        const blob = new Blob([htmlContent], { type: 'text/html; charset=utf-8' });
        const url = URL.createObjectURL(blob);
        setHtmlReportUrl(url);
      } else {
        // 处理业务错误
        message.error(response.msg || '加载HTML报告失败');
        setHtmlModalVisible(false);
      }
    } catch (error: any) {
      // 处理网络错误
      message.error('网络错误，加载HTML报告失败');
      setHtmlModalVisible(false);
    } finally {
      setHtmlLoading(false);
    }
  };

  // 监听visible变化
  useEffect(() => {
    if (visible && taskId) {
      setLoading(true);
      // 直接获取结果，因为结果接口包含了所有需要的信息
      fetchTaskResult();
    }
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
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      ellipsis: true,
      render: (name, record) => {
        // 优先显示文件名，如果没有则显示文件ID的前8位
        const displayName = name || `${record.file_id.substring(0, 8)}...`;
        return (
          <span title={name || record.file_id}>
            {displayName}
          </span>
        );
      },
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
      title: '报告',
      key: 'report',
      width: 80,
      align: 'center' as const,
      render: (_, record) => {
        if (record.status !== 'completed') {
          return '-';
        }
        
        return (
          <Button
            type="link"
            size="small"
            icon={<FilePdfOutlined />}
            onClick={() => viewHtmlReport(record.file_id)}
          >
            查看
          </Button>
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
              fetchTaskResult();
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
        ) : taskResult ? (
          <div>
            {/* 任务概要 */}
            <div style={{ marginBottom: 16 }}>
              <Space>
                <span>总文件数: <strong>{taskResult.summary.total_files}</strong></span>
                <span>完成数: <strong style={{ color: '#52c41a' }}>{taskResult.summary.completed_files}</strong></span>
                <span>失败数: <strong style={{ color: '#ff4d4f' }}>{taskResult.summary.failed_files}</strong></span>
              </Space>
            </div>

            {/* 文件扫描结果列表 */}
            <Table
              dataSource={taskResult.files}
              columns={fileColumns}
              rowKey="file_id"
              pagination={false}
              size="small"
            />
          </div>
        ) : (
          <Alert
            message="获取任务详情失败"
            description="请刷新重试"
            type="error"
            showIcon
          />
        )}
      </Modal>


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
        styles={{ body: { padding: 0, height: '70vh' } }}
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