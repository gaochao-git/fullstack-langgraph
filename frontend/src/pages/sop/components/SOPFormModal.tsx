import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  App,
  Space
} from 'antd';
import { SOPTemplate, SOPTemplateRequest } from '../types/sop';
import { SOPApi } from '@/services/sopApi';

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
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);

  // 初始化表单
  useEffect(() => {
    if (visible && editData) {
      form.setFieldsValue({
        sop_id: editData.sop_id,
        sop_title: editData.sop_title,
        sop_description: editData.sop_description
      });
    } else if (visible && !editData) {
      form.resetFields();
      // 新建时自动生成SOP ID
      form.setFieldValue('sop_id', generateSOPId());
    }
  }, [visible, editData, form]);

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const request: SOPTemplateRequest = {
        sop_id: values.sop_id,
        sop_title: values.sop_title,
        sop_description: values.sop_description || ''
      };

      if (editData) {
        // 更新
        const response = await SOPApi.updateTemplate(editData.sop_id, request);
        if (response.status === 'ok' || response.status === 'success') {
          message.success(response.msg || 'SOP更新成功');
          onSuccess();
          handleCancel();
        } else if (response.status === 'error') {
          message.error(response.msg || '更新失败');
        }
      } else {
        // 创建
        const response = await SOPApi.createTemplate(request);
        if (response.status === 'ok' || response.status === 'success') {
          message.success(response.msg || 'SOP创建成功');
          onSuccess();
          handleCancel();
        } else if (response.status === 'error') {
          message.error(response.msg || '创建失败');
        }
      }
    } catch (error) {
      console.error('提交失败:', error);
      message.error('操作失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 关闭弹窗
  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  // 生成SOP ID
  const generateSOPId = () => {
    const timestamp = Date.now().toString(36).toUpperCase();
    const random = Math.random().toString(36).substring(2, 5).toUpperCase();
    return `SOP-${timestamp}-${random}`;
  };

  // 示例文本常量
  const EXAMPLE_TEXT = `## 故障现象
描述具体的故障表现...

## 诊断步骤
1. **检查服务状态**
   - 执行命令：systemctl status [service_name]
   - 预期结果：服务处于active (running)状态

2. **检查日志**
   - 查看系统日志：tail -f /var/log/messages
   - 查看应用日志：根据具体应用查看对应日志文件

3. **检查资源使用**
   - CPU使用率：top或htop
   - 内存使用：free -h
   - 磁盘空间：df -h

## 处理方案
1. 如果服务未运行，尝试重启服务
2. 如果资源不足，清理或扩容
3. 如果有错误日志，根据错误信息进行相应处理

## 注意事项
- 操作前备份重要数据
- 记录操作步骤便于回溯
- 如无法解决，及时上报
`;

  // 使用示例模板
  const handleUseTemplate = () => {
    form.setFieldsValue({
      sop_description: EXAMPLE_TEXT
    });
  };

  return (
    <Modal
      title={editData ? '编辑SOP' : '创建SOP'}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={loading}
      width={800}
      okText="保存"
      cancelText="取消"
    >
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          name="sop_id"
          label="SOP ID"
          rules={[
            { required: true, message: '请输入SOP ID' },
            { 
              pattern: /^[a-zA-Z0-9_-]+$/, 
              message: 'SOP ID只能包含字母、数字、下划线和连字符' 
            }
          ]}
        >
          <Input 
            placeholder="系统将自动生成ID" 
            disabled={!!editData}
          />
        </Form.Item>

        <Form.Item
          name="sop_title"
          label="SOP标题"
          rules={[
            { required: true, message: '请输入SOP标题' },
            { max: 500, message: '标题最多500个字符' }
          ]}
        >
          <Input placeholder="请输入SOP标题，例如：MySQL数据库连接数过高处理流程" />
        </Form.Item>

        <Form.Item
          name="sop_description"
          label="SOP详细步骤"
          extra={
            <a onClick={handleUseTemplate}>
              使用示例模板
            </a>
          }
          rules={[
            { required: true, message: '请输入SOP详细步骤' },
            { max: 10000, message: '内容最多10000个字符' }
          ]}
          help="支持Markdown格式，建议包含：故障现象、诊断步骤、处理方案、注意事项等"
        >
          <TextArea
            placeholder="请输入SOP的详细步骤和说明..."
            autoSize={{ minRows: 8, maxRows: 12 }}
            showCount
            maxLength={10000}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default SOPFormModal;