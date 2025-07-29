import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  App,
  Card,
  Divider,
  Row,
  Col
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { SOPTemplate, SOPTemplateRequest, SOPStep } from '../types/sop';
import { SOPApi, SOPUtils } from '../services/sopApi';

const { TextArea } = Input;
const { Option } = Select;

interface SOPFormModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  editData?: SOPTemplate | null;
}

const SOPFormModal: React.FC<SOPFormModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  editData
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<SOPStep[]>([]);
  const { message } = App.useApp();

  // 初始化表单数据
  useEffect(() => {
    if (visible) {
      if (editData) {
        // 编辑模式
        const parsedSteps = SOPUtils.parseSteps(editData.sop_steps);
        const parsedTools = editData.tools_required ? SOPUtils.parseTools(editData.tools_required) : [];
        
        form.setFieldsValue({
          sop_id: editData.sop_id,
          sop_title: editData.sop_title,
          sop_category: editData.sop_category,
          sop_description: editData.sop_description,
          sop_severity: editData.sop_severity,
          sop_recommendations: editData.sop_recommendations,
          team_name: editData.team_name,
          tools_required: parsedTools
        });
        setSteps(parsedSteps);
      } else {
        // 新建模式
        form.resetFields();
        setSteps([{
          step: 1,
          description: '',
          ai_generated: false,
          tool: '',
          args: '',
          requires_approval: false
        }]);
      }
    }
  }, [visible, editData, form]);

  // 添加步骤
  const addStep = () => {
    const newStep: SOPStep = {
      step: steps.length + 1,
      description: '',
      ai_generated: false,
      tool: '',
      args: '',
      requires_approval: false
    };
    setSteps([...steps, newStep]);
  };

  // 删除步骤
  const removeStep = (index: number) => {
    if (steps.length <= 1) {
      message.warning('至少需要保留一个步骤');
      return;
    }
    const newSteps = steps.filter((_, i) => i !== index);
    // 重新编号
    const reorderedSteps = newSteps.map((step, i) => ({ ...step, step: i + 1 }));
    setSteps(reorderedSteps);
  };

  // 更新步骤
  const updateStep = (index: number, field: keyof SOPStep, value: any) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setSteps(newSteps);
  };

  // 表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 验证步骤
      for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        if (!step.description.trim()) {
          message.error(`第${i + 1}步的描述不能为空`);
          return;
        }
        if (!step.tool.trim()) {
          message.error(`第${i + 1}步的工具不能为空`);
          return;
        }
      }

      setLoading(true);

      if (editData) {
        // 更新模式 - 只发送修改的字段
        const updateData: Partial<SOPTemplateRequest> = {};
        if (values.sop_title !== editData.sop_title) updateData.sop_title = values.sop_title;
        if (values.sop_category !== editData.sop_category) updateData.sop_category = values.sop_category;
        if (values.sop_description !== editData.sop_description) updateData.sop_description = values.sop_description;
        if (values.sop_severity !== editData.sop_severity) updateData.sop_severity = values.sop_severity;
        if (values.sop_recommendations !== editData.sop_recommendations) updateData.sop_recommendations = values.sop_recommendations;
        if (values.team_name !== editData.team_name) updateData.team_name = values.team_name;
        if (JSON.stringify(steps) !== editData.sop_steps) updateData.steps = steps;
        
        const currentTools = editData.tools_required ? JSON.parse(editData.tools_required) : [];
        const newTools = values.tools_required || [];
        if (JSON.stringify(currentTools) !== JSON.stringify(newTools)) {
          updateData.tools_required = newTools;
        }

        const response = await SOPApi.updateSOP(editData.sop_id, updateData);
        
        if (response.success) {
          message.success('更新成功');
          onSuccess();
        } else {
          message.error(response.error || '更新失败');
        }
      } else {
        // 创建模式 - 发送完整数据
        const requestData: SOPTemplateRequest = {
          sop_id: values.sop_id,
          sop_title: values.sop_title,
          sop_category: values.sop_category,
          sop_description: values.sop_description,
          sop_severity: values.sop_severity,
          steps: steps,
          tools_required: values.tools_required || [],
          sop_recommendations: values.sop_recommendations,
          team_name: values.team_name
        };

        const response = await SOPApi.createSOP(requestData);
        
        if (response.success) {
          message.success('创建成功');
          onSuccess();
        } else {
          message.error(response.error || '创建失败');
        }
      }
    } catch (error) {
      console.error('Form validation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={editData ? '编辑SOP' : '新建SOP'}
      open={visible}
      onCancel={onCancel}
      width={800}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {editData ? '更新' : '创建'}
        </Button>
      ]}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          sop_severity: 'medium',
          team_name: 'ops-team'
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="sop_id"
              label="SOP ID"
              rules={[{ required: true, message: '请输入SOP ID' }]}
            >
              <Input placeholder="如：SOP-DB-001" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="sop_category"
              label="分类"
              rules={[{ required: true, message: '请选择分类' }]}
            >
              <Select placeholder="选择分类">
                <Option value="database">数据库</Option>
                <Option value="system">系统</Option>
                <Option value="network">网络</Option>
                <Option value="application">应用</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="sop_title"
          label="SOP标题"
          rules={[{ required: true, message: '请输入SOP标题' }]}
        >
          <Input placeholder="输入SOP标题" />
        </Form.Item>

        <Form.Item
          name="sop_description"
          label="SOP描述"
        >
          <TextArea rows={3} placeholder="输入SOP描述" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="sop_severity"
              label="严重性"
              rules={[{ required: true, message: '请选择严重性' }]}
            >
              <Select>
                <Option value="low">低</Option>
                <Option value="medium">中</Option>
                <Option value="high">高</Option>
                <Option value="critical">紧急</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="team_name"
              label="负责团队"
              rules={[{ required: true, message: '请输入负责团队' }]}
            >
              <Input placeholder="如：ops-team" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="tools_required"
          label="所需工具"
        >
          <Select
            mode="tags"
            placeholder="输入所需工具，按回车添加"
            style={{ width: '100%' }}
          >
            <Option value="execute_mysql_query">execute_mysql_query</Option>
            <Option value="get_es_data">get_es_data</Option>
            <Option value="get_zabbix_metric_data">get_zabbix_metric_data</Option>
            <Option value="execute_system_command">execute_system_command</Option>
            <Option value="llm">llm</Option>
          </Select>
        </Form.Item>

        <Divider>执行步骤</Divider>
        
        {steps.map((step, index) => (
          <Card 
            key={index} 
            size="small" 
            className="mb-4"
            title={`步骤 ${step.step}`}
            extra={
              <Button 
                type="text" 
                danger 
                size="small"
                icon={<DeleteOutlined />}
                onClick={() => removeStep(index)}
              >
                删除
              </Button>
            }
          >
            <Row gutter={16}>
              <Col span={24}>
                <Form.Item label="步骤描述" required>
                  <TextArea 
                    value={step.description}
                    onChange={(e) => updateStep(index, 'description', e.target.value)}
                    placeholder="输入步骤描述"
                    rows={2}
                  />
                </Form.Item>
              </Col>
            </Row>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item label="工具" required>
                  <Select 
                    value={step.tool}
                    onChange={(value) => updateStep(index, 'tool', value)}
                    placeholder="选择工具"
                  >
                    <Option value="execute_mysql_query">execute_mysql_query</Option>
                    <Option value="get_es_data">get_es_data</Option>
                    <Option value="get_zabbix_metric_data">get_zabbix_metric_data</Option>
                    <Option value="execute_system_command">execute_system_command</Option>
                    <Option value="llm">llm</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="AI生成">
                  <Select 
                    value={step.ai_generated}
                    onChange={(value) => updateStep(index, 'ai_generated', value)}
                  >
                    <Option value={false}>否</Option>
                    <Option value={true}>是</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={18}>
                <Form.Item label="参数">
                  <TextArea 
                    value={step.args}
                    onChange={(e) => updateStep(index, 'args', e.target.value)}
                    placeholder="输入工具参数"
                    rows={2}
                  />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item label="需要审批">
                  <Select 
                    value={step.requires_approval}
                    onChange={(value) => updateStep(index, 'requires_approval', value)}
                  >
                    <Option value={false}>否</Option>
                    <Option value={true}>是</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Card>
        ))}

        <Button 
          type="dashed" 
          onClick={addStep}
          icon={<PlusOutlined />}
          style={{ width: '100%', marginBottom: 16 }}
        >
          添加步骤
        </Button>

        <Form.Item
          name="sop_recommendations"
          label="建议"
        >
          <TextArea rows={3} placeholder="输入相关建议" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default SOPFormModal;