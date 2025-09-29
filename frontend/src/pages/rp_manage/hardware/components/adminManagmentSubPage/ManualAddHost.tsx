// @ts-nocheck
import React, { useState } from 'react';
import { Card, Button, Form, Input, Select, Row, Col, message, Tabs, InputNumber } from 'antd';
import { PlusOutlined, SaveOutlined } from '@ant-design/icons';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

const ManualAddHost: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      console.log('手动添加主机:', values);
      message.success('主机添加成功');
      form.resetFields();
    } catch (error) {
      console.error('添加主机失败:', error);
      message.error('添加主机失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    form.resetFields();
  };

  return (
    <Card title="手动添加主机">
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Tabs defaultActiveKey="basic">
          <TabPane tab="基本信息" key="basic">
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label="主机IP"
                  name="hostIp"
                  rules={[
                    { required: true, message: '请输入主机IP' },
                    {
                      pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
                      message: '请输入有效的IP地址'
                    }
                  ]}
                >
                  <Input placeholder="请输入主机IP地址" />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="主机名"
                  name="hostName"
                  rules={[{ required: true, message: '请输入主机名' }]}
                >
                  <Input placeholder="请输入主机名" />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="主机类型"
                  name="hostType"
                  rules={[{ required: true, message: '请选择主机类型' }]}
                >
                  <Select placeholder="选择主机类型">
                    <Option value="0">Cloud Host</Option>
                    <Option value="1">Bare Metal</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label="操作系统"
                  name="operatingSystem"
                >
                  <Input placeholder="请输入操作系统" />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="CPU核数"
                  name="cpuCores"
                >
                  <InputNumber placeholder="CPU核数" style={{ width: '100%' }} />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="内存大小(GB)"
                  name="memorySize"
                >
                  <InputNumber placeholder="内存大小" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label="磁盘大小(GB)"
                  name="diskSize"
                >
                  <InputNumber placeholder="磁盘大小" style={{ width: '100%' }} />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="所属部门"
                  name="department"
                >
                  <Input placeholder="请输入所属部门" />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="管理员"
                  name="admin"
                >
                  <Input placeholder="请输入管理员" />
                </Form.Item>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="应用信息" key="application">
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label="服务类型"
                  name="serverType"
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
              </Col>

              <Col span={8}>
                <Form.Item
                  label="服务版本"
                  name="serverVersion"
                >
                  <Input placeholder="请输入服务版本" />
                </Form.Item>
              </Col>

              <Col span={8}>
                <Form.Item
                  label="服务端口"
                  name="serverPort"
                >
                  <InputNumber placeholder="服务端口" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label="集群名称"
                  name="clusterName"
                >
                  <Input placeholder="请输入集群名称" />
                </Form.Item>
              </Col>

              <Col span={12}>
                <Form.Item
                  label="服务地址"
                  name="serverAddress"
                >
                  <Input placeholder="请输入服务地址" />
                </Form.Item>
              </Col>
            </Row>
          </TabPane>

          <TabPane tab="其他信息" key="other">
            <Row gutter={16}>
              <Col span={24}>
                <Form.Item
                  label="备注"
                  name="remarks"
                >
                  <TextArea
                    rows={4}
                    placeholder="请输入备注信息"
                  />
                </Form.Item>
              </Col>
            </Row>
          </TabPane>
        </Tabs>

        <Form.Item>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<SaveOutlined />}
            style={{ marginRight: 8 }}
          >
            保存主机
          </Button>
          <Button onClick={handleReset}>
            重置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ManualAddHost;