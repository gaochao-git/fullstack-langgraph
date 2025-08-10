import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Card, Table, Button, Form, Input, Modal,
  Space, Alert, Tag, Tooltip, Switch, Radio,
  Select, Typography, Divider, Spin, App
} from 'antd';
import { 
  PlusOutlined, DeleteOutlined, CopyOutlined, 
  KeyOutlined, InfoCircleOutlined, ExclamationCircleOutlined,
  UserOutlined
} from '@ant-design/icons';
import { apiKeyService, APIKeyInfo, CreateAPIKeyRequest } from '@/services/apiKeyService';
import { permissionApi, userApi } from '@/pages/user/services/rbacApi';
import dayjs from 'dayjs';

const { Text, Paragraph } = Typography;

export function APIKeyManagement() {
  const { message, modal } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [apiKeys, setApiKeys] = useState<APIKeyInfo[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAPIKey, setNewAPIKey] = useState<string>('');
  const [createdKeyInfo, setCreatedKeyInfo] = useState<APIKeyInfo | null>(null);
  const [permissions, setPermissions] = useState<{
    label: string;
    value: number;
    description?: string;
    http_method: string;
    api_route: string;
    permission_name: string;
    module: string;
  }[]>([]);
  const [loadingPermissions, setLoadingPermissions] = useState(false);
  const [users, setUsers] = useState<{
    label: string;
    value: string;
    user_name: string;
    display_name?: string;
    email?: string;
  }[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'revoked'>('active');
  const [form] = Form.useForm();

  // 加载API密钥列表
  const loadAPIKeys = useCallback(async () => {
    setLoading(true);
    try {
      const keys = await apiKeyService.listAPIKeys();
      setApiKeys(keys);
    } catch {
      message.error('加载API密钥列表失败');
    } finally {
      setLoading(false);
    }
  }, [message]);

  // 加载API权限列表
  const loadPermissions = useCallback(async () => {
    setLoadingPermissions(true);
    try {
      const response = await permissionApi.listPermissions({ page: 1, page_size: 1000 });
      console.log('权限响应数据:', response); // 调试日志
      
      if (response.items) {
        // 将权限转换为Select组件需要的格式
        const permissionOptions = response.items
          .filter((perm: {
            release_disable?: string;
            permission_id: number;
            permission_name: string;
            permission_description?: string;
            http_method: string;
          }) => perm.release_disable !== 'on') // 只显示启用的权限
          .map((perm) => ({
            label: `${perm.http_method} ${perm.permission_name}${perm.permission_description ? ' - ' + perm.permission_description : ''}`,
            value: perm.permission_id, // 使用 permission_id 作为唯一值
            description: perm.permission_description,
            http_method: perm.http_method,
            api_route: perm.permission_name, // permission_name 就是 API 路由
            permission_name: perm.permission_name,
            module: perm.permission_name ? perm.permission_name.split('/')[3] : 'other' // 从路由提取模块名
          }));
        console.log('转换后的权限选项:', permissionOptions); // 调试日志
        setPermissions(permissionOptions);
      } else {
        console.warn('权限数据结构异常:', response);
        message.warning('权限数据为空');
      }
    } catch {
      message.error('加载权限列表失败');
    } finally {
      setLoadingPermissions(false);
    }
  }, [message]);

  // 加载用户列表
  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const response = await userApi.listUsers({ page: 1, page_size: 1000 });
      console.log('用户响应数据:', response); // 调试日志
      
      if (response.items) {
        // 将用户转换为Select组件需要的格式
        const userOptions = response.items
          .filter((user: {
            is_active: number;
            user_id: string;
            user_name: string;
            display_name?: string;
            email?: string;
          }) => user.is_active === 1) // 只显示激活的用户
          .map((user) => ({
            label: `${user.user_name} (${user.display_name || user.email || user.user_id})`,
            value: user.user_id,
            user_name: user.user_name,
            display_name: user.display_name,
            email: user.email
          }));
        console.log('转换后的用户选项:', userOptions); // 调试日志
        setUsers(userOptions);
      } else {
        console.warn('用户数据结构异常:', response);
        message.warning('用户数据为空');
      }
    } catch {
      message.error('加载用户列表失败');
    } finally {
      setLoadingUsers(false);
    }
  }, [message]);

  useEffect(() => {
    loadAPIKeys();
    loadPermissions();
    loadUsers();
  }, [loadAPIKeys, loadPermissions, loadUsers]);

  // 创建API密钥
  const handleCreateAPIKey = async (values: CreateAPIKeyRequest) => {
    try {
      const response = await apiKeyService.createAPIKey(values);
      setNewAPIKey(response.api_key);
      setCreatedKeyInfo(response.key_info);
      message.success('API密钥创建成功');
      loadAPIKeys();
      // 不要在这里重置表单，因为需要显示创建的密钥
    } catch {
      message.error('创建API密钥失败');
    }
  };

  // 切换激活状态
  const handleToggleStatus = async (keyId: string, keyName: string, currentStatus: boolean) => {
    try {
      const result = await apiKeyService.toggleAPIKeyStatus(keyId);
      message.success(result.message);
      loadAPIKeys();
    } catch (error: any) {
      console.error('切换状态失败:', error);
      const errorMsg = error?.message || error?.msg || '切换状态失败';
      message.error(errorMsg);
    }
  };

  // 撤销API密钥
  const handleRevokeAPIKey = (keyId: string, keyName: string) => {
    modal.confirm({
      title: '确认永久撤销',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要永久撤销API密钥 "{keyName}" 吗？</p>
          <Alert
            message="警告"
            description="撤销是永久性操作，无法恢复。如果只是想临时禁用，请使用启用/禁用开关。"
            type="warning"
            showIcon
            style={{ marginTop: 12 }}
          />
        </div>
      ),
      okText: '确认永久撤销',
      okType: 'danger',
      cancelText: '取消',
      width: 500,
      onOk: async () => {
        try {
          await apiKeyService.revokeAPIKey(keyId);
          message.success('API密钥已永久撤销');
          loadAPIKeys();
        } catch (error: any) {
          console.error('撤销API密钥失败:', error);
          const errorMsg = error?.message || error?.msg || '撤销失败';
          message.error(errorMsg);
        }
      }
    });
  };

  // 复制API密钥
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('已复制到剪贴板');
    }).catch(() => {
      message.error('复制失败');
    });
  };

  // 过滤后的数据
  const filteredApiKeys = useMemo(() => {
    if (statusFilter === 'all') {
      return apiKeys;
    } else if (statusFilter === 'active') {
      return apiKeys.filter(key => !key.revoked_at);
    } else {
      return apiKeys.filter(key => !!key.revoked_at);
    }
  }, [apiKeys, statusFilter]);

  const columns = [
    {
      title: '用户',
      dataIndex: 'user_name',
      key: 'user_name',
      filters: Array.from(new Set(apiKeys.map(k => k.user_name || k.user_id))).map(name => ({ text: name, value: name })),
      onFilter: (value: string, record: APIKeyInfo) => (record.user_name || record.user_id) === value,
      render: (text: string, record: APIKeyInfo) => (
        <Space>
          <UserOutlined />
          <Text>{record.user_name || record.user_id}</Text>
        </Space>
      )
    },
    {
      title: '名称',
      dataIndex: 'key_name',
      key: 'key_name',
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索名称"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      onFilter: (value: string, record: APIKeyInfo) => 
        record.key_name.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '工单号',
      dataIndex: 'mark_comment',
      key: 'mark_comment',
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: any) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索工单号"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              size="small"
              style={{ width: 90 }}
            >
              搜索
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              重置
            </Button>
          </Space>
        </div>
      ),
      onFilter: (value: string, record: APIKeyInfo) => 
        record.mark_comment?.toLowerCase().includes(value.toLowerCase()) || false,
      render: (text: string) => text || <Text type="secondary">-</Text>
    },
    {
      title: '密钥前缀',
      dataIndex: 'key_prefix',
      key: 'key_prefix',
      render: (text: string) => <Tag color="blue">{text}...</Tag>
    },
    {
      title: '权限范围',
      dataIndex: 'scopes',
      key: 'scopes',
      render: (scopes: number[] | undefined) => {
        if (!scopes || scopes.length === 0) {
          return <Text type="secondary">无权限</Text>;
        }
        
        // 获取第一个权限的信息
        const firstScope = scopes[0];
        const firstPerm = permissions.find(p => p.value === firstScope);
        
        if (!firstPerm) {
          return <Text type="secondary">无权限</Text>;
        }
        
        // 根据方法类型设置Tag颜色
        const methodColor = {
          'GET': 'green',
          'POST': 'blue',
          'PUT': 'orange',
          'DELETE': 'red',
          'PATCH': 'purple'
        }[firstPerm.http_method] || 'default';
        
        return (
          <Space size={4}>
            <Tag color={methodColor} style={{ borderRadius: 4 }}>
              {firstPerm.http_method}&nbsp;&nbsp;{firstPerm.api_route}
            </Tag>
            {scopes.length > 1 && (
              <Tooltip title={
                <div>
                  {scopes.map(scope => {
                    const perm = permissions.find(p => p.value === scope);
                    if (!perm) return null;
                    return (
                      <div key={scope} style={{ marginBottom: 4 }}>
                        {perm.http_method} {perm.api_route}
                        {perm.description && ` - ${perm.description}`}
                      </div>
                    );
                  })}
                </div>
              }>
                <span style={{ 
                  color: '#666', 
                  backgroundColor: '#f0f0f0', 
                  padding: '2px 8px', 
                  borderRadius: 4,
                  fontSize: 12
                }}>
                  +{scopes.length - 1}
                </span>
              </Tooltip>
            )}
          </Space>
        );
      }
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: (a: APIKeyInfo, b: APIKeyInfo) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm')
    },
    {
      title: '过期时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (text: string | undefined) => 
        text ? dayjs(text).format('YYYY-MM-DD HH:mm') : <Text type="secondary">永不过期</Text>
    },
    {
      title: '最后使用',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      render: (text: string | undefined) => 
        text ? dayjs(text).format('YYYY-MM-DD HH:mm') : <Text type="secondary">从未使用</Text>
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      render: (text: string) => text || <Text type="secondary">-</Text>
    },
    {
      title: '更新人',
      dataIndex: 'update_by',
      key: 'update_by',
      render: (text: string) => text || <Text type="secondary">-</Text>
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      filters: [
        { text: '启用', value: true },
        { text: '禁用', value: false },
      ],
      onFilter: (value: boolean, record: APIKeyInfo) => record.is_active === value,
      render: (active: boolean, record: APIKeyInfo) => {
        // 如果已经被撤销
        if (record.revoked_at) {
          return (
            <Tooltip title={`撤销时间: ${dayjs(record.revoked_at).format('YYYY-MM-DD HH:mm:ss')}${record.revoke_reason ? `\n原因: ${record.revoke_reason}` : ''}`}>
              <Tag color="error">已撤销</Tag>
            </Tooltip>
          );
        }
        // 如果已过期
        if (record.expires_at && new Date(record.expires_at) < new Date()) {
          return <Tag color="warning">已过期</Tag>;
        }
        // 正常的激活/禁用状态
        return (
          <Tag color={active ? 'success' : 'default'}>
            {active ? '启用' : '禁用'}
          </Tag>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      render: (_: unknown, record: APIKeyInfo) => {
        // 检查是否已过期
        const isExpired = record.expires_at && new Date(record.expires_at) < new Date();
        // 检查是否已撤销
        const isRevoked = !!record.revoked_at;
        
        return (
          <Space size="small">
            {!isRevoked && !isExpired && (
              <>
                <Switch
                  size="small"
                  checked={record.is_active}
                  onChange={() => handleToggleStatus(record.key_id, record.key_name, record.is_active)}
                  checkedChildren="启用"
                  unCheckedChildren="禁用"
                />
                <Button
                  type="link"
                  danger
                  size="small"
                  icon={<DeleteOutlined />}
                  onClick={() => handleRevokeAPIKey(record.key_id, record.key_name)}
                >
                  撤销
                </Button>
              </>
            )}
            {(isRevoked || isExpired) && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {isRevoked ? '已撤销' : '已过期'}
              </Text>
            )}
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      <Card 
        title={
          <Space>
            <KeyOutlined />
            <span>API密钥管理</span>
            <Tooltip 
              title={
                <div>
                  <div>• API密钥创建后只显示一次，请立即复制保存</div>
                  <div>• 使用Bearer Token认证方式：Authorization: Bearer &lt;token&gt;</div>
                  <div>• 建议为不同用途创建不同的密钥，便于管理和撤销</div>
                  <div>• 定期轮换密钥以保证安全</div>
                </div>
              }
              placement="bottomLeft"
            >
              <InfoCircleOutlined style={{ fontSize: 14, color: '#1890ff', marginLeft: 8 }} />
            </Tooltip>
          </Space>
        }
        extra={
          <Space>
            <Radio.Group 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              buttonStyle="solid"
            >
              <Radio.Button value="all">全部</Radio.Button>
              <Radio.Button value="active">未撤销</Radio.Button>
              <Radio.Button value="revoked">已撤销</Radio.Button>
            </Radio.Group>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setShowCreateModal(true)}
            >
              创建密钥
            </Button>
          </Space>
        }
      >
        <Table
          loading={loading}
          dataSource={filteredApiKeys}
          columns={columns}
          rowKey="key_id"
          scroll={{ x: 'max-content' }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            pageSizeOptions: ['10', '20', '50', '100'],
            defaultPageSize: 10,
          }}
        />
      </Card>

      {/* 创建API密钥对话框 */}
      <Modal
        title="创建API密钥"
        open={showCreateModal}
        onCancel={() => {
          setShowCreateModal(false);
          setNewAPIKey('');
          setCreatedKeyInfo(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        {newAPIKey ? (
          // 显示新创建的密钥
          <div>
            <Alert
              message="API密钥创建成功！"
              description="请立即复制并妥善保存，此密钥只显示一次。"
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Form layout="vertical">
              <Form.Item label="API Token">
                <Input.Password
                  value={newAPIKey}
                  readOnly
                  addonAfter={
                    <Button
                      type="text"
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(newAPIKey)}
                    >
                      复制
                    </Button>
                  }
                />
              </Form.Item>
            </Form>

            <Divider />
            
            <div>
              <Text strong>授权的权限：</Text>
              <div style={{ marginBottom: 16 }}>
                {createdKeyInfo && createdKeyInfo.scopes && createdKeyInfo.scopes.length > 0 ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {createdKeyInfo.scopes.map(scopeId => {
                      const perm = permissions.find(p => p.value === scopeId);
                      if (!perm) return null;
                      return (
                        <Tag key={scopeId} color={{
                          'GET': 'green',
                          'POST': 'blue',
                          'PUT': 'orange',
                          'DELETE': 'red',
                          'PATCH': 'purple'
                        }[perm.http_method] || 'default'}>
                          {perm.http_method} {perm.api_route}
                          {perm.description && ` - ${perm.description}`}
                        </Tag>
                      );
                    })}
                  </Space>
                ) : (
                  <Text type="secondary">无特定权限限制（完全访问）</Text>
                )}
              </div>
            </div>
            
            <Divider />
            
            <div>
              <Text strong>使用示例：</Text>
              <Paragraph>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  overflow: 'auto'
                }}>
{(() => {
  // 获取创建时选择的权限
  const selectedScopes = createdKeyInfo?.scopes || [];
  const selectedPermissions = permissions.filter(p => selectedScopes.includes(p.value));
  
  // 如果有选择权限，使用第一个权限作为示例
  let exampleUrl = 'http://localhost:8000/api/v1/auth/me';
  let exampleMethod = 'GET';
  
  if (selectedPermissions.length > 0) {
    const firstPerm = selectedPermissions[0];
    exampleUrl = `http://localhost:8000${firstPerm.api_route}`;
    exampleMethod = firstPerm.http_method;
  }
  
  // 根据方法生成不同的示例
  if (exampleMethod === 'GET') {
    return `# Python 示例
import requests

headers = {
    'Authorization': 'Bearer ${newAPIKey}'
}

response = requests.get(
    '${exampleUrl}',
    headers=headers
)
print(response.json())

# Shell 示例
curl -H "Authorization: Bearer ${newAPIKey}" \\
     ${exampleUrl}

# JavaScript 示例
const response = await fetch('${exampleUrl}', {
  headers: {
    'Authorization': 'Bearer ${newAPIKey}'
  }
});
const data = await response.json();
console.log(data);`;
  } else if (exampleMethod === 'POST') {
    return `# Python 示例
import requests

headers = {
    'Authorization': 'Bearer ${newAPIKey}',
    'Content-Type': 'application/json'
}

data = {
    # 根据接口要求填写请求数据
}

response = requests.post(
    '${exampleUrl}',
    headers=headers,
    json=data
)
print(response.json())

# Shell 示例
curl -X POST \\
     -H "Authorization: Bearer ${newAPIKey}" \\
     -H "Content-Type: application/json" \\
     -d '{"key": "value"}' \\
     ${exampleUrl}

# JavaScript 示例
const response = await fetch('${exampleUrl}', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ${newAPIKey}',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    // 根据接口要求填写请求数据
  })
});
const data = await response.json();
console.log(data);`;
  } else {
    // PUT/DELETE/PATCH 等其他方法
    return `# Python 示例
import requests

headers = {
    'Authorization': 'Bearer ${newAPIKey}',
    'Content-Type': 'application/json'
}

response = requests.${exampleMethod.toLowerCase()}(
    '${exampleUrl}',
    headers=headers
)
print(response.json())

# Shell 示例
curl -X ${exampleMethod} \\
     -H "Authorization: Bearer ${newAPIKey}" \\
     -H "Content-Type: application/json" \\
     ${exampleUrl}

# JavaScript 示例
const response = await fetch('${exampleUrl}', {
  method: '${exampleMethod}',
  headers: {
    'Authorization': 'Bearer ${newAPIKey}',
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
console.log(data);`;
  }
})()}
                </pre>
              </Paragraph>
            </div>

            <Button
              type="primary"
              block
              onClick={() => {
                setShowCreateModal(false);
                setNewAPIKey('');
                setCreatedKeyInfo(null);
                form.resetFields();
              }}
            >
              完成
            </Button>
          </div>
        ) : (
          // 创建表单
          <Form
            form={form}
            layout="vertical"
            onFinish={handleCreateAPIKey}
          >
            <Form.Item
              name="user_id"
              label="选择用户"
              rules={[{ required: true, message: '请选择用户' }]}
              extra="为哪个用户创建API密钥"
            >
              <Select
                placeholder="请选择用户"
                loading={loadingUsers}
                options={users}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                optionFilterProp="label"
                notFoundContent={loadingUsers ? <Spin size="small" /> : '暂无用户数据'}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item
              name="key_name"
              label="密钥名称"
              rules={[{ required: true, message: '请输入密钥名称' }]}
            >
              <Input 
                placeholder="例如：生产环境数据同步" 
                maxLength={100}
              />
            </Form.Item>

            <Form.Item
              name="mark_comment"
              label="工单号"
              rules={[{ required: true, message: '请输入工单号' }]}
              extra="请输入相关的工单号或申请单号，用于审计追踪"
            >
              <Input 
                placeholder="工单号" 
                maxLength={64}
              />
            </Form.Item>

            <Form.Item
              name="expires_in_days"
              label="有效期（天）"
              extra="留空表示永不过期"
            >
              <Input 
                type="number" 
                placeholder="例如：365" 
                min={1}
                max={3650}
              />
            </Form.Item>

            <Form.Item
              name="scopes"
              label="权限范围"
              rules={[{ required: true, message: '请选择至少一个权限' }]}
              extra="请选择API密钥可以访问的具体权限，安全起见，请只选择必要的权限"
            >
              <Select
                mode="multiple"
                placeholder="选择权限范围"
                loading={loadingPermissions}
                options={permissions}
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                showSearch
                optionFilterProp="label"
                notFoundContent={loadingPermissions ? <Spin size="small" /> : '暂无权限数据'}
                style={{ width: '100%' }}
                popupMatchSelectWidth={false}
                styles={{
                  popup: {
                    root: { maxHeight: 400, overflow: 'auto', minWidth: 500 }
                  }
                }}
                optionRender={(option) => (
                  <div style={{ padding: '4px 0' }}>
                    <Space size={4}>
                      <Tag size="small" color={
                        option.data.http_method === 'GET' ? 'green' :
                        option.data.http_method === 'POST' ? 'blue' :
                        option.data.http_method === 'PUT' ? 'orange' :
                        option.data.http_method === 'DELETE' ? 'red' : 'default'
                      }>
                        {option.data.http_method}
                      </Tag>
                      <span>{option.data.api_route}</span>
                      {option.data.description && (
                        <span style={{ color: '#666' }}>- {option.data.description}</span>
                      )}
                    </Space>
                  </div>
                )}
              />
            </Form.Item>

            <Form.Item
              name="allowed_ips"
              label="IP白名单"
              extra="限制只能从指定IP访问，留空表示不限制"
            >
              <Select
                mode="tags"
                placeholder="输入IP地址，如：192.168.1.100"
                tokenSeparators={[',', ' ']}
              />
            </Form.Item>

            <Form.Item>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button onClick={() => setShowCreateModal(false)}>
                  取消
                </Button>
                <Button type="primary" htmlType="submit">
                  创建
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
}