import { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Input, Modal, Form, message, 
  Tag, Tooltip, Row, Col, InputNumber, Select, Statistic, Tabs
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, 
  KeyOutlined, ReloadOutlined, SettingOutlined, ApiOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { TabsProps } from 'antd';
import { permissionApi } from '../services/rbacApi';
import type { 
  RbacPermission, PermissionCreateRequest, PermissionUpdateRequest, PermissionQueryParams 
} from '../types/rbac';

const { Search } = Input;
const { Option } = Select;

export function PermissionManagement() {
  const [loading, setLoading] = useState(false);
  const [permissions, setPermissions] = useState<RbacPermission[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState<RbacPermission | null>(null);
  const [form] = Form.useForm();
  
  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filters, setFilters] = useState({
    release_disable: undefined as string | undefined,
  });
  const [activeTab, setActiveTab] = useState('all');

  const columns: ColumnsType<RbacPermission> = [
    {
      title: '权限ID',
      dataIndex: 'permission_id',
      key: 'permission_id',
      width: 100,
    },
    {
      title: '权限名称',
      dataIndex: 'permission_name',
      key: 'permission_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '权限描述',
      dataIndex: 'permission_description',
      key: 'permission_description',
      width: 200,
      ellipsis: true,
    },
    {
      title: '发布状态',
      dataIndex: 'release_disable',
      key: 'release_disable',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'off' ? 'green' : 'red'}>
          {status === 'off' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '允许客户端',
      dataIndex: 'permission_allow_client',
      key: 'permission_allow_client',
      width: 150,
      ellipsis: true,
      render: (text: string) => text || '-',
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
      width: 120,
      fixed: 'right',
      render: (_: any, record: RbacPermission) => (
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

  // 获取权限列表
  const fetchPermissions = async () => {
    try {
      setLoading(true);
      const params: PermissionQueryParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
        search: searchKeyword || undefined,
        release_disable: filters.release_disable,
      };
      
      const response = await permissionApi.listPermissions(params);
      console.log('权限API响应:', response);
      const items = response.items || [];
      console.log('设置权限数据:', items.length, '条');
      setPermissions(items);
      setPagination(prev => ({
        ...prev,
        total: response.pagination?.total || 0,
      }));
    } catch (error) {
      message.error('获取权限列表失败');
      console.error('获取权限列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, [pagination.current, pagination.pageSize, searchKeyword, filters]);

  const handleAdd = () => {
    setEditingPermission(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (permission: RbacPermission) => {
    setEditingPermission(permission);
    form.setFieldsValue({
      permission_id: permission.permission_id,
      permission_name: permission.permission_name,
      permission_description: permission.permission_description,
      release_disable: permission.release_disable,
      permission_allow_client: permission.permission_allow_client,
    });
    setModalVisible(true);
  };

  const handleDelete = (permission: RbacPermission) => {
    Modal.confirm({
      title: '确认删除',
      content: (
        <div>
          <p>确定要删除权限 <strong>"{permission.permission_name}"</strong> 吗？</p>
          <p className="text-gray-500">删除后，关联该权限的所有角色将失去此权限。</p>
        </div>
      ),
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await permissionApi.deletePermission(permission.permission_id);
          message.success('删除成功');
          fetchPermissions();
        } catch (error) {
          message.error('删除失败');
          console.error('删除权限失败:', error);
        }
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingPermission) {
        // 更新权限
        const updateData: PermissionUpdateRequest = {
          permission_name: values.permission_name,
          permission_description: values.permission_description,
          release_disable: values.release_disable,
          permission_allow_client: values.permission_allow_client,
        };
        
        await permissionApi.updatePermission(editingPermission.permission_id, updateData);
        message.success('更新成功');
        setModalVisible(false);
        form.resetFields();
        fetchPermissions();
      } else {
        // 创建权限
        const createData: PermissionCreateRequest = {
          permission_id: values.permission_id,
          permission_name: values.permission_name,
          permission_description: values.permission_description,
          release_disable: values.release_disable || 'off',
          permission_allow_client: values.permission_allow_client,
        };
        
        await permissionApi.createPermission(createData);
        message.success('创建成功');
        setModalVisible(false);
        form.resetFields();
        fetchPermissions();
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

  // 筛选数据
  const filteredPermissions = permissions.filter(permission => {
    if (activeTab === 'all') return true;
    if (activeTab === 'enabled') return permission.release_disable === 'off';
    if (activeTab === 'disabled') return permission.release_disable !== 'off';
    return true;
  });

  // 统计信息
  const totalPermissions = pagination.total;
  const enabledCount = permissions.filter(p => p.release_disable === 'off').length;
  const disabledCount = permissions.filter(p => p.release_disable !== 'off').length;

  const tabItems: TabsProps['items'] = [
    {
      key: 'all',
      label: `全部权限 (${totalPermissions})`,
    },
    {
      key: 'enabled',
      label: `启用 (${enabledCount})`,
    },
    {
      key: 'disabled',
      label: `禁用 (${disabledCount})`,
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <KeyOutlined />
            权限管理
          </Space>
        }
        extra={
          <Space>
            <Search
              placeholder="搜索权限名称、描述"
              allowClear
              style={{ width: 240 }}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchPermissions()}
              title="刷新"
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增权限
            </Button>
          </Space>
        }
      >
        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="总权限数"
              value={totalPermissions}
              prefix={<KeyOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="启用权限"
              value={enabledCount}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="禁用权限"
              value={disabledCount}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
        </Row>

        {/* 筛选器 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Select
              placeholder="选择发布状态"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters(prev => ({ ...prev, release_disable: value }))}
            >
              <Option value="off">启用</Option>
              <Option value="on">禁用</Option>
            </Select>
          </Col>
        </Row>

        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab} 
          items={tabItems}
          style={{ marginBottom: 16 }}
        />

        <Table
          columns={columns}
          dataSource={filteredPermissions}
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
        title={editingPermission ? '编辑权限' : '新增权限'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        okText="确定"
        cancelText="取消"
        width={600}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="permission_id"
                label="权限ID"
                rules={[{ required: true, message: '请输入权限ID' }]}
              >
                <InputNumber 
                  placeholder="请输入权限ID" 
                  style={{ width: '100%' }}
                  disabled={!!editingPermission}
                  min={1}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="permission_name"
                label="权限名称"
                rules={[{ required: true, message: '请输入权限名称' }]}
              >
                <Input placeholder="请输入权限名称" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="permission_description"
            label="权限描述"
            rules={[{ required: true, message: '请输入权限描述' }]}
          >
            <Input.TextArea 
              placeholder="请输入权限描述" 
              rows={3} 
              showCount 
              maxLength={200}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="release_disable"
                label="发布状态"
                initialValue="off"
              >
                <Select>
                  <Option value="off">启用</Option>
                  <Option value="on">禁用</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="permission_allow_client"
                label="允许客户端"
              >
                <Input placeholder="允许访问的客户端列表" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}