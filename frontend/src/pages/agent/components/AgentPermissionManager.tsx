import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  message, 
  Popconfirm,
  Tag,
  Tooltip,
  Typography,
  Empty,
  Spin,
  Switch
} from 'antd';
import { 
  PlusOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  CopyOutlined,
  KeyOutlined,
  UserOutlined
} from '@ant-design/icons';
import { agentApi } from '@/services/agentApi';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface Permission {
  id: number;
  agent_id: string;
  user_name: string;
  agent_key: string;
  agent_key_preview?: string;
  mark_comment: string;
  is_active: boolean;
  create_by: string;
  create_time: string;
}

interface AgentPermissionManagerProps {
  agentId: string;
  isEditable?: boolean;
}

const AgentPermissionManager: React.FC<AgentPermissionManagerProps> = ({ 
  agentId, 
  isEditable = true 
}) => {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [regeneratingKeys, setRegeneratingKeys] = useState<Set<number>>(new Set());
  const [togglingStatus, setTogglingStatus] = useState<Set<number>>(new Set());
  const [form] = Form.useForm();

  // 加载权限列表
  const loadPermissions = async () => {
    if (!agentId) return;
    
    setLoading(true);
    try {
      const response = await agentApi.listAgentPermissions(agentId);
      if (response.status === 'ok' && response.data) {
        setPermissions(response.data.items || []);
      }
    } catch (error) {
      message.error('加载权限列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (agentId) {
      loadPermissions();
    }
  }, [agentId]);

  // 创建权限
  const handleCreatePermission = async (values: any) => {
    try {
      const response = await agentApi.createAgentPermission(
        agentId,
        values.user_name,
        values.mark_comment
      );
      
      if (response.status === 'ok') {
        message.success('权限创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        loadPermissions();
      } else {
        // 使用 antd v5 的 message 用法
        message.error({
          content: response.msg || '权限创建失败',
          duration: 3,
        });
      }
    } catch (error) {
      message.error('权限创建失败');
    }
  };

  // 撤销权限
  const handleRevokePermission = async (permissionId: number) => {
    try {
      const response = await agentApi.revokeAgentPermission(permissionId);
      
      if (response.status === 'ok') {
        message.success('权限已撤销');
        loadPermissions();
      } else {
        message.error(response.msg || '撤销权限失败');
      }
    } catch (error) {
      message.error('撤销权限失败');
    }
  };

  // 重新生成密钥
  const handleRegenerateKey = async (permissionId: number) => {
    setRegeneratingKeys(prev => new Set(prev).add(permissionId));
    
    try {
      const response = await agentApi.regeneratePermissionKey(permissionId);
      
      if (response.status === 'ok') {
        message.success('密钥重新生成成功');
        loadPermissions();
      } else {
        message.error(response.msg || '重新生成密钥失败');
      }
    } catch (error) {
      message.error('重新生成密钥失败');
    } finally {
      setRegeneratingKeys(prev => {
        const newSet = new Set(prev);
        newSet.delete(permissionId);
        return newSet;
      });
    }
  };

  // 切换权限状态
  const handleToggleStatus = async (permissionId: number, isActive: boolean) => {
    setTogglingStatus(prev => new Set(prev).add(permissionId));
    
    try {
      const response = await agentApi.togglePermissionStatus(permissionId, isActive);
      
      if (response.status === 'ok') {
        message.success(response.msg || `权限已${isActive ? '启用' : '禁用'}`);
        loadPermissions();
      } else {
        message.error(response.msg || '切换权限状态失败');
      }
    } catch (error) {
      message.error('切换权限状态失败');
    } finally {
      setTogglingStatus(prev => {
        const newSet = new Set(prev);
        newSet.delete(permissionId);
        return newSet;
      });
    }
  };


  const columns: ColumnsType<Permission> = [
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 150,
      render: (text: string) => (
        <Space>
          <UserOutlined />
          <Text>{text}</Text>
        </Space>
      )
    },
    {
      title: '密钥',
      dataIndex: 'agent_key',
      key: 'agent_key',
      width: 200,
      render: (text: string, record: Permission) => {
        // 使用预览版本显示，如果没有则自行截取
        const displayKey = record.agent_key_preview || text.substring(0, 10) + '...';
        const fullKey = text;  // 完整密钥
        
        const handleCopy = () => {
          // 确保复制的是完整密钥
          navigator.clipboard.writeText(fullKey).then(() => {
            message.success('密钥已复制到剪贴板');
          }).catch(() => {
            // 降级方案：创建临时输入框
            const input = document.createElement('input');
            input.value = fullKey;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            message.success('密钥已复制到剪贴板');
          });
        };
        
        return (
          <Space>
            <Text code>{displayKey}</Text>
            <Tooltip title="复制完整密钥">
              <Button 
                size="small" 
                icon={<CopyOutlined />} 
                onClick={handleCopy}
              />
            </Tooltip>
          </Space>
        );
      }
    },
    {
      title: '工单号',
      dataIndex: 'mark_comment',
      key: 'mark_comment',
      width: 150,
      render: (text: string) => text ? (
        <Text>{text}</Text>
      ) : (
        <Text type="secondary">-</Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 120,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      fixed: 'right',
      render: (_: any, record: Permission) => (
        <Space size="small">
          <Switch
            size="small"
            checked={record.is_active}
            checkedChildren="启用"
            unCheckedChildren="禁用"
            loading={togglingStatus.has(record.id)}
            disabled={!isEditable}
            onChange={(checked) => handleToggleStatus(record.id, checked)}
          />
          <Tooltip title="重新生成密钥">
            <Button
              size="small"
              icon={<KeyOutlined />}
              onClick={() => handleRegenerateKey(record.id)}
              loading={regeneratingKeys.has(record.id)}
              disabled={!isEditable || !record.is_active}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除此权限吗？"
            description="删除后将永久移除此权限记录"
            onConfirm={() => handleRevokePermission(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={!isEditable}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className="mb-4">
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
            disabled={!isEditable}
          >
            创建权限
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadPermissions}
          >
            刷新
          </Button>
        </Space>
      </div>

      <Spin spinning={loading}>
        {permissions.length > 0 ? (
          <Table
            dataSource={permissions}
            columns={columns}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`
            }}
            scroll={{ x: 1200 }}
          />
        ) : (
          <Empty 
            description="暂无权限记录"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Spin>

      <Modal
        title="创建权限"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreatePermission}
        >
          <Form.Item
            label="授权用户名"
            name="user_name"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="请输入要授权的用户名" 
            />
          </Form.Item>

          <Form.Item
            label="工单号"
            name="mark_comment"
            extra="可选，用于记录授权原因或关联的工单"
          >
            <Input 
              placeholder="例如：TICKET-20240101" 
            />
          </Form.Item>

          <Form.Item className="mb-0">
            <Space className="w-full justify-end">
              <Button onClick={() => {
                setCreateModalVisible(false);
                form.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AgentPermissionManager;