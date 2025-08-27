/**
 * 目录创建弹窗组件
 */

import React, { useEffect } from 'react';
import { Modal, Form, Input, message } from 'antd';
import { FolderModalProps } from '../types/kb';
import { kbApi } from '@/services/kbApi';

const { TextArea } = Input;

const FolderCreateModal: React.FC<FolderModalProps> = ({
  open,
  onCancel,
  onSuccess,
  kbId,
  parentFolderId,
  initialData
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);

  const isEdit = !!initialData?.folder_id;

  useEffect(() => {
    if (open && initialData) {
      form.setFieldsValue({
        folder_name: initialData.folder_name,
        folder_description: initialData.folder_description,
      });
    } else if (open) {
      form.resetFields();
    }
  }, [open, initialData, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (isEdit && initialData?.folder_id) {
        const response = await kbApi.updateFolder(initialData.folder_id, values);
        if (response.status === 'ok') {
          message.success('目录更新成功');
          onSuccess?.();
          onCancel();
        } else {
          message.error(response.msg || '更新失败');
        }
      } else {
        const requestData = {
          ...values,
          parent_folder_id: parentFolderId,
        };
        
        const response = await kbApi.createFolder(kbId, requestData);
        if (response.status === 'ok') {
          message.success('目录创建成功');
          onSuccess?.();
          onCancel();
        } else {
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

  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title={isEdit ? '编辑目录' : '创建目录'}
      open={open}
      onCancel={handleCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={500}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          name="folder_name"
          label="目录名称"
          rules={[
            { required: true, message: '请输入目录名称' },
            { max: 100, message: '名称长度不能超过100字符' }
          ]}
        >
          <Input placeholder="请输入目录名称" />
        </Form.Item>

        <Form.Item
          name="folder_description"
          label="目录描述"
          rules={[{ max: 500, message: '描述长度不能超过500字符' }]}
        >
          <TextArea 
            placeholder="请输入目录描述（可选）"
            rows={3}
            showCount
            maxLength={500}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default FolderCreateModal;