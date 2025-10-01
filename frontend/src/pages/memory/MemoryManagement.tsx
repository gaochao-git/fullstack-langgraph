/**
 * 记忆管理页面 - 标签页分类管理
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
  Radio,
  message,
  Popconfirm,
  Tag,
  Tabs,
  Row,
  Col
} from 'antd';
import { 
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  DatabaseOutlined,
  ClusterOutlined
} from '@ant-design/icons';

import { memoryApi, Memory, MemoryCreate } from '../../services/memoryApi';

const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

/**
 * 记忆分类定义
 */
const MEMORY_CATEGORIES = {
  personal: {
    label: '个人记忆',
    icon: <UserOutlined />,
    single: true, // 标记为单条记录模式
    types: {
      'user_profile': '个人档案'
    }
  },
  system: {
    label: '业务系统记忆',
    icon: <DatabaseOutlined />,
    types: {
      'crm_system': 'CRM系统',
      'erp_system': 'ERP系统',
      'oa_system': 'OA系统',
      'monitoring_system': '监控系统',
      'log_system': '日志系统',
      'database_system': '数据库系统'
    }
  },
  architecture: {
    label: '基础设施架构记忆',
    icon: <ClusterOutlined />,
    types: {
      'system_topology': '系统拓扑',
      'service_dependencies': '服务依赖',
      'deployment_info': '部署架构',
      'network_architecture': '网络架构',
      'data_architecture': '数据架构'
    }
  }
};

/**
 * 记忆管理页面组件
 */
const MemoryManagement: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [currentCategory, setCurrentCategory] = useState('personal');
  const [currentType, setCurrentType] = useState('user_profile');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [form] = Form.useForm();

  /**
   * 初始化数据
   */
  useEffect(() => {
    loadMemories();
  }, [currentType]);

  /**
   * 加载指定类型的记忆数据
   */
  const loadMemories = async () => {
    setLoading(true);
    try {
      // 构建请求参数 - 为个人记忆传递用户参数，其他类型暂时不传参数
      const params: { user_name?: string; system_id?: string } = {};
      
      // 个人记忆不需要手动传参，后端会自动获取当前用户
      // 其他类型的记忆目前不需要特定参数
      
      // 使用管理接口加载记忆数据
      const response = await memoryApi.listMemories(currentType, params);
      console.log('Memory API request:', { currentType, params }); // 添加调试日志
      console.log('Memory API response:', response); // 添加调试日志
      
      if (response.status === 'ok' && response.data) {
        const memoriesWithType = response.data.map((mem: Memory) => ({
          ...mem,
          memory_category: currentCategory,
          memory_type: currentType,
          type_label: getCurrentTypeLabel()
        }));
        setMemories(memoriesWithType);
        console.log('Loaded memories:', memoriesWithType); // 添加调试日志
      } else {
        console.log('Empty response or error:', response);
        setMemories([]);
      }
    } catch (error) {
      console.error(`加载${getCurrentTypeLabel()}记忆失败:`, error);
      setMemories([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取当前类型的标签
   */
  const getCurrentTypeLabel = () => {
    const category = MEMORY_CATEGORIES[currentCategory as keyof typeof MEMORY_CATEGORIES];
    return category?.types[currentType as keyof typeof category.types] || currentType;
  };

  /**
   * 处理标签页变化
   */
  const handleTabChange = (key: string) => {
    setCurrentCategory(key);
    const category = MEMORY_CATEGORIES[key as keyof typeof MEMORY_CATEGORIES];
    const firstType = Object.keys(category.types)[0];
    setCurrentType(firstType);
  };

  /**
   * 处理子类型变化
   */
  const handleTypeChange = (type: string) => {
    setCurrentType(type);
  };

  /**
   * 显示添加/编辑记忆模态框
   */
  const showMemoryModal = (memory?: Memory) => {
    if (memory) {
      setEditingMemory(memory);
      form.setFieldsValue({
        content: memory.content
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
        namespace: currentType,
        content: values.content,
        metadata: {
          namespace_type: currentType,
          memory_category: currentCategory
        },
        namespace_params: {}
      };

      if (editingMemory) {
        // 更新记忆
        await memoryApi.updateMemory({
          namespace: currentType,
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
      await loadMemories();
    } catch (error) {
      console.error('保存记忆失败:', error);
      message.error('保存记忆失败');
    }
  };

  /**
   * 删除记忆
   */
  const handleDeleteMemory = async (memory: Memory) => {
    try {
      await memoryApi.deleteMemory(memory.id, currentType);
      message.success('记忆删除成功');
      await loadMemories();
    } catch (error) {
      console.error('删除记忆失败:', error);
      message.error('删除记忆失败');
    }
  };

  /**
   * 个人记忆表格列定义（简化版）
   */
  const getPersonalColumns = () => [
    {
      title: '个人档案内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string) => (
        <div style={{ maxWidth: 300 }}>
          {text.length > 150 ? `${text.substring(0, 150)}...` : text}
        </div>
      ),
    },
    {
      title: '创建人',
      dataIndex: 'created_by',
      key: 'created_by',
      width: 100,
      render: (text: string, record: Memory) => {
        const metadata = record.metadata || {};
        return metadata.created_by || text || '-';
      },
    },
    {
      title: '修改人',
      dataIndex: 'updated_by',
      key: 'updated_by',
      width: 100,
      render: (text: string, record: Memory) => {
        const metadata = record.metadata || {};
        return metadata.updated_by || text || '-';
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 110,
      render: (text: string, record: Memory) => {
        // 优先使用create_time，其次使用created_at
        const createTime = record.metadata?.create_time || text;
        return createTime ? new Date(createTime).toLocaleDateString() : '-';
      },
    },
    {
      title: '修改时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 110,
      render: (text: string, record: Memory) => {
        // 优先使用update_time，其次使用updated_at
        const updateTime = record.metadata?.update_time || text;
        return updateTime ? new Date(updateTime).toLocaleDateString() : '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: Memory) => (
        <Button
          type="primary"
          size="small"
          icon={<EditOutlined />}
          onClick={() => showMemoryModal(record)}
        >
          编辑
        </Button>
      ),
    },
  ];

  /**
   * 普通记忆表格列定义
   */
  const getNormalColumns = () => [
    {
      title: '记忆内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: { showTitle: false },
      render: (text: string) => (
        <div style={{ maxWidth: 250 }}>
          {text.length > 120 ? `${text.substring(0, 120)}...` : text}
        </div>
      ),
    },
    {
      title: '创建人',
      dataIndex: 'created_by',
      key: 'created_by',
      width: 100,
      render: (text: string, record: Memory) => {
        const metadata = record.metadata || {};
        return metadata.created_by || text || '-';
      },
    },
    {
      title: '修改人',
      dataIndex: 'updated_by',
      key: 'updated_by',
      width: 100,
      render: (text: string, record: Memory) => {
        const metadata = record.metadata || {};
        return metadata.updated_by || text || '-';
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 110,
      render: (text: string, record: Memory) => {
        // 优先使用create_time，其次使用created_at
        const createTime = record.metadata?.create_time || text;
        return createTime ? new Date(createTime).toLocaleDateString() : '-';
      },
    },
    {
      title: '修改时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 110,
      render: (text: string, record: Memory) => {
        // 优先使用update_time，其次使用updated_at
        const updateTime = record.metadata?.update_time || text;
        return updateTime ? new Date(updateTime).toLocaleDateString() : '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: Memory) => (
        <Space size="small">
          <Button
            type="primary"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showMemoryModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除这条记忆吗？"
            icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
            onConfirm={() => handleDeleteMemory(record)}
            okText="确认"
            cancelText="取消"
          >
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  /**
   * 渲染操作按钮区域
   */
  const renderActionBar = () => {
    const isPersonal = currentCategory === 'personal';
    
    return (
      <Row justify="end" align="middle" style={{ marginBottom: '16px' }}>
        <Col>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadMemories}
              loading={loading}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => showMemoryModal()}
            >
              {isPersonal ? '新增个人档案' : 
               currentCategory === 'system' ? '新增系统记忆' :
               currentCategory === 'architecture' ? '新增架构记忆' : 
               `新增${getCurrentTypeLabel()}`}
            </Button>
          </Space>
        </Col>
      </Row>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <Tabs 
        activeKey={currentCategory} 
        onChange={handleTabChange}
        type="card"
        size="large"
      >
          {Object.entries(MEMORY_CATEGORIES).map(([key, category]) => (
            <TabPane
              tab={
                <span>
                  {category.icon}
                  {category.label}
                </span>
              }
              key={key}
            >
              {renderActionBar()}
              
              <Table
                dataSource={memories}
                columns={currentCategory === 'personal' ? getPersonalColumns() : getNormalColumns()}
                rowKey="id"
                loading={loading}
                scroll={{ x: 1000 }}
                pagination={{
                  pageSize: 15,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                }}
                size="small"
                locale={{
                  emptyText: `暂无${getCurrentTypeLabel()}记忆数据`
                }}
              />
            </TabPane>
          ))}
        </Tabs>

      {/* 添加/编辑记忆模态框 */}
      <Modal
        title={editingMemory ? `编辑${getCurrentTypeLabel()}` : `新增${getCurrentTypeLabel()}`}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
          setEditingMemory(null);
        }}
        width={700}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="content"
            label={`${getCurrentTypeLabel()}内容`}
            rules={[{ required: true, message: `请输入${getCurrentTypeLabel()}内容` }]}
          >
            <TextArea
              rows={8}
              placeholder={currentCategory === 'personal' ? 
                '请输入您的个人档案信息，包括教育背景、工作经历、技能特长、专业领域、个人偏好等...' : 
                `请输入详细的${getCurrentTypeLabel()}内容...`
              }
              maxLength={2000}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MemoryManagement;