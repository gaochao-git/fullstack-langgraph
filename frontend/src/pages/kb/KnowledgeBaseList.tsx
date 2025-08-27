/**
 * 知识库列表页面
 */

import React, { useState, useEffect } from 'react';
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
  UsergroupAddOutlined
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
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(12);
  const [searchText, setSearchText] = useState('');
  const [filterType, setFilterType] = useState<string>('');
  const [filterVisibility, setFilterVisibility] = useState<string>('');

  // Modal状态
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);

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
        setKnowledgeBases(response.data.items || []);
        setTotal(response.data.total || 0);
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
  }, [currentPage, searchText]);

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchText(value);
    setCurrentPage(1);
  };

  // 筛选处理
  const handleFilterChange = () => {
    setCurrentPage(1);
    loadKnowledgeBases();
  };

  // 删除知识库
  const handleDelete = async (kb: KnowledgeBase) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除知识库"${kb.kb_name}"吗？此操作不可恢复。`,
      onOk: async () => {
        try {
          const response = await kbApi.deleteKnowledgeBase(kb.kb_id);
          if (response.status === 'ok') {
            message.success('删除成功');
            loadKnowledgeBases();
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

  // 管理权限
  const handleManagePermissions = (kb: KnowledgeBase) => {
    // TODO: 实现权限管理弹窗
    message.info('权限管理功能开发中');
  };

  // 操作菜单项
  const getActionItems = (kb: KnowledgeBase) => [
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
    <div>
      {/* 页面头部 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <Title level={3} style={{ margin: 0 }}>
            知识库管理
          </Title>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          创建知识库
        </Button>
      </div>

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="middle" wrap>
          <Search
            placeholder="搜索知识库名称或描述"
            allowClear
            style={{ width: 300 }}
            onSearch={handleSearch}
            enterButton={<SearchOutlined />}
          />
          
          <Select
            placeholder="知识库类型"
            style={{ width: 150 }}
            allowClear
            value={filterType || undefined}
            onChange={(value) => {
              setFilterType(value || '');
              handleFilterChange();
            }}
          >
            <Option value={KB_TYPES.GENERAL}>通用知识库</Option>
            <Option value={KB_TYPES.TECHNICAL}>技术文档</Option>
            <Option value={KB_TYPES.FAQ}>常见问题</Option>
            <Option value={KB_TYPES.TRAINING}>培训资料</Option>
          </Select>

          <Select
            placeholder="可见性"
            style={{ width: 120 }}
            allowClear
            value={filterVisibility || undefined}
            onChange={(value) => {
              setFilterVisibility(value || '');
              handleFilterChange();
            }}
          >
            <Option value={VISIBILITY_OPTIONS.PRIVATE}>私有</Option>
            <Option value={VISIBILITY_OPTIONS.INTERNAL}>内部</Option>
            <Option value={VISIBILITY_OPTIONS.PUBLIC}>公开</Option>
          </Select>

          <Text type="secondary">
            共 {total} 个知识库
          </Text>
        </Space>
      </Card>

      {/* 知识库列表 */}
      <Spin spinning={loading}>
        {filteredKBs.length === 0 ? (
          <Empty
            description="暂无知识库"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => setCreateModalVisible(true)}>
              创建第一个知识库
            </Button>
          </Empty>
        ) : (
          <Row gutter={[24, 24]}>
            {filteredKBs.map((kb) => (
              <Col key={kb.kb_id} xs={24} sm={12} lg={8} xl={6}>
                <Card
                  hoverable
                  actions={[
                    <Dropdown
                      key="actions"
                      menu={{
                        items: getActionItems(kb).map(item => ({
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
                      <Button type="text" icon={<MoreOutlined />} />
                    </Dropdown>
                  ]}
                >
                  <Card.Meta
                    avatar={
                      <Avatar
                        size={48}
                        style={{ 
                          backgroundColor: KB_TYPE_COLORS[kb.kb_type as keyof typeof KB_TYPE_COLORS] || '#1677ff'
                        }}
                        icon={KB_TYPE_ICONS[kb.kb_type as keyof typeof KB_TYPE_ICONS] || <BookOutlined />}
                      />
                    }
                    title={
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Text strong style={{ fontSize: 16 }}>
                            {kb.kb_name}
                          </Text>
                          <Tag color={VISIBILITY_COLORS[kb.visibility as keyof typeof VISIBILITY_COLORS]}>
                            {VISIBILITY_TEXTS[kb.visibility as keyof typeof VISIBILITY_TEXTS]}
                          </Tag>
                        </div>
                      </Space>
                    }
                    description={
                      <div>
                        <Paragraph 
                          ellipsis={{ rows: 2 }} 
                          style={{ fontSize: 12, marginBottom: 12, minHeight: 32 }}
                        >
                          {kb.kb_description || '暂无描述'}
                        </Paragraph>
                        
                        {/* 标签 */}
                        {kb.tags && kb.tags.length > 0 && (
                          <div style={{ marginBottom: 12 }}>
                            <Space size={[4, 4]} wrap>
                              {kb.tags.slice(0, 3).map((tag, index) => (
                                <Tag key={index} size="small">
                                  {tag}
                                </Tag>
                              ))}
                              {kb.tags.length > 3 && (
                                <Tag size="small">+{kb.tags.length - 3}</Tag>
                              )}
                            </Space>
                          </div>
                        )}

                        {/* 统计信息 */}
                        <div style={{ marginBottom: 12 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            文档数量: {kb.doc_count}
                          </Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            分块数量: {kb.total_chunks}
                          </Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            更新时间: {new Date(kb.update_time).toLocaleDateString()}
                          </Text>
                        </div>

                        {/* 权限标识 */}
                        {kb.user_permission && (
                          <div style={{ marginBottom: 8 }}>
                            <Tag size="small" color="blue">
                              {kb.user_permission === 'owner' ? '所有者' : 
                               kb.user_permission === 'admin' ? '管理员' :
                               kb.user_permission === 'write' ? '编辑' : '只读'}
                            </Tag>
                          </div>
                        )}

                        {/* 使用率（模拟数据） */}
                        <div>
                          <Text type="secondary" style={{ fontSize: 12, marginBottom: 4, display: 'block' }}>
                            使用活跃度
                          </Text>
                          <Progress 
                            percent={Math.floor(Math.random() * 100)} 
                            size="small" 
                            strokeColor="#52c41a"
                          />
                        </div>
                      </div>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>

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