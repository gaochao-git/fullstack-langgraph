// @ts-nocheck
import React, { useState } from 'react';
import { Card, Button, Form, Input, Select, Table, Space, message, Modal } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;

interface Application {
  id: string;
  host_id: string;
  server_type: string;
  server_version: string;
  cluster_name: string;
}

const BatchApplicationManagement: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const columns = [
    {
      title: '主机ID',
      dataIndex: 'host_id',
      key: 'host_id',
    },
    {
      title: '服务类型',
      dataIndex: 'server_type',
      key: 'server_type',
    },
    {
      title: '服务版本',
      dataIndex: 'server_version',
      key: 'server_version',
    },
    {
      title: '集群名称',
      dataIndex: 'cluster_name',
      key: 'cluster_name',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: Application) => (
        <Space size="middle">
          <Button type="link" icon={<EditOutlined />}>
            编辑
          </Button>
          <Button type="link" danger icon={<DeleteOutlined />}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const handleAddApplication = () => {
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    console.log('批量应用管理提交:', values);
    message.success('应用添加成功');
    setIsModalVisible(false);
    form.resetFields();
  };

  return (
    <div>
      <Card
        title="批量应用管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAddApplication}>
            添加应用
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={applications}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="添加应用"
        open={isModalVisible}
        onCancel={handleCancel}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="服务类型"
            name="server_type"
            rules={[{ required: true, message: '请选择服务类型' }]}
          >
            <Select placeholder="选择服务类型">
              <Option value="mysql">MySQL</Option>
              <Option value="mssql">MS SQL Server</Option>
              <Option value="tidb">TiDB</Option>
              <Option value="goldendb">GoldenDB</Option>
              <Option value="redis">Redis</Option>
              <Option value="mongodb">MongoDB</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="服务版本"
            name="server_version"
          >
            <Input placeholder="请输入服务版本" />
          </Form.Item>

          <Form.Item
            label="集群名称"
            name="cluster_name"
          >
            <Input placeholder="请输入集群名称" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                添加
              </Button>
              <Button onClick={handleCancel}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default BatchApplicationManagement;