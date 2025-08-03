import { useState } from 'react';
import { Card, Table, Button, Space, Input, Modal, Form, message, Tree } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';

const { Search } = Input;

interface Role {
  id: number;
  name: string;
  description: string;
  status: 'active' | 'inactive';
  createTime: string;
  permissions: string[];
}

export function RoleManagement() {
  const [loading, setLoading] = useState(false);
  const [roles, setRoles] = useState<Role[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [form] = Form.useForm();

  const permissionTreeData = [
    {
      title: '系统管理',
      key: 'system',
      children: [
        { title: '用户管理', key: 'user' },
        { title: '角色管理', key: 'role' },
        { title: '权限管理', key: 'permission' },
      ],
    },
    {
      title: '运维管理',
      key: 'ops',
      children: [
        { title: '智能体管理', key: 'agent' },
        { title: 'SOP管理', key: 'sop' },
        { title: 'MCP管理', key: 'mcp' },
        { title: '模型管理', key: 'model' },
        { title: '任务管理', key: 'task' },
      ],
    },
  ];

  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
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
      render: (_: any, record: Role) => (
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
    setEditingRole(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (role: Role) => {
    setEditingRole(role);
    form.setFieldsValue(role);
    setModalVisible(true);
  };

  const handleDelete = (role: Role) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除角色 "${role.name}" 吗？`,
      onOk: async () => {
        message.success('删除成功');
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      message.success(editingRole ? '更新成功' : '创建成功');
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <div>
      <Card
        title="角色管理"
        extra={
          <Space>
            <Search
              placeholder="搜索角色"
              allowClear
              style={{ width: 200 }}
              prefix={<SearchOutlined />}
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增角色
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={roles}
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
        title={editingRole ? '编辑角色' : '新增角色'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        okText="确定"
        cancelText="取消"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="请输入角色名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="角色描述"
            rules={[{ required: true, message: '请输入角色描述' }]}
          >
            <Input.TextArea placeholder="请输入角色描述" rows={3} />
          </Form.Item>
          <Form.Item
            name="permissions"
            label="权限配置"
          >
            <Tree
              checkable
              treeData={permissionTreeData}
              defaultExpandAll
              onCheck={(checkedKeys) => {
                form.setFieldsValue({ permissions: checkedKeys });
              }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}