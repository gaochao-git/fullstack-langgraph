/**
 * 知识库列表页面 - 左右分栏树形管理布局
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
  Empty
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
  FileAddOutlined
} from '@ant-design/icons';

import { KnowledgeBase, ListParams, VISIBILITY_OPTIONS, KB_TYPES } from './types/kb';
import { kbApi } from '@/services/kbApi';
import { KBCreateModal } from './components';

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

const KnowledgeBaseList: React.FC = () => {
  const navigate = useNavigate();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(100); // 增大页面大小，用于左侧列表显示
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterVisibility, setFilterVisibility] = useState<string>('');

  // 选中的知识库
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);

  // Modal状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);

  // 加载知识库列表
  const loadKnowledgeBases = async (params: ListParams = {}) => {
    try {
      setLoading(true);
      const requestParams = {
        page: currentPage,
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
  }, [currentPage, pageSize]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchText(value);
    setCurrentPage(1);
    loadKnowledgeBases({ page: 1, search: value });
  };

  // 筛选处理
  const handleFilterChange = () => {
    setCurrentPage(1);
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
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <Title level={3} style={{ margin: 0 }}>
            知识库管理
          </Title>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            创建知识库
          </Button>
        </div>
      </div>

      {/* 主要内容区域 - 左右分栏布局 */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        overflow: 'hidden',
        backgroundColor: '#f0f2f5'
      }}>
        {/* 左侧知识库树 */}
        <div style={{ 
          width: '300px', 
          backgroundColor: '#fff',
          borderRight: '1px solid #f0f0f0',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* 搜索和筛选 */}
          <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Search
                placeholder="搜索知识库"
                allowClear
                size="small"
                onSearch={handleSearch}
                onChange={(e) => setSearchText(e.target.value)}
                value={searchText}
              />
              <Space size="small" wrap>
                <Select
                  placeholder="类型"
                  allowClear
                  size="small"
                  style={{ width: 80 }}
                  onChange={(value) => {
                    setFilterType(value || '');
                    handleFilterChange();
                  }}
                  value={filterType || undefined}
                >
                  <Option value={KB_TYPES.GENERAL}>通用</Option>
                  <Option value={KB_TYPES.TECHNICAL}>技术</Option>
                  <Option value={KB_TYPES.FAQ}>问答</Option>
                  <Option value={KB_TYPES.TRAINING}>培训</Option>
                </Select>
                <Select
                  placeholder="可见性"
                  allowClear
                  size="small"
                  style={{ width: 80 }}
                  onChange={(value) => {
                    setFilterVisibility(value || '');
                    handleFilterChange();
                  }}
                  value={filterVisibility || undefined}
                >
                  <Option value={VISIBILITY_OPTIONS.PRIVATE}>私有</Option>
                  <Option value={VISIBILITY_OPTIONS.INTERNAL}>内部</Option>
                  <Option value={VISIBILITY_OPTIONS.PUBLIC}>公开</Option>
                </Select>
              </Space>
            </Space>
          </div>

          {/* 知识库列表 */}
          <div style={{ flex: 1, overflow: 'auto', padding: '8px' }}>
            <Spin spinning={loading}>
              {filteredKBs.length === 0 ? (
                <Empty
                  description="暂无知识库"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  style={{ padding: '40px 20px' }}
                >
                  <Button type="primary" onClick={() => setCreateModalVisible(true)}>
                    创建知识库
                  </Button>
                </Empty>
              ) : (
                <div>
                  {filteredKBs.map((kb) => (
                    <Card
                      key={kb.kb_id}
                      size="small"
                      hoverable
                      style={{ 
                        marginBottom: 8,
                        cursor: 'pointer',
                        borderColor: selectedKB?.kb_id === kb.kb_id ? '#1890ff' : undefined,
                        backgroundColor: selectedKB?.kb_id === kb.kb_id ? '#f6ffed' : undefined
                      }}
                      bodyStyle={{ padding: '12px' }}
                      onClick={() => setSelectedKB(kb)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Avatar
                          size={32}
                          style={{ 
                            backgroundColor: KB_TYPE_COLORS[kb.kb_type as keyof typeof KB_TYPE_COLORS] || '#1677ff'
                          }}
                          icon={KB_TYPE_ICONS[kb.kb_type as keyof typeof KB_TYPE_ICONS] || <BookOutlined />}
                        />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text strong style={{ fontSize: 14 }} ellipsis>
                              {kb.kb_name}
                            </Text>
                            <Tag 
                              size="small" 
                              color={VISIBILITY_COLORS[kb.visibility as keyof typeof VISIBILITY_COLORS]}
                            >
                              {VISIBILITY_TEXTS[kb.visibility as keyof typeof VISIBILITY_TEXTS]}
                            </Tag>
                          </div>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {kb.doc_count} 文档 · {kb.total_chunks} 分块
                          </Text>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Spin>
          </div>
        </div>

        {/* 右侧详情管理区域 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#fff' }}>
          {selectedKB ? (
            <>
              {/* 选中知识库的详情头部 */}
              <div style={{
                padding: '16px 24px',
                borderBottom: '1px solid #f0f0f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <Space>
                    <Avatar
                      size={40}
                      style={{ 
                        backgroundColor: KB_TYPE_COLORS[selectedKB.kb_type as keyof typeof KB_TYPE_COLORS] || '#1677ff'
                      }}
                      icon={KB_TYPE_ICONS[selectedKB.kb_type as keyof typeof KB_TYPE_ICONS] || <BookOutlined />}
                    />
                    <div>
                      <Title level={4} style={{ margin: 0 }}>
                        {selectedKB.kb_name}
                      </Title>
                      <Text type="secondary">
                        {selectedKB.doc_count} 个文档 · {selectedKB.total_chunks} 个分块
                      </Text>
                    </div>
                  </Space>
                </div>
                <Space>
                  <Button
                    icon={<FolderOutlined />}
                    onClick={() => handleManageContent(selectedKB)}
                    disabled={!['read', 'write', 'admin', 'owner'].includes(selectedKB.user_permission || '')}
                  >
                    管理内容
                  </Button>
                  <Dropdown
                    menu={{
                      items: getActionItems(selectedKB).map(item => ({
                        key: item.key,
                        icon: item.icon,
                        label: item.label,
                        disabled: item.disabled,
                        danger: item.danger,
                        onClick: item.onClick,
                      }))
                    }}
                    trigger={['click']}
                  >
                    <Button icon={<MoreOutlined />} />
                  </Dropdown>
                </Space>
              </div>

              {/* 知识库详细信息 */}
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
                            {Math.floor(Math.random() * 100)}%
                          </div>
                          <div>使用率</div>
                        </div>
                      </Col>
                    </Row>
                  </Card>
                </Space>
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
        onSuccess={() => {
          loadKnowledgeBases();
        }}
        initialData={selectedKB || undefined}
      />
    </div>
  );
};

export default KnowledgeBaseList;