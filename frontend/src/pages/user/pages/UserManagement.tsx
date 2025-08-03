import { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Input, Modal, Form, message, 
  Select, Tag, Tooltip, Row, Col 
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, 
  UserOutlined, ReloadOutlined 
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { userApi, roleApi } from '../services/rbacApi';
import type { 
  RbacUser, RbacRole, UserCreateRequest, UserUpdateRequest, UserQueryParams 
} from '../types/rbac';

const { Search } = Input;
const { Option } = Select;

export function UserManagement() {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<RbacUser[]>([]);
  const [availableRoles, setAvailableRoles] = useState<RbacRole[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<RbacUser | null>(null);
  const [form] = Form.useForm();
  
  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filters, setFilters] = useState({
    is_active: undefined as number | undefined,
    department_name: undefined as string | undefined,
    group_name: undefined as string | undefined,
  });

  const columns: ColumnsType<RbacUser> = [
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 120,
    },
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200,
      ellipsis: true,
    },
    {
      title: '手机号',
      dataIndex: 'mobile',
      key: 'mobile',
      width: 130,
    },
    {
      title: '部门',
      dataIndex: 'department_name',
      key: 'department_name',
      width: 120,
      ellipsis: true,
    },
    {
      title: '组',
      dataIndex: 'group_name',
      key: 'group_name',
      width: 100,
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive: number) => (
        <Tag color={isActive === 1 ? 'green' : 'red'}>
          {isActive === 1 ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '来源',
      dataIndex: 'user_source',
      key: 'user_source',
      width: 80,
      render: (source: number) => {
        const sourceMap: Record<number, string> = {
          1: '系统',
          2: 'LDAP',
          3: '手动'
        };
        return sourceMap[source] || '未知';
      },
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_: any, record: RbacUser) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params: UserQueryParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
        search: searchKeyword || undefined,
        is_active: filters.is_active,
        department_name: filters.department_name,
        group_name: filters.group_name,
      };
      
      const response = await userApi.listUsers(params);
      console.log('用户API响应:', response);
      const items = response.items || [];
      console.log('设置用户数据:', items.length, '条');
      setUsers(items);
      setPagination(prev => ({
        ...prev,
        total: response.pagination?.total || 0,
      }));
    } catch (error) {
      message.error('获取用户列表失败');
      console.error('获取用户列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      const response = await roleApi.listRoles({ page: 1, page_size: 100 });
      setAvailableRoles(response.items || []);
    } catch (error) {
      console.error('获取角色列表失败:', error);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, [pagination.current, pagination.pageSize, searchKeyword, filters]);

  const handleAdd = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (user: RbacUser) => {
    setEditingUser(user);
    form.setFieldsValue({
      ...user,
      role_ids: user.roles?.map(role => role.role_id) || [],
    });
    setModalVisible(true);
  };

  const handleDelete = (user: RbacUser) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户 "${user.display_name}(${user.user_name})" 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await userApi.deleteUser(user.user_id);
          if (response.success) {
            message.success('删除成功');
            fetchUsers();
          } else {
            message.error(response.message || '删除失败');
          }
        } catch (error) {
          message.error('删除失败');
          console.error('删除用户失败:', error);
        }
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingUser) {
        // 更新用户
        const updateData: UserUpdateRequest = {
          user_name: values.user_name,
          display_name: values.display_name,
          department_name: values.department_name,
          group_name: values.group_name,
          email: values.email,
          mobile: values.mobile,
          user_source: values.user_source,
          is_active: values.is_active,
          role_ids: values.role_ids || [],
        };
        
        const response = await userApi.updateUser(editingUser.user_id, updateData);
        if (response.success) {
          message.success('更新成功');
          setModalVisible(false);
          form.resetFields();
          fetchUsers();
        } else {
          message.error(response.message || '更新失败');
        }
      } else {
        // 创建用户
        const createData: UserCreateRequest = {
          user_id: values.user_id,
          user_name: values.user_name,
          display_name: values.display_name,
          department_name: values.department_name,
          group_name: values.group_name,
          email: values.email,
          mobile: values.mobile,
          user_source: values.user_source || 3,
          is_active: values.is_active ?? 1,
          role_ids: values.role_ids || [],
        };
        
        const response = await userApi.createUser(createData);
        if (response.success) {
          message.success('创建成功');
          setModalVisible(false);
          form.resetFields();
          fetchUsers();
        } else {
          message.error(response.message || '创建失败');
        }
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleTableChange = (paginationConfig: any) => {
    setPagination({
      current: paginationConfig.current,
      pageSize: paginationConfig.pageSize,
      total: paginationConfig.total,
    });
  };

  return (
    <div>
      <Card
        title={
          <Space>
            <UserOutlined />
            用户管理
          </Space>
        }
        extra={
          <Space>
            <Search
              placeholder="搜索用户名、显示名称、邮箱"
              allowClear
              style={{ width: 260 }}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchUsers()}
              title="刷新"
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增用户
            </Button>
          </Space>
        }
      >
        {/* 筛选器 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Select
              placeholder="选择状态"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters(prev => ({ ...prev, is_active: value }))}
            >
              <Option value={1}>启用</Option>
              <Option value={0}>禁用</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Input
              placeholder="部门名称"
              allowClear
              onChange={(e) => setFilters(prev => ({ ...prev, department_name: e.target.value }))}
            />
          </Col>
          <Col span={6}>
            <Input
              placeholder="组名"
              allowClear
              onChange={(e) => setFilters(prev => ({ ...prev, group_name: e.target.value }))}
            />
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={users}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1400 }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title={editingUser ? '编辑用户' : '新增用户'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        okText="确定"
        cancelText="取消"
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="user_id"
                label="用户ID"
                rules={[{ required: true, message: '请输入用户ID' }]}
              >
                <Input 
                  placeholder="请输入用户ID" 
                  disabled={!!editingUser}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="user_name"
                label="用户名"
                rules={[{ required: true, message: '请输入用户名' }]}
              >
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="display_name"
                label="显示名称"
                rules={[{ required: true, message: '请输入显示名称' }]}
              >
                <Input placeholder="请输入显示名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="email"
                label="邮箱"
                rules={[
                  { required: true, message: '请输入邮箱' },
                  { type: 'email', message: '请输入有效的邮箱地址' }
                ]}
              >
                <Input placeholder="请输入邮箱" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="mobile"
                label="手机号"
                rules={[{ required: true, message: '请输入手机号' }]}
              >
                <Input placeholder="请输入手机号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="department_name"
                label="部门名称"
                rules={[{ required: true, message: '请输入部门名称' }]}
              >
                <Input placeholder="请输入部门名称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="group_name"
                label="组名"
                rules={[{ required: true, message: '请输入组名' }]}
              >
                <Input placeholder="请输入组名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="user_source"
                label="用户来源"
                initialValue={3}
              >
                <Select>
                  <Option value={1}>系统</Option>
                  <Option value={2}>LDAP</Option>
                  <Option value={3}>手动</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="状态"
                initialValue={1}
              >
                <Select>
                  <Option value={1}>启用</Option>
                  <Option value={0}>禁用</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="role_ids"
                label="分配角色"
              >
                <Select
                  mode="multiple"
                  placeholder="选择角色"
                  allowClear
                  optionFilterProp="children"
                >
                  {availableRoles.map((role: RbacRole) => (
                    <Option key={role.role_id} value={role.role_id}>
                      {role.role_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}