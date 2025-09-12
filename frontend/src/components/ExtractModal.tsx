import React, { useState, useEffect } from 'react';
import { Modal, Table, Tag, Space, Spin, Typography, message, Input } from 'antd';
import { FileTextOutlined, AlertOutlined } from '@ant-design/icons';
import { omind_get, omind_post } from '@/utils/base_api';

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
  const [fileNameMap, setFileNameMap] = useState<Record<string, string>>({});

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
        
        // 获取所有唯一的file_id
        console.log('Response data:', response.data);
        console.log('Items:', response.data.items);
        const fileIds = new Set<string>();
        response.data.items?.forEach((item: any, index: number) => {
          console.log(`Item ${index}:`, item);
          // 优先使用 file_id，如果没有则从 file 字段提取
          if (item.file_id) {
            fileIds.add(item.file_id);
          } else if (item.file && item.file.startsWith('document_')) {
            // 从 document_xxx 格式中提取文件ID
            const fileId = item.file.substring('document_'.length);
            fileIds.add(fileId);
          }
        });
        
        // 批量查询文件名（使用批量metadata接口）
        console.log('File IDs to query:', Array.from(fileIds));
        const nameMap: Record<string, string> = {};
        
        if (fileIds.size > 0) {
          try {
            console.log('Batch querying metadata for files:', Array.from(fileIds));
            const batchResponse = await omind_post('/api/v1/chat/files/batch/metadata', Array.from(fileIds));
            
            console.log('Batch metadata response:', batchResponse);
            
            if (batchResponse.status === 'ok' && batchResponse.data?.files) {
              // 从响应中提取文件名映射
              const files = batchResponse.data.files;
              for (const fileId of fileIds) {
                if (files[fileId]) {
                  nameMap[fileId] = files[fileId].file_name || fileId;
                } else {
                  nameMap[fileId] = fileId; // 如果没有找到，使用file_id
                }
              }
            }
          } catch (error) {
            console.error('Failed to batch get metadata:', error);
            // 如果批量查询失败，所有文件都使用file_id
            for (const fileId of fileIds) {
              nameMap[fileId] = fileId;
            }
          }
        }
        
        console.log('Final file name map:', nameMap);
        setFileNameMap(nameMap);
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
      title: '脱敏值',
      dataIndex: 'masked_value',
      key: 'masked_value',
      width: 200,
      render: (value: string) => value ? <Typography.Text code style={{ fontSize: '12px' }}>{value}</Typography.Text> : '-'
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
      width: 250,
      render: (_: any, record: any) => {
        // 获取file_id，兼容新旧数据格式
        let fileId = record.file_id;
        if (!fileId && record.file && record.file.startsWith('document_')) {
          fileId = record.file.substring('document_'.length);
        }
        
        // 如果有fileId且在nameMap中有对应的文件名，使用真实文件名
        const fileName = fileId && fileNameMap[fileId] ? fileNameMap[fileId] : (record.file || '-');
        
        return (
          <Typography.Text ellipsis={{ tooltip: fileName }} style={{ fontSize: '12px' }}>
            <FileTextOutlined style={{ marginRight: 4 }} />
            {fileName}
          </Typography.Text>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      align: 'center' as const,
      render: (_: any, record: any) => {
        // 获取file_id，兼容新旧数据格式
        let fileId = record.file_id;
        if (!fileId && record.file) {
          if (record.file.startsWith('document_')) {
            fileId = record.file.substring('document_'.length);
          } else {
            fileId = record.file;
          }
        }
        
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
        ) : !data || !data.items || data.items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>暂无数据</div>
        ) : (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Typography.Text type="secondary">
                共 {data.total_sensitive || data.items.length} 条记录
              </Typography.Text>
            </div>
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