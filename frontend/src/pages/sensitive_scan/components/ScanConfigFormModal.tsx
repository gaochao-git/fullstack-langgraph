import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Switch, Button, Space, message } from 'antd';
import { MinusCircleOutlined, PlusOutlined } from '@ant-design/icons';
import type { ScanConfig, ScanConfigCreate, ScanConfigUpdate } from '../types/scanConfig';
import { ScanConfigApi } from '../services/scanConfigApi';

const { TextArea } = Input;

interface ScanConfigFormModalProps {
  visible: boolean;
  config?: ScanConfig;
  onClose: () => void;
  onSuccess: () => void;
}

const ScanConfigFormModal: React.FC<ScanConfigFormModalProps> = ({
  visible,
  config,
  onClose,
  onSuccess
}) => {
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const isEdit = !!config;

  useEffect(() => {
    if (visible) {
      if (config) {
        // 编辑模式：回填数据
        form.setFieldsValue({
          config_name: config.config_name,
          config_description: config.config_description,
          prompt_description: config.prompt_description,
          examples: config.examples || [],
          is_default: config.is_default
        });
      } else {
        // 新建模式：清空表单
        form.resetFields();
      }
    }
  }, [visible, config, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);

      const requestData = {
        config_name: values.config_name,
        config_description: values.config_description,
        prompt_description: values.prompt_description,
        examples: values.examples || [],
        is_default: values.is_default
      };

      let response;
      if (isEdit && config) {
        // 更新配置
        response = await ScanConfigApi.updateConfig(config.config_id, requestData);
      } else {
        // 创建配置
        response = await ScanConfigApi.createConfig(requestData as ScanConfigCreate);
      }

      // omind_post/omind_put返回的response结构: {status, msg, data, code}
      if (response.status === 'ok') {
        message.success(isEdit ? '更新配置成功' : '创建配置成功');
        onSuccess();
        onClose();
      } else {
        message.error(response.msg || (isEdit ? '更新配置失败' : '创建配置失败'));
      }
    } catch (error) {
      console.error('操作失败:', error);
      message.error(isEdit ? '更新配置失败' : '创建配置失败');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑扫描配置' : '新建扫描配置'}
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="cancel" onClick={onClose} disabled={submitting}>
          取消
        </Button>,
        <Button key="submit" type="primary" onClick={handleSubmit} loading={submitting}>
          {isEdit ? '更新' : '创建'}
        </Button>
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          is_default: false,
          examples: []
        }}
      >
        <Form.Item
          label="配置名称"
          name="config_name"
          rules={[{ required: true, message: '请输入配置名称' }]}
        >
          <Input placeholder="例如：标准敏感信息扫描" />
        </Form.Item>

        <Form.Item
          label="配置描述"
          name="config_description"
        >
          <TextArea rows={2} placeholder="简要描述该配置的用途" />
        </Form.Item>

        <Form.Item
          label="扫描提示词"
          name="prompt_description"
          rules={[{ required: true, message: '请输入扫描提示词' }]}
        >
          <TextArea
            rows={6}
            placeholder="用于指导LLM识别敏感信息的提示词，例如：识别并提取文本中的敏感信息，包括身份证号、手机号、银行卡号..."
          />
        </Form.Item>

        <Form.Item label="Few-shot示例（可选）">
          <Form.List name="examples">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <div
                    key={key}
                    style={{
                      marginBottom: 16,
                      padding: 16,
                      border: '1px solid #d9d9d9',
                      borderRadius: 4,
                      position: 'relative'
                    }}
                  >
                    <Button
                      type="text"
                      danger
                      icon={<MinusCircleOutlined />}
                      onClick={() => remove(name)}
                      style={{ position: 'absolute', right: 8, top: 8 }}
                    />

                    <Form.Item
                      {...restField}
                      label="示例文本"
                      name={[name, 'text']}
                      rules={[{ required: true, message: '请输入示例文本' }]}
                    >
                      <TextArea rows={2} placeholder="例如：客户姓名：李明，手机：13912345678" />
                    </Form.Item>

                    <Form.Item label="提取的敏感信息">
                      <Form.List name={[name, 'extractions']}>
                        {(extFields, { add: addExt, remove: removeExt }) => (
                          <>
                            {extFields.map(({ key: extKey, name: extName }) => (
                              <Space key={extKey} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                                <Form.Item
                                  name={[extName, 'extraction_class']}
                                  rules={[{ required: true, message: '请输入类型' }]}
                                  style={{ marginBottom: 0, width: 120 }}
                                >
                                  <Input placeholder="类型（如：姓名）" />
                                </Form.Item>
                                <Form.Item
                                  name={[extName, 'extraction_text']}
                                  rules={[{ required: true, message: '请输入文本' }]}
                                  style={{ marginBottom: 0, flex: 1 }}
                                >
                                  <Input placeholder="提取的文本（如：李明）" />
                                </Form.Item>
                                <MinusCircleOutlined onClick={() => removeExt(extName)} />
                              </Space>
                            ))}
                            <Button
                              type="dashed"
                              onClick={() => addExt()}
                              block
                              icon={<PlusOutlined />}
                              size="small"
                            >
                              添加提取项
                            </Button>
                          </>
                        )}
                      </Form.List>
                    </Form.Item>
                  </div>
                ))}
                <Button
                  type="dashed"
                  onClick={() => add()}
                  block
                  icon={<PlusOutlined />}
                >
                  添加示例
                </Button>
              </>
            )}
          </Form.List>
        </Form.Item>

        <Form.Item
          label="设为默认配置"
          name="is_default"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ScanConfigFormModal;
