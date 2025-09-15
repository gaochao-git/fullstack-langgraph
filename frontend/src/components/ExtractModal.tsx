import React, { useState, useEffect, useMemo } from 'react';
import { Modal, Table, Tag, Space, Spin, Typography, message, Input, Button, Card, Row, Col, Statistic, ConfigProvider } from 'antd';
import { FileTextOutlined, AlertOutlined, DownloadOutlined, FolderOpenOutlined, WarningOutlined, FileSearchOutlined, FileImageOutlined } from '@ant-design/icons';
import { omind_get, omind_post } from '@/utils/base_api';
import { fileApi } from '@/services/fileApi';
import zhCN from 'antd/locale/zh_CN';

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
    console.log('loadReport called with reportPath:', reportPath, 'reportType:', reportType);
    setLoading(true);
    try {
      let response;
      
      // 根据不同的报告类型使用不同的API
      if (reportType === 'LANGEXTRACT') {
        // 对于 LANGEXTRACT 类型，reportPath 就是 task_id
        console.log('Loading LANGEXTRACT report for task:', reportPath);
        response = await omind_get(`/api/v1/extract/task/${reportPath}`);
      } else {
        // 默认处理（兼容旧格式）
        const filename = reportPath.split('/').pop() || '';
        console.log('Loading report filename:', filename);
        response = await omind_get(`/api/v1/extract/${filename}`);
      }
      
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

  // 根据reportType决定是否需要转换数据
  const fileBasedData = useMemo(() => {
    if (!data || reportType !== 'LANGEXTRACT') {
      return data;
    }
    
    // 如果后端已经返回了files字段，直接使用
    if (data.files && Array.isArray(data.files)) {
      // 处理后端返回的文件列表
      const processedFiles = data.files.map((file: any) => {
        // 收集该文件的所有敏感信息
        const fileSensitiveItems = data.items?.filter((item: any) => item.file_id === file.file_id) || [];
        
        // 从敏感信息项中获取文件信息（如果file对象中没有）
        const firstItem = fileSensitiveItems[0];
        const char_count = file.char_count || firstItem?.char_count || 0;
        const image_count = file.image_count || firstItem?.image_count || 0;
        
        return {
          file_id: file.file_id,
          file_name: file.file_name || `文档_${file.file_id}`,
          file_size: file.file_size || 0,
          char_count: char_count,
          image_count: image_count,
          sensitive_items: fileSensitiveItems.map((item: any) => ({
            type: item.type,
            context: item.context,
            masked_value: item.masked_value,
            position: item.position
          })),
          sensitive_count: file.sensitive_count || fileSensitiveItems.length,
          status: 'completed',
          // 基于文件名构建路径
          jsonl_path: `/tmp/scan_visualizations/${reportPath}_${file.file_id}.jsonl`,
          html_path: `/tmp/scan_visualizations/${reportPath}_${file.file_id}.html`
        };
      });
      
      return {
        ...data,
        files: processedFiles,
        total_files: processedFiles.length,
        files_with_sensitive: processedFiles.filter(f => f.sensitive_items.length > 0).length
      };
    }
    
    // 如果没有files字段，从items构建（兼容旧版本）
    const fileMap = new Map();
    
    if (data.items) {
      data.items.forEach((item: any) => {
        const fileId = item.file_id;
        if (!fileMap.has(fileId)) {
          fileMap.set(fileId, {
            file_id: fileId,
            file_name: item.file_name || `文档_${fileId}`,
            file_size: item.file_size || 0,
            char_count: item.char_count || 0,
            image_count: item.image_count || 0,
            sensitive_items: [],
            status: 'completed',
            jsonl_path: `/tmp/scan_visualizations/${reportPath}_${fileId}.jsonl`,
            html_path: `/tmp/scan_visualizations/${reportPath}_${fileId}.html`
          });
        }
        // 添加敏感信息到文件记录中
        fileMap.get(fileId).sensitive_items.push({
          type: item.type,
          context: item.context,
          masked_value: item.masked_value,
          position: item.position
        });
      });
    }
    
    const files = Array.from(fileMap.values());
    
    return {
      ...data,
      files: files,
      total_files: data.total_files || files.length,
      files_with_sensitive: data.files_with_sensitive || files.filter(f => f.sensitive_items.length > 0).length
    };
  }, [data, reportType, reportPath]);

  // 文件列表表格列定义（用于LANGEXTRACT类型）
  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'file_name',
      key: 'file_name',
      width: 300,
      render: (fileName: string, record: any) => {
        const fileId = record.file_id;
        
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
            <Typography.Text ellipsis={{ tooltip: fileName }} style={{ maxWidth: '200px' }}>
              <FileTextOutlined style={{ marginRight: 4 }} />
              {fileName}
            </Typography.Text>
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={handleDownload}
              style={{ padding: '0 4px' }}
              title="下载原始文件"
            />
          </Space>
        );
      }
    },
    {
      title: '扫描状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          'completed': { color: 'green', text: '已完成' },
          'failed': { color: 'red', text: '失败' },
          'scanning': { color: 'blue', text: '扫描中' },
          'pending': { color: 'gray', text: '待处理' }
        };
        const config = statusMap[status] || { color: 'gray', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '敏感信息',
      key: 'sensitive_count',
      width: 120,
      render: (_: any, record: any) => {
        const count = record.sensitive_items?.length || 0;
        return count > 0 ? (
          <Tag color="red" icon={<AlertOutlined />}>{count} 条</Tag>
        ) : (
          <Tag color="green">无</Tag>
        );
      }
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (fileSize: number) => {
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
      dataIndex: 'char_count',
      key: 'char_count',
      width: 100,
      render: (charCount: number, record: any) => {
        const imageCount = record.image_count || 0;
        
        return (
          <Space direction="vertical" size={0} style={{ fontSize: '12px' }}>
            <span>{(charCount || 0).toLocaleString()}</span>
            {imageCount > 0 && <span style={{ color: '#8c8c8c' }}>含{imageCount}图</span>}
          </Space>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => {
        const fileId = record.file_id;
        const hasSensitiveInfo = record.sensitive_items?.length > 0 || record.sensitive_count > 0;
        
        // 构建扫描报告文件名：task_id_file_id
        const scanId = `${reportPath}_${fileId}`;
        
        return (
          <Space size={8}>
            {hasSensitiveInfo && (
              <Typography.Link 
                onClick={() => {
                  // 在新标签页打开HTML报告
                  window.open(`/api/v1/extract/${scanId}/html`, '_blank');
                }}
                style={{ fontSize: '12px' }}
              >
                查看报告
              </Typography.Link>
            )}
            <Typography.Link 
              onClick={() => viewFileContent(fileId)}
              style={{ fontSize: '12px' }}
            >
              查看原始文本
            </Typography.Link>
          </Space>
        );
      }
    }
  ];

  // 通用表格列定义（用于其他类型）
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
            查看原始文本
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
                {reportType === 'LANGEXTRACT' && (
                  <Col span={4}>
                    <Statistic
                      title="扫描文件总数"
                      value={fileBasedData.total_files || 0}
                      prefix={<FolderOpenOutlined />}
                    />
                  </Col>
                )}
                <Col span={reportType === 'LANGEXTRACT' ? 4 : 6}>
                  <Statistic
                    title="包含敏感信息的文件"
                    value={(() => {
                      // 使用Set去重计算包含敏感信息的文件数量
                      if (reportType === 'LANGEXTRACT' && fileBasedData.files_with_sensitive !== undefined) {
                        return fileBasedData.files_with_sensitive;
                      }
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
                        if (reportType === 'LANGEXTRACT' && fileBasedData.files_with_sensitive !== undefined) {
                          return fileBasedData.files_with_sensitive;
                        }
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
                <Col span={reportType === 'LANGEXTRACT' ? 3 : 4}>
                  <Statistic
                    title="敏感信息总数"
                    value={data.total_sensitive || data.items?.length || 0}
                    prefix={<WarningOutlined />}
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Col>
                <Col span={reportType === 'LANGEXTRACT' ? 4 : 5}>
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
                <Col span={reportType === 'LANGEXTRACT' ? 4 : 5}>
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
                <Col span={reportType === 'LANGEXTRACT' ? 5 : 4}>
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
                  <Space align="start" style={{ width: '100%' }}>
                    <Typography.Text type="secondary" style={{ whiteSpace: 'nowrap' }}>
                      敏感信息类型分布：
                    </Typography.Text>
                    <Space wrap>
                      {Object.entries(data.statistics).map(([type, count]) => (
                        <Tag key={type} color={getTypeColor(type)}>
                          {type}: {count as number}
                        </Tag>
                      ))}
                    </Space>
                  </Space>
                </div>
              )}
            </Card>
            
            <ConfigProvider locale={zhCN}>
              <Table
                columns={reportType === 'LANGEXTRACT' ? fileColumns : columns}
                dataSource={
                  reportType === 'LANGEXTRACT' 
                    ? fileBasedData.files?.map((item: any, index: number) => ({ ...item, key: index })) || []
                    : data.items.map((item: any, index: number) => ({ ...item, key: index }))
                }
                pagination={{ 
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  pageSizeOptions: ['10', '20', '50', '100'],
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                  position: ['bottomRight'],
                  responsive: true,
                  showLessItems: false,
                  showTitle: true,
                  itemRender: (page, type, originalElement) => {
                    if (type === 'prev') {
                      return <a>上一页</a>;
                    }
                    if (type === 'next') {
                      return <a>下一页</a>;
                    }
                    return originalElement;
                  }
                }}
                size="small"
                scroll={{ x: 'max-content' }}
                locale={{
                  filterTitle: '筛选',
                  filterConfirm: '确定',
                  filterReset: '重置',
                  emptyText: '暂无数据'
                }}
              />
            </ConfigProvider>
          </div>
        )}
      </Modal>
      
      {/* 文件内容弹窗 */}
      <Modal
        title={currentFileName}
        open={fileContentVisible}
        onCancel={() => {
          setFileContentVisible(false);
        }}
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
          <div style={{ 
            maxHeight: '70vh', 
            overflowY: 'auto', 
            padding: '16px',
            backgroundColor: '#f5f5f5',
            borderRadius: '4px',
            border: '1px solid #d9d9d9'
          }}>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              wordWrap: 'break-word',
              fontFamily: 'monospace',
              fontSize: '14px',
              lineHeight: '1.6',
              margin: 0
            }}>
              {fileContent}
            </pre>
          </div>
        )}
      </Modal>
    </>
  );
};