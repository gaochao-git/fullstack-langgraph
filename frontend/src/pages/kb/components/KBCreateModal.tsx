/**
 * 知识库创建/编辑弹窗组件
 */

import React, { useEffect } from 'react';
import { Modal, Form, Input, Select, Space, Tag, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { KBCreateRequest, KBUpdateRequest, KBModalProps, KB_TYPES, VISIBILITY_OPTIONS } from '../types/kb';
import { kbApi } from '@/services/kbApi';

const { Option } = Select;
const { TextArea } = Input;

const KBCreateModal: React.FC<KBModalProps> = ({
  open,
  onCancel,
  onSuccess,
  initialData
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);
  const [tags, setTags] = React.useState<string[]>([]);
  const [inputVisible, setInputVisible] = React.useState(false);
  const [inputValue, setInputValue] = React.useState('');

  const isEdit = !!initialData?.kb_id;

  useEffect(() => {
    if (open && initialData) {
      form.setFieldsValue({
        kb_name: initialData.kb_name,
        kb_description: initialData.kb_description,
        kb_type: initialData.kb_type || KB_TYPES.GENERAL,
        visibility: initialData.visibility || VISIBILITY_OPTIONS.PRIVATE,
        department: initialData.department,
      });
      setTags(initialData.tags || []);
    } else if (open) {
      form.resetFields();
      setTags([]);
    }
  }, [open, initialData, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const requestData = {
        ...values,
        tags,
      };

      if (isEdit && initialData?.kb_id) {
        const response = await kbApi.updateKnowledgeBase(initialData.kb_id, requestData as KBUpdateRequest);
        if (response.status === 'ok') {
          message.success('知识库更新成功');
          onSuccess?.(response.data); // 传递更新后的数据
          onCancel();
        } else {
          message.error(response.msg || '更新失败');
        }
      } else {
        const response = await kbApi.createKnowledgeBase(requestData as KBCreateRequest);
        if (response.status === 'ok') {
          message.success('知识库创建成功');
          onSuccess?.(response.data); // 传递创建后的数据
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
    setTags([]);
    setInputVisible(false);
    setInputValue('');
    onCancel();
  };

  // 标签相关处理
  const handleClose = (removedTag: string) => {
    const newTags = tags.filter(tag => tag !== removedTag);
    setTags(newTags);
  };

  const showInput = () => {
    setInputVisible(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  };

  const handleInputConfirm = () => {
    if (inputValue && tags.indexOf(inputValue) === -1) {
      setTags([...tags, inputValue]);
    }
    setInputVisible(false);
    setInputValue('');
  };

  return (
    <Modal
      title={isEdit ? '编辑知识库' : '创建知识库'}
      open={open}
      onCancel={handleCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={600}
      destroyOnHidden
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          kb_type: KB_TYPES.GENERAL,
          visibility: VISIBILITY_OPTIONS.PRIVATE,
        }}
      >
        <Form.Item
          name="kb_name"
          label="知识库名称"
          rules={[
            { required: true, message: '请输入知识库名称' },
            { max: 100, message: '名称长度不能超过100字符' }
          ]}
        >
          <Input placeholder="请输入知识库名称" />
        </Form.Item>

        <Form.Item
          name="kb_description"
          label="描述"
          rules={[{ max: 500, message: '描述长度不能超过500字符' }]}
        >
          <TextArea 
            placeholder="请输入知识库描述"
            rows={3}
            showCount
            maxLength={500}
          />
        </Form.Item>

        <Form.Item
          name="kb_type"
          label="知识库类型"
          rules={[{ required: true, message: '请选择知识库类型' }]}
        >
          <Select placeholder="请选择知识库类型">
            <Option value={KB_TYPES.GENERAL}>通用知识库</Option>
            <Option value={KB_TYPES.TECHNICAL}>技术文档</Option>
            <Option value={KB_TYPES.FAQ}>常见问题</Option>
            <Option value={KB_TYPES.TRAINING}>培训资料</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="visibility"
          label="可见性"
          rules={[{ required: true, message: '请选择可见性' }]}
        >
          <Select placeholder="请选择可见性">
            <Option value={VISIBILITY_OPTIONS.PRIVATE}>私有</Option>
            <Option value={VISIBILITY_OPTIONS.INTERNAL}>内部</Option>
            <Option value={VISIBILITY_OPTIONS.PUBLIC}>公开</Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="department"
          label="所属部门"
        >
          <Input placeholder="请输入所属部门" />
        </Form.Item>

        <Form.Item label="标签">
          <Space size={[0, 8]} wrap>
            {tags.map((tag) => (
              <Tag
                key={tag}
                closable
                onClose={() => handleClose(tag)}
              >
                {tag}
              </Tag>
            ))}
            {inputVisible && (
              <Input
                type="text"
                size="small"
                style={{ width: 78 }}
                value={inputValue}
                onChange={handleInputChange}
                onBlur={handleInputConfirm}
                onPressEnter={handleInputConfirm}
                autoFocus
              />
            )}
            {!inputVisible && (
              <Tag
                onClick={showInput}
                style={{
                  background: '#fafafa',
                  borderStyle: 'dashed',
                  cursor: 'pointer',
                }}
              >
                <PlusOutlined /> 添加标签
              </Tag>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default KBCreateModal;