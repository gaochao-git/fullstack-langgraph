import { useState } from 'react';
import { Card, Table, Button, Space, Input, Modal, Form, message, Tabs, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';

const { Search } = Input;
const { Option } = Select;

interface Permission {
  id: number;
  name: string;
  code: string;
  description: string;
  module: string;
  type: 'menu' | 'button' | 'api';
  status: 'active' | 'inactive';
  createTime: string;
}

export function PermissionManagement() {
  const [loading, setLoading] = useState(false);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('all');

  const permissionTypes = {
    menu: '菜单权限',
    button: '按钮权限',
    api: '接口权限',
  };

  const columns = [
    {
      title: '权限名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '权限编码',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: keyof typeof permissionTypes) => permissionTypes[type],
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <span className={status === 'active' ? 'text-green-600' : 'text-red-600'}>
          {status === 'active' ? '启用' : '禁用'}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      key: 'createTime',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Permission) => (
        <Space size="middle">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const handleAdd = () => {
    setEditingPermission(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (permission: Permission) => {
    setEditingPermission(permission);
    form.setFieldsValue(permission);
    setModalVisible(true);
  };

  const handleDelete = (permission: Permission) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除权限 "${permission.name}" 吗？`,
      onOk: async () => {
        message.success('删除成功');
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      message.success(editingPermission ? '更新成功' : '创建成功');
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const filteredPermissions = permissions.filter(permission => {
    if (activeTab === 'all') return true;
    return permission.type === activeTab;
  });

  const tabItems = [
    { label: '全部权限', key: 'all' },
    { label: '菜单权限', key: 'menu' },
    { label: '按钮权限', key: 'button' },
    { label: '接口权限', key: 'api' },
  ];

  return (
    <div>
      <Card
        title="权限管理"
        extra={
          <Space>
            <Search
              placeholder="搜索权限"
              allowClear
              style={{ width: 200 }}
              prefix={<SearchOutlined />}
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增权限
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
        <Table
          columns={columns}
          dataSource={filteredPermissions}
          loading={loading}
          rowKey="id"
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      <Modal
        title={editingPermission ? '编辑权限' : '新增权限'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="权限名称"
            rules={[{ required: true, message: '请输入权限名称' }]}
          >
            <Input placeholder="请输入权限名称" />
          </Form.Item>
          <Form.Item
            name="code"
            label="权限编码"
            rules={[{ required: true, message: '请输入权限编码' }]}
          >
            <Input placeholder="请输入权限编码" />
          </Form.Item>
          <Form.Item
            name="description"
            label="权限描述"
            rules={[{ required: true, message: '请输入权限描述' }]}
          >
            <Input.TextArea placeholder="请输入权限描述" rows={3} />
          </Form.Item>
          <Form.Item
            name="module"
            label="所属模块"
            rules={[{ required: true, message: '请输入所属模块' }]}
          >
            <Input placeholder="请输入所属模块" />
          </Form.Item>
          <Form.Item
            name="type"
            label="权限类型"
            rules={[{ required: true, message: '请选择权限类型' }]}
          >
            <Select placeholder="请选择权限类型">
              <Option value="menu">菜单权限</Option>
              <Option value="button">按钮权限</Option>
              <Option value="api">接口权限</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}