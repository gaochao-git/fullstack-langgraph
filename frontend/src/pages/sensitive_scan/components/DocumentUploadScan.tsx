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
  FileUnknownOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
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

const DocumentUploadScan: React.FC<DocumentUploadScanProps> = ({ onTaskCreated }) => {
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);  // 新增：文件解析中
  const [scanning, setScanning] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedCount, setUploadedCount] = useState(0);
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
    showUploadList: {
      showRemoveIcon: true,
      removeIcon: <DeleteOutlined style={{ color: '#ff4d4f' }} />
    },
    beforeUpload: async (file) => {
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

        return false; // 阻止自动上传
      } catch (error) {
        console.error('获取上传配置失败:', error);
        message.error('获取上传配置失败，请刷新页面重试');
        return false;
      }
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

      // 等待所有文件解析完成
      message.info('文件上传完成，等待文件解析...');
      setParsing(true);

      try {
        // 并行等待所有文件解析完成
        const parseResults = await Promise.allSettled(
          uploadedFileIds.map(fileId =>
            fileApi.waitForFileReady(fileId, undefined, (status) => {
              console.log(`文件 ${fileId} 解析状态: ${status.status}`);
            })
          )
        );

        // 检查是否有解析失败的文件
        const failedFiles = parseResults
          .map((result, index) => ({
            result,
            fileId: uploadedFileIds[index],
            fileName: fileList[index]?.name || uploadedFileIds[index]
          }))
          .filter(item => item.result.status === 'rejected');

        if (failedFiles.length > 0) {
          // 显示详细的错误信息
          failedFiles.forEach(({ fileName, result }) => {
            const errorMsg = result.status === 'rejected' ? result.reason.message : '未知错误';
            message.error(`文件 "${fileName}" 解析失败: ${errorMsg}`, 10); // 显示10秒
          });
          throw new Error(`${failedFiles.length} 个文件解析失败`);
        }

        message.success('所有文件解析完成，开始创建扫描任务...');
      } catch (error: any) {
        // 如果不是文件解析失败（已经显示过详细错误），才显示通用错误
        if (!error.message?.includes('文件解析失败')) {
          message.error(`处理失败: ${error.message || '未知错误'}`);
        }
        throw error;
      }

      setParsing(false);
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
      setParsing(false);
      setScanning(false);
    }
  };

  return (
    <Card>
      <style>{`
        .document-upload-scan .ant-upload-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 12px;
        }
        .document-upload-scan .ant-upload-list-item {
          margin: 0 !important;
          padding: 4px 8px !important;
          height: auto !important;
          border: 1px solid #d9d9d9;
          border-radius: 4px;
          background: #fafafa;
        }
        .document-upload-scan .ant-upload-list-item-info {
          display: flex;
          align-items: center;
        }
        .document-upload-scan .ant-upload-list-item-name {
          padding: 0 4px !important;
        }
        .document-upload-scan .ant-upload-list-item-actions {
          position: static !important;
          opacity: 1 !important;
          margin-left: 4px;
        }
        .document-upload-scan .ant-upload-list-item-actions .anticon-delete {
          font-size: 14px;
        }
      `}</style>
      <Space direction="vertical" style={{ width: '100%' }} size="large" className="document-upload-scan">
        {/* 文件上传区域 */}
        <Dragger {...uploadProps} style={{ padding: 20 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持多文件上传，支持格式: {supportedFormats}
          </p>
        </Dragger>


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
            loading={uploading || parsing || scanning}
            disabled={fileList.length === 0}
          >
            {uploading ? '上传中...' : parsing ? '文件解析中...' : scanning ? '创建任务中...' : '开始扫描'}
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