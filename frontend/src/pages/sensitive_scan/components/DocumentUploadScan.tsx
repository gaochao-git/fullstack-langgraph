import React, { useState } from 'react';
import {
  Card,
  Upload,
  Button,
  Alert,
  List,
  Space,
  message,
  Progress,
  Typography,
  Tag
} from 'antd';
import {
  InboxOutlined,
  DeleteOutlined,
  ScanOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FileUnknownOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { ScanApi } from '../services/scanApi';
import { fileApi } from '@/services/fileApi';

const { Dragger } = Upload;
const { Title, Text } = Typography;

interface DocumentUploadScanProps {
  onTaskCreated?: (taskId: string) => void;
}

const DocumentUploadScan: React.FC<DocumentUploadScanProps> = ({ onTaskCreated }) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedCount, setUploadedCount] = useState(0);

  // 获取文件图标
  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase() || '';
    
    if (['pdf'].includes(ext)) return <FilePdfOutlined style={{ fontSize: 48 }} />;
    if (['doc', 'docx'].includes(ext)) return <FileWordOutlined style={{ fontSize: 48 }} />;
    if (['xls', 'xlsx', 'csv'].includes(ext)) return <FileExcelOutlined style={{ fontSize: 48 }} />;
    if (['txt', 'md'].includes(ext)) return <FileTextOutlined style={{ fontSize: 48 }} />;
    
    return <FileUnknownOutlined style={{ fontSize: 48 }} />;
  };

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    fileList: fileList,
    beforeUpload: (file) => {
      // 检查文件类型
      const allowedTypes = [
        'text/plain',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv'
      ];
      
      const isAllowed = allowedTypes.includes(file.type) || 
                       /\.(txt|pdf|doc|docx|xls|xlsx|csv|md)$/i.test(file.name);
      
      if (!isAllowed) {
        message.error(`${file.name} 不是支持的文件格式`);
        return false;
      }
      
      // 检查文件大小（100MB）
      const isLt100M = file.size / 1024 / 1024 < 100;
      if (!isLt100M) {
        message.error('文件大小不能超过 100MB');
        return false;
      }
      
      return false; // 阻止自动上传
    },
    onChange: ({ fileList: newFileList }) => {
      setFileList(newFileList);
    },
    onRemove: (file) => {
      const newFileList = fileList.filter(f => f.uid !== file.uid);
      setFileList(newFileList);
    }
  };

  // 开始扫描
  const handleStartScan = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择要扫描的文件');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadedCount(0);

    try {
      // 上传所有文件
      const uploadedFileIds: string[] = [];

      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        if (file.originFileObj) {
          try {
            // 调用真实的文件上传API
            const uploadResult = await fileApi.uploadFile(
              file.originFileObj,
              undefined, // agent_id
              undefined, // user_name (从token获取)
              (percent) => {
                // 计算总体上传进度
                const fileProgress = percent / fileList.length;
                const previousProgress = (i / fileList.length) * 100;
                setUploadProgress(Math.round(previousProgress + fileProgress));
              }
            );

            uploadedFileIds.push(uploadResult.file_id);
            setUploadedCount(i + 1);
          } catch (error: any) {
            message.error(`文件 ${file.name} 上传失败: ${error.message || '未知错误'}`);
            throw error;
          }
        }
      }

      setUploading(false);
      setScanning(true);

      // 创建扫描任务
      const response = await ScanApi.createTask(uploadedFileIds);

      if (response.data.status === 'ok') {
        message.success('扫描任务创建成功');

        // 清空文件列表
        setFileList([]);
        setUploadProgress(0);
        setUploadedCount(0);

        // 通知父组件任务已创建
        if (onTaskCreated && response.data.data?.task_id) {
          onTaskCreated(response.data.data.task_id);
        }
      } else {
        message.error(response.data.msg || '创建扫描任务失败');
      }
    } catch (error: any) {
      message.error(error.message || '扫描任务创建失败');
    } finally {
      setUploading(false);
      setScanning(false);
    }
  };

  return (
    <Card>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 使用说明 */}
        <Alert
          message="使用说明"
          description={
            <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
              <li>支持上传 TXT、PDF、Word、Excel、CSV 等格式的文档</li>
              <li>单个文件大小不超过 100MB</li>
              <li>系统将自动识别并提取文档中的敏感信息</li>
              <li>扫描结果包括：身份证号、手机号、邮箱、银行卡号、API密钥等</li>
            </ul>
          }
          type="info"
          showIcon
        />

        {/* 文件上传区域 */}
        <Dragger {...uploadProps} style={{ padding: 20 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持多文件上传，支持 txt, pdf, doc, docx, xls, xlsx, csv 格式
          </p>
        </Dragger>

        {/* 文件列表 */}
        {fileList.length > 0 && (
          <Card title={`已选择 ${fileList.length} 个文件`} size="small">
            <List
              dataSource={fileList}
              renderItem={(file) => (
                <List.Item
                  actions={[
                    <Button
                      type="text"
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => {
                        const newFileList = fileList.filter(f => f.uid !== file.uid);
                        setFileList(newFileList);
                      }}
                      disabled={uploading || scanning}
                    >
                      删除
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={getFileIcon(file.name)}
                    title={file.name}
                    description={
                      <Space>
                        <Text type="secondary">
                          {(file.size! / 1024 / 1024).toFixed(2)} MB
                        </Text>
                        {file.status === 'error' && (
                          <Tag color="error">上传失败</Tag>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* 上传进度 */}
        {uploading && (
          <Card size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>正在上传文件... ({uploadedCount}/{fileList.length})</Text>
              <Progress percent={uploadProgress} />
            </Space>
          </Card>
        )}

        {/* 操作按钮 */}
        <Space>
          <Button
            type="primary"
            size="large"
            icon={<ScanOutlined />}
            onClick={handleStartScan}
            loading={uploading || scanning}
            disabled={fileList.length === 0}
          >
            {uploading ? '上传中...' : scanning ? '创建任务中...' : '开始扫描'}
          </Button>
          
          <Button
            size="large"
            onClick={() => setFileList([])}
            disabled={uploading || scanning}
          >
            清空列表
          </Button>
        </Space>
      </Space>
    </Card>
  );
};

export default DocumentUploadScan;