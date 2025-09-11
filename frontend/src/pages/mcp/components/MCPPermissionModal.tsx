import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Button,
  Form,
  Input,
  Tag,
  Space,
  App,
  Switch,
  Popconfirm,
  Typography,
  Tooltip,
  message as antdMessage
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  KeyOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';

const { Text } = Typography;

interface Permission {
  id: number;
  server_id: string;
  user_name: string;
  server_key: string;
  is_active: number;
  mark_comment: string;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

interface Props {
  visible: boolean;
  server: {
    id: string;
    name: string;
  } | null;
  onClose: () => void;
}


const MCPPermissionModal: React.FC<Props> = ({ visible, server, onClose }) => {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  // 获取权限列表
  const fetchPermissions = async () => {
    if (!server) return;
    
    setLoading(true);
    try {
      const result = await omind_get(`/api/v1/mcp/servers/${server.id}/permissions`);
      if (result.status === 'ok') {
        setPermissions(result.data);
      } else {
        message.error(result.msg || '获取权限列表失败');
      }
    } catch (error) {
      console.error('获取权限列表错误:', error);
      message.error('获取权限列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 添加权限
  const handleAddPermission = async (values: any) => {
    if (!server) return;

    try {
      // 转换 is_active 从布尔值到数字
      const data = {
        ...values,
        is_active: values.is_active ? 1 : 0
      };
      const result = await omind_post(`/api/v1/mcp/servers/${server.id}/permissions`, data);
      
      if (result.status === 'ok') {
        message.success('权限添加成功');
        setAddModalVisible(false);
        form.resetFields();
        await fetchPermissions();
      } else {
        message.error(result.msg || '添加权限失败');
      }
    } catch (error) {
      console.error('添加权限错误:', error);
      message.error('添加权限失败');
    }
  };

  // 更新权限状态
  const handleToggleActive = async (permission: Permission) => {
    if (!server) return;

    try {
      const result = await omind_put(
        `/api/v1/mcp/servers/${server.id}/permissions/${permission.id}`,
        { is_active: permission.is_active ? 0 : 1 }  // 切换状态：如果当前是1（激活）则改为0，反之亦然
      );
      
      if (result.status === 'ok') {
        message.success('状态更新成功');
        await fetchPermissions();
      } else {
        message.error(result.msg || '更新状态失败');
      }
    } catch (error) {
      console.error('更新状态错误:', error);
      message.error('更新状态失败');
    }
  };

  // 删除权限
  const handleDeletePermission = async (permission: Permission) => {
    if (!server) return;

    try {
      const result = await omind_del(`/api/v1/mcp/servers/${server.id}/permissions/${permission.id}`);
      
      if (result.status === 'ok') {
        message.success('权限删除成功');
        await fetchPermissions();
      } else {
        message.error(result.msg || '删除权限失败');
      }
    } catch (error) {
      console.error('删除权限错误:', error);
      message.error('删除权限失败');
    }
  };

  // 重新生成密钥
  const handleRegenerateKey = async (permission: Permission) => {
    if (!server) return;

    try {
      const newKey = `sk_${Math.random().toString(36).substr(2, 9)}_${Date.now()}`;
      const result = await omind_put(
        `/api/v1/mcp/servers/${server.id}/permissions/${permission.id}`,
        { server_key: newKey }
      );
      
      if (result.status === 'ok') {
        message.success('密钥重新生成成功');
        await fetchPermissions();
      } else {
        message.error(result.msg || '重新生成密钥失败');
      }
    } catch (error) {
      console.error('重新生成密钥错误:', error);
      message.error('重新生成密钥失败');
    }
  };

  useEffect(() => {
    if (visible && server) {
      fetchPermissions();
    }
  }, [visible, server]);

  const columns: ColumnsType<Permission> = [
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
      width: 120,
    },
    {
      title: '密钥',
      dataIndex: 'server_key',
      key: 'server_key',
      width: 200,
      render: (key: string) => (
        <Space size="small">
          <Text code copyable={{ text: key }}>
            {key.substr(0, 10)}...{key.substr(-6)}
          </Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: number, record: Permission) => (
        <Switch
          checked={!!active}
          onChange={() => handleToggleActive(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '备注',
      dataIndex: 'mark_comment',
      key: 'mark_comment',
      width: 150,
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 160,
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record: Permission) => (
        <Space size="small">
          <Tooltip title="重新生成密钥">
            <Popconfirm
              title="重新生成密钥"
              description="确定要重新生成密钥吗？旧密钥将失效。"
              onConfirm={() => handleRegenerateKey(record)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined />}
              />
            </Popconfirm>
          </Tooltip>
          <Popconfirm
            title="删除权限"
            description="确定要删除这个权限吗？"
            onConfirm={() => handleDeletePermission(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Modal
        title={`权限管理 - ${server?.name || ''}`}
        open={visible}
        onCancel={onClose}
        width={900}
        footer={[
          <Button key="close" onClick={onClose}>
            关闭
          </Button>,
        ]}
      >
        <div style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setAddModalVisible(true)}
          >
            添加权限
          </Button>
        </div>

        <Table
          dataSource={permissions}
          columns={columns}
          rowKey="id"
          loading={loading}
          size="small"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Modal>

      <Modal
        title="添加权限"
        open={addModalVisible}
        onCancel={() => {
          setAddModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddPermission}
          initialValues={{
            is_active: true,
            mark_comment: '',
          }}
        >
          <Form.Item
            name="user_name"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="请输入要授权的用户名" />
          </Form.Item>

          <Form.Item
            name="mark_comment"
            label="备注/工单号"
          >
            <Input placeholder="请输入备注信息或工单号" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="立即启用"
            valuePropName="checked"
          >
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default MCPPermissionModal;