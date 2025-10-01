/**
 * 记忆搜索面板组件
 */

import React, { useState } from 'react';
import { 
  Card,
  Form,
  Input,
  Select,
  Button,
  Table,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Typography,
  Tooltip,
  message,
  Empty
} from 'antd';
import { 
  SearchOutlined,
  ClearOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

import { memoryApi, Memory, NamespaceInfo } from '../../../services/memoryApi';

const { Search, TextArea } = Input;
const { Option } = Select;
const { Text, Paragraph } = Typography;

interface MemorySearchPanelProps {
  namespaces: NamespaceInfo | null;
}

/**
 * 记忆搜索面板组件
 */
const MemorySearchPanel: React.FC<MemorySearchPanelProps> = ({
  namespaces
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<Memory[]>([]);
  const [searchPerformed, setSearchPerformed] = useState(false);

  /**
   * 执行记忆搜索
   */
  const handleSearch = async (values: any) => {
    if (!values.query?.trim()) {
      message.warning('请输入搜索内容');
      return;
    }

    setLoading(true);
    setSearchPerformed(true);
    
    try {
      const searchData = {
        namespace: values.namespace,
        query: values.query,
        limit: values.limit || 10,
        namespace_params: {
          user_id: values.user_id || '',
          system_id: values.system_id || '',
          problem_type: values.problem_type || ''
        }
      };

      // 清理空的参数
      Object.keys(searchData.namespace_params).forEach(key => {
        if (!searchData.namespace_params[key]) {
          delete searchData.namespace_params[key];
        }
      });

      const response = await memoryApi.searchMemories(searchData);
      if (response.status === 'ok') {
        setSearchResults(response.data || []);
      }
    } catch (error) {
      console.error('搜索记忆失败:', error);
      message.error('搜索记忆失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 清空搜索结果
   */
  const handleClear = () => {
    form.resetFields();
    setSearchResults([]);
    setSearchPerformed(false);
  };

  /**
   * 快速搜索示例
   */
  const quickSearchExamples = [
    { label: 'Kubernetes故障', query: 'Kubernetes Pod重启', namespace: 'solution_patterns' },
    { label: 'MySQL优化', query: 'MySQL慢查询优化', namespace: 'solution_patterns' },
    { label: '网络问题', query: '网络连接超时', namespace: 'incident_history' },
    { label: '系统架构', query: '微服务架构', namespace: 'deployment_info' }
  ];

  /**
   * 快速搜索
   */
  const handleQuickSearch = (example: any) => {
    form.setFieldsValue({
      query: example.query,
      namespace: example.namespace
    });
    handleSearch({ 
      query: example.query, 
      namespace: example.namespace 
    });
  };

  /**
   * 搜索结果表格列定义
   */
  const columns = [
    {
      title: '记忆内容',
      dataIndex: 'content',
      key: 'content',
      render: (text: string) => (
        <Paragraph ellipsis={{ rows: 3, expandable: true }}>
          {text}
        </Paragraph>
      ),
    },
    {
      title: '相关性',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      render: (score: number) => (
        <div style={{ textAlign: 'center' }}>
          <Tag color={score < 0.3 ? 'green' : score < 0.6 ? 'orange' : 'red'}>
            {(score * 100).toFixed(1)}%
          </Tag>
          <div style={{ fontSize: '11px', color: '#999' }}>
            {score < 0.3 ? '高相关' : score < 0.6 ? '中相关' : '低相关'}
          </div>
        </div>
      ),
      sorter: (a: Memory, b: Memory) => (a.score || 0) - (b.score || 0),
    },
    {
      title: '来源类型',
      dataIndex: 'metadata',
      key: 'namespace',
      width: 120,
      render: (metadata: Record<string, any>) => {
        const namespaceType = metadata.namespace_type;
        const allNamespaces = {
          ...namespaces?.user || {},
          ...namespaces?.architecture || {},
          ...namespaces?.business || {},
          ...namespaces?.operations || {}
        };
        return (
          <Tag color="blue">
            {allNamespaces[namespaceType] || namespaceType || '未知'}
          </Tag>
        );
      },
    },
    {
      title: '关键信息',
      dataIndex: 'metadata',
      key: 'metadata',
      width: 200,
      render: (metadata: Record<string, any>) => (
        <Space direction="vertical" size="small">
          {metadata.business_namespace && (
            <Text style={{ fontSize: '11px' }} type="secondary">
              {metadata.business_namespace}
            </Text>
          )}
          {Object.entries(metadata)
            .filter(([key]) => !['namespace_type', 'business_namespace', 'timestamp', 'version'].includes(key))
            .slice(0, 2)
            .map(([key, value]) => (
              <Tag key={key} style={{ fontSize: '10px' }}>
                {key}: {String(value).substring(0, 15)}
              </Tag>
            ))}
        </Space>
      ),
    }
  ];

  /**
   * 获取所有命名空间选项
   */
  const getAllNamespaces = () => {
    if (!namespaces) return [];
    
    const options: Array<{ label: string; options: Array<{ label: string; value: string }> }> = [];
    
    if (namespaces.user) {
      options.push({
        label: '个人记忆',
        options: Object.entries(namespaces.user).map(([key, label]) => ({ label, value: key }))
      });
    }
    
    if (namespaces.architecture) {
      options.push({
        label: '系统架构',
        options: Object.entries(namespaces.architecture).map(([key, label]) => ({ label, value: key }))
      });
    }
    
    if (namespaces.business) {
      options.push({
        label: '业务知识',
        options: Object.entries(namespaces.business).map(([key, label]) => ({ label, value: key }))
      });
    }
    
    if (namespaces.operations) {
      options.push({
        label: '运维知识',
        options: Object.entries(namespaces.operations).map(([key, label]) => ({ label, value: key }))
      });
    }
    
    return options;
  };

  return (
    <div>
      {/* 搜索表单 */}
      <Card title="智能记忆搜索" size="small" style={{ marginBottom: '16px' }}>
        <Alert
          message="搜索提示"
          description="使用自然语言描述您要查找的内容，系统会基于语义相似度返回最相关的记忆。支持按命名空间、用户、系统等维度过滤。"
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />

        <Form
          form={form}
          onFinish={handleSearch}
          layout="vertical"
          initialValues={{
            limit: 10,
            namespace: 'solution_patterns'
          }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="query"
                label="搜索内容"
                rules={[{ required: true, message: '请输入搜索内容' }]}
              >
                <TextArea
                  rows={3}
                  placeholder="请输入您要搜索的内容，例如：MySQL慢查询优化、Kubernetes Pod重启问题、网络连接超时解决方案..."
                  maxLength={500}
                  showCount
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Row gutter={[8, 8]}>
                <Col span={24}>
                  <Form.Item
                    name="namespace"
                    label="搜索范围"
                    rules={[{ required: true, message: '请选择搜索范围' }]}
                  >
                    <Select placeholder="选择记忆类型">
                      {getAllNamespaces().map(group => (
                        <Select.OptGroup key={group.label} label={group.label}>
                          {group.options.map(option => (
                            <Option key={option.value} value={option.value}>
                              {option.label}
                            </Option>
                          ))}
                        </Select.OptGroup>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item name="user_id" label="用户ID (可选)">
                    <Input placeholder="筛选特定用户" />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item name="system_id" label="系统ID (可选)">
                    <Input placeholder="筛选特定系统" />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item name="problem_type" label="问题类型 (可选)">
                    <Input placeholder="如: database, network" />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item name="limit" label="结果数量">
                    <Select>
                      <Option value={5}>5条</Option>
                      <Option value={10}>10条</Option>
                      <Option value={20}>20条</Option>
                      <Option value={50}>50条</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
            </Col>
          </Row>

          <Row>
            <Col span={24}>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SearchOutlined />}
                  loading={loading}
                  size="large"
                >
                  智能搜索
                </Button>
                <Button
                  icon={<ClearOutlined />}
                  onClick={handleClear}
                  size="large"
                >
                  清空
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>

        {/* 快速搜索示例 */}
        <div style={{ marginTop: '16px' }}>
          <Text strong>
            <ThunderboltOutlined /> 快速搜索示例：
          </Text>
          <div style={{ marginTop: '8px' }}>
            <Space wrap>
              {quickSearchExamples.map((example, index) => (
                <Button
                  key={index}
                  size="small"
                  onClick={() => handleQuickSearch(example)}
                  style={{ borderRadius: '12px' }}
                >
                  {example.label}
                </Button>
              ))}
            </Space>
          </div>
        </div>
      </Card>

      {/* 搜索结果 */}
      {searchPerformed && (
        <Card
          title={
            <Space>
              <SearchOutlined />
              搜索结果
              {searchResults.length > 0 && (
                <Tag color="blue">{searchResults.length} 条结果</Tag>
              )}
            </Space>
          }
          size="small"
        >
          <Table
            dataSource={searchResults}
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
              emptyText: (
                <Empty 
                  description="未找到相关记忆，尝试调整搜索条件或关键词" 
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )
            }}
          />
        </Card>
      )}
    </div>
  );
};

export default MemorySearchPanel;