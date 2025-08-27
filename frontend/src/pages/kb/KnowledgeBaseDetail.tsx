/**
 * 知识库详情页面 - 包含拖拽目录树和文档管理
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Row,
  Col,
  Card,
  Typography,
  Button,
  Space,
  Breadcrumb,
  Tag,
  message,
  Spin,
  Upload,
  Modal,
  Table,
  Tooltip,
  Progress,
} from 'antd';
import {
  ArrowLeftOutlined,
  UploadOutlined,
  FileTextOutlined,
  FolderOutlined,
  EyeOutlined,
  DeleteOutlined,
  DownloadOutlined,
  PushpinOutlined,
  PushpinFilled,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

import { KnowledgeBase, KBFolder, KBDocument, VISIBILITY_TEXTS, VISIBILITY_COLORS } from './types/kb';
import { kbApi } from '@/services/kbApi';
import { KBFolderTree } from './components';

const { Title, Text } = Typography;

interface RouteParams {
  kbId: string;
}

const KnowledgeBaseDetail: React.FC = () => {
  const { kbId } = useParams<RouteParams>();
  const navigate = useNavigate();

  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [loading, setLoading] = useState(false);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  
  // 当前选中的目录
  const [selectedFolder, setSelectedFolder] = useState<KBFolder | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [folderPath, setFolderPath] = useState<string[]>(['根目录']);
  
  // 文档列表
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [totalDocs, setTotalDocs] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  // 上传相关
  const [uploadVisible, setUploadVisible] = useState(false);

  // 加载知识库信息
  const loadKnowledgeBase = async () => {
    if (!kbId) return;
    
    try {
      setLoading(true);
      const response = await kbApi.getKnowledgeBase(kbId);
      
      if (response.status === 'ok') {
        setKb(response.data);
      } else {
        message.error(response.msg || '获取知识库信息失败');
        navigate('/kb');
      }
    } catch (error) {
      console.error('加载知识库失败:', error);
      message.error('加载失败，请重试');
      navigate('/kb');
    } finally {
      setLoading(false);
    }
  };

  // 加载文档列表
  const loadDocuments = async (folderId: string | null = null, page: number = 1) => {
    if (!kbId) return;
    
    try {
      setDocumentsLoading(true);
      const response = await kbApi.getFolderDocuments(kbId, folderId, {
        page,
        page_size: pageSize,
      });
      
      if (response.status === 'ok') {
        setDocuments(response.data.items || []);
        setTotalDocs(response.data.total || 0);
      } else {
        message.error(response.msg || '获取文档列表失败');
        setDocuments([]);
        setTotalDocs(0);
      }
    } catch (error) {
      console.error('加载文档列表失败:', error);
      message.error('加载文档失败，请重试');
      setDocuments([]);
      setTotalDocs(0);
    } finally {
      setDocumentsLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    if (kbId) {
      loadKnowledgeBase();
      loadDocuments();
    }
  }, [kbId]);

  // 目录选择处理
  const handleFolderSelect = (folderId: string | null, folderInfo: KBFolder | null) => {
    setSelectedFolderId(folderId);
    setSelectedFolder(folderInfo);
    setCurrentPage(1);
    loadDocuments(folderId, 1);
    
    // 更新面包屑路径
    if (folderId === null) {
      setFolderPath(['根目录']);
    } else if (folderInfo) {
      // TODO: 构建完整路径，这里简化处理
      setFolderPath(['根目录', folderInfo.folder_name]);
    }
  };

  // 文档选择处理
  const handleDocumentSelect = (document: KBDocument) => {
    // TODO: 实现文档预览或详情
    message.info(`选中文档: ${document.file_name}`);
  };

  // 置顶/取消置顶文档
  const handlePinDocument = async (document: KBDocument) => {
    try {
      await kbApi.addDocumentToFolder(kbId!, selectedFolderId, {
        file_id: document.file_id,
        is_pinned: !document.is_pinned,
      });
      
      message.success(document.is_pinned ? '已取消置顶' : '已置顶');
      loadDocuments(selectedFolderId, currentPage);
    } catch (error) {
      console.error('置顶操作失败:', error);
      message.error('操作失败，请重试');
    }
  };

  // 删除文档
  const handleDeleteDocument = (document: KBDocument) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要从知识库中删除文档"${document.file_name}"吗？`,
      onOk: async () => {
        try {
          await kbApi.removeDocumentFromKB(kbId!, document.file_id);
          message.success('文档删除成功');
          loadDocuments(selectedFolderId, currentPage);
        } catch (error) {
          console.error('删除文档失败:', error);
          message.error('删除失败，请重试');
        }
      },
    });
  };

  // 获取处理状态文本
  const getProcessStatusText = (status: number) => {
    const statusMap = {
      0: '待处理',
      1: '处理中',
      2: '已完成',
      3: '处理失败',
    };
    return statusMap[status as keyof typeof statusMap] || '未知';
  };

  // 获取处理状态颜色
  const getProcessStatusColor = (status: number) => {
    const colorMap = {
      0: 'default',
      1: 'processing',
      2: 'success',
      3: 'error',
    };
    return colorMap[status as keyof typeof colorMap] || 'default';
  };

  // 文档表格列定义
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
      render: (size) => {
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
      },
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
      render: (status) => (
        <Tag color={getProcessStatusColor(status)}>
          {getProcessStatusText(status)}
        </Tag>
      ),
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
              onClick={() => handlePinDocument(record)}
            />
          </Tooltip>
          <Tooltip title="预览">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleDocumentSelect(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteDocument(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!kb) {
    return <div>知识库不存在</div>;
  }

  return (
    <div style={{ padding: '0 24px' }}>
      {/* 页面头部 */}
      <div style={{ marginBottom: 24 }}>
        <Space align="start" style={{ marginBottom: 16 }}>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/kb')}
          >
            返回
          </Button>
          <div>
            <Title level={3} style={{ margin: 0 }}>
              {kb.kb_name}
            </Title>
            <Space size="small" style={{ marginTop: 4 }}>
              <Tag color={VISIBILITY_COLORS[kb.visibility as keyof typeof VISIBILITY_COLORS]}>
                {VISIBILITY_TEXTS[kb.visibility as keyof typeof VISIBILITY_TEXTS]}
              </Tag>
              <Text type="secondary">
                {kb.doc_count} 个文档 · {kb.total_chunks} 个分块
              </Text>
            </Space>
          </div>
        </Space>
        
        {kb.kb_description && (
          <Text type="secondary">{kb.kb_description}</Text>
        )}
      </div>

      {/* 主要内容区域 */}
      <Row gutter={24} style={{ height: 'calc(100vh - 200px)' }}>
        {/* 左侧目录树 */}
        <Col xs={24} sm={24} md={8} lg={6} xl={5}>
          <KBFolderTree
            kbId={kbId!}
            onFolderSelect={handleFolderSelect}
            onDocumentSelect={handleDocumentSelect}
            selectedFolderId={selectedFolderId}
          />
        </Col>

        {/* 右侧文档列表 */}
        <Col xs={24} sm={24} md={16} lg={18} xl={19}>
          <Card
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <Breadcrumb>
                    {folderPath.map((path, index) => (
                      <Breadcrumb.Item key={index}>
                        <FolderOutlined />
                        {path}
                      </Breadcrumb.Item>
                    ))}
                  </Breadcrumb>
                  <Text type="secondary">({totalDocs} 个文档)</Text>
                </Space>
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={() => setUploadVisible(true)}
                >
                  上传文档
                </Button>
              </div>
            }
            style={{ height: '100%' }}
            bodyStyle={{ height: 'calc(100% - 57px)', padding: 0 }}
          >
            <Spin spinning={documentsLoading}>
              <Table
                columns={columns}
                dataSource={documents}
                rowKey="file_id"
                pagination={{
                  current: currentPage,
                  pageSize: pageSize,
                  total: totalDocs,
                  onChange: (page) => {
                    setCurrentPage(page);
                    loadDocuments(selectedFolderId, page);
                  },
                  showSizeChanger: false,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                }}
                scroll={{ y: 'calc(100vh - 350px)' }}
                size="small"
              />
            </Spin>
          </Card>
        </Col>
      </Row>

      {/* 上传文档弹窗 */}
      <Modal
        title="上传文档"
        open={uploadVisible}
        onCancel={() => setUploadVisible(false)}
        footer={null}
        width={600}
      >
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <Text type="secondary">
            文档上传功能开发中，请先通过智能体对话上传文档
          </Text>
        </div>
      </Modal>
    </div>
  );
};

export default KnowledgeBaseDetail;