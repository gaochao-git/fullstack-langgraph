// @ts-nocheck
// 主机资源池详情页（弹出）
import React, { useState, useEffect } from 'react';
import { Descriptions, Card, Typography, Button, Modal, Form, Input, Select, Popconfirm, message, Row, Col, Tag, Divider, InputNumber, Space } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import './HostPoolStyles.css';

const { Option } = Select;

const HostDetail = ({ host, onRefresh }) => {
  const [editingApp, setEditingApp] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [localHostData, setLocalHostData] = useState(host);

  // 当父组件传入的host数据变化时，更新本地状态
  useEffect(() => {
    setLocalHostData(host);
  }, [host]);

  const formatValue = (key, value) => {
    if (key === 'host_type') {
      return value === '0' ? 'Cloud Host' : 'Bare Metal';
    }
    if (key === 'is_deleted' || key === 'is_static') {
      return value ? 'Yes' : 'No';
    }
    if (key === 'create_time' || key === 'update_time') {
      return new Date(value).toLocaleString();
    }
    return value?.toString() || 'N/A';
  };

  const handleAddApplication = () => {
    setEditingApp(null);
    setIsModalVisible(true);
  };

  const handleEditApplication = (app) => {
    setEditingApp(app);
    setIsModalVisible(true);
  };

  const handleDeleteApplication = async (appId) => {
    try {
      setLoading(true);
      const response = await apiClient.delete('/api/cmdb/v1/delete_hosts_application', {
        app_ids: [parseInt(appId, 10)]
      });
      
      if (response.data.success) {
        message.success('Application deleted successfully');
        
        // 立即从本地数据中移除该应用
        setLocalHostData(prevHost => ({
          ...prevHost,
          host_applications: prevHost.host_applications.filter(app => app.id !== appId)
        }));
        
        // 同时通知父组件刷新数据
        if (onRefresh) onRefresh();
      } else {
        message.error(response.data.message || 'Failed to delete application');
      }
    } catch (error) {
      console.error('删除应用失败:', error);
      message.error('Failed to delete application');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setEditingApp(null);
  };

  return (
    <div className="host-detail-container">
      <div className="host-detail-section">
        <Typography.Title level={4} className="host-detail-title">Host Basic Information</Typography.Title>
        <Descriptions bordered column={3} size="small">
          {Object.entries(localHostData).map(([key, value]) => {
            if (key !== 'host_applications' && key !== 'idc_info') {
              return (
                <Descriptions.Item 
                  key={`host-${key}`} 
                  label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                >
                  {formatValue(key, value)}
                </Descriptions.Item>
              );
            }
            return null;
          })}
        </Descriptions>

        {/* IDC信息单独显示 */}
        {localHostData.idc_info && (
          <>
            <Divider orientation="left">IDC Machine Room Information</Divider>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Machine Room Name">
                <Tag color="blue">{localHostData.idc_info.idc_name}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Machine Room Code">
                <Tag color="green">{localHostData.idc_info.idc_code}</Tag>
              </Descriptions.Item>
              {localHostData.idc_info.idc_location && (
                <Descriptions.Item label="Location" span={2}>
                  {localHostData.idc_info.idc_location}
                </Descriptions.Item>
              )}
              {localHostData.idc_info.idc_description && (
                <Descriptions.Item label="Description" span={2}>
                  {localHostData.idc_info.idc_description}
                </Descriptions.Item>
              )}
            </Descriptions>
          </>
        )}
        
        {!localHostData.idc_info && (
          <>
            <Divider orientation="left">IDC Machine Room Information</Divider>
            <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>
              <ExclamationCircleOutlined style={{ marginRight: '8px' }} />
              No IDC information available for this host
            </div>
          </>
        )}
      </div>
      
      <div className="applications-section">
        <Row type="flex" justify="space-between" align="middle" style={{ marginBottom: '16px' }}>
          <Col>
            <Typography.Title level={4} className="host-detail-title">Application Information</Typography.Title>
          </Col>
          <Col>
            <Button 
              type="primary" 
              onClick={handleAddApplication}
              size="small"
            >
              <PlusOutlined />
              Add Application
            </Button>
          </Col>
        </Row>
        
        {localHostData.host_applications && localHostData.host_applications.map((app, index) => (
          <Card 
            key={`app-${app.id || index}`} 
            title={
              <Row type="flex" justify="space-between" align="middle">
                <Col>
                  <span className="application-title">Application {index + 1}</span>
                </Col>
                <Col>
                  <Button 
                    type="link" 
                    onClick={() => handleEditApplication(app)}
                    size="small"
                    style={{ marginRight: '8px' }}
                  >
                    <EditOutlined />
                    Edit
                  </Button>
                  <Popconfirm
                    title="Are you sure to delete this application?"
                    onConfirm={() => handleDeleteApplication(app.id)}
                    okText="OK"
                    cancelText="Cancel"
                  >
                    <Button 
                      type="link" 
                      style={{ color: 'red' }}
                      size="small"
                    >
                      <DeleteOutlined />
                      Delete
                    </Button>
                  </Popconfirm>
                </Col>
              </Row>
            }
            className="application-card"
            size="small"
          >
            <Descriptions bordered column={2} size="small">
              {Object.entries(app).map(([key, value]) => (
                <Descriptions.Item 
                  key={`app-${app.id || index}-${key}`} 
                  label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                >
                  {formatValue(key, value)}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        ))}
      </div>

      <ApplicationModal
        visible={isModalVisible}
        editingApp={editingApp}
        hostId={localHostData.id}
        onCancel={handleCancel}
        onSuccess={() => {
          setIsModalVisible(false);
          setEditingApp(null);
          if (onRefresh) onRefresh();
        }}
      />
    </div>
  );
};

// 单独的应用编辑模态框组件
interface ApplicationModalProps {
  visible: boolean;
  editingApp: any;
  hostId: string;
  onCancel: () => void;
  onSuccess: () => void;
}


const ApplicationModal: React.FC<ApplicationModalProps> = ({ visible, editingApp, hostId, onCancel, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (visible && editingApp) {
      form.setFieldsValue(editingApp);
    } else {
      form.resetFields();
    }
  }, [visible, editingApp, form]);

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      // 简化版本，添加基本的保存逻辑
      console.log('Saving application:', values);
      onSuccess();
    } catch (error) {
      console.error('Error saving application:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={editingApp ? "Edit Application" : "Add Application"}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={editingApp || {}}
      >
        <Form.Item
          name="server_type"
          label="Service Type"
          rules={[{ required: true, message: '请选择应用类型' }]}
        >
          <Select placeholder="Select service type">
            <Option value="mysql">MySQL</Option>
            <Option value="mssql">MS SQL Server</Option>
            <Option value="tidb">TiDB</Option>
            <Option value="goldendb">GoldenDB</Option>
            <Option value="redis">Redis</Option>
            <Option value="mongodb">MongoDB</Option>
            <Option value="other">Other</Option>
          </Select>
        </Form.Item>

        <Form.Item name="server_version" label="Service Version">
          <Input placeholder="Enter service version" />
        </Form.Item>

        <Form.Item name="server_subtitle" label="Service Subtitle">
          <Input placeholder="Enter service subtitle" />
        </Form.Item>

        <Form.Item name="cluster_name" label="Cluster Name">
          <Input placeholder="Enter cluster name" />
        </Form.Item>

        <Form.Item name="server_addr" label="Server Address">
          <Input placeholder="Enter server address" />
        </Form.Item>

        <Form.Item name="server_port" label="Server Port">
          <InputNumber placeholder="Enter server port" style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {editingApp ? 'Update' : 'Add'} Application
            </Button>
            <Button onClick={onCancel}>Cancel</Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

// 导出 ApplicationModal 组件供内部使用
const ApplicationModalComponent = ApplicationModal;

export default HostDetail;