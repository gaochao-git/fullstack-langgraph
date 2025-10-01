/**
 * 系统记忆查看器组件
 */

import React, { useState, useEffect } from 'react';
import { 
  Card,
  Table,
  Select,
  Input,
  Button,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Typography,
  Modal,
  Form,
  message,
  Empty
} from 'antd';
import { 
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  DatabaseOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';

import { memoryApi, Memory } from '../../../services/memoryApi';

const { Option } = Select;
const { Search } = Input;
const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface SystemMemoryViewerProps {
  namespaces: Record<string, string>;
  onMemoryChange: () => void;
}

/**
 * 系统记忆查看器组件
 */
const SystemMemoryViewer: React.FC<SystemMemoryViewerProps> = ({
  namespaces,
  onMemoryChange
}) => {
  const [loading, setLoading] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [selectedNamespace, setSelectedNamespace] = useState<string>('');
  const [searchParams, setSearchParams] = useState({
    user_id: '',
    system_id: ''
  });
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [viewingMemory, setViewingMemory] = useState<Memory | null>(null);

  /**
   * 初始化
   */
  useEffect(() => {
    // 默认选择第一个命名空间
    const firstNamespace = Object.keys(namespaces)[0];
    if (firstNamespace) {
      setSelectedNamespace(firstNamespace);
    }
  }, [namespaces]);

  /**
   * 监听命名空间变化，自动加载记忆
   */
  useEffect(() => {
    if (selectedNamespace) {
      loadMemories();
    }
  }, [selectedNamespace]);

  /**
   * 加载指定命名空间的记忆
   */
  const loadMemories = async () => {
    if (!selectedNamespace) return;

    setLoading(true);
    try {
      const params: any = {};
      if (searchParams.user_id) {
        params.user_id = searchParams.user_id;
      }
      if (searchParams.system_id) {
        params.system_id = searchParams.system_id;
      }

      const response = await memoryApi.listMemories(selectedNamespace, params);
      if (response.status === 'ok') {
        setMemories(response.data || []);
      }
    } catch (error) {
      console.error('加载系统记忆失败:', error);
      message.error('加载系统记忆数据失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 查看记忆详情
   */
  const viewMemoryDetail = (memory: Memory) => {
    setViewingMemory(memory);
    setViewModalVisible(true);
  };

  /**
   * 处理搜索参数变化
   */
  const handleSearchParamChange = (field: string, value: string) => {
    setSearchParams(prev => ({
      ...prev,
      [field]: value
    }));
  };

  /**
   * 表格列定义
   */
  const columns = [
    {
      title: '记忆内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string, record: Memory) => (
        <div>
          <Paragraph ellipsis={{ rows: 2, expandable: true }}>
            {text}
          </Paragraph>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => viewMemoryDetail(record)}
          >
            查看详情
          </Button>
        </div>
      ),
    },
    {
      title: '相关性分数',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      render: (score: number) => (
        score !== undefined ? (
          <Tag color={score < 0.3 ? 'green' : score < 0.6 ? 'orange' : 'red'}>
            {score.toFixed(3)}
          </Tag>
        ) : '-'
      ),
    },
    {
      title: '元数据',
      dataIndex: 'metadata',
      key: 'metadata',
      width: 250,
      render: (metadata: Record<string, any>) => (
        <Space direction="vertical" size="small">
          {Object.entries(metadata).slice(0, 3).map(([key, value]) => (
            <Tag key={key} color="blue" style={{ fontSize: '11px' }}>
              {key}: {String(value).substring(0, 20)}
            </Tag>
          ))}
          {Object.keys(metadata).length > 3 && (
            <Text type="secondary" style={{ fontSize: '11px' }}>
              +{Object.keys(metadata).length - 3} 更多...
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (text: string) => text ? new Date(text).toLocaleDateString() : '-',
    }
  ];

  /**
   * 获取命名空间说明
   */
  const getNamespaceDescription = (namespace: string) => {
    const descriptions: Record<string, string> = {
      'system_topology': '系统拓扑结构和架构信息',
      'service_dependencies': '服务间的依赖关系',
      'deployment_info': '系统部署和配置信息',
      'business_flows': '业务流程和规则',
      'sla_requirements': 'SLA要求和指标',
      'critical_services': '关键服务清单',
      'incident_history': '历史故障案例和解决方案',
      'solution_patterns': '通用解决方案模式',
      'runbooks': '运维操作手册',
      'best_practices': '最佳实践经验'
    };
    return descriptions[namespace] || '系统相关知识';
  };

  return (
    <div>
      {/* 搜索和筛选区域 */}
      <Card size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>记忆类型</Text>
              <Select
                value={selectedNamespace}
                onChange={setSelectedNamespace}
                style={{ width: '100%' }}
                placeholder="选择记忆类型"
              >
                {Object.entries(namespaces).map(([key, label]) => (
                  <Option key={key} value={key}>
                    <Space>
                      <DatabaseOutlined />
                      {label}
                    </Space>
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>

          <Col xs={24} sm={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>用户ID筛选</Text>
              <Input
                placeholder="输入用户ID"
                value={searchParams.user_id}
                onChange={(e) => handleSearchParamChange('user_id', e.target.value)}
                allowClear
              />
            </Space>
          </Col>

          <Col xs={24} sm={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>系统ID筛选</Text>
              <Input
                placeholder="输入系统ID"
                value={searchParams.system_id}
                onChange={(e) => handleSearchParamChange('system_id', e.target.value)}
                allowClear
              />
            </Space>
          </Col>
        </Row>

        <Row style={{ marginTop: '16px' }}>
          <Col span={24}>
            <Space>
              <Button
                type="primary"
                icon={<SearchOutlined />}
                onClick={loadMemories}
                loading={loading}
              >
                查询记忆
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  setSearchParams({ user_id: '', system_id: '' });
                  loadMemories();
                }}
              >
                重置
              </Button>
              <Tooltip title={getNamespaceDescription(selectedNamespace)}>
                <InfoCircleOutlined style={{ color: '#999', fontSize: '16px' }} />
              </Tooltip>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 记忆列表 */}
      <Card
        title={`${namespaces[selectedNamespace] || '系统记忆'} (${memories.length} 条)`}
        size="small"
      >
        <Table
          dataSource={memories}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
          locale={{ 
            emptyText: selectedNamespace ? 
              <Empty description={`暂无${namespaces[selectedNamespace]}记忆数据`} /> :
              <Empty description="请选择记忆类型" />
          }}
        />
      </Card>

      {/* 记忆详情查看模态框 */}
      <Modal
        title="记忆详情"
        open={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false);
          setViewingMemory(null);
        }}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {viewingMemory && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Text strong>记忆内容：</Text>
                <Paragraph 
                  style={{ 
                    marginTop: '8px', 
                    padding: '12px', 
                    backgroundColor: '#f5f5f5', 
                    borderRadius: '6px' 
                  }}
                >
                  {viewingMemory.content}
                </Paragraph>
              </Col>

              {viewingMemory.score !== undefined && (
                <Col span={12}>
                  <Text strong>相关性分数：</Text>
                  <div style={{ marginTop: '4px' }}>
                    <Tag color={viewingMemory.score < 0.3 ? 'green' : viewingMemory.score < 0.6 ? 'orange' : 'red'}>
                      {viewingMemory.score.toFixed(4)}
                    </Tag>
                  </div>
                </Col>
              )}

              <Col span={12}>
                <Text strong>记忆ID：</Text>
                <div style={{ marginTop: '4px' }}>
                  <Text code>{viewingMemory.id}</Text>
                </div>
              </Col>

              <Col span={24}>
                <Text strong>元数据：</Text>
                <TextArea
                  value={JSON.stringify(viewingMemory.metadata, null, 2)}
                  rows={6}
                  readOnly
                  style={{ marginTop: '8px', fontFamily: 'monospace' }}
                />
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SystemMemoryViewer;