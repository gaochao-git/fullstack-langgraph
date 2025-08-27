/**
 * 知识库管理页面 - 左右分栏树形管理布局
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Typography,
  Tag,
  Avatar,
  Button,
  Space,
  Progress,
  Input,
  Select,
  Dropdown,
  Modal,
  message,
  Spin,
  Empty,
  Upload,
  List,
  Breadcrumb,
  Divider,
  Table,
  Tooltip
} from 'antd';
import {
  BookOutlined,
  PlusOutlined,
  FileTextOutlined,
  QuestionCircleOutlined,
  ReadOutlined,
  SearchOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UsergroupAddOutlined,
  FolderOutlined,
  FileAddOutlined,
  FolderAddOutlined,
  UploadOutlined,
  InboxOutlined,
  CloseOutlined,
  PushpinOutlined,
  PushpinFilled
} from '@ant-design/icons';

import { KnowledgeBase, ListParams, VISIBILITY_OPTIONS, KB_TYPES } from './types/kb';
import { kbApi } from '@/services/kbApi';
import { KBCreateModal } from './components';
import KBTreeStructure from './components/KBTreeStructure';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;
const { Option } = Select;

// 知识库类型图标映射
const KB_TYPE_ICONS = {
  [KB_TYPES.GENERAL]: <BookOutlined />,
  [KB_TYPES.TECHNICAL]: <FileTextOutlined />,
  [KB_TYPES.FAQ]: <QuestionCircleOutlined />,
  [KB_TYPES.TRAINING]: <ReadOutlined />,
};

// 知识库类型颜色映射
const KB_TYPE_COLORS = {
  [KB_TYPES.GENERAL]: '#1677ff',
  [KB_TYPES.TECHNICAL]: '#52c41a',
  [KB_TYPES.FAQ]: '#fa8c16',
  [KB_TYPES.TRAINING]: '#722ed1',
};

// 可见性标签颜色映射
const VISIBILITY_COLORS = {
  [VISIBILITY_OPTIONS.PRIVATE]: 'default',
  [VISIBILITY_OPTIONS.INTERNAL]: 'processing',
  [VISIBILITY_OPTIONS.PUBLIC]: 'success',
};

// 可见性标签文本映射
const VISIBILITY_TEXTS = {
  [VISIBILITY_OPTIONS.PRIVATE]: '私有',
  [VISIBILITY_OPTIONS.INTERNAL]: '内部',
  [VISIBILITY_OPTIONS.PUBLIC]: '公开',
};

const KnowledgeManagement: React.FC = () => {
  const navigate = useNavigate();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [kbCurrentPage, setKbCurrentPage] = useState(1); // 知识库列表分页
  const [pageSize] = useState(100); // 增大页面大小，用于左侧列表显示
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterVisibility, setFilterVisibility] = useState<string>('');

  // 选中的知识库和目录
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null); // 选中的节点（知识库或目录）
  const [currentPath, setCurrentPath] = useState<string[]>([]); // 当前路径面包屑
  
  // Modal状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [uploadVisible, setUploadVisible] = useState(false);
  
  // 上传相关状态
  const [fileList, setFileList] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  
  // 文档列表相关状态
  const [documents, setDocuments] = useState<any[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsTotal, setDocumentsTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [docPageSize] = useState(20);

  // 加载知识库列表
  const loadKnowledgeBases = async (params: ListParams = {}) => {
    try {
      setLoading(true);
      const requestParams = {
        page: kbCurrentPage,
        page_size: pageSize,
        search: searchText || undefined,
        ...params,
      };

      const response = await kbApi.getKnowledgeBases(requestParams);

      if (response.status === 'ok') {
        const { items, total: totalCount } = response.data;
        setKnowledgeBases(items || []);
        setTotal(totalCount || 0);
      } else {
        message.error(response.msg || '获取知识库列表失败');
        setKnowledgeBases([]);
        setTotal(0);
      }
    } catch (error) {
      console.error('加载知识库列表失败:', error);
      message.error('加载失败，请重试');
      setKnowledgeBases([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    loadKnowledgeBases();
  }, [kbCurrentPage, pageSize]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchText(value);
    setKbCurrentPage(1);
    loadKnowledgeBases({ page: 1, search: value });
  };

  // 筛选处理
  const handleFilterChange = () => {
    setKbCurrentPage(1);
    loadKnowledgeBases({ page: 1 });
  };

  // 删除知识库
  const handleDelete = (kb: KnowledgeBase) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除知识库"${kb.kb_name}"吗？此操作不可恢复。`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await kbApi.deleteKnowledgeBase(kb.kb_id);
          if (response.status === 'ok') {
            message.success('知识库删除成功');
            loadKnowledgeBases();
            // 如果删除的是当前选中的知识库，清空选中状态
            if (selectedKB?.kb_id === kb.kb_id) {
              setSelectedKB(null);
            }
          } else {
            message.error(response.msg || '删除失败');
          }
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败，请重试');
        }
      },
    });
  };

  // 编辑知识库
  const handleEdit = (kb: KnowledgeBase) => {
    setSelectedKB(kb);
    setEditModalVisible(true);
  };

  // 处理树节点选择（知识库、目录或文档）
  const handleKBSelect = (kb: KnowledgeBase | null) => {
    setSelectedKB(kb);
    setSelectedNode(null); // 清空选中的具体节点，只选中知识库
    setCurrentPath(kb ? [kb.kb_name] : []);
  };

  // 加载文档列表
  const loadDocuments = async (kbId: string, folderId: string | null = null, page: number = 1) => {
    try {
      setDocumentsLoading(true);
      const response = await kbApi.getFolderDocuments(kbId, folderId, {
        page,
        page_size: docPageSize,
      });
      
      if (response.status === 'ok') {
        setDocuments(response.data.items || []);
        setDocumentsTotal(response.data.total || 0);
      } else {
        message.error(response.msg || '获取文档列表失败');
        setDocuments([]);
        setDocumentsTotal(0);
      }
    } catch (error) {
      console.error('加载文档列表失败:', error);
      message.error('加载文档失败，请重试');
      setDocuments([]);
      setDocumentsTotal(0);
    } finally {
      setDocumentsLoading(false);
    }
  };

  // 处理目录或文档选择（从树组件回调中获取）
  const handleNodeSelect = (node: any, path: string[]) => {
    if (node.type === 'kb') {
      handleKBSelect(node.data as KnowledgeBase);
    } else {
      // 选中目录或文档时，同时选中对应的知识库
      const kb = knowledgeBases.find(k => k.kb_id === node.kbId);
      setSelectedKB(kb || null);
      setSelectedNode(node);
      setCurrentPath(path);
      setCurrentPage(1);
      
      // 如果是目录，加载该目录下的文档
      if (node.type === 'folder' && node.kbId) {
        const folderId = node.data?.folder_id || null;
        loadDocuments(node.kbId, folderId, 1);
      } else if (node.type === 'document') {
        // 选中文档时清空列表或显示该文档的详情
        setDocuments([]);
        setDocumentsTotal(0);
      }
    }
  };

  // 文件上传处理
  const handleUpload = () => {
    if (!selectedKB) {
      message.warning('请先选择一个知识库');
      return;
    }
    setUploadVisible(true);
  };

  // 上传文件到知识库
  const uploadFiles = async () => {
    if (!selectedKB || fileList.length === 0) {
      message.warning('请选择要上传的文件');
      return;
    }
    
    try {
      setUploading(true);
      
      // 确定目标目录ID
      const folderId = selectedNode?.type === 'folder' 
        ? (selectedNode.data?.folder_id || null) 
        : null;
      
      // 这里应该调用实际的上传API
      // 暂时模拟上传过程
      for (let i = 0; i < fileList.length; i++) {
        const file = fileList[i];
        // TODO: 调用实际的文件上传API
        // await kbApi.uploadDocument(selectedKB.kb_id, file, folderId);
        await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟上传延迟
      }
      
      message.success(`成功上传 ${fileList.length} 个文件到${folderId ? '指定目录' : '根目录'}`);
      setFileList([]);
      setUploadVisible(false);
      
      // 上传完成后刷新文档列表
      if (selectedNode?.type === 'folder' && selectedNode.kbId) {
        loadDocuments(selectedNode.kbId, selectedNode.data?.folder_id || null, currentPage);
      }
      
    } catch (error) {
      console.error('上传失败:', error);
      message.error('上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  // 置顶/取消置顶文档
  const handlePinDocument = async (document: any) => {
    if (!selectedKB) return;
    
    try {
      await kbApi.addDocumentToFolder(selectedKB.kb_id, selectedNode?.data?.folder_id || null, {
        file_id: document.file_id,
        is_pinned: !document.is_pinned,
      });
      
      message.success(document.is_pinned ? '已取消置顶' : '已置顶');
      // 重新加载文档列表
      if (selectedNode?.type === 'folder' && selectedNode.kbId) {
        loadDocuments(selectedNode.kbId, selectedNode.data?.folder_id || null, currentPage);
      }
    } catch (error) {
      console.error('置顶操作失败:', error);
      message.error('操作失败，请重试');
    }
  };

  // 删除文档
  const handleDeleteDocument = (document: any) => {
    if (!selectedKB) return;
    
    Modal.confirm({
      title: '确认删除',
      content: `确定要从知识库中删除文档"${document.file_name}"吗？`,
      onOk: async () => {
        try {
          await kbApi.removeDocumentFromKB(selectedKB.kb_id, document.file_id);
          message.success('文档删除成功');
          // 重新加载文档列表
          if (selectedNode?.type === 'folder' && selectedNode.kbId) {
            loadDocuments(selectedNode.kbId, selectedNode.data?.folder_id || null, currentPage);
          }
        } catch (error) {
          console.error('删除文档失败:', error);
          message.error('删除失败，请重试');
        }
      },
    });
  };

  // 文档表格列定义
  const documentColumns = [
    {
      title: '文档名称',
      dataIndex: 'file_name',
      key: 'file_name',
      render: (text: string, record: any) => (
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
      render: (size: number) => {
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
      render: (type: string) => <Tag>{type?.toUpperCase()}</Tag>,
    },
    {
      title: '处理状态',
      dataIndex: 'process_status',
      key: 'process_status',
      width: 120,
      render: (status: number) => {
        const statusMap = {
          0: { text: '待处理', color: 'default' },
          1: { text: '处理中', color: 'processing' },
          2: { text: '已完成', color: 'success' },
          3: { text: '处理失败', color: 'error' },
        };
        const statusInfo = statusMap[status as keyof typeof statusMap] || { text: '未知', color: 'default' };
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>;
      },
    },
    {
      title: '添加时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: any) => (
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
              onClick={() => message.info(`预览文档: ${record.file_name}`)}
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

  // 查看详情（跳转到知识库详情页）
  const handleView = (kb: KnowledgeBase) => {
    // TODO: 实现跳转到知识库详情页
    message.info('知识库详情页开发中');
  };

  // 管理内容（文件和目录管理）
  const handleManageContent = (kb: KnowledgeBase) => {
    navigate(`/kb/${kb.kb_id}`);
  };

  // 管理权限
  const handleManagePermissions = (kb: KnowledgeBase) => {
    // TODO: 实现权限管理弹窗
    message.info('权限管理功能开发中');
  };

  // 操作菜单项
  const getActionItems = (kb: KnowledgeBase) => [
    {
      key: 'manage',
      icon: <FolderOutlined />,
      label: '管理内容',
      onClick: () => handleManageContent(kb),
      disabled: !['read', 'write', 'admin', 'owner'].includes(kb.user_permission || ''),
    },
    {
      key: 'view',
      icon: <EyeOutlined />,
      label: '查看详情',
      onClick: () => handleView(kb),
    },
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑',
      onClick: () => handleEdit(kb),
      disabled: !['admin', 'owner'].includes(kb.user_permission || ''),
    },
    {
      key: 'permissions',
      icon: <UsergroupAddOutlined />,
      label: '权限管理',
      onClick: () => handleManagePermissions(kb),
      disabled: !['admin', 'owner'].includes(kb.user_permission || ''),
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: '删除',
      onClick: () => handleDelete(kb),
      disabled: kb.user_permission !== 'owner',
      danger: true,
    },
  ];

  // 过滤知识库
  const filteredKBs = knowledgeBases.filter(kb => {
    if (filterType && kb.kb_type !== filterType) return false;
    if (filterVisibility && kb.visibility !== filterVisibility) return false;
    return true;
  });

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 页面头部 */}
      <div style={{ 
        padding: '16px 24px', 
        borderBottom: '1px solid #f0f0f0',
        backgroundColor: '#fff'
      }}>
        <Title level={3} style={{ margin: 0 }}>
          知识库管理
        </Title>
      </div>

      {/* 主要内容区域 - 左右分栏布局 */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        overflow: 'hidden',
        backgroundColor: '#f0f2f5'
      }}>
        {/* 左侧知识库树形目录结构 */}
        <div style={{ 
          width: '300px', 
          backgroundColor: '#fff',
          borderRight: '1px solid #f0f0f0',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* 顶部标题栏 */}
          <div style={{
            padding: '12px 16px',
            borderBottom: '1px solid #f0f0f0',
            backgroundColor: '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span style={{ fontWeight: 500 }}>知识库目录</span>
            <Button
              type="primary"
              size="small"
              icon={<FolderAddOutlined />}
              onClick={() => setCreateModalVisible(true)}
            >
              新建库
            </Button>
          </div>

          {/* 搜索框 */}
          <div style={{ padding: '8px 16px', borderBottom: '1px solid #f0f0f0' }}>
            <Search
              placeholder="搜索目录或文档"
              allowClear
              size="small"
              onSearch={handleSearch}
              onChange={(e) => setSearchText(e.target.value)}
              value={searchText}
            />
          </div>

          {/* 树形目录结构 */}
          <KBTreeStructure 
            knowledgeBases={filteredKBs}
            loading={loading}
            onKBSelect={handleKBSelect}
            selectedKB={selectedKB}
            onCreateKB={() => setCreateModalVisible(true)}
            onEditKB={handleEdit}
            onDeleteKB={handleDelete}
            onManageContent={handleManageContent}
            onRefresh={loadKnowledgeBases}
            onNodeSelect={handleNodeSelect}
            searchText={searchText}
          />
        </div>

        {/* 右侧详情管理区域 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#fff' }}>
          {selectedKB ? (
            <>
              {/* 顶部面包屑和操作区域 */}
              <div style={{
                padding: '16px 24px',
                borderBottom: '1px solid #f0f0f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  {/* 当前路径面包屑 */}
                  <Space direction="vertical" size={4}>
                    <Breadcrumb>
                      {currentPath.length > 0 ? (
                        currentPath.map((path, index) => (
                          <Breadcrumb.Item key={index}>
                            {index === 0 ? (
                              <BookOutlined style={{ marginRight: 4 }} />
                            ) : (
                              <FolderOutlined style={{ marginRight: 4 }} />
                            )}
                            {path}
                          </Breadcrumb.Item>
                        ))
                      ) : (
                        <Breadcrumb.Item>
                          <BookOutlined style={{ marginRight: 4 }} />
                          {selectedKB.kb_name}
                        </Breadcrumb.Item>
                      )}
                    </Breadcrumb>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {selectedNode 
                        ? (selectedNode.type === 'folder' ? '目录' : selectedNode.type === 'document' ? '文档' : '知识库')
                        : '知识库'}
                      {selectedKB && ` · ${selectedKB.doc_count} 个文档 · ${selectedKB.total_chunks} 个分块`}
                    </Text>
                  </Space>
                </div>
                <Space>
                  {/* 只保留上传功能，其他操作都在左侧树中完成 */}
                  {selectedNode?.type === 'folder' && (
                    <Button
                      type="primary"
                      icon={<UploadOutlined />}
                      onClick={handleUpload}
                    >
                      上传到此目录
                    </Button>
                  )}
                  {selectedKB && !selectedNode && (
                    <Button
                      icon={<UploadOutlined />}
                      onClick={handleUpload}
                    >
                      上传文档
                    </Button>
                  )}
                </Space>
              </div>

              {/* 内容区域 - 根据选中节点类型显示不同内容 */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {selectedNode?.type === 'folder' ? (
                  // 选中目录时显示文档列表表格
                  <div style={{ flex: 1, padding: '0', overflow: 'hidden' }}>
                    <Spin spinning={documentsLoading}>
                      <Table
                        columns={documentColumns}
                        dataSource={documents}
                        rowKey="file_id"
                        pagination={{
                          current: currentPage,
                          pageSize: docPageSize,
                          total: documentsTotal,
                          onChange: (page) => {
                            setCurrentPage(page);
                            if (selectedNode?.kbId) {
                              loadDocuments(selectedNode.kbId, selectedNode.data?.folder_id || null, page);
                            }
                          },
                          showSizeChanger: false,
                          showQuickJumper: true,
                          showTotal: (total, range) => 
                            `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                        }}
                        scroll={{ y: 'calc(100vh - 200px)' }}
                        size="middle"
                        locale={{
                          emptyText: (
                            <div style={{ padding: '40px', textAlign: 'center' }}>
                              <InboxOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                              <div style={{ marginBottom: 16 }}>
                                <Text type="secondary">该目录暂无文档</Text>
                              </div>
                              <Button 
                                type="primary" 
                                icon={<UploadOutlined />}
                                onClick={handleUpload}
                              >
                                上传文档
                              </Button>
                            </div>
                          )
                        }}
                      />
                    </Spin>
                  </div>
                ) : selectedNode?.type === 'document' ? (
                  // 选中文档时显示文档详情
                  <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                      <Card title="文档信息" size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text strong>文档名称：</Text>
                            <Text style={{ marginLeft: 8 }}>{selectedNode.title}</Text>
                          </div>
                          <div>
                            <Text strong>所属知识库：</Text>
                            <Text style={{ marginLeft: 8 }}>{selectedKB.kb_name}</Text>
                          </div>
                          <div>
                            <Text strong>文档类型：</Text>
                            <Tag style={{ marginLeft: 8 }}>文档</Tag>
                          </div>
                        </Space>
                      </Card>
                    </Space>
                  </div>
                ) : (
                  // 选中知识库时显示基本信息（默认）
                  <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                      {/* 基本信息 */}
                      <Card title="基本信息" size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text strong>描述：</Text>
                            <Paragraph style={{ margin: '4px 0' }}>
                              {selectedKB.kb_description || '暂无描述'}
                            </Paragraph>
                          </div>
                          <div>
                            <Text strong>类型：</Text>
                            <Tag style={{ marginLeft: 8 }}>
                              {selectedKB.kb_type === KB_TYPES.GENERAL ? '通用' :
                               selectedKB.kb_type === KB_TYPES.TECHNICAL ? '技术' :
                               selectedKB.kb_type === KB_TYPES.FAQ ? '问答' :
                               selectedKB.kb_type === KB_TYPES.TRAINING ? '培训' : selectedKB.kb_type}
                            </Tag>
                          </div>
                          <div>
                            <Text strong>创建时间：</Text>
                            <Text style={{ marginLeft: 8 }}>
                              {new Date(selectedKB.create_time).toLocaleString()}
                            </Text>
                          </div>
                          <div>
                            <Text strong>更新时间：</Text>
                            <Text style={{ marginLeft: 8 }}>
                              {new Date(selectedKB.update_time).toLocaleString()}
                            </Text>
                          </div>
                        </Space>
                      </Card>

                      {/* 标签 */}
                      {selectedKB.tags && selectedKB.tags.length > 0 && (
                        <Card title="标签" size="small">
                          <Space wrap>
                            {selectedKB.tags.map((tag, index) => (
                              <Tag key={index}>{tag}</Tag>
                            ))}
                          </Space>
                        </Card>
                      )}

                      {/* 统计信息 */}
                      <Card title="统计信息" size="small">
                        <Row gutter={[16, 16]}>
                          <Col span={8}>
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                                {selectedKB.doc_count}
                              </div>
                              <div>文档数量</div>
                            </div>
                          </Col>
                          <Col span={8}>
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                                {selectedKB.total_chunks}
                              </div>
                              <div>分块数量</div>
                            </div>
                          </Col>
                          <Col span={8}>
                            <div style={{ textAlign: 'center' }}>
                              <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
                                25%
                              </div>
                              <div>使用率</div>
                            </div>
                          </Col>
                        </Row>
                      </Card>
                    </Space>
                  </div>
                )}
              </div>
            </>
          ) : (
            /* 未选中知识库时的提示 */
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#999'
            }}>
              <div style={{ textAlign: 'center' }}>
                <BookOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>请在左侧选择一个知识库进行查看或编辑</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 创建知识库弹窗 */}
      <KBCreateModal
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onSuccess={() => {
          loadKnowledgeBases();
        }}
      />

      {/* 编辑知识库弹窗 */}
      <KBCreateModal
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedKB(null);
        }}
        onSuccess={(updatedKB) => {
          // 立即更新选中的知识库状态
          if (updatedKB) {
            setSelectedKB(updatedKB);
          }
          // 重新加载列表数据
          loadKnowledgeBases();
          // 关闭弹窗
          setEditModalVisible(false);
        }}
        initialData={selectedKB || undefined}
      />

      {/* 上传文档弹窗 */}
      <Modal
        title={
          <Space>
            <UploadOutlined />
            上传文档
            {selectedNode?.type === 'folder' && (
              <Text type="secondary">到目录 "{selectedNode.title}"</Text>
            )}
          </Space>
        }
        open={uploadVisible}
        onOk={uploadFiles}
        onCancel={() => {
          setUploadVisible(false);
          setFileList([]);
        }}
        width={600}
        okText="开始上传"
        cancelText="取消"
        confirmLoading={uploading}
        okButtonProps={{ disabled: fileList.length === 0 }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">
            上传文档到知识库 "{selectedKB?.kb_name}"
            {selectedNode?.type === 'folder' && ` 的 "${selectedNode.title}" 目录`}
          </Text>
        </div>

        <Upload.Dragger
          multiple
          accept=".pdf,.docx,.txt,.md"
          fileList={fileList}
          onChange={({ fileList }) => setFileList(fileList)}
          beforeUpload={() => false} // 禁止自动上传
          onRemove={(file) => {
            setFileList(fileList.filter(f => f.uid !== file.uid));
          }}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传。支持格式：PDF、Word文档、文本文件、Markdown
          </p>
        </Upload.Dragger>

        {fileList.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Text strong>待上传文件 ({fileList.length})：</Text>
            <List
              size="small"
              style={{ marginTop: 8 }}
              dataSource={fileList}
              renderItem={(file) => (
                <List.Item
                  actions={[
                    <Button
                      type="text"
                      size="small"
                      icon={<CloseOutlined />}
                      onClick={() => setFileList(fileList.filter(f => f.uid !== file.uid))}
                    />
                  ]}
                >
                  <List.Item.Meta
                    avatar={<FileTextOutlined />}
                    title={file.name}
                    description={`${(file.size! / 1024 / 1024).toFixed(2)} MB`}
                  />
                </List.Item>
              )}
            />
          </div>
        )}

        {uploading && (
          <div style={{ marginTop: 16 }}>
            <Progress percent={50} status="active" />
            <Text type="secondary">正在上传文档...</Text>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default KnowledgeManagement;