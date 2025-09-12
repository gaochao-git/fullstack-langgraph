import React, { useState, useEffect } from 'react';
import { Modal, Table, Tag, Space, Spin, Typography, message, Input, Button, Card, Row, Col, Statistic } from 'antd';
import { FileTextOutlined, AlertOutlined, DownloadOutlined, FolderOpenOutlined, WarningOutlined, FileSearchOutlined, FileImageOutlined } from '@ant-design/icons';
import { omind_get, omind_post } from '@/utils/base_api';
import { fileApi } from '@/services/fileApi';

const { TextArea } = Input;

interface ExtractModalProps {
  visible: boolean;
  onClose: () => void;
  reportType: string;
  reportPath: string;
  title?: string;
}

export const ExtractModal: React.FC<ExtractModalProps> = ({
  visible,
  onClose,
  reportType,
  reportPath,
  title = '查看报告'
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [fileContentVisible, setFileContentVisible] = useState(false);
  const [fileContent, setFileContent] = useState('');
  const [fileContentLoading, setFileContentLoading] = useState(false);
  const [currentFileName, setCurrentFileName] = useState('');
  useEffect(() => {
    if (visible && reportPath) {
      loadReport();
    }
  }, [visible, reportPath]);

  const loadReport = async () => {
    console.log('loadReport called with reportPath:', reportPath);
    setLoading(true);
    try {
      const filename = reportPath.split('/').pop() || '';
      console.log('Loading report filename:', filename);
      const response = await omind_get(`/api/v1/extract/${filename}`);
      console.log('Extract response:', response);
      if (response.status === 'ok') {
        setData(response.data);
      } else {
        message.error(response.msg || '加载提取结果失败');
      }
    } catch (error) {
      message.error('加载提取结果失败');
    } finally {
      setLoading(false);
    }
  };

  // 敏感信息类型配色
  const getTypeColor = (type: string) => {
    const colorMap: Record<string, string> = {
      '身份证号': 'red',
      '手机号': 'orange',
      '邮箱地址': 'green',
      '银行卡号': 'purple',
      'API密钥': 'magenta',
      '密码': 'volcano',
      '内网IP': 'cyan',
      '默认': 'blue'
    };
    return colorMap[type] || colorMap['默认'];
  };

  // 查看文件内容
  const viewFileContent = async (fileId: string) => {
    try {
      setFileContentLoading(true);
      setFileContentVisible(true);
      
      // 去掉 document_ 前缀
      const actualFileId = fileId.startsWith('document_') ? fileId.substring(9) : fileId;
      // 调用获取文档内容的API（会返回解析后的内容）
      const response = await omind_get(`/api/v1/chat/files/${actualFileId}/content`);
      if (response.status === 'ok' && response.data) {
        setFileContent(response.data.content || '暂无内容');
        setCurrentFileName(response.data.file_name || '文档内容');
      } else {
        message.error(response.msg || '获取文件内容失败');
        setFileContentVisible(false);
      }
    } catch (error) {
      message.error('查看文件失败');
      setFileContentVisible(false);
    } finally {
      setFileContentLoading(false);
    }
  };

  // 通用表格列定义
  const columns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => type ? <Tag color={getTypeColor(type)}>{type}</Tag> : '-'
    },
    {
      title: '上下文',
      dataIndex: 'context',
      key: 'context',
      render: (context: string) => (
        <Typography.Paragraph ellipsis={{ rows: 2, expandable: true }} style={{ marginBottom: 0 }}>
          {context || '-'}
        </Typography.Paragraph>
      )
    },
    {
      title: '文件名',
      key: 'fileName',
      width: 300,
      render: (_: any, record: any) => {
        // 优先使用后端返回的file_name
        const fileId = record.file_id;
        const fileName = record.file_name || `文档_${fileId}` || '-';
        
        // 下载文件函数
        const handleDownload = async () => {
          if (!fileId) {
            message.error('无法下载：文件ID不存在');
            return;
          }
          
          try {
            const blob = await fileApi.downloadDocument(fileId);
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = fileName;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
          } catch (error) {
            console.error('下载文件失败:', error);
            message.error('下载文件失败');
          }
        };
        
        return (
          <Space size={4}>
            <Typography.Text ellipsis={{ tooltip: fileName }} style={{ fontSize: '12px', maxWidth: '200px' }}>
              <FileTextOutlined style={{ marginRight: 4 }} />
              {fileName}
            </Typography.Text>
            {fileId && (
              <Button
                type="link"
                size="small"
                icon={<DownloadOutlined />}
                onClick={handleDownload}
                style={{ padding: '0 4px' }}
                title="下载原始文件"
              />
            )}
          </Space>
        );
      }
    },
    {
      title: '文件大小',
      key: 'fileSize',
      width: 100,
      render: (_: any, record: any) => {
        const fileSize = record.file_size || 0;
        
        // 格式化文件大小
        const formatFileSize = (bytes: number) => {
          if (bytes === 0) return '0 B';
          const k = 1024;
          const sizes = ['B', 'KB', 'MB', 'GB'];
          const i = Math.floor(Math.log(bytes) / Math.log(k));
          return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };
        
        return <span style={{ fontSize: '12px' }}>{formatFileSize(fileSize)}</span>;
      }
    },
    {
      title: '文档字数',
      key: 'charCount',
      width: 100,
      render: (_: any, record: any) => {
        const charCount = record.char_count || 0;
        const imageCount = record.image_count || 0;
        
        return (
          <Space direction="vertical" size={0} style={{ fontSize: '12px' }}>
            <span>{charCount.toLocaleString()}</span>
            {imageCount > 0 && <span style={{ color: '#8c8c8c' }}>含{imageCount}图</span>}
          </Space>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      align: 'center' as const,
      render: (_: any, record: any) => {
        const fileId = record.file_id;
        
        return fileId ? (
          <Typography.Link 
            onClick={() => viewFileContent(fileId)}
            style={{ fontSize: '12px' }}
          >
            查看原始解析文档
          </Typography.Link>
        ) : '-';
      }
    }
  ];

  return (
    <>
      <Modal
        title={
          <Space>
            <AlertOutlined />
            <span>{title}</span>
          </Space>
        }
        open={visible}
        onCancel={onClose}
        width="90%"
        style={{ top: 20 }}
        styles={{
          body: {
            height: 'calc(100vh - 200px)', 
            overflow: 'auto'
          }
        }}
        footer={null}
      >
        {loading ? (
          <Spin size="large" tip="加载中..." style={{ display: 'block', margin: '50px auto' }} />
        ) : !data || (!data.items || data.items.length === 0) ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>暂无数据</div>
        ) : (
          <div>
            {/* 扫描统计信息 */}
            <Card style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={4}>
                  <Statistic
                    title="扫描文件总数"
                    value={(() => {
                      // 使用Set去重计算实际的文件数量
                      const uniqueFileIds = new Set();
                      if (data.items && Array.isArray(data.items)) {
                        data.items.forEach((item: any) => {
                          if (item.file_id) {
                            uniqueFileIds.add(item.file_id);
                          }
                        });
                      }
                      return uniqueFileIds.size || data.total_files || 0;
                    })()}
                    prefix={<FolderOpenOutlined />}
                  />
                </Col>
                <Col span={4}>
                  <Statistic
                    title="包含敏感信息的文件"
                    value={(() => {
                      // 使用Set去重计算包含敏感信息的文件数量
                      const sensitiveFileIds = new Set();
                      if (data.items && Array.isArray(data.items)) {
                        data.items.forEach((item: any) => {
                          if (item.file_id) {
                            sensitiveFileIds.add(item.file_id);
                          }
                        });
                      }
                      return sensitiveFileIds.size || data.files_with_sensitive || 0;
                    })()}
                    prefix={<FileSearchOutlined />}
                    valueStyle={{ color: (() => {
                      const count = (() => {
                        const sensitiveFileIds = new Set();
                        if (data.items && Array.isArray(data.items)) {
                          data.items.forEach((item: any) => {
                            if (item.file_id) {
                              sensitiveFileIds.add(item.file_id);
                            }
                          });
                        }
                        return sensitiveFileIds.size || data.files_with_sensitive || 0;
                      })();
                      return count > 0 ? '#cf1322' : '#3f8600';
                    })() }}
                  />
                </Col>
                <Col span={4}>
                  <Statistic
                    title="敏感信息总数"
                    value={data.total_sensitive || data.items?.length || 0}
                    prefix={<WarningOutlined />}
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Col>
                <Col span={4}>
                  <Statistic
                    title="扫描总字数"
                    value={(() => {
                      // 计算所有文件的总字数
                      let totalChars = 0;
                      if (data.items && Array.isArray(data.items)) {
                        // 使用Map去重file_id，避免重复计算
                        const fileCharMap = new Map();
                        data.items.forEach((item: any) => {
                          if (item.file_id && item.char_count) {
                            fileCharMap.set(item.file_id, item.char_count);
                          }
                        });
                        fileCharMap.forEach(charCount => {
                          totalChars += charCount;
                        });
                      }
                      return totalChars.toLocaleString();
                    })()}
                  />
                </Col>
                <Col span={4}>
                  <Statistic
                    title="扫描总大小"
                    value={(() => {
                      // 计算所有文件的总大小
                      let totalSize = 0;
                      if (data.items && Array.isArray(data.items)) {
                        // 使用Map去重file_id，避免重复计算
                        const fileSizeMap = new Map();
                        data.items.forEach((item: any) => {
                          if (item.file_id && item.file_size) {
                            fileSizeMap.set(item.file_id, item.file_size);
                          }
                        });
                        fileSizeMap.forEach(fileSize => {
                          totalSize += fileSize;
                        });
                      }
                      
                      // 格式化文件大小
                      if (totalSize === 0) return '0 B';
                      const k = 1024;
                      const sizes = ['B', 'KB', 'MB', 'GB'];
                      const i = Math.floor(Math.log(totalSize) / Math.log(k));
                      return parseFloat((totalSize / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                    })()}
                  />
                </Col>
                <Col span={4}>
                  <Statistic
                    title="扫描图片数量"
                    value={(() => {
                      // 计算所有文件的图片总数
                      let totalImages = 0;
                      if (data.items && Array.isArray(data.items)) {
                        // 使用Map去重file_id，避免重复计算
                        const fileImageMap = new Map();
                        data.items.forEach((item: any) => {
                          if (item.file_id && item.image_count !== undefined) {
                            fileImageMap.set(item.file_id, item.image_count);
                          }
                        });
                        fileImageMap.forEach(imageCount => {
                          totalImages += imageCount;
                        });
                      }
                      return totalImages;
                    })()}
                    prefix={<FileImageOutlined />}
                  />
                </Col>
              </Row>
              
              {/* 敏感信息类型分布 */}
              {data.statistics && Object.keys(data.statistics).length > 0 && (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
                  <Typography.Text type="secondary" style={{ marginBottom: 8, display: 'block' }}>
                    敏感信息类型分布：
                  </Typography.Text>
                  <Space wrap>
                    {Object.entries(data.statistics).map(([type, count]) => (
                      <Tag key={type} color={getTypeColor(type)}>
                        {type}: {count as number}
                      </Tag>
                    ))}
                  </Space>
                </div>
              )}
            </Card>
            
            <Table
              columns={columns}
              dataSource={data.items.map((item: any, index: number) => ({ ...item, key: index }))}
              pagination={{ 
                pageSize: 10,
                showTotal: (total) => `共 ${total} 条`
              }}
              size="small"
            />
          </div>
        )}
      </Modal>
      
      {/* 文件内容弹窗 */}
      <Modal
        title={currentFileName}
        open={fileContentVisible}
        onCancel={() => setFileContentVisible(false)}
        width="80%"
        style={{ top: 20 }}
        styles={{
          body: { padding: '24px' }
        }}
        footer={null}
      >
        {fileContentLoading ? (
          <Spin size="large" tip="加载中..." style={{ display: 'block', margin: '50px auto' }} />
        ) : (
          <TextArea
            value={fileContent}
            readOnly
            autoSize={{ minRows: 10, maxRows: 30 }}
            style={{ fontSize: '14px', fontFamily: 'monospace' }}
          />
        )}
      </Modal>
    </>
  );
};