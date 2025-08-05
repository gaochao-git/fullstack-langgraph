import { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Input, Modal, Form, message, 
  Tag, Tooltip, Row, Col, InputNumber, Select, App
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, 
  KeyOutlined, ReloadOutlined, SearchOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { permissionApi } from '../services/rbacApi';
import type { 
  RbacPermission, PermissionCreateRequest, PermissionUpdateRequest, PermissionQueryParams 
} from '../types/rbac';

const { Option } = Select;

export function PermissionManagement() {
  const { modal } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [permissions, setPermissions] = useState<RbacPermission[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState<RbacPermission | null>(null);
  const [form] = Form.useForm();
  
  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 100,
    total: 0,
  });
  const [searchText, setSearchText] = useState('');

  const columns: ColumnsType<RbacPermission> = [
    {
      title: '权限ID',
      dataIndex: 'permission_id',
      key: 'permission_id',
      width: 100,
      sorter: (a, b) => a.permission_id - b.permission_id,
    },
    {
      title: 'HTTP方法',
      dataIndex: 'http_method',
      key: 'http_method',
      filters: [
        { text: 'GET', value: 'GET' },
        { text: 'POST', value: 'POST' },
        { text: 'PUT', value: 'PUT' },
        { text: 'DELETE', value: 'DELETE' },
        { text: 'PATCH', value: 'PATCH' },
        { text: '全部(*)', value: '*' },
      ],
      onFilter: (value, record) => record.http_method === value,
      sorter: (a, b) => a.http_method.localeCompare(b.http_method),
      render: (method: string) => (
        <Tag color={
          method === 'GET' ? 'blue' :
          method === 'POST' ? 'green' :
          method === 'PUT' ? 'orange' :
          method === 'DELETE' ? 'red' :
          method === 'PATCH' ? 'purple' : 'default'
        }>
          {method}
        </Tag>
      ),
    },
    {
      title: '权限名称',
      dataIndex: 'permission_name',
      key: 'permission_name',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => a.permission_name.localeCompare(b.permission_name),
    },
    {
      title: '权限描述',
      dataIndex: 'permission_description',
      key: 'permission_description',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => a.permission_description.localeCompare(b.permission_description),
    },
    {
      title: '发布状态',
      dataIndex: 'release_disable',
      key: 'release_disable',
      filters: [
        { text: '启用', value: 'off' },
        { text: '禁用', value: 'on' },
      ],
      onFilter: (value, record) => record.release_disable === value,
      sorter: (a, b) => a.release_disable.localeCompare(b.release_disable),
      render: (status: string) => (
        <Tag color={status === 'off' ? 'green' : 'red'}>
          {status === 'off' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '删除状态',
      dataIndex: 'is_deleted',
      key: 'is_deleted',
      filters: [
        { text: '正常', value: 0 },
        { text: '已删除', value: 1 },
      ],
      onFilter: (value, record) => record.is_deleted === value,
      sorter: (a, b) => a.is_deleted - b.is_deleted,
      render: (status: number) => (
        <Tag color={status === 0 ? 'green' : 'volcano'}>
          {status === 0 ? '正常' : '已删除'}
        </Tag>
      ),
    },
    {
      title: '允许客户端',
      dataIndex: 'permission_allow_client',
      key: 'permission_allow_client',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => (a.permission_allow_client || '').localeCompare(b.permission_allow_client || ''),
      render: (text: string) => text || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => new Date(a.create_time).getTime() - new Date(b.create_time).getTime(),
    },
    {
      title: '修改时间',
      dataIndex: 'update_time',
      key: 'update_time',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => new Date(a.update_time).getTime() - new Date(b.update_time).getTime(),
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => a.create_by.localeCompare(b.create_by),
    },
    {
      title: '修改人',
      dataIndex: 'update_by',
      key: 'update_by',
      ellipsis: {
        showTitle: true,
      },
      sorter: (a, b) => a.update_by.localeCompare(b.update_by),
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      render: (_: any, record: RbacPermission) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              disabled={record.is_deleted === 1}
            />
          </Tooltip>
          {record.is_deleted === 0 && (
            <Tooltip title="删除">
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => {
                  console.log('删除按钮被点击，record:', record);
                  handleDelete(record);
                }}
              />
            </Tooltip>
          )}
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
        search: searchText || undefined,
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
  }, [pagination.current, pagination.pageSize]);

  const handleAdd = async () => {
    setEditingPermission(null);
    form.resetFields();
    
    // 自动生成权限ID（基于当前最大权限ID + 1）
    const maxPermissionId = permissions.reduce((max, perm) => 
      Math.max(max, perm.permission_id), 0
    );
    const nextPermissionId = maxPermissionId + 1;
    
    form.setFieldsValue({
      permission_id: nextPermissionId,
      http_method: 'GET', // 默认选择GET
      release_disable: 'off' // 默认启用
    });
    
    setModalVisible(true);
  };

  const handleEdit = (permission: RbacPermission) => {
    setEditingPermission(permission);
    form.setFieldsValue({
      permission_id: permission.permission_id,
      permission_name: permission.permission_name,
      permission_description: permission.permission_description,
      http_method: permission.http_method,
      release_disable: permission.release_disable,
      permission_allow_client: permission.permission_allow_client,
    });
    setModalVisible(true);
  };

  const handleDelete = (permission: RbacPermission) => {
    console.log('handleDelete函数被调用，权限:', permission);
    
    if (!permission) {
      console.error('权限数据为空');
      message.error('权限数据错误');
      return;
    }
    
    console.log('准备显示删除确认弹窗');
    
    modal.confirm({
      title: '确认删除',
      content: (
        <div>
          <p>确定要删除权限 <strong>"{permission.permission_name}"</strong> 吗？</p>
          <p style={{ color: '#999', fontSize: '12px' }}>删除后，关联该权限的所有角色将失去此权限。</p>
        </div>
      ),
      okText: '确定',
      cancelText: '取消',
      centered: true,
      onOk: async () => {
        try {
          console.log('开始删除权限，ID:', permission.permission_id);
          await permissionApi.deletePermission(permission.permission_id);
          // API成功时直接返回数据，失败时抛出异常
          message.success(`权限"${permission.permission_name}"删除成功`);
          fetchPermissions();
        } catch (error) {
          console.error('删除权限失败，详细错误:', error);
          const errorMessage = error instanceof Error ? error.message : '删除操作失败，请重试';
          message.error(errorMessage);
        }
      },
      onCancel: () => {
        console.log('用户取消删除');
      }
    });
  };


  const handleSubmit = async () => {
    try {
      setSubmitting(true);
      const values = await form.validateFields();
      
      if (editingPermission) {
        // 更新权限
        const updateData: PermissionUpdateRequest = {
          permission_name: values.permission_name,
          permission_description: values.permission_description,
          http_method: values.http_method,
          release_disable: values.release_disable,
          permission_allow_client: values.permission_allow_client,
        };
        
        await permissionApi.updatePermission(editingPermission.permission_id, updateData);
        // API成功时直接返回数据，失败时抛出异常
        message.success(`权限"${values.permission_name}"更新成功`);
        setModalVisible(false);
        form.resetFields();
        fetchPermissions();
      } else {
        // 创建权限
        const createData: PermissionCreateRequest = {
          permission_id: values.permission_id,
          permission_name: values.permission_name,
          permission_description: values.permission_description,
          http_method: values.http_method || '*',
          release_disable: values.release_disable || 'off',
          permission_allow_client: values.permission_allow_client,
        };
        
        await permissionApi.createPermission(createData);
        // API成功时直接返回数据，失败时抛出异常
        message.success(`权限"${values.permission_name}"创建成功`);
        setModalVisible(false);
        form.resetFields();
        fetchPermissions();
      }
    } catch (error) {
      console.error('操作失败:', error);
      const errorMessage = error instanceof Error ? error.message : '操作失败，请重试';
      message.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
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
            <KeyOutlined />
            权限管理
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="搜索权限名称"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              onPressEnter={() => {
                setPagination(prev => ({ ...prev, current: 1 }));
                fetchPermissions();
              }}
              onClear={() => {
                setSearchText('');
                setPagination(prev => ({ ...prev, current: 1 }));
                fetchPermissions();
              }}
              style={{ width: 200 }}
              allowClear
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
        <Table
          columns={columns}
          dataSource={permissions}
          loading={loading}
          rowKey="permission_id"
          scroll={{ x: 'max-content' }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            pageSizeOptions: ['20', '50', '100', '200'],
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
        width={800}
        destroyOnClose
        confirmLoading={submitting}
        okButtonProps={{
          disabled: submitting
        }}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="permission_id"
                label="权限ID"
                rules={[{ required: true, message: '请输入权限ID' }]}
              >
                <InputNumber 
                  placeholder="自动生成" 
                  style={{ width: '100%' }}
                  disabled={true}
                  min={1}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="permission_name"
                label="权限名称"
                rules={[{ required: true, message: '请输入权限名称' }]}
              >
                <Input placeholder="请输入权限名称" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="http_method"
                label="HTTP方法"
                rules={[{ required: true, message: '请选择HTTP方法' }]}
              >
                <Select placeholder="选择HTTP方法">
                  <Option value="GET">GET</Option>
                  <Option value="POST">POST</Option>
                  <Option value="PUT">PUT</Option>
                  <Option value="DELETE">DELETE</Option>
                  <Option value="PATCH">PATCH</Option>
                  <Option value="*">全部(*)</Option>
                </Select>
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