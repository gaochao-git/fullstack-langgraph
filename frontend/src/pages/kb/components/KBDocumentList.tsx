/**
 * 知识库文档列表组件
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Space,
  Button,
  Tooltip,
  Tag,
  Modal,
  message,
  Input,
  Select,
} from 'antd';
import {
  FileTextOutlined,
  EyeOutlined,
  DeleteOutlined,
  PushpinOutlined,
  PushpinFilled,
  SearchOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { KBDocument, ListParams } from '../types/kb';
import { kbApi } from '@/services/kbApi';

const { Search } = Input;
const { Option } = Select;

interface KBDocumentListProps {
  kbId: string;
  folderId?: string | null;
  onDocumentSelect?: (document: KBDocument) => void;
  height?: string | number;
}

const KBDocumentList: React.FC<KBDocumentListProps> = ({
  kbId,
  folderId,
  onDocumentSelect,
  height = 'calc(100vh - 300px)'
}) => {
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState<number | undefined>(undefined);

  // 加载文档列表
  const loadDocuments = async (params: ListParams = {}) => {
    try {
      setLoading(true);
      const requestParams = {
        page: currentPage,
        page_size: pageSize,
        ...params,
      };

      const response = await kbApi.getFolderDocuments(kbId, folderId, requestParams);
      
      if (response.status === 'ok') {
        setDocuments(response.data.items || []);
        setTotal(response.data.total || 0);
      } else {
        message.error(response.msg || '获取文档列表失败');
        setDocuments([]);
        setTotal(0);
      }
    } catch (error) {
      console.error('加载文档列表失败:', error);
      message.error('加载失败，请重试');
      setDocuments([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和依赖更新
  useEffect(() => {
    setCurrentPage(1);
    loadDocuments();
  }, [kbId, folderId]);

  useEffect(() => {
    loadDocuments();
  }, [currentPage]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchText(value);
    setCurrentPage(1);
    // 这里应该调用后端搜索API，暂时使用前端过滤
    loadDocuments();
  };

  // 置顶/取消置顶
  const handlePin = async (document: KBDocument) => {
    try {
      await kbApi.addDocumentToFolder(kbId, folderId, {
        file_id: document.file_id,
        is_pinned: !document.is_pinned,
      });
      
      message.success(document.is_pinned ? '已取消置顶' : '已置顶');
      loadDocuments();
    } catch (error) {
      console.error('置顶操作失败:', error);
      message.error('操作失败，请重试');
    }
  };

  // 删除文档
  const handleDelete = (document: KBDocument) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要从知识库中删除文档"${document.file_name}"吗？`,
      onOk: async () => {
        try {
          await kbApi.removeDocumentFromKB(kbId, document.file_id);
          message.success('文档删除成功');
          loadDocuments();
        } catch (error) {
          console.error('删除文档失败:', error);
          message.error('删除失败，请重试');
        }
      },
    });
  };

  // 格式化文件大小
  const formatFileSize = (size: number) => {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  };

  // 获取处理状态
  const getProcessStatus = (status: number) => {
    const statusMap = {
      0: { text: '待处理', color: 'default' },
      1: { text: '处理中', color: 'processing' },
      2: { text: '已完成', color: 'success' },
      3: { text: '处理失败', color: 'error' },
    };
    return statusMap[status as keyof typeof statusMap] || { text: '未知', color: 'default' };
  };

  // 过滤文档
  const filteredDocuments = documents.filter(doc => {
    if (searchText && !doc.file_name.toLowerCase().includes(searchText.toLowerCase())) {
      return false;
    }
    if (filterStatus !== undefined && doc.process_status !== filterStatus) {
      return false;
    }
    return true;
  });

  const columns: ColumnsType<KBDocument> = [
    {
      title: '文档名称',
      dataIndex: 'file_name',
      key: 'file_name',
      render: (text, record) => (
        <Space>
          <FileTextOutlined />
          <span>{record.display_name || text}</span>
          {record.is_pinned && (
            <Tooltip title="已置顶">
              <PushpinFilled style={{ color: '#1890ff' }} />
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 120,
      render: (size) => formatFileSize(size),
    },
    {
      title: '文件类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 100,
      render: (type) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '处理状态',
      dataIndex: 'process_status',
      key: 'process_status',
      width: 120,
      render: (status) => {
        const statusInfo = getProcessStatus(status);
        return (
          <Tag color={statusInfo.color}>
            {statusInfo.text}
          </Tag>
        );
      },
    },
    {
      title: '添加时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title={record.is_pinned ? '取消置顶' : '置顶'}>
            <Button
              type="text"
              size="small"
              icon={record.is_pinned ? <PushpinFilled /> : <PushpinOutlined />}
              onClick={() => handlePin(record)}
            />
          </Tooltip>
          <Tooltip title="预览">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => onDocumentSelect?.(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 搜索和筛选 */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Search
          placeholder="搜索文档名称"
          allowClear
          style={{ width: 250 }}
          onSearch={handleSearch}
          enterButton={<SearchOutlined />}
        />
        
        <Select
          placeholder="处理状态"
          style={{ width: 120 }}
          allowClear
          value={filterStatus}
          onChange={setFilterStatus}
        >
          <Option value={0}>待处理</Option>
          <Option value={1}>处理中</Option>
          <Option value={2}>已完成</Option>
          <Option value={3}>处理失败</Option>
        </Select>
      </Space>

      {/* 文档表格 */}
      <Table
        columns={columns}
        dataSource={filteredDocuments}
        rowKey="file_id"
        loading={loading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          onChange: (page) => {
            setCurrentPage(page);
          },
          showSizeChanger: false,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
        }}
        scroll={{ y: height }}
        size="small"
      />
    </div>
  );
};

export default KBDocumentList;