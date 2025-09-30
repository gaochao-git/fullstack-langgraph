// @ts-nocheck
// 主机资源池详情页（弹出）
import React, { useState, useEffect } from 'react';
import { Descriptions, Card, Typography, Button, Modal, Form, Input, Select, Popconfirm, message, Row, Col, Tag, Divider, InputNumber, Space, Badge } from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  DesktopOutlined,
  CloudOutlined,
  HddOutlined,
  SafetyOutlined,
  EnvironmentOutlined,
  NumberOutlined,
  ApiOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  HomeOutlined,
  BarcodeOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import './HostPoolStyles.css';

const { Option } = Select;

// 字段中文名映射
const FIELD_LABELS = {
  // 基础信息
  id: '主机ID',
  host_name: '主机名称',
  host_ip: 'IP地址',
  host_type: '主机类型',

  // 硬件配置
  vcpus: 'CPU核心数',
  ram: '内存容量',
  disk_size: '磁盘容量',
  serial_number: '序列号',

  // 机架信息
  rack_number: '机架编号',
  rack_height: '机架高度',
  rack_start_number: '机架起始位置',
  leaf_number: '叶子节点编号',
  from_factor: '形态因子',

  // H3C信息
  h3c_id: 'H3C ID',
  h3c_status: 'H3C状态',
  if_h3c_sync: 'H3C同步状态',
  h3c_img_id: 'H3C镜像ID',
  h3c_hm_name: 'H3C主机名',

  // 状态信息
  is_deleted: '删除状态',
  is_static: '静态配置',
  is_delete: '标记删除',
  create_time: '创建时间',
  update_time: '更新时间',
};

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
    if (value === null || value === undefined || value === '') {
      return <span style={{ color: '#ccc' }}>未设置</span>;
    }

    // 主机类型
    if (key === 'host_type') {
      const isCloud = value === '0';
      return (
        <Tag icon={isCloud ? <CloudOutlined /> : <DesktopOutlined />} color={isCloud ? 'blue' : 'purple'}>
          {isCloud ? '云主机' : '裸金属服务器'}
        </Tag>
      );
    }

    // 布尔值
    if (key === 'is_deleted' || key === 'is_static') {
      return (
        <Tag icon={<CheckCircleOutlined />} color={value ? 'red' : 'green'}>
          {value ? '是' : '否'}
        </Tag>
      );
    }

    // 时间字段
    if (key === 'create_time' || key === 'update_time') {
      return <span style={{ color: '#666' }}>{new Date(value).toLocaleString('zh-CN')}</span>;
    }

    // 硬件字段带单位和颜色
    if (key === 'ram') {
      return <Tag color="green" icon={<HddOutlined />}>{value} GB</Tag>;
    }
    if (key === 'disk_size') {
      return <Tag color="orange" icon={<DatabaseOutlined />}>{value} GB</Tag>;
    }
    if (key === 'vcpus') {
      return <Tag color="blue" icon={<ApiOutlined />}>{value} 核</Tag>;
    }
    if (key === 'rack_height') {
      return <Tag color="cyan">{value} U</Tag>;
    }

    // ID字段
    if (key === 'id' || key.includes('_id')) {
      return <code style={{ background: '#f5f5f5', padding: '2px 8px', borderRadius: '4px' }}>{value}</code>;
    }

    // IP地址
    if (key === 'host_ip') {
      return <code style={{ background: '#e6f7ff', padding: '2px 8px', borderRadius: '4px', color: '#1890ff' }}>{value}</code>;
    }

    // H3C同步状态
    if (key === 'if_h3c_sync') {
      return <Tag icon={<SyncOutlined />} color="processing">{value}</Tag>;
    }

    return value.toString();
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
      const response = await apiClient.delete('cmdb/v1/delete_hosts_application', {
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

  // 字段分组
  const basicFields = ['id', 'host_name', 'host_ip', 'host_type'];
  const hardwareFields = ['vcpus', 'ram', 'disk_size', 'serial_number'];
  const rackFields = ['rack_number', 'rack_height', 'rack_start_number', 'leaf_number', 'from_factor'];
  const h3cFields = ['h3c_id', 'h3c_status', 'if_h3c_sync', 'h3c_img_id', 'h3c_hm_name'];
  const statusFields = ['is_deleted', 'is_static', 'is_delete', 'create_time', 'update_time'];

  // 获取分组图标
  const getSectionIcon = (title: string) => {
    const iconMap = {
      '硬件配置': <HddOutlined style={{ color: '#52c41a' }} />,
      '机架信息': <HomeOutlined style={{ color: '#1890ff' }} />,
      'H3C信息': <SafetyOutlined style={{ color: '#faad14' }} />,
      '状态信息': <CheckCircleOutlined style={{ color: '#722ed1' }} />,
    };
    return iconMap[title] || <NumberOutlined />;
  };

  const renderFieldGroup = (title: string, fields: string[]) => {
    return (
      <Card
        size="small"
        style={{ marginBottom: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
        title={
          <span style={{ fontSize: 16, fontWeight: 600 }}>
            {getSectionIcon(title)}
            <span style={{ marginLeft: 8 }}>{title}</span>
          </span>
        }
      >
        <Descriptions bordered column={2} size="small" labelStyle={{ fontWeight: 500, background: '#fafafa' }}>
          {fields.map(key => {
            const value = localHostData[key];
            return (
              <Descriptions.Item
                key={`host-${key}`}
                label={FIELD_LABELS[key] || key}
              >
                {formatValue(key, value)}
              </Descriptions.Item>
            );
          })}
        </Descriptions>
      </Card>
    );
  };

  return (
    <div className="host-detail-container" style={{ background: '#f5f7fa', padding: '16px' }}>
      <div className="host-detail-section">
        {/* 基础信息 - 重点突出 */}
        <Card
          size="small"
          style={{ marginBottom: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.08)', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          bodyStyle={{ padding: 0 }}
        >
          <div style={{ background: 'white', borderRadius: '8px', padding: '16px' }}>
            <div style={{ marginBottom: 12 }}>
              <DesktopOutlined style={{ fontSize: 20, color: '#667eea', marginRight: 8 }} />
              <span style={{ fontSize: 18, fontWeight: 600, color: '#333' }}>基础信息</span>
            </div>
            <Descriptions bordered column={2} size="small" labelStyle={{ fontWeight: 500, background: '#fafafa' }}>
              {basicFields.map(key => {
                const value = localHostData[key];
                return (
                  <Descriptions.Item
                    key={`host-${key}`}
                    label={FIELD_LABELS[key] || key}
                  >
                    {formatValue(key, value)}
                  </Descriptions.Item>
                );
              })}
            </Descriptions>
          </div>
        </Card>

        {/* 硬件配置 */}
        {renderFieldGroup('硬件配置', hardwareFields)}

        {/* 机架信息 */}
        {renderFieldGroup('机架信息', rackFields)}

        {/* H3C信息 */}
        {renderFieldGroup('H3C信息', h3cFields)}

        {/* 状态信息 */}
        {renderFieldGroup('状态信息', statusFields)}

        {/* IDC信息单独显示 */}
        {localHostData.idc_info && (
          <Card
            size="small"
            style={{ marginBottom: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
            title={
              <span style={{ fontSize: 16, fontWeight: 600 }}>
                <EnvironmentOutlined style={{ color: '#eb2f96' }} />
                <span style={{ marginLeft: 8 }}>IDC机房信息</span>
              </span>
            }
          >
            <Descriptions bordered column={2} size="small" labelStyle={{ fontWeight: 500, background: '#fafafa' }}>
              <Descriptions.Item label="机房名称">
                <Tag color="blue" icon={<HomeOutlined />}>{localHostData.idc_info.idc_name}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="机房代码">
                <Tag color="green" icon={<BarcodeOutlined />}>{localHostData.idc_info.idc_code}</Tag>
              </Descriptions.Item>
              {localHostData.idc_info.idc_location && (
                <Descriptions.Item label="机房位置" span={2}>
                  <span style={{ color: '#666' }}>
                    <EnvironmentOutlined style={{ marginRight: 4 }} />
                    {localHostData.idc_info.idc_location}
                  </span>
                </Descriptions.Item>
              )}
              {localHostData.idc_info.idc_description && (
                <Descriptions.Item label="机房描述" span={2}>
                  {localHostData.idc_info.idc_description}
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>
        )}

        {!localHostData.idc_info && (
          <Card
            size="small"
            style={{ marginBottom: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
            title={
              <span style={{ fontSize: 16, fontWeight: 600 }}>
                <EnvironmentOutlined style={{ color: '#eb2f96' }} />
                <span style={{ marginLeft: 8 }}>IDC机房信息</span>
              </span>
            }
          >
            <div style={{ padding: '24px', textAlign: 'center', color: '#999' }}>
              <ExclamationCircleOutlined style={{ fontSize: 32, marginBottom: 8, display: 'block' }} />
              <div>该主机暂无IDC机房信息</div>
            </div>
          </Card>
        )}
      </div>
      
      <div className="applications-section">
        <Card
          size="small"
          style={{ marginBottom: 16, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
          title={
            <Row type="flex" justify="space-between" align="middle">
              <Col>
                <span style={{ fontSize: 16, fontWeight: 600 }}>
                  <DatabaseOutlined style={{ color: '#13c2c2', marginRight: 8 }} />
                  应用信息
                  {localHostData.host_applications && (
                    <Badge
                      count={localHostData.host_applications.length}
                      style={{ marginLeft: 12, backgroundColor: '#52c41a' }}
                    />
                  )}
                </span>
              </Col>
              <Col>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAddApplication}
                  size="small"
                  style={{ borderRadius: 6 }}
                >
                  添加应用
                </Button>
              </Col>
            </Row>
          }
        >
          {localHostData.host_applications && localHostData.host_applications.length > 0 ? (
            localHostData.host_applications.map((app, index) => (
              <Card
                key={`app-${app.id || index}`}
                size="small"
                style={{
                  marginBottom: 12,
                  borderRadius: 8,
                  border: '1px solid #e8e8e8',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
                }}
                title={
                  <Row type="flex" justify="space-between" align="middle">
                    <Col>
                      <Tag color="processing" style={{ fontSize: 14, padding: '2px 12px' }}>
                        <ClusterOutlined style={{ marginRight: 4 }} />
                        应用 {index + 1}
                      </Tag>
                    </Col>
                    <Col>
                      <Space size="small">
                        <Button
                          type="link"
                          icon={<EditOutlined />}
                          onClick={() => handleEditApplication(app)}
                          size="small"
                          style={{ color: '#1890ff' }}
                        >
                          编辑
                        </Button>
                        <Popconfirm
                          title="确定要删除这个应用吗？"
                          onConfirm={() => handleDeleteApplication(app.id)}
                          okText="确定"
                          cancelText="取消"
                          okButtonProps={{ danger: true }}
                        >
                          <Button
                            type="link"
                            icon={<DeleteOutlined />}
                            size="small"
                            danger
                          >
                            删除
                          </Button>
                        </Popconfirm>
                      </Space>
                    </Col>
                  </Row>
                }
              >
                <Descriptions bordered column={2} size="small" labelStyle={{ fontWeight: 500, background: '#fafafa' }}>
                  <Descriptions.Item label="服务类型">
                    <Tag color="blue" icon={<DatabaseOutlined />}>
                      {app.server_type || '未设置'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="服务版本">
                    <Tag color="cyan">{app.server_version || '未设置'}</Tag>
                  </Descriptions.Item>
                  {app.server_subtitle && (
                    <Descriptions.Item label="服务副标题" span={2}>
                      {app.server_subtitle}
                    </Descriptions.Item>
                  )}
                  <Descriptions.Item label="集群名称">
                    <Tag color="purple" icon={<ClusterOutlined />}>
                      {app.cluster_name || '未设置'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="协议类型">
                    <Tag color="orange" icon={<ApiOutlined />}>
                      {app.server_protocol || '未设置'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="服务地址" span={2}>
                    <code style={{ background: '#f5f5f5', padding: '4px 8px', borderRadius: '4px' }}>
                      {app.server_addr || '未设置'}
                    </code>
                  </Descriptions.Item>
                  <Descriptions.Item label="所属部门">
                    <Tag color="geekblue">{app.department_name || '未设置'}</Tag>
                  </Descriptions.Item>
                  {app.pool_id && (
                    <Descriptions.Item label="资源池ID">
                      <code style={{ background: '#f5f5f5', padding: '4px 8px', borderRadius: '4px' }}>
                        {app.pool_id}
                      </code>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            ))
          ) : (
            <div style={{ padding: '32px', textAlign: 'center', color: '#999' }}>
              <DatabaseOutlined style={{ fontSize: 48, marginBottom: 16, display: 'block', color: '#d9d9d9' }} />
              <div style={{ fontSize: 14 }}>该主机暂无应用信息</div>
              <Button
                type="dashed"
                icon={<PlusOutlined />}
                onClick={handleAddApplication}
                style={{ marginTop: 16 }}
              >
                添加第一个应用
              </Button>
            </div>
          )}
        </Card>
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
      title={
        <span>
          <DatabaseOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          {editingApp ? "编辑应用" : "添加应用"}
        </span>
      }
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={600}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        initialValues={editingApp || {}}
      >
        <Form.Item
          name="server_type"
          label={<span><DatabaseOutlined style={{ marginRight: 4 }} />服务类型</span>}
          rules={[{ required: true, message: '请选择服务类型' }]}
        >
          <Select placeholder="请选择服务类型" size="large">
            <Option value="mysql">
              <DatabaseOutlined style={{ marginRight: 4 }} />MySQL
            </Option>
            <Option value="mssql">
              <DatabaseOutlined style={{ marginRight: 4 }} />MS SQL Server
            </Option>
            <Option value="tidb">
              <DatabaseOutlined style={{ marginRight: 4 }} />TiDB
            </Option>
            <Option value="goldendb">
              <DatabaseOutlined style={{ marginRight: 4 }} />GoldenDB
            </Option>
            <Option value="redis">
              <DatabaseOutlined style={{ marginRight: 4 }} />Redis
            </Option>
            <Option value="mongodb">
              <DatabaseOutlined style={{ marginRight: 4 }} />MongoDB
            </Option>
            <Option value="other">其他</Option>
          </Select>
        </Form.Item>

        <Form.Item name="server_version" label="服务版本">
          <Input placeholder="请输入服务版本号，如：8.0.28" size="large" />
        </Form.Item>

        <Form.Item name="server_subtitle" label="服务副标题">
          <Input placeholder="请输入服务副标题（可选）" size="large" />
        </Form.Item>

        <Form.Item name="cluster_name" label={<span><ClusterOutlined style={{ marginRight: 4 }} />集群名称</span>}>
          <Input placeholder="请输入集群名称" size="large" />
        </Form.Item>

        <Form.Item name="server_protocol" label={<span><ApiOutlined style={{ marginRight: 4 }} />协议类型</span>}>
          <Select placeholder="请选择协议类型" size="large">
            <Option value="mysql">MySQL</Option>
            <Option value="mssql">MS SQL</Option>
            <Option value="redis">Redis</Option>
            <Option value="mongodb">MongoDB</Option>
            <Option value="http">HTTP</Option>
            <Option value="https">HTTPS</Option>
            <Option value="tcp">TCP</Option>
            <Option value="other">其他</Option>
          </Select>
        </Form.Item>

        <Form.Item name="server_addr" label="服务地址">
          <Input
            placeholder="请输入服务地址，如：192.168.1.100:3306 或 :3306"
            size="large"
            prefix={<EnvironmentOutlined />}
          />
        </Form.Item>

        <Form.Item name="department_name" label="所属部门">
          <Input placeholder="请输入所属部门" size="large" />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={onCancel} size="large">
              取消
            </Button>
            <Button type="primary" htmlType="submit" loading={loading} icon={editingApp ? <EditOutlined /> : <PlusOutlined />} size="large">
              {editingApp ? '更新应用' : '添加应用'}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

// 导出 ApplicationModal 组件供内部使用
const ApplicationModalComponent = ApplicationModal;

export default HostDetail;