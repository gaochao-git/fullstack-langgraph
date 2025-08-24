import { useState, useEffect } from 'react';
import { useIsMobile } from '@/hooks';
import { 
  Card, Table, Button, Space, Input, Modal, Form, message, 
  Tag, Tooltip, Row, Col, InputNumber, Transfer, Tabs, App
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, 
  TeamOutlined, ReloadOutlined, SettingOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
// import type { TransferProps } from 'antd/es/transfer';
import { roleApi, permissionApi, menuApi } from '@/pages/user/services/rbacApi';
import type { 
  RbacRole, RbacPermission, RbacMenu, RoleCreateRequest, RoleUpdateRequest, RoleQueryParams 
} from '../types/rbac';

const { Search } = Input;

interface TransferItem {
  key: string;
  title: string;
  description?: string;
}

export function RoleManagement() {
  const { modal } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [roles, setRoles] = useState<RbacRole[]>([]);
  const [permissions, setPermissions] = useState<RbacPermission[]>([]);
  const [menus, setMenus] = useState<RbacMenu[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<RbacRole | null>(null);
  const [form] = Form.useForm();
  const isMobile = useIsMobile();
  
  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [selectedMenus, setSelectedMenus] = useState<string[]>([]);

  const columns: ColumnsType<RbacRole> = [
    {
      title: '角色ID',
      dataIndex: 'role_id',
      key: 'role_id',
      width: 100,
    },
    {
      title: '角色名称',
      dataIndex: 'role_name',
      key: 'role_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '角色描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
    },
    {
      title: '权限数量',
      dataIndex: 'permission_count',
      key: 'permission_count',
      width: 100,
      render: (count: number) => (
        <Tag color="blue">{count || 0}</Tag>
      ),
    },
    {
      title: '用户数量',
      dataIndex: 'user_count',
      key: 'user_count',
      width: 100,
      render: (count: number) => (
        <Tag color="green">{count || 0}</Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      ellipsis: true,
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 100,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: isMobile ? undefined : 'right',
      render: (_: any, record: RbacRole) => (
        <Space size="small">
          <Tooltip title="配置">
            <Button
              type="link"
              icon={<SettingOutlined />}
              onClick={() => handleManagePermissions(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 获取角色列表
  const fetchRoles = async () => {
    try {
      setLoading(true);
      const params: RoleQueryParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
        search: searchKeyword || undefined,
      };
      
      const response = await roleApi.listRoles(params);
      const items = response.items || [];
      setRoles(items);
      setPagination(prev => ({
        ...prev,
        total: response.pagination?.total || 0,
      }));
    } catch (error) {
      message.error('获取角色列表失败');
      console.error('获取角色列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取权限列表
  const fetchPermissions = async () => {
    try {
      const response = await permissionApi.listPermissions({ page: 1, page_size: 1000 });
      setPermissions(response.items || []);
    } catch (error) {
      console.error('获取权限列表失败:', error);
    }
  };

  // 获取菜单列表
  const fetchMenus = async () => {
    try {
      const response = await menuApi.listMenus({ page: 1, page_size: 1000 });
      setMenus(response.items || []);
    } catch (error) {
      console.error('获取菜单列表失败:', error);
    }
  };

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
    fetchMenus();
  }, [pagination.current, pagination.pageSize, searchKeyword]);

  const handleAdd = () => {
    setEditingRole(null);
    form.resetFields();
    setSelectedPermissions([]);
    setSelectedMenus([]);
    setModalVisible(true);
  };

  const handleEdit = async (role: RbacRole) => {
    setEditingRole(role);
    form.setFieldsValue({
      role_id: role.role_id,
      role_name: role.role_name,
      description: role.description,
    });
    
    try {
      // 获取角色的现有权限
      const rolePermissions = await roleApi.getRolePermissions(role.role_id);
      setSelectedPermissions(rolePermissions.api_permission_ids.map(id => id.toString()));
      setSelectedMenus(rolePermissions.menu_ids.map(id => id.toString()));
    } catch (error) {
      console.error('获取角色权限失败:', error);
      // 如果获取失败，设置为空数组
      setSelectedPermissions([]);
      setSelectedMenus([]);
    }
    
    setModalVisible(true);
  };

  const handleManagePermissions = async (role: RbacRole) => {
    setEditingRole(role);
    form.setFieldsValue({
      role_id: role.role_id,
      role_name: role.role_name,
      description: role.description,
    });
    
    try {
      // 获取角色的现有权限
      const rolePermissions = await roleApi.getRolePermissions(role.role_id);
      setSelectedPermissions(rolePermissions.api_permission_ids.map(id => id.toString()));
      setSelectedMenus(rolePermissions.menu_ids.map(id => id.toString()));
    } catch (error) {
      console.error('获取角色权限失败:', error);
      message.error('获取角色权限失败');
    }
    
    setModalVisible(true);
  };

  const handleDelete = (role: RbacRole) => {
    modal.confirm({
      title: '确认删除',
      content: (
        <div>
          <p>确定要删除角色 <strong>"{role.role_name}"</strong> 吗？</p>
          <p className="text-gray-500">删除后，该角色关联的所有用户权限将被清除。</p>
        </div>
      ),
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await roleApi.deleteRole(role.role_id);
          // API成功时直接返回数据，失败时抛出异常
          message.success(`角色"${role.role_name}"删除成功`);
          fetchRoles();
        } catch (error) {
          console.error('删除角色失败:', error);
          const errorMessage = error instanceof Error ? error.message : '删除操作失败，请重试';
          message.error(errorMessage);
        }
      },
    });
  };

  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      const values = await form.validateFields();
      
      if (editingRole) {
        // 更新角色
        const updateData: RoleUpdateRequest = {
          role_name: values.role_name,
          description: values.description,
          permission_ids: selectedPermissions.map(id => parseInt(id)),
          menu_ids: selectedMenus.map(id => parseInt(id)),
        };
        
        await roleApi.updateRole(editingRole.role_id, updateData);
        // API成功时直接返回数据，失败时抛出异常
        message.success(`角色"${values.role_name}"更新成功`);
        setModalVisible(false);
        form.resetFields();
        setSelectedPermissions([]);
        setSelectedMenus([]);
        fetchRoles();
      } else {
        // 创建角色（不包含role_id，由后端自动生成）
        const createData: RoleCreateRequest = {
          role_name: values.role_name,
          description: values.description,
          permission_ids: selectedPermissions.map(id => parseInt(id)),
          menu_ids: selectedMenus.map(id => parseInt(id)),
        };
        
        await roleApi.createRole(createData);
        // API成功时直接返回数据，失败时抛出异常
        message.success(`角色"${values.role_name}"创建成功`);
        setModalVisible(false);
        form.resetFields();
        setSelectedPermissions([]);
        setSelectedMenus([]);
        fetchRoles();
      }
    } catch (error) {
      console.error('操作失败:', error);
      const errorMessage = error instanceof Error ? error.message : '操作失败，请重试';
      message.error(errorMessage);
    } finally {
      setSubmitting(false);
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

  // 准备穿梭框数据
  const transferDataSource: TransferItem[] = permissions.map(permission => ({
    key: permission.permission_id.toString(),
    title: permission.permission_name,
    description: permission.permission_description,
  }));

  const menuTransferDataSource: TransferItem[] = menus.map(menu => ({
    key: menu.menu_id.toString(),
    title: menu.menu_name,
    description: menu.route_path,
  }));

  const handleTransferChange = (nextTargetKeys: string[]) => {
    setSelectedPermissions(nextTargetKeys);
  };

  const handleMenuTransferChange = (nextTargetKeys: string[]) => {
    setSelectedMenus(nextTargetKeys);
  };

  // 统计信息
  // 统计信息已移除，节省空间

  return (
    <div>
      <Card
        title={
          <Space>
            <TeamOutlined />
            角色管理
          </Space>
        }
        extra={
          <Space>
            <Search
              placeholder="搜索角色名称、描述"
              allowClear
              style={{ width: 240 }}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchRoles()}
              title="刷新"
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
          scroll={{ x: 1200 }}
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
        title={editingRole ? '编辑角色' : '新增角色'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setSelectedPermissions([]);
        }}
        okText="确定"
        cancelText="取消"
        width={800}
        destroyOnHidden
        confirmLoading={submitting}
        okButtonProps={{
          disabled: submitting
        }}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            {editingRole && (
              <Col span={12}>
                <Form.Item
                  name="role_id"
                  label="角色ID"
                >
                  <InputNumber 
                    style={{ width: '100%' }}
                    disabled
                  />
                </Form.Item>
              </Col>
            )}
            <Col span={editingRole ? 12 : 24}>
              <Form.Item
                name="role_name"
                label="角色名称"
                rules={[{ required: true, message: '请输入角色名称' }]}
              >
                <Input placeholder="请输入角色名称" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="角色描述"
            rules={[{ required: true, message: '请输入角色描述' }]}
          >
            <Input.TextArea 
              placeholder="请输入角色描述" 
              rows={3} 
              showCount 
              maxLength={200}
            />
          </Form.Item>

          <Form.Item label="权限分配">
            <Tabs
              items={[
                {
                  key: 'api',
                  label: `API权限 (${selectedPermissions.length})`,
                  children: (
                    <Transfer
                      dataSource={transferDataSource}
                      targetKeys={selectedPermissions}
                      onChange={(targetKeys) => handleTransferChange(targetKeys as string[])}
                      render={item => `${item.title} - ${item.description}`}
                      titles={['可选API权限', '已分配API权限']}
                      showSearch
                      listStyle={{
                        width: 300,
                        height: 300,
                      }}
                      operations={['分配', '取消']}
                      filterOption={(inputValue, item) => 
                        (item.title.toLowerCase().includes(inputValue.toLowerCase()) ||
                        (item.description?.toLowerCase().includes(inputValue.toLowerCase()) || false))
                      }
                    />
                  )
                },
                {
                  key: 'menu',
                  label: `菜单权限 (${selectedMenus.length})`,
                  children: (
                    <Transfer
                      dataSource={menuTransferDataSource}
                      targetKeys={selectedMenus}
                      onChange={(targetKeys) => handleMenuTransferChange(targetKeys as string[])}
                      render={item => `${item.title} - ${item.description}`}
                      titles={['可选菜单', '已分配菜单']}
                      showSearch
                      listStyle={{
                        width: 300,
                        height: 300,
                      }}
                      operations={['分配', '取消']}
                      filterOption={(inputValue, item) => 
                        (item.title.toLowerCase().includes(inputValue.toLowerCase()) ||
                        (item.description?.toLowerCase().includes(inputValue.toLowerCase()) || false))
                      }
                    />
                  )
                }
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}