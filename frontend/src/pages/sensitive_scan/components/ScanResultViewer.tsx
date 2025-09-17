import React, { useState, useEffect } from 'react';
import {
  Modal,
  Tabs,
  Spin,
  Typography,
  Tag,
  Space,
  Button,
  message,
  Alert
} from 'antd';
import {
  FileTextOutlined,
  FilePdfOutlined,
  CopyOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { ScanApi } from '../services/scanApi';
import { SensitiveItem } from '../types/scanTask';

const { TabPane } = Tabs;
const { Text, Paragraph } = Typography;

interface ScanResultViewerProps {
  visible: boolean;
  taskId: string;
  fileId: string;
  onClose: () => void;
}

const ScanResultViewer: React.FC<ScanResultViewerProps> = ({
  visible,
  taskId,
  fileId,
  onClose
}) => {
  const [loading, setLoading] = useState(false);
  const [jsonlContent, setJsonlContent] = useState<string>('');
  const [parsedData, setParsedData] = useState<{
    document_id: string;
    text: string;
    extractions: SensitiveItem[];
  } | null>(null);
  const [htmlModalVisible, setHtmlModalVisible] = useState(false);
  const [htmlReportUrl, setHtmlReportUrl] = useState<string>('');
  const [htmlLoading, setHtmlLoading] = useState(false);

  // 敏感类型颜色映射
  const typeColorMap: Record<string, string> = {
    '身份证号': 'red',
    '手机号': 'orange',
    '邮箱地址': 'blue',
    '银行卡号': 'purple',
    'API密钥': 'gold',
    '用户名密码': 'magenta',
    '内网IP': 'green',
    '护照号': 'cyan',
    '车牌号': 'lime',
    '社保号': 'geekblue'
  };

  // 获取扫描结果
  const fetchScanResult = async () => {
    if (!taskId || !fileId) return;
    
    setLoading(true);
    try {
      const content = await ScanApi.getJsonlContent(taskId, fileId);
      setJsonlContent(content);
      
      // 解析JSONL
      try {
        const lines = content.trim().split('\n');
        if (lines.length > 0) {
          const data = JSON.parse(lines[0]);
          setParsedData(data);
        }
      } catch (error) {
        console.error('解析JSONL失败:', error);
      }
    } catch (error) {
      message.error('获取扫描结果失败');
    } finally {
      setLoading(false);
    }
  };

  // 查看HTML报告
  const viewHtmlReport = async () => {
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
        throw new Error(response.msg || '加载HTML报告失败');
      }
    } catch (error) {
      message.error('加载HTML报告失败');
      setHtmlModalVisible(false);
    } finally {
      setHtmlLoading(false);
    }
  };

  // 复制内容
  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('复制成功');
    }).catch(() => {
      message.error('复制失败');
    });
  };

  // 下载JSONL
  const downloadJsonl = () => {
    const blob = new Blob([jsonlContent], { type: 'application/x-ndjson' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scan_result_${fileId}.jsonl`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (visible && taskId && fileId) {
      fetchScanResult();
    }
  }, [visible, taskId, fileId]);

  return (
    <>
      <Modal
      title={
        <Space>
          <FileTextOutlined />
          扫描结果查看器
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
        <Button
          key="html"
          type="primary"
          icon={<FilePdfOutlined />}
          onClick={viewHtmlReport}
        >
          查看HTML报告
        </Button>
      ]}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : (
        <Tabs defaultActiveKey="summary">
          <TabPane tab="扫描摘要" key="summary">
            {parsedData ? (
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Alert
                  message="扫描统计"
                  description={`共发现 ${parsedData.extractions.length} 个敏感信息`}
                  type="info"
                  showIcon
                />
                
                {/* 敏感信息列表 */}
                <div>
                  <Text strong style={{ marginBottom: 8, display: 'block' }}>
                    敏感信息详情：
                  </Text>
                  {parsedData.extractions.map((item, index) => (
                    <div
                      key={index}
                      style={{
                        padding: '12px',
                        marginBottom: '8px',
                        background: '#f5f5f5',
                        borderRadius: '4px',
                        border: '1px solid #e8e8e8'
                      }}
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Space>
                          <Tag color={typeColorMap[item.type] || 'default'}>
                            {item.type}
                          </Tag>
                          <Button
                            type="text"
                            size="small"
                            icon={<CopyOutlined />}
                            onClick={() => handleCopy(item.text)}
                          >
                            复制
                          </Button>
                        </Space>
                        <Paragraph
                          style={{ margin: 0 }}
                          code
                          copyable={false}
                        >
                          {item.text}
                        </Paragraph>
                        {item.position && (
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            位置: [{item.position.start}, {item.position.end}]
                          </Text>
                        )}
                      </Space>
                    </div>
                  ))}
                  {parsedData.extractions.length === 0 && (
                    <Text type="secondary">未发现敏感信息</Text>
                  )}
                </div>
                
                {/* 文档预览 */}
                <div>
                  <Text strong style={{ marginBottom: 8, display: 'block' }}>
                    文档内容预览：
                  </Text>
                  <div
                    style={{
                      padding: '12px',
                      background: '#fafafa',
                      border: '1px solid #e8e8e8',
                      borderRadius: '4px',
                      maxHeight: '200px',
                      overflow: 'auto'
                    }}
                  >
                    <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {parsedData.text.length > 500 
                        ? parsedData.text.substring(0, 500) + '...' 
                        : parsedData.text}
                    </Paragraph>
                  </div>
                </div>
              </Space>
            ) : (
              <Alert
                message="无数据"
                description="未能解析扫描结果"
                type="warning"
                showIcon
              />
            )}
          </TabPane>
          
          <TabPane tab="原始数据" key="raw">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Button
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(jsonlContent)}
                >
                  复制
                </Button>
                <Button
                  icon={<DownloadOutlined />}
                  onClick={downloadJsonl}
                >
                  下载
                </Button>
              </Space>
              
              <pre
                style={{
                  background: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '500px'
                }}
              >
                {jsonlContent || '无数据'}
              </pre>
            </Space>
          </TabPane>
        </Tabs>
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

export default ScanResultViewer;