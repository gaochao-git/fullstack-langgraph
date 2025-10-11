import React, { useState, useEffect } from 'react';
import {
  Card,
  Upload,
  Button,
  Alert,
  List,
  Space,
  App,
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
  FileUnknownOutlined,
  CloseCircleOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd/es/upload/interface';
import { ScanApi } from '../services/scanApi';
import { ScanConfigApi } from '../services/scanConfigApi';
import { fileApi } from '@/services/fileApi';
import { configService } from '@/services/configApi';
import type { ScanConfig } from '../types/scanConfig';

const { Dragger } = Upload;
const { Title, Text } = Typography;
const { Option } = Select;

interface DocumentUploadScanProps {
  onTaskCreated?: (taskId: string) => void;
}

// 文件上传状态接口
interface FileUploadStatus {
  uid: string;
  fileId?: string;
  fileName: string;
  fileSize: number;
  status: 'pending' | 'uploading' | 'processing' | 'success' | 'failed';
  progress?: number;
  error?: string;
}

const DocumentUploadScan: React.FC<DocumentUploadScanProps> = ({ onTaskCreated }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [uploadedFiles, setUploadedFiles] = useState<FileUploadStatus[]>([]);
  const [scanning, setScanning] = useState(false);
  const [configs, setConfigs] = useState<ScanConfig[]>([]);
  const [loadingConfigs, setLoadingConfigs] = useState(false);
  const [supportedFormats, setSupportedFormats] = useState<string>('加载中...');

  // 获取上传配置
  useEffect(() => {
    configService.getUploadConfig().then(config => {
      setSupportedFormats(config.allowed_extensions.join(', '));
    }).catch(err => {
      console.error('获取上传配置失败:', err);
      setSupportedFormats('常见文档和图片格式');
    });
  }, []);

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

    if (['pdf'].includes(ext)) return <FilePdfOutlined style={{ fontSize: 20 }} />;
    if (['doc', 'docx'].includes(ext)) return <FileWordOutlined style={{ fontSize: 20 }} />;
    if (['xls', 'xlsx', 'csv'].includes(ext)) return <FileExcelOutlined style={{ fontSize: 20 }} />;
    if (['txt', 'md'].includes(ext)) return <FileTextOutlined style={{ fontSize: 20 }} />;

    return <FileUnknownOutlined style={{ fontSize: 20 }} />;
  };

  // 处理文件选择 - 立即上传
  const handleFileSelect = async (file: File): Promise<boolean> => {
    try {
      // 获取全局上传配置
      const config = await configService.getUploadConfig();

      // 检查文件大小
      const maxSize = config.max_upload_size_mb * 1024 * 1024;
      if (file.size > maxSize) {
        message.error(`文件 ${file.name} 超过大小限制（最大 ${config.max_upload_size_mb}MB）`);
        return false;
      }

      // 检查文件类型
      const fileExt = `.${file.name.split('.').pop()?.toLowerCase()}`;
      if (!config.allowed_extensions.includes(fileExt)) {
        message.error(`不支持的文件类型: ${fileExt}。支持的格式: ${config.allowed_extensions.join(', ')}`);
        return false;
      }

      // 添加到文件列表（pending状态）
      const fileStatus: FileUploadStatus = {
        uid: `${Date.now()}-${Math.random()}`,
        file,
        fileName: file.name,
        status: 'pending'
      };
      setUploadedFiles(prev => [...prev, fileStatus]);

      // 立即上传文件
      uploadFile(fileStatus);

      return false; // 阻止 antd Upload 组件的默认上传
    } catch (error) {
      console.error('文件验证失败:', error);
      message.error('文件验证失败，请重试');
      return false;
    }
  };

  // 上传单个文件
  const uploadFile = async (fileStatus: FileUploadStatus) => {
    let parseFailedInCallback = false;

    try {
      // 更新状态为上传中
      setUploadedFiles(prev =>
        prev.map(f => f.uid === fileStatus.uid ? { ...f, status: 'uploading', progress: 0 } : f)
      );

      // 上传文件
      const uploadResult = await fileApi.uploadFile(
        fileStatus.file,
        undefined,
        undefined,
        (percent) => {
          setUploadedFiles(prev =>
            prev.map(f => f.uid === fileStatus.uid ? { ...f, progress: percent } : f)
          );
        }
      );

      // 上传成功，更新状态为解析中
      setUploadedFiles(prev =>
        prev.map(f => f.uid === fileStatus.uid
          ? { ...f, status: 'processing', fileId: uploadResult.file_id, progress: 100 }
          : f
        )
      );

      // 等待文件解析完成
      try {
        await fileApi.waitForFileReady(uploadResult.file_id, undefined, (status) => {
          console.log(`文件 ${uploadResult.file_id} 解析状态:`, status);

          // 如果解析失败，立即更新状态
          if (status.status === 'failed' || status.status === 3) {
            parseFailedInCallback = true;
            setUploadedFiles(prev =>
              prev.map(f => f.uid === fileStatus.uid
                ? { ...f, status: 'failed', error: status.message || '文件解析失败' }
                : f
              )
            );
          }
        });

        // 解析成功
        setUploadedFiles(prev =>
          prev.map(f => f.uid === fileStatus.uid ? { ...f, status: 'success' } : f)
        );
        message.success(`文件 ${fileStatus.fileName} 上传并解析成功`);

      } catch (parseError: any) {
        // 如果已经在回调中处理过失败状态，只显示消息，不再重复设置状态
        if (parseFailedInCallback) {
          message.error(`文件 ${fileStatus.fileName} 解析失败: ${parseError.message || '未知错误'}`);
          return;
        }
        // 否则抛出错误，由外层处理
        throw parseError;
      }

    } catch (error: any) {
      // 上传失败（解析失败已在上面处理）
      setUploadedFiles(prev =>
        prev.map(f => f.uid === fileStatus.uid
          ? { ...f, status: 'failed', error: error.message || '处理失败' }
          : f
        )
      );
      message.error(`文件 ${fileStatus.fileName} 处理失败: ${error.message || '未知错误'}`);
    }
  };

  // 移除文件
  const handleRemoveFile = (uid: string) => {
    setUploadedFiles(prev => prev.filter(f => f.uid !== uid));
  };

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    fileList: [],
    showUploadList: false,
    beforeUpload: handleFileSelect
  };

  // 开始扫描
  const handleStartScan = async () => {
    // 检查是否有文件
    if (uploadedFiles.length === 0) {
      message.warning('请先上传文件');
      return;
    }

    // 检查是否所有文件都已成功上传
    const successFiles = uploadedFiles.filter(f => f.status === 'success' && f.fileId);
    const processingFiles = uploadedFiles.filter(f => f.status === 'uploading' || f.status === 'processing');
    const failedFiles = uploadedFiles.filter(f => f.status === 'failed');

    if (processingFiles.length > 0) {
      message.warning(`还有 ${processingFiles.length} 个文件正在上传或解析中，请稍候...`);
      return;
    }

    if (successFiles.length === 0) {
      message.error('没有可用于扫描的文件，请重新上传');
      return;
    }

    if (failedFiles.length > 0) {
      message.warning(`有 ${failedFiles.length} 个文件上传失败，将仅扫描成功上传的文件`);
    }

    setScanning(true);

    try {
      // 获取表单参数
      const formValues = await form.validateFields();

      // 创建扫描任务
      const fileIds = successFiles.map(f => f.fileId!);
      const response = await ScanApi.createTask({
        file_ids: fileIds,
        config_id: formValues.config_id,
        max_workers: formValues.max_workers || 10,
        batch_length: formValues.batch_length || 10,
        extraction_passes: formValues.extraction_passes || 1,
        max_char_buffer: formValues.max_char_buffer || 2000
      });

      if (response.status === 'ok') {
        message.success('扫描任务创建成功');

        // 清空文件列表
        setUploadedFiles([]);

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
      setScanning(false);
    }
  };

  // 获取状态标签
  const getStatusTag = (file: FileUploadStatus) => {
    switch (file.status) {
      case 'uploading':
        return <Tag icon={<LoadingOutlined />} color="processing">上传中 {file.progress}%</Tag>;
      case 'processing':
        return <Tag icon={<LoadingOutlined />} color="processing">解析中</Tag>;
      case 'success':
        return <Tag icon={<CheckCircleOutlined />} color="success">已完成</Tag>;
      case 'failed':
        return <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>;
      default:
        return <Tag color="default">等待中</Tag>;
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
            支持多文件上传，文件将自动上传并解析。支持格式: {supportedFormats}
          </p>
        </Dragger>

        {/* 已上传文件列表 - 紧凑横向显示 */}
        {uploadedFiles.length > 0 && (
          <Card size="small" title="已上传文件">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {uploadedFiles.map((file) => (
                <div
                  key={file.uid}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '4px 12px',
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                    backgroundColor: '#fafafa',
                    maxWidth: '300px'
                  }}
                >
                  {getFileIcon(file.fileName)}
                  <span style={{
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontSize: '14px'
                  }}>
                    {file.fileName}
                  </span>
                  {getStatusTag(file)}
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => handleRemoveFile(file.uid)}
                    disabled={file.status === 'uploading' || file.status === 'processing'}
                    style={{ padding: '0 4px', minWidth: 'auto' }}
                  />
                </div>
              ))}
            </div>
            {/* 显示错误信息 */}
            {uploadedFiles.some(f => f.error) && (
              <div style={{ marginTop: '12px' }}>
                {uploadedFiles
                  .filter(f => f.error)
                  .map(f => (
                    <Alert
                      key={f.uid}
                      message={`${f.fileName}: ${f.error}`}
                      type="error"
                      showIcon
                      closable
                      style={{ marginBottom: '8px' }}
                    />
                  ))}
              </div>
            )}
            {/* 显示上传进度 */}
            {uploadedFiles.some(f => f.status === 'uploading' && f.progress !== undefined) && (
              <div style={{ marginTop: '12px' }}>
                {uploadedFiles
                  .filter(f => f.status === 'uploading' && f.progress !== undefined)
                  .map(f => (
                    <div key={f.uid} style={{ marginBottom: '8px' }}>
                      <div style={{ marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                        {f.fileName}
                      </div>
                      <Progress percent={f.progress} size="small" />
                    </div>
                  ))}
              </div>
            )}
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
                  <InputNumber min={1000} max={10000} style={{ width: 120 }} />
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
            loading={scanning}
            disabled={uploadedFiles.length === 0 || uploadedFiles.every(f => f.status !== 'success')}
          >
            {scanning ? '创建任务中...' : '开始扫描'}
          </Button>

          <Button
            size="large"
            onClick={() => setUploadedFiles([])}
            disabled={scanning || uploadedFiles.some(f => f.status === 'uploading' || f.status === 'processing')}
          >
            清空列表
          </Button>
        </Space>
      </Space>
    </Card>
  );
};

export default DocumentUploadScan;
