import React, { useState, useEffect } from 'react';
import { useIsMobile } from '@/hooks';
import { getBaseUrl } from '@/utils/base_api';
import {
  Table,
  Button,
  Space,
  Badge,
  Tooltip,
  Modal,
  Form,
  Input,
  Select,
  Row,
  Col,
  App
} from 'antd';
import {
  ClockCircleOutlined,
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  DeleteOutlined,
  MessageOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;

interface ScheduledTaskManagerProps {
  agentId: string;
  visible?: boolean;
}

const ScheduledTaskManager: React.FC<ScheduledTaskManagerProps> = ({ agentId, visible = true }) => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingTask, setEditingTask] = useState<any>(null);
  const [messageModalVisible, setMessageModalVisible] = useState(false);
  const [selectedTaskMessages, setSelectedTaskMessages] = useState<any[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const isMobile = useIsMobile();
  
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  
  const { message, modal } = App.useApp();
  const API_BASE_URL = getBaseUrl();

  // 获取任务列表
  const fetchTasks = async () => {
    if (!agentId) return;
    
    setLoading(true);
    try {
      // 正在获取智能体定时任务: agentId
      // 获取所有任务，然后在前端过滤
      const response = await fetch(`${API_BASE_URL}/api/v1/scheduled-tasks`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // 获取到的任务数据
      
      const allTasks = data?.data?.items || [];
      
      // 在前端过滤属于当前智能体的任务
      const filteredTasks = allTasks.filter(task => {
        try {
          if (task.task_extra_config) {
            const config = JSON.parse(task.task_extra_config);
            return config.agent_id === agentId;
          }
          return false;
        } catch (error) {
          // 解析任务配置失败
          return false;
        }
      });
      
      // 过滤后的任务列表
      setTasks(filteredTasks);
    } catch (error) {
      // 获取智能体定时任务失败
      message.error('获取定时任务列表失败');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  // 创建任务
  const handleCreateTask = async (values: any) => {
    try {
      // 构建智能体任务配置
      const extraConfig = {
        task_type: 'agent',
        agent_id: agentId,
        message: values.task_message || '执行定时任务',
        user: 'zhangsan123',
        task_timeout: values.task_timeout || 300,
        max_retries: values.max_retries || 3,
        queue: 'priority_low'  // 可选，默认 priority_low
      };
      
      const taskData = {
        task_name: values.task_name,
        task_path: 'celery_app.agent_tasks.execute_agent_periodic_task', // 使用通用的智能体任务函数
        task_description: values.task_description,
        task_extra_config: JSON.stringify(extraConfig),
        task_interval: values.schedule_type === 'interval' ? values.task_interval : null,
        task_crontab_minute: values.schedule_type === 'crontab' ? values.task_crontab_minute : null,
        task_crontab_hour: values.schedule_type === 'crontab' ? values.task_crontab_hour : null,
        task_crontab_day_of_week: values.schedule_type === 'crontab' ? values.task_crontab_day_of_week : null,
        task_crontab_day_of_month: values.schedule_type === 'crontab' ? values.task_crontab_day_of_month : null,
        task_crontab_month_of_year: values.schedule_type === 'crontab' ? values.task_crontab_month_of_year : null,
        task_enabled: true,
        create_by: 'zhangsan123',
        update_by: 'zhangsan123'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/v1/scheduled-tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success('创建定时任务成功');
      setCreateModalVisible(false);
      createForm.resetFields();
      await fetchTasks();
    } catch (error) {
      // 创建任务失败
      message.error('创建任务失败');
    }
  };

  // 编辑任务
  const handleEditTask = (task: any) => {
    setEditingTask(task);
    
    // 解析task_extra_config获取配置信息
    let extraConfig: any = {};
    try {
      if (task.task_extra_config) {
        extraConfig = JSON.parse(task.task_extra_config);
      }
    } catch (error) {
      // 解析任务配置失败
    }
    
    // 设置智能体任务表单初始值
    const formValues: any = {
      task_name: task.task_name,
      task_description: task.task_description,
      task_message: extraConfig.message || '执行定时任务',
      task_timeout: extraConfig.task_timeout || 300,
      max_retries: extraConfig.max_retries || 3,
      schedule_type: task.task_interval ? 'interval' : 'crontab',
      task_interval: task.task_interval,
      task_crontab_minute: task.task_crontab_minute,
      task_crontab_hour: task.task_crontab_hour,
      task_crontab_day_of_week: task.task_crontab_day_of_week,
      task_crontab_day_of_month: task.task_crontab_day_of_month,
      task_crontab_month_of_year: task.task_crontab_month_of_year,
    };
    
    editForm.setFieldsValue(formValues);
    setEditModalVisible(true);
  };

  // 更新任务
  const handleUpdateTask = async (values: any) => {
    if (!editingTask) return;
    
    try {
      // 构建智能体任务配置
      const extraConfig = {
        task_type: 'agent',
        agent_id: agentId,
        message: values.task_message || '执行定时任务',
        user: 'zhangsan123',
        task_timeout: values.task_timeout || 300,
        max_retries: values.max_retries || 3,
        queue: 'priority_low'  // 可选，默认 priority_low
      };
      
      const taskData = {
        task_name: values.task_name,
        task_description: values.task_description,
        task_extra_config: JSON.stringify(extraConfig),
        task_interval: values.schedule_type === 'interval' ? values.task_interval : null,
        task_crontab_minute: values.schedule_type === 'crontab' ? values.task_crontab_minute : null,
        task_crontab_hour: values.schedule_type === 'crontab' ? values.task_crontab_hour : null,
        task_crontab_day_of_week: values.schedule_type === 'crontab' ? values.task_crontab_day_of_week : null,
        task_crontab_day_of_month: values.schedule_type === 'crontab' ? values.task_crontab_day_of_month : null,
        task_crontab_month_of_year: values.schedule_type === 'crontab' ? values.task_crontab_month_of_year : null,
        update_by: 'zhangsan123'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/v1/scheduled-tasks/${editingTask.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success('更新任务成功');
      setEditModalVisible(false);
      setEditingTask(null);
      editForm.resetFields();
      await fetchTasks();
    } catch (error) {
      // 更新任务失败
      message.error('更新任务失败');
    }
  };

  // 切换任务状态
  const handleToggleTask = async (task: any) => {
    try {
      const endpoint = task.task_enabled ? 'disable' : 'enable';
      const response = await fetch(`${API_BASE_URL}/api/v1/scheduled-tasks/${task.id}/${endpoint}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      message.success(`任务已${task.task_enabled ? '暂停' : '启动'}`);
      await fetchTasks();
    } catch (error) {
      // 切换任务状态失败
      message.error('操作失败');
    }
  };

  // 查看任务执行消息
  const handleViewMessages = async (task: any) => {
    setMessagesLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/scheduled-tasks/${task.id}/logs`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSelectedTaskMessages(Array.isArray(data) ? data : []);
      setMessageModalVisible(true);
    } catch (error) {
      // 获取任务执行记录失败
      message.error('获取执行记录失败');
      setSelectedTaskMessages([]);
    } finally {
      setMessagesLoading(false);
    }
  };

  // 删除任务
  const handleDeleteTask = (task: any) => {
    modal.confirm({
      title: '确认删除',
      content: `确定要删除任务 "${task.task_name}" 吗？`,
      okText: '删除',
      okType: 'danger',
      onOk: async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/scheduled-tasks/${task.id}`, {
            method: 'DELETE',
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          message.success('删除任务成功');
          await fetchTasks();
        } catch (error) {
          // 删除任务失败
          message.error('删除任务失败');
        }
      },
    });
  };

  // 当agentId变化时重新获取任务
  useEffect(() => {
    if (agentId && visible) {
      fetchTasks();
    }
  }, [agentId, visible]);

  // 表格列定义
  const columns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      width: 150,
      fixed: isMobile ? undefined : 'left' as const,
    },
    {
      title: '类型',
      key: 'task_type',
      width: 80,
      render: () => (
        <Badge 
          status="processing"
          text="智能体"
        />
      )
    },
    {
      title: '描述',
      dataIndex: 'task_description',
      key: 'task_description',
      width: 150,
      ellipsis: true,
    },
    {
      title: '调度配置',
      key: 'schedule',
      width: 120,
      render: (_: any, record: any) => {
        if (record.task_interval) {
          return `每${record.task_interval}秒`;
        }
        const cron = [
          record.task_crontab_minute || '*',
          record.task_crontab_hour || '*',
          record.task_crontab_day_of_month || '*',
          record.task_crontab_month_of_year || '*',
          record.task_crontab_day_of_week || '*'
        ].join(' ');
        return <code className="text-xs">{cron}</code>;
      }
    },
    {
      title: '状态',
      dataIndex: 'task_enabled',
      key: 'task_enabled',
      width: 80,
      render: (enabled: boolean) => (
        <Badge 
          status={enabled ? "success" : "default"} 
          text={enabled ? "启用" : "暂停"} 
        />
      )
    },
    {
      title: '最后运行',
      dataIndex: 'task_last_run_time',
      key: 'task_last_run_time',
      width: 140,
      render: (time: string) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: isMobile ? undefined : 'right' as const,
      render: (_: any, record: any) => (
        <Space size="small">
          <Tooltip title="暂停/启动">
            <Button
              type="text"
              size="small"
              icon={record.task_enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleTask(record)}
            />
          </Tooltip>
          <Tooltip title="查看消息">
            <Button
              type="text"
              size="small"
              icon={<MessageOutlined />}
              onClick={() => handleViewMessages(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => handleEditTask(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteTask(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // 任务表单组件
  const TaskForm = ({ form, onFinish, initialValues }: any) => {
    return (
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={initialValues}
      >
        <Form.Item
          label="任务名称"
          name="task_name"
          rules={[{ required: true, message: '请输入任务名称' }]}
        >
          <Input placeholder="输入任务名称" />
        </Form.Item>

        <Form.Item
          label="任务描述"
          name="task_description"
        >
          <TextArea rows={2} placeholder="输入任务描述（可选）" />
        </Form.Item>

        <Form.Item
          label="执行消息"
          name="task_message"
          rules={[{ required: true, message: '请输入执行消息' }]}
          tooltip="这是智能体在定时任务执行时收到的消息"
        >
          <TextArea rows={2} placeholder="输入智能体执行的消息内容" />
        </Form.Item>

        <Form.Item
          label="超时时间（秒）"
          name="task_timeout"
          initialValue={300}
          rules={[{ required: true, message: '请输入超时时间' }]}
          tooltip="任务执行的最大等待时间"
        >
          <Input type="number" min={60} max={3600} placeholder="300" />
        </Form.Item>

        <Form.Item
          label="最大重试次数"
          name="max_retries"
          initialValue={3}
          rules={[{ required: true, message: '请输入最大重试次数' }]}
          tooltip="任务失败后的最大重试次数"
        >
          <Input type="number" min={0} max={10} placeholder="3" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="调度方式"
              name="schedule_type"
              initialValue="interval"
            >
              <Select>
                <Option value="interval">间隔执行</Option>
                <Option value="crontab">Crontab</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="间隔时间（秒）"
              name="task_interval"
              dependencies={['schedule_type']}
              rules={[
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (getFieldValue('schedule_type') === 'interval' && (!value || value < 60)) {
                      return Promise.reject(new Error('间隔时间不能少于60秒'));
                    }
                    return Promise.resolve();
                  },
                }),
              ]}
            >
              <Input type="number" min={60} placeholder="3600" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.schedule_type !== currentValues.schedule_type}>
          {({ getFieldValue }) => {
            return getFieldValue('schedule_type') === 'crontab' ? (
              <Row gutter={8}>
                <Col span={4}>
                  <Form.Item label="分钟" name="task_crontab_minute">
                    <Input placeholder="*" />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Form.Item label="小时" name="task_crontab_hour">
                    <Input placeholder="*" />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Form.Item label="日" name="task_crontab_day_of_month">
                    <Input placeholder="*" />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Form.Item label="月" name="task_crontab_month_of_year">
                    <Input placeholder="*" />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <Form.Item label="周" name="task_crontab_day_of_week">
                    <Input placeholder="*" />
                  </Form.Item>
                </Col>
                <Col span={4}>
                  <div className="text-xs text-gray-500 mt-6">
                    Crontab格式
                  </div>
                </Col>
              </Row>
            ) : null;
          }}
        </Form.Item>
      </Form>
    );
  };

  if (!visible) return null;

  return (
    <div className="space-y-4">
      {/* 任务管理头部 */}
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-medium">智能体定时任务</h4>
        <Button 
          type="primary" 
          size="small"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          新建任务
        </Button>
      </div>
      
      {/* 任务表格 */}
      <Table
        dataSource={tasks}
        loading={loading}
        size="small"
        pagination={false}
        rowKey="id"
        scroll={{ x: 800 }}
        columns={columns}
      />

      {/* 创建任务模态框 */}
      <Modal
        title="创建定时任务"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        width={600}
        footer={null}
      >
        <TaskForm 
          form={createForm} 
          onFinish={handleCreateTask}
        />
        <div className="flex justify-end space-x-2 mt-6">
          <Button onClick={() => {
            setCreateModalVisible(false);
            createForm.resetFields();
          }}>
            取消
          </Button>
          <Button type="primary" onClick={() => createForm.submit()}>
            创建任务
          </Button>
        </div>
      </Modal>

      {/* 编辑任务模态框 */}
      <Modal
        title="编辑定时任务"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingTask(null);
          editForm.resetFields();
        }}
        width={600}
        footer={null}
      >
        <TaskForm 
          form={editForm} 
          onFinish={handleUpdateTask}
        />
        <div className="flex justify-end space-x-2 mt-6">
          <Button onClick={() => {
            setEditModalVisible(false);
            setEditingTask(null);
            editForm.resetFields();
          }}>
            取消
          </Button>
          <Button type="primary" onClick={() => editForm.submit()}>
            保存修改
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default ScheduledTaskManager;