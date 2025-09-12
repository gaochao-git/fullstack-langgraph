import React, { useState, useEffect } from 'react';
import { Modal, Table, Tag, Space, Spin, Typography, message, Input } from 'antd';
import { FileTextOutlined, AlertOutlined } from '@ant-design/icons';
import { omind_get } from '@/utils/base_api';

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
    setLoading(true);
    try {
      const filename = reportPath.split('/').pop() || '';
      const response = await omind_get(`/api/v1/extract/${filename}`);
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
      title: '操作',
      key: 'action',
      width: 150,
      align: 'center' as const,
      render: (_: any, record: any) => record.file ? (
        <Typography.Link 
          onClick={() => viewFileContent(record.file)}
          style={{ fontSize: '12px' }}
        >
          查看原始解析文档
        </Typography.Link>
      ) : '-'
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
        bodyStyle={{ 
          height: 'calc(100vh - 200px)', 
          overflow: 'auto'
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
        bodyStyle={{ padding: '24px' }}
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