// @ts-nocheck
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Input, 
  Select, 
  InputNumber, 
  Switch, 
  Upload, 
  message, 
  Tag, 
  Popconfirm,
  Typography,
  Row,
  Col,
  Divider,
  Icon
} from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import ScheduledTaskExecutionDetails from './ScheduledTaskExecutionDetails';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { Dragger } = Upload;

const ScheduledTaskManagement = () => {
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [executionDetailsModalVisible, setExecutionDetailsModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedExecutionTaskId, setSelectedExecutionTaskId] = useState(null);
  const [executionHistory, setExecutionHistory] = useState([]);
  
  // 表单状态
  const [hostIpList, setHostIpList] = useState([]);
  const [fileUploaded, setFileUploaded] = useState(false);
  const [formData, setFormData] = useState({
    task_name: '',
    description: '',
    resource_type: '',
    cron_expression: '',
    target_percent: 30,
    duration: 300,
    script_params: '',
    force_execution: false
  });

  // 获取定时任务列表
  const fetchTasks = async () => {
    setLoading(true);
    try {
      const result = await apiClient.get('cmdb/v1/scheduled-tasks');
      if (result.data.success) {
        setTasks(result.data.tasks || []);
      } else {
        message.error(result.data.message || '获取定时任务列表失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  // 创建定时任务
  const handleCreate = async () => {
    // 验证必填字段
    if (!formData.task_name.trim()) {
      message.error('请输入任务名称');
      return;
    }
    if (!formData.resource_type) {
      message.error('请选择资源类型');
      return;
    }
    if (!formData.cron_expression.trim()) {
      message.error('请输入Cron表达式');
      return;
    }
    if (!formData.target_percent || formData.target_percent < 1 || formData.target_percent > 100) {
      message.error('请输入有效的目标阈值 (1-100)');
      return;
    }
    if (!formData.duration || formData.duration < 60) {
      message.error('执行持续时间至少60秒');
      return;
    }
    if (!fileUploaded || hostIpList.length === 0) {
      message.error('请先上传包含主机IP的文件');
      return;
    }

    try {
      const result = await apiClient.post('cmdb/v1/scheduled-tasks', {
        ...formData,
        host_ip_list: hostIpList,
        created_by: 'system' // 可以从用户上下文获取
      });
      
      if (result.data.success) {
        message.success('定时任务创建成功');
        setCreateModalVisible(false);
        resetForm();
        fetchTasks();
      } else {
        message.error(result.data.message || '创建失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    }
  };

  // 显示编辑任务模态框
  const showEditModal = (task) => {
    setSelectedTask(task);
    // 解析IP列表
    let ipList = [];
    try {
      ipList = typeof task.host_ip_list === 'string' ? JSON.parse(task.host_ip_list) : task.host_ip_list;
    } catch (e) {
      console.error('解析IP列表失败:', e);
      ipList = [];
    }
    
    setFormData({
      task_name: task.task_name,
      description: task.description || '',
      resource_type: task.resource_type,
      cron_expression: task.cron_expression,
      target_percent: task.target_percent,
      duration: task.duration,
      script_params: task.script_params || '',
      force_execution: task.force_execution
    });
    setHostIpList(ipList);
    setFileUploaded(ipList.length > 0);
    setEditModalVisible(true);
  };

  // 更新定时任务
  const handleUpdate = async () => {
    // 验证必填字段
    if (!formData.task_name.trim()) {
      message.error('请输入任务名称');
      return;
    }
    if (!formData.resource_type) {
      message.error('请选择资源类型');
      return;
    }
    if (!formData.cron_expression.trim()) {
      message.error('请输入Cron表达式');
      return;
    }
    if (!formData.target_percent || formData.target_percent < 1 || formData.target_percent > 100) {
      message.error('请输入有效的目标阈值 (1-100)');
      return;
    }
    if (!formData.duration || formData.duration < 60) {
      message.error('执行持续时间至少60秒');
      return;
    }
    if (!fileUploaded || hostIpList.length === 0) {
      message.error('请先上传包含主机IP的文件');
      return;
    }

    try {
      const result = await apiClient.put(`cmdb/v1/scheduled-tasks/${selectedTask.id}`, {
        ...formData,
        host_ip_list: hostIpList
      });
      
      if (result.data.success) {
        message.success('定时任务更新成功');
        setEditModalVisible(false);
        resetForm();
        fetchTasks();
      } else {
        message.error(result.data.message || '更新失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    }
  };

  // 重置表单
  const resetForm = () => {
    setFormData({
      task_name: '',
      description: '',
      resource_type: '',
      cron_expression: '',
      target_percent: 30,
      duration: 300,
      script_params: '',
      force_execution: false
    });
    setHostIpList([]);
    setFileUploaded(false);
    setSelectedTask(null);
  };

  // 启用/禁用任务
  const handleToggleEnable = async (taskId, enabled) => {
    try {
      const result = await apiClient.put('cmdb/v1/scheduled-tasks/enable', {
        id: taskId,
        is_enabled: enabled
      });
      
      if (result.data.success) {
        message.success(enabled ? '任务已启用' : '任务已禁用');
        fetchTasks();
      } else {
        message.error(result.data.message || '操作失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    }
  };

  // 删除任务
  const handleDelete = async (taskId) => {
    try {
      const result = await apiClient.delete(`cmdb/v1/scheduled-tasks/${taskId}`);
      
      if (result.data.success) {
        message.success('任务删除成功');
        fetchTasks();
      } else {
        message.error(result.data.message || '删除失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    }
  };

  // 查看执行历史
  const showExecutionHistory = async (task) => {
    setSelectedTask(task);
    setHistoryModalVisible(true);
    
    try {
      const result = await apiClient.get('cmdb/v1/scheduled-tasks/execution-history', {
        scheduled_task_id: task.id,
        limit: 20
      });
      
      if (result.data.success) {
        // 确保每个历史记录都有host_details字段，并且数据格式正确
        const historyRecords = (result.data.history_records || []).map(record => ({
          ...record,
          host_details: record.host_details || record.HostDetails || []
        }));
        setExecutionHistory(historyRecords);
      } else {
        message.error(result.data.message || '获取执行历史失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    }
  };

  // 查看执行详情（新的综合视图）
  const showExecutionDetails = (executionRecord) => {
    const executionTaskId = executionRecord.execution_task_id || executionRecord.id;
    if (executionTaskId) {
      setSelectedExecutionTaskId(executionTaskId);
      setExecutionDetailsModalVisible(true);
    } else {
      message.error('无法获取执行任务ID');
    }
  };

  // 显示单个主机的执行详情
  const showHostExecutionDetail = (hostRecord, executionRecord) => {
    Modal.info({
      title: `主机 ${hostRecord.host_ip} 执行详情`,
      width: 800,
      content: (
        <div style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={24}>
              <Text strong>任务信息:</Text>
              <div style={{ marginLeft: 16, marginTop: 8 }}>
                <p><Text strong>任务名称:</Text> {executionRecord.task_name || '定时任务'}</p>
                <p><Text strong>主机IP:</Text> {hostRecord.host_ip}</p>
                <p><Text strong>资源类型:</Text> 
                  <Tag color={getResourceTypeColor(hostRecord.resource_type)} style={{ marginLeft: 8 }}>
                    {hostRecord.resource_type?.toUpperCase()}
                  </Tag>
                </p>
                <p><Text strong>执行状态:</Text> 
                  <Tag color={getStatusColor(hostRecord.execution_status)} style={{ marginLeft: 8 }}>
                    {getStatusText(hostRecord.execution_status)}
                  </Tag>
                </p>
                <p><Text strong>退出代码:</Text> {hostRecord.exit_code || '-'}</p>
                <p><Text strong>开始时间:</Text> {hostRecord.start_time || '-'}</p>
                <p><Text strong>结束时间:</Text> {hostRecord.end_time || '-'}</p>
              </div>
            </Col>
            
            {hostRecord.result_summary && (
              <Col span={24} style={{ marginTop: 16 }}>
                <Text strong>执行结果摘要:</Text>
                <div style={{ marginTop: 8, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                  <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                    {hostRecord.result_summary}
                  </pre>
                </div>
              </Col>
            )}
            
            {hostRecord.stdout_log && (
              <Col span={24} style={{ marginTop: 16 }}>
                <Text strong>标准输出:</Text>
                <div style={{ marginTop: 8, padding: 12, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 4, maxHeight: 300, overflow: 'auto' }}>
                  <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                    {hostRecord.stdout_log}
                  </pre>
                </div>
              </Col>
            )}
            
            {hostRecord.stderr_log && (
              <Col span={24} style={{ marginTop: 16 }}>
                <Text strong>标准错误:</Text>
                <div style={{ marginTop: 8, padding: 12, backgroundColor: '#fff2f0', border: '1px solid #ffccc7', borderRadius: 4, maxHeight: 300, overflow: 'auto' }}>
                  <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                    {hostRecord.stderr_log}
                  </pre>
                </div>
              </Col>
            )}
            
            {hostRecord.ssh_error && (
              <Col span={24} style={{ marginTop: 16 }}>
                <Text strong>SSH错误:</Text>
                <div style={{ marginTop: 8, padding: 12, backgroundColor: '#fff1f0', border: '1px solid #ffa39e', borderRadius: 4 }}>
                  <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                    {hostRecord.ssh_error}
                  </pre>
                </div>
              </Col>
            )}
          </Row>
        </div>
      ),
      okText: '关闭'
    });
  };

  // 处理文件上传
  const handleFileUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
      
      // 简单IP格式验证
      const validIpPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
      const validIps = lines.filter(line => validIpPattern.test(line));
      
      if (validIps.length === 0) {
        message.error('文件中没有找到有效的IP地址');
        return;
      }
      
      setHostIpList(validIps);
      setFileUploaded(true);
      message.success(`成功读取到 ${validIps.length} 个有效IP地址`);
    };
    reader.readAsText(file);
    return false; // 阻止自动上传
  };

  // 状态标签颜色映射
  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'green';
      case 'failed': return 'red';
      case 'partial': return 'orange';
      default: return 'default';
    }
  };

  // 状态文本映射
  const getStatusText = (status) => {
    switch (status) {
      case 'success': return '成功';
      case 'failed': return '失败';
      case 'partial': return '部分成功';
      default: return status;
    }
  };

  // 资源类型标签颜色映射
  const getResourceTypeColor = (type) => {
    switch (type) {
      case 'cpu': return 'blue';
      case 'memory': return 'green';
      case 'disk': return 'orange';
      default: return 'default';
    }
  };

  // 任务列表表格列定义
  const taskColumns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      width: 150,
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 100,
      render: (type) => (
        <Tag color={type === 'cpu' ? 'blue' : type === 'memory' ? 'green' : 'orange'}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Cron表达式',
      dataIndex: 'cron_expression',
      key: 'cron_expression',
      width: 120,
    },
    {
      title: '目标阈值',
      dataIndex: 'target_percent',
      key: 'target_percent',
      width: 80,
      render: (percent) => `${percent}%`,
    },
    {
      title: '持续时间',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      render: (duration) => `${duration}秒`,
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      width: 80,
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '下次执行时间',
      dataIndex: 'next_execution_time',
      key: 'next_execution_time',
      width: 150,
      render: (time) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (text, record) => (
        <div>
          <Switch
            checked={record.is_enabled}
            onChange={(checked) => handleToggleEnable(record.id, checked)}
            size="small"
            style={{ marginRight: 8 }}
          />
          <Button 
            type="link" 
            size="small" 
            onClick={() => showEditModal(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            size="small" 
            onClick={() => showExecutionHistory(record)}
          >
            历史
          </Button>
          <Popconfirm
            title="确定删除这个定时任务吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </div>
      ),
    },
  ];

  // 执行历史表格列定义 - 增强版，支持展开显示host_details
  const historyColumns = [
    {
      title: '执行时间',
      dataIndex: 'execution_time',
      key: 'execution_time',
      render: (time) => new Date(time).toLocaleString(),
    },
    {
      title: '执行状态',
      dataIndex: 'execution_status',
      key: 'execution_status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '总主机数',
      dataIndex: 'total_hosts',
      key: 'total_hosts',
    },
    {
      title: '成功主机数',
      dataIndex: 'success_hosts',
      key: 'success_hosts',
      render: (count) => (
        <Tag color="green">{count}</Tag>
      ),
    },
    {
      title: '失败主机数',
      dataIndex: 'failed_hosts',
      key: 'failed_hosts',
      render: (count) => (
        <Tag color="red">{count}</Tag>
      ),
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      render: (message) => message || '-',
    },
    {
      title: '执行详情',
      key: 'execution_details',
      width: 120,
      render: (text, record) => (
        <div>
          <Button 
            type="link" 
            size="small" 
            onClick={() => showExecutionDetails(record)}
            style={{ padding: 0 }}
          >
            完整详情
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <Card 
        title="定时任务管理" 
        extra={
          <Button type="primary" onClick={() => setCreateModalVisible(true)}>
            创建定时任务
          </Button>
        }
      >
        <Table
          dataSource={tasks}
          columns={taskColumns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: '暂无定时任务' }}
        />
      </Card>

      {/* 创建定时任务模态框 */}
      <Modal
        title="创建定时任务"
        visible={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          resetForm();
        }}
        footer={null}
        width={800}
      >
        <div style={{ padding: '0 0 24px 0' }}>
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  任务名称 <span style={{ color: 'red' }}>*</span>
                </label>
                <Input 
                  placeholder="请输入任务名称" 
                  value={formData.task_name}
                  onChange={(e) => setFormData({...formData, task_name: e.target.value})}
                />
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  资源类型 <span style={{ color: 'red' }}>*</span>
                </label>
                <Select 
                  placeholder="请选择资源类型" 
                  style={{ width: '100%' }}
                  value={formData.resource_type}
                  onChange={(value) => setFormData({...formData, resource_type: value})}
                >
                  <Option value="cpu">CPU</Option>
                  <Option value="memory">内存</Option>
                  <Option value="disk">磁盘</Option>
                </Select>
              </div>
            </Col>
          </Row>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              任务描述
            </label>
            <TextArea 
              rows={2} 
              placeholder="请输入任务描述" 
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>

          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  Cron表达式 <span style={{ color: 'red' }}>*</span>
                </label>
                <Input 
                  placeholder="例: 0 2 * * * (每天凌晨2点执行) | 0 */6 * * * (每6小时执行一次)" 
                  value={formData.cron_expression}
                  onChange={(e) => setFormData({...formData, cron_expression: e.target.value})}
                />
                <div style={{ color: '#666', fontSize: '12px', marginTop: '4px' }}>
                  格式：分 时 日 月 周，常用示例：「0 2 * * *」每天凌晨2:00，「30 14 * * 1」每周一下午14:30
                </div>
              </div>
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  目标阈值(%) <span style={{ color: 'red' }}>*</span>
                </label>
                <InputNumber
                  min={1}
                  max={100}
                  placeholder="1-100"
                  style={{ width: '100%' }}
                  value={formData.target_percent}
                  onChange={(value) => setFormData({...formData, target_percent: value})}
                />
              </div>
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  持续时间(秒) <span style={{ color: 'red' }}>*</span>
                </label>
                <InputNumber
                  min={60}
                  placeholder="至少60秒"
                  style={{ width: '100%' }}
                  value={formData.duration}
                  onChange={(value) => setFormData({...formData, duration: value})}
                />
              </div>
            </Col>
          </Row>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              主机IP列表文件 <span style={{ color: 'red' }}>*</span>
            </label>
            {fileUploaded && <Tag color="green" style={{ marginBottom: 8 }}>已上传 {hostIpList.length} 个IP</Tag>}
            <Dragger
              name="file"
              accept=".txt,.csv"
              beforeUpload={handleFileUpload}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个文件上传，文件格式为 .txt 或 .csv，每行一个IP地址
              </p>
            </Dragger>
          </div>

          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  脚本参数(JSON格式)
                </label>
                <TextArea 
                  rows={2} 
                  placeholder='例: {"nice_level": "19"}' 
                  value={formData.script_params}
                  onChange={(e) => setFormData({...formData, script_params: e.target.value})}
                />
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  强制执行
                </label>
                <Switch 
                  checkedChildren="是" 
                  unCheckedChildren="否" 
                  checked={formData.force_execution}
                  onChange={(checked) => setFormData({...formData, force_execution: checked})}
                />
                <div style={{ color: '#666', fontSize: '12px', marginTop: '4px' }}>
                  启用后将强制终止冲突的任务并执行新任务
                </div>
              </div>
            </Col>
          </Row>

          <Divider />

          <div>
            <Button type="primary" onClick={handleCreate} style={{ marginRight: 8 }}>
              创建任务
            </Button>
            <Button onClick={() => setCreateModalVisible(false)}>
              取消
            </Button>
          </div>
        </div>
      </Modal>

      {/* 编辑定时任务模态框 */}
      <Modal
        title="编辑定时任务"
        visible={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          resetForm();
        }}
        footer={null}
        width={800}
      >
        <div style={{ padding: '0 0 24px 0' }}>
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  任务名称 <span style={{ color: 'red' }}>*</span>
                </label>
                <Input 
                  placeholder="请输入任务名称" 
                  value={formData.task_name}
                  onChange={(e) => setFormData({...formData, task_name: e.target.value})}
                />
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  资源类型 <span style={{ color: 'red' }}>*</span>
                </label>
                <Select 
                  placeholder="请选择资源类型" 
                  style={{ width: '100%' }}
                  value={formData.resource_type}
                  onChange={(value) => setFormData({...formData, resource_type: value})}
                >
                  <Option value="cpu">CPU</Option>
                  <Option value="memory">内存</Option>
                  <Option value="disk">磁盘</Option>
                </Select>
              </div>
            </Col>
          </Row>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              任务描述
            </label>
            <TextArea 
              rows={2} 
              placeholder="请输入任务描述" 
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>

          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  Cron表达式 <span style={{ color: 'red' }}>*</span>
                </label>
                <Input 
                  placeholder="例: 0 2 * * * (每天凌晨2点执行) | 0 */6 * * * (每6小时执行一次)" 
                  value={formData.cron_expression}
                  onChange={(e) => setFormData({...formData, cron_expression: e.target.value})}
                />
                <div style={{ color: '#666', fontSize: '12px', marginTop: '4px' }}>
                  格式：分 时 日 月 周，常用示例：「0 2 * * *」每天凌晨2:00，「30 14 * * 1」每周一下午14:30
                </div>
              </div>
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  目标阈值(%) <span style={{ color: 'red' }}>*</span>
                </label>
                <InputNumber
                  min={1}
                  max={100}
                  placeholder="1-100"
                  style={{ width: '100%' }}
                  value={formData.target_percent}
                  onChange={(value) => setFormData({...formData, target_percent: value})}
                />
              </div>
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  持续时间(秒) <span style={{ color: 'red' }}>*</span>
                </label>
                <InputNumber
                  min={60}
                  placeholder="至少60秒"
                  style={{ width: '100%' }}
                  value={formData.duration}
                  onChange={(value) => setFormData({...formData, duration: value})}
                />
              </div>
            </Col>
          </Row>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              主机IP列表文件 <span style={{ color: 'red' }}>*</span>
            </label>
            {fileUploaded && <Tag color="green" style={{ marginBottom: 8 }}>已上传 {hostIpList.length} 个IP</Tag>}
            <Dragger
              name="file"
              accept=".txt,.csv"
              beforeUpload={handleFileUpload}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个文件上传，文件格式为 .txt 或 .csv，每行一个IP地址
              </p>
            </Dragger>
          </div>

          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  脚本参数(JSON格式)
                </label>
                <TextArea 
                  rows={2} 
                  placeholder='例: {"nice_level": "19"}' 
                  value={formData.script_params}
                  onChange={(e) => setFormData({...formData, script_params: e.target.value})}
                />
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
                  强制执行
                </label>
                <Switch 
                  checkedChildren="是" 
                  unCheckedChildren="否" 
                  checked={formData.force_execution}
                  onChange={(checked) => setFormData({...formData, force_execution: checked})}
                />
                <div style={{ color: '#666', fontSize: '12px', marginTop: '4px' }}>
                  启用后将强制终止冲突的任务并执行新任务
                </div>
              </div>
            </Col>
          </Row>

          <Divider />

          <div>
            <Button type="primary" onClick={handleUpdate} style={{ marginRight: 8 }}>
              更新任务
            </Button>
            <Button onClick={() => setEditModalVisible(false)}>
              取消
            </Button>
          </div>
        </div>
      </Modal>

      {/* 执行历史模态框 - 增强版，支持展开显示host_details */}
      <Modal
        title={`任务 "${selectedTask?.task_name}" 的执行历史`}
        visible={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setHistoryModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1200}
        bodyStyle={{ maxHeight: '80vh', overflow: 'auto' }}
      >
        <Table
          dataSource={executionHistory}
          columns={historyColumns}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          locale={{ emptyText: '暂无执行历史' }}
          expandable={{
            expandedRowRender: (record) => {
              if (!record.host_details || record.host_details.length === 0) {
                return <div style={{ padding: '20px', textAlign: 'center' }}>暂无主机执行详情</div>;
              }
              
              return (
                <div style={{ margin: 0, padding: '16px', backgroundColor: '#fafafa' }}>
                  <Title level={4} style={{ marginBottom: 16 }}>
                    主机执行详情 ({record.host_details.length}台主机)
                  </Title>
                  <Table
                    dataSource={record.host_details}
                    columns={[
                      {
                        title: '主机IP',
                        dataIndex: 'host_ip',
                        key: 'host_ip',
                        width: 120,
                      },
                      {
                        title: '资源类型',
                        dataIndex: 'resource_type',
                        key: 'resource_type',
                        width: 100,
                        render: (type) => (
                          <Tag color={getResourceTypeColor(type)}>
                            {type?.toUpperCase()}
                          </Tag>
                        ),
                      },
                      {
                        title: '执行状态',
                        dataIndex: 'execution_status',
                        key: 'execution_status',
                        width: 100,
                        render: (status) => (
                          <Tag color={getStatusColor(status)}>
                            {getStatusText(status)}
                          </Tag>
                        ),
                      },
                      {
                        title: '目标阈值',
                        dataIndex: 'target_percent',
                        key: 'target_percent',
                        width: 80,
                        render: (percent) => `${percent}%`,
                      },
                      {
                        title: '持续时间',
                        dataIndex: 'duration',
                        key: 'duration',
                        width: 80,
                        render: (duration) => `${duration}秒`,
                      },
                      {
                        title: '开始时间',
                        dataIndex: 'start_time',
                        key: 'start_time',
                        width: 150,
                        render: (time) => time ? new Date(time).toLocaleString() : '-',
                      },
                      {
                        title: '结束时间',
                        dataIndex: 'end_time',
                        key: 'end_time',
                        width: 150,
                        render: (time) => time ? new Date(time).toLocaleString() : '-',
                      },
                      {
                        title: '退出代码',
                        dataIndex: 'exit_code',
                        key: 'exit_code',
                        width: 80,
                        render: (code) => code !== undefined && code !== null ? code : '-',
                      },
                      {
                        title: '结果摘要',
                        dataIndex: 'result_summary',
                        key: 'result_summary',
                        ellipsis: true,
                        width: 200,
                        render: (summary) => {
                          if (!summary) return '-';
                          try {
                            const result = JSON.parse(summary);
                            return result.success ? (
                              <Tag color="green">成功</Tag>
                            ) : (
                              <Tag color="red">失败</Tag>
                            );
                          } catch {
                            return summary;
                          }
                        },
                      },
                      {
                        title: 'SSH错误',
                        dataIndex: 'ssh_error',
                        key: 'ssh_error',
                        ellipsis: true,
                        width: 150,
                        render: (error) => error || '-',
                      },
                      {
                        title: '日志',
                        key: 'logs',
                        width: 100,
                        render: (text, hostRecord) => (
                          <Button 
                            type="link" 
                            size="small"
                            onClick={() => showHostExecutionDetail(hostRecord, record)}
                          >
                            查看日志
                          </Button>
                        ),
                      },
                    ]}
                    rowKey={(record, index) => `${record.host_ip}-${index}`}
                    pagination={false}
                    size="small"
                    scroll={{ x: 1000 }}
                    style={{ backgroundColor: 'white' }}
                  />
                </div>
              );
            },
            rowExpandable: (record) => record.host_details && record.host_details.length > 0,
            expandIconColumnIndex: 7,
            expandRowByClick: false,
          }}
        />
      </Modal>

      {/* 执行详情模态框 - 使用新的综合组件 */}
      <ScheduledTaskExecutionDetails
        executionTaskId={selectedExecutionTaskId}
        visible={executionDetailsModalVisible}
        onCancel={() => setExecutionDetailsModalVisible(false)}
      />
    </div>
  );
};

export default ScheduledTaskManagement;