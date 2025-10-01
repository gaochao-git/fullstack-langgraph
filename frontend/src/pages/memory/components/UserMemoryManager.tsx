/**
 * 用户记忆管理组件
 */

import React, { useState, useEffect } from 'react';
import { 
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  Tooltip,
  Row,
  Col,
  Typography,
  Divider
} from 'antd';
import { 
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

import { memoryApi, Memory, MemoryCreate, UserProfileMemories } from '../../../services/memoryApi';

const { TextArea } = Input;
const { Option } = Select;
const { Text, Paragraph } = Typography;

interface UserMemoryManagerProps {
  namespaces: Record<string, string>;
  onMemoryChange: () => void;
}

/**
 * 用户记忆管理组件
 */
const UserMemoryManager: React.FC<UserMemoryManagerProps> = ({
  namespaces,
  onMemoryChange
}) => {
  const [loading, setLoading] = useState(false);
  const [userMemories, setUserMemories] = useState<UserProfileMemories | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [form] = Form.useForm();

  /**
   * 初始化用户记忆数据
   */
  useEffect(() => {
    loadUserMemories();
  }, []);

  /**
   * 加载用户记忆数据
   */
  const loadUserMemories = async () => {
    setLoading(true);
    try {
      const response = await memoryApi.getUserProfileMemories();
      if (response.status === 'ok') {
        setUserMemories(response.data);
      }
    } catch (error) {
      console.error('加载用户记忆失败:', error);
      message.error('加载用户记忆数据失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 显示添加/编辑记忆模态框
   */
  const showMemoryModal = (memory?: Memory, namespace?: string) => {
    if (memory) {
      setEditingMemory(memory);
      form.setFieldsValue({
        namespace: namespace,
        content: memory.content,
        metadata: JSON.stringify(memory.metadata, null, 2)
      });
    } else {
      setEditingMemory(null);
      form.resetFields();
    }
    setIsModalVisible(true);
  };

  /**
   * 处理模态框确认
   */
  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      const memoryData: MemoryCreate = {
        namespace: values.namespace,
        content: values.content,
        metadata: values.metadata ? JSON.parse(values.metadata) : {},
        namespace_params: {
          user_id: userMemories?.user_id || 'system'
        }
      };

      if (editingMemory) {
        // 更新记忆
        await memoryApi.updateMemory({
          namespace: values.namespace,
          memory_id: editingMemory.id,
          content: values.content,
          namespace_params: memoryData.namespace_params
        });
        message.success('记忆更新成功');
      } else {
        // 添加新记忆
        await memoryApi.addMemory(memoryData);
        message.success('记忆添加成功');
      }

      setIsModalVisible(false);
      form.resetFields();
      setEditingMemory(null);
      await loadUserMemories();
      onMemoryChange();
    } catch (error) {
      console.error('保存记忆失败:', error);
      message.error('保存记忆失败');
    }
  };

  /**
   * 删除记忆
   */
  const handleDeleteMemory = async (memory: Memory, namespace: string) => {
    try {
      await memoryApi.deleteMemory(memory.id, namespace);
      message.success('记忆删除成功');
      await loadUserMemories();
      onMemoryChange();
    } catch (error) {
      console.error('删除记忆失败:', error);
      message.error('删除记忆失败');
    }
  };

  /**
   * 表格列定义
   */
  const getColumns = (namespace: string) => [
    {
      title: '记忆内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: '元数据',
      dataIndex: 'metadata',
      key: 'metadata',
      width: 200,
      render: (metadata: Record<string, any>) => (
        <Space direction="vertical" size="small">
          {Object.entries(metadata).map(([key, value]) => (
            <Tag key={key} color="blue">
              {key}: {String(value)}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (text: string) => text ? new Date(text).toLocaleDateString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Memory) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="primary"
              size="small"
              icon={<EditOutlined />}
              onClick={() => showMemoryModal(record, namespace)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除这条记忆吗？"
            icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
            onConfirm={() => handleDeleteMemory(record, namespace)}
            okText="确认"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  /**
   * 渲染记忆表格
   */
  const renderMemoryTable = (title: string, memories: Memory[], namespace: string) => (
    <Card
      title={title}
      size="small"
      extra={
        <Button
          type="primary"
          size="small"
          icon={<PlusOutlined />}
          onClick={() => showMemoryModal(undefined, namespace)}
        >
          添加{title}
        </Button>
      }
      style={{ marginBottom: '16px' }}
    >
      <Table
        dataSource={memories}
        columns={getColumns(namespace)}
        rowKey="id"
        size="small"
        loading={loading}
        pagination={{ pageSize: 5, showSizeChanger: false }}
        locale={{ emptyText: `暂无${title}记忆` }}
      />
    </Card>
  );

  return (
    <div>
      {/* 用户信息 */}
      <Card size="small" style={{ marginBottom: '16px' }}>
        <Row>
          <Col span={24}>
            <Text strong>当前用户: </Text>
            <Tag color="blue">{userMemories?.user_id || '未知'}</Tag>
            <Button
              type="link"
              size="small"
              onClick={loadUserMemories}
              loading={loading}
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 个人档案记忆 */}
      {renderMemoryTable('个人档案', userMemories?.profile || [], 'user_profile')}

      {/* 专业技能记忆 */}
      {renderMemoryTable('专业技能', userMemories?.expertise || [], 'user_expertise')}

      {/* 个人偏好记忆 */}
      {renderMemoryTable('个人偏好', userMemories?.preferences || [], 'user_preferences')}

      {/* 添加/编辑记忆模态框 */}
      <Modal
        title={editingMemory ? '编辑记忆' : '添加记忆'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingMemory(null);
        }}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            namespace: 'user_profile'
          }}
        >
          <Form.Item
            name="namespace"
            label="记忆类型"
            rules={[{ required: true, message: '请选择记忆类型' }]}
          >
            <Select placeholder="选择记忆类型">
              {Object.entries(namespaces).map(([key, label]) => (
                <Option key={key} value={key}>{label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="content"
            label="记忆内容"
            rules={[{ required: true, message: '请输入记忆内容' }]}
          >
            <TextArea
              rows={4}
              placeholder="请输入详细的记忆内容..."
              maxLength={2000}
              showCount
            />
          </Form.Item>

          <Form.Item
            name="metadata"
            label="元数据 (JSON格式)"
            extra="可选，用于添加额外的分类标签和属性"
          >
            <TextArea
              rows={3}
              placeholder={'{\n  "department": "ops",\n  "skill_level": "senior"\n}'}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserMemoryManager;