import React, { useState, useEffect } from 'react';
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
  Tag,
  Form,
  Select,
  InputNumber,
  Divider
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
import { ScanConfigApi } from '../services/scanConfigApi';
import { fileApi } from '@/services/fileApi';
import type { ScanConfig } from '../types/scanConfig';

const { Dragger } = Upload;
const { Title, Text } = Typography;
const { Option } = Select;

interface DocumentUploadScanProps {
  onTaskCreated?: (taskId: string) => void;
}

const DocumentUploadScan: React.FC<DocumentUploadScanProps> = ({ onTaskCreated }) => {
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedCount, setUploadedCount] = useState(0);
  const [configs, setConfigs] = useState<ScanConfig[]>([]);
  const [loadingConfigs, setLoadingConfigs] = useState(false);

  // 获取配置列表
  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    setLoadingConfigs(true);
    try {
      const response = await ScanConfigApi.listConfigs({
        page: 1,
        size: 100,
        status: 'active'
      });

      if (response.status === 'ok') {
        setConfigs(response.data.items);
        // 设置默认配置
        const defaultConfig = response.data.items.find((c: ScanConfig) => c.is_default);
        if (defaultConfig) {
          form.setFieldValue('config_id', defaultConfig.config_id);
        }
      }
    } catch (error) {
      console.error('获取配置列表失败:', error);
    } finally {
      setLoadingConfigs(false);
    }
  };

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

      // 获取表单参数
      const formValues = await form.validateFields();

      // 创建扫描任务，传递配置和参数
      const response = await ScanApi.createTask({
        file_ids: uploadedFileIds,
        config_id: formValues.config_id,
        max_workers: formValues.max_workers || 10,
        batch_length: formValues.batch_length || 10,
        extraction_passes: formValues.extraction_passes || 1,
        max_char_buffer: formValues.max_char_buffer || 2000
      });

      if (response.status === 'ok') {
        message.success('扫描任务创建成功');

        // 清空文件列表
        setFileList([]);
        setUploadProgress(0);
        setUploadedCount(0);

        // 通知父组件任务已创建
        if (onTaskCreated && response.data?.task_id) {
          onTaskCreated(response.data.task_id);
        }
      } else {
        message.error(response.msg || '创建扫描任务失败');
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

        {/* 扫描配置 */}
        <Card title="扫描配置" size="small">
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              max_workers: 10,
              batch_length: 10,
              extraction_passes: 1,
              max_char_buffer: 2000
            }}
          >
            <Form.Item
              label="配置模板"
              name="config_id"
              tooltip="选择预定义的扫描配置模板"
            >
              <Select
                placeholder="选择配置模板"
                loading={loadingConfigs}
                allowClear
              >
                {configs.map((config) => (
                  <Option key={config.config_id} value={config.config_id}>
                    {config.is_default && '【默认】'}
                    {config.config_name}
                    {config.config_description && ` - ${config.config_description}`}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item label="高级参数">
              <Space size="middle" wrap>
                <Form.Item
                  label="并行线程数"
                  name="max_workers"
                  tooltip="最大并行工作线程数（1-50）"
                  style={{ marginBottom: 0 }}
                >
                  <InputNumber min={1} max={50} style={{ width: 120 }} />
                </Form.Item>

                <Form.Item
                  label="批处理长度"
                  name="batch_length"
                  tooltip="批处理长度（1-100）"
                  style={{ marginBottom: 0 }}
                >
                  <InputNumber min={1} max={100} style={{ width: 120 }} />
                </Form.Item>

                <Form.Item
                  label="提取遍数"
                  name="extraction_passes"
                  tooltip="提取遍数（1-5）"
                  style={{ marginBottom: 0 }}
                >
                  <InputNumber min={1} max={5} style={{ width: 120 }} />
                </Form.Item>

                <Form.Item
                  label="字符缓冲区"
                  name="max_char_buffer"
                  tooltip="最大字符缓冲区大小（100-10000）"
                  style={{ marginBottom: 0 }}
                >
                  <InputNumber min={100} max={10000} style={{ width: 120 }} />
                </Form.Item>
              </Space>
            </Form.Item>
          </Form>
        </Card>

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