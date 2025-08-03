import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, SearchOutlined } from '@ant-design/icons';
import { tenantMockData, Tenant } from './tenantMockData';
import { useTheme } from '../../hooks/ThemeContext';

const { Option } = Select;

const TenantManagement: React.FC = () => {
  const { isDark } = useTheme();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [visible, setVisible] = useState<boolean>(false);
  const [detailVisible, setDetailVisible] = useState<boolean>(false);
  const [currentTenant, setCurrentTenant] = useState<Tenant | null>(null);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [searchText, setSearchText] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [form] = Form.useForm();

  // 模拟API加载数据
  useEffect(() => {
    setTimeout(() => {
      setTenants(tenantMockData);
      setLoading(false);
    }, 500);
  }, []);

  // 过滤数据
  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchText.toLowerCase()) ||
                          tenant.description.toLowerCase().includes(searchText.toLowerCase()) ||
                          tenant.domain.toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = statusFilter === 'all' || tenant.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // 打开创建/编辑模态框
  const openModal = (tenant?: Tenant) => {
    if (tenant) {
      setCurrentTenant(tenant);
      setIsEditing(true);
      form.setFieldsValue(tenant);
    } else {
      setCurrentTenant(null);
      setIsEditing(false);
      form.resetFields();
    }
    setVisible(true);
  };

  // 打开详情模态框
  const openDetailModal = (tenant: Tenant) => {
    setCurrentTenant(tenant);
    setDetailVisible(true);
  };

  // 保存租户
  const saveTenant = async () => {
    try {
      const values = await form.validateFields();
      let updatedTenants;

      if (isEditing && currentTenant) {
        updatedTenants = tenants.map(tenant =>
          tenant.id === currentTenant.id ? { ...tenant, ...values, updatedAt: new Date().toISOString() } : tenant
        );
        message.success('租户更新成功');
      } else {
        const newTenant: Tenant = {
          ...values,
          id: `tenant${Date.now()}`,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          userCount: 0
        };
        updatedTenants = [...tenants, newTenant];
        message.success('租户创建成功');
      }

      setTenants(updatedTenants);
      setVisible(false);
    } catch (error) {
      console.error('保存失败:', error);
    }
  };

  // 删除租户
  const deleteTenant = (id: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个租户吗？此操作不可撤销。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => {
        const updatedTenants = tenants.filter(tenant => tenant.id !== id);
        setTenants(updatedTenants);
        message.success('租户删除成功');
      }
    });
  };

  // 表格列配置
  const columns = [
      {
        title: '租户名称',
        dataIndex: 'name',
        key: 'name',
        sorter: (a: Tenant, b: Tenant) => a.name.localeCompare(b.name),
        render: (name: string) => <span className={isDark ? 'text-white' : 'text-gray-800'}>{name}</span>,
      },
      {
        title: '描述',
        dataIndex: 'description',
        key: 'description',
        render: (description: string) => <span className={isDark ? 'text-white' : 'text-gray-800'}>{description}</span>,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        filters: [
          { text: '全部', value: 'all' },
          { text: '活跃', value: 'active' },
          { text: '未激活', value: 'inactive' },
          { text: '已暂停', value: 'suspended' },
        ],
        onFilter: (value: any, record: Tenant) => {
          if (value === 'all') return true;
          return record.status === value;
        },
        render: (status: string) => {
          let color = 'default';
          switch (status) {
            case 'active':
              color = 'success';
              break;
            case 'inactive':
              color = 'default';
              break;
            case 'suspended':
              color = 'warning';
              break;
            default:
              color = 'default';
          }
          return <Tag color={color}>{status === 'active' ? '活跃' : status === 'inactive' ? '未激活' : '已暂停'}</Tag>;
        },
      },
      {
        title: '域名',
        dataIndex: 'domain',
        key: 'domain',
        render: (domain: string) => <span className={isDark ? 'text-white' : 'text-gray-800'}>{domain}</span>,
      },
      {
        title: '创建时间',
        dataIndex: 'createdAt',
        key: 'createdAt',
        sorter: (a: Tenant, b: Tenant) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
        render: (time: string) => <span className={isDark ? 'text-white' : 'text-gray-800'}>{new Date(time).toLocaleString()}</span>,
      },
      {
        title: '用户数量',
        dataIndex: 'userCount',
        key: 'userCount',
        sorter: (a: Tenant, b: Tenant) => a.userCount - b.userCount,
        render: (userCount: number) => <span className={isDark ? 'text-white' : 'text-gray-800'}>{userCount}</span>,
      },
      {
        title: '操作',
        key: 'action',
        render: (_: any, record: Tenant) => (
          <Space size="middle">
            <Button icon={<EyeOutlined />} onClick={() => openDetailModal(record)}>查看</Button>
            <Button icon={<EditOutlined />} onClick={() => openModal(record)}>编辑</Button>
            <Button icon={<DeleteOutlined />} danger onClick={() => deleteTenant(record.id)}>删除</Button>
          </Space>
        ),
      },
    ];

  return (
    <div className={`p-4 rounded-lg shadow-md ${isDark ? 'bg-slate-800' : 'bg-white'}`}>
      <div className="flex justify-between items-center mb-4">
        <h1 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-800'}`}>租户管理</h1>
        <div className="flex items-center space-x-2">
          <Input
            placeholder="搜索租户..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>创建租户</Button>
        </div>
      </div>

      <Table
        columns={columns}
        dataSource={filteredTenants}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 'max-content' }}
        tableLayout="fixed"
        style={{ backgroundColor: isDark ? '#0f172a' : '#fff',
          color: isDark ? '#fff' : '#000',
          borderColor: isDark ? '#334155' : '#e5e7eb'
        }}
      />

      {/* 创建/编辑租户模态框 */}
      <Modal
        title={isEditing ? '编辑租户' : '创建租户'}
        visible={visible}
        onOk={saveTenant}
        onCancel={() => setVisible(false)}
        bodyStyle={{ backgroundColor: isDark ? '#1e293b' : '#fff', color: isDark ? '#fff' : '#000' }}

      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="租户名称" rules={[{ required: true, message: '请输入租户名称' }]}>
            <Input placeholder="请输入租户名称" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入租户描述" />
          </Form.Item>
          <Form.Item name="domain" label="域名" rules={[{ required: true, message: '请输入域名' }]}>
            <Input placeholder="请输入域名" />
          </Form.Item>
          <Form.Item name="adminEmail" label="管理员邮箱" rules={[{ required: true, message: '请输入管理员邮箱' }]}>
            <Input placeholder="请输入管理员邮箱" />
          </Form.Item>
          {!isEditing && (
            <Form.Item name="status" label="状态" rules={[{ required: true }]}>
              <Select defaultValue="active">
                <Option value="active">活跃</Option>
                <Option value="inactive">未激活</Option>
              </Select>
            </Form.Item>
          )}
          {isEditing && (
            <Form.Item name="status" label="状态" rules={[{ required: true }]}>
              <Select>
                <Option value="active">活跃</Option>
                <Option value="inactive">未激活</Option>
                <Option value="suspended">已暂停</Option>
              </Select>
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 租户详情模态框 */}
      <Modal
        title="租户详情"
        visible={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        bodyStyle={{ backgroundColor: isDark ? '#1e293b' : '#fff', color: isDark ? '#fff' : '#000' }}
      >
        {currentTenant && (
          <div className="space-y-4">
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>租户名称:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{currentTenant.name}</span>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>描述:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{currentTenant.description}</span>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>状态:</span>
              <Tag color={currentTenant.status === 'active' ? 'success' : currentTenant.status === 'suspended' ? 'warning' : 'default'}>
                {currentTenant.status === 'active' ? '活跃' : currentTenant.status === 'inactive' ? '未激活' : '已暂停'}
              </Tag>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>域名:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{currentTenant.domain}</span>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>管理员邮箱:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{currentTenant.adminEmail}</span>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>创建时间:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{new Date(currentTenant.createdAt).toLocaleString()}</span>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>更新时间:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{new Date(currentTenant.updatedAt).toLocaleString()}</span>
            </div>
            <div className={`flex justify-between p-2 border-b ${isDark ? 'border-slate-700' : 'border-gray-200'}`}>
              <span className={`font-bold ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>用户数量:</span>
              <span className={isDark ? 'text-white' : 'text-gray-600'}>{currentTenant.userCount}</span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default TenantManagement;