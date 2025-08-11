import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  App,
  Popconfirm,
  Tag,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LinkOutlined,
  ApiOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { SOPApi } from '@/services/sopApi';
import { sopProblemRuleApi } from '@/services/sopProblemRuleApi';
import type { 
  SOPProblemRule, 
  SOPProblemRuleRequest,
  RuleInfo 
} from '../types/sopProblemRule';
import type { SOPTemplate } from '../types/sop';

const { Option } = Select;

const SOPProblemRuleManagement: React.FC = () => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState<SOPProblemRule[]>([]);
  const [sops, setSops] = useState<SOPTemplate[]>([]);
  const [zabbixItems, setZabbixItems] = useState<Array<{value: string, label: string}>>([]);
  const [loadingItems, setLoadingItems] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<SOPProblemRule | null>(null);
  const [form] = Form.useForm();

  // 加载规则列表
  const loadRules = async () => {
    setLoading(true);
    try {
      const response = await sopProblemRuleApi.getRules({
        page: 1,
        page_size: 100
      });
      
      if (response.status === 'ok' && response.data) {
        setRules(response.data.items || []);
      }
    } catch (error) {
      message.error('加载规则列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 加载SOP列表
  const loadSOPs = async () => {
    try {
      const response = await SOPApi.getSOPs({ page: 1, size: 100 });
      if (response.status === 'ok' && response.data) {
        setSops(response.data.items || []);
      }
    } catch (error) {
      message.error('加载SOP列表失败');
    }
  };

  // 加载Zabbix指标列表
  const loadZabbixItems = async () => {
    console.log('开始加载Zabbix指标...');
    setLoadingItems(true);
    try {
      const response = await sopProblemRuleApi.getZabbixItems({ limit: 200 });
      console.log('Zabbix API响应:', response);
      
      if (response.status === 'ok' && response.data) {
        setZabbixItems(response.data);
        console.log('设置了', response.data.length, '个Zabbix指标');
      }
    } catch (error) {
      console.error('加载Zabbix指标失败:', error);
      message.error('加载Zabbix指标失败');
    } finally {
      setLoadingItems(false);
    }
  };

  useEffect(() => {
    loadRules();
    loadSOPs();
  }, []);

  // 当打开模态框时加载Zabbix指标
  useEffect(() => {
    console.log('modalVisible:', modalVisible, 'zabbixItems.length:', zabbixItems.length);
    if (modalVisible && zabbixItems.length === 0) {
      loadZabbixItems();
    }
  }, [modalVisible]);

  // 解析规则信息
  const parseRuleInfo = (ruleInfo: string | RuleInfo): RuleInfo => {
    if (typeof ruleInfo === 'string') {
      try {
        return JSON.parse(ruleInfo);
      } catch {
        return { source_type: 'zabbix', item_keys: [] };
      }
    }
    return ruleInfo;
  };

  // 创建/编辑规则
  const handleSubmit = async (values: any) => {
    try {
      const ruleInfo: RuleInfo = {
        source_type: values.source_type,
        item_keys: values.item_keys || []
      };

      const request: SOPProblemRuleRequest = {
        rule_name: values.rule_name,
        sop_id: values.sop_id,
        rules_info: ruleInfo,
        is_enabled: values.is_enabled ?? true
      };

      if (editingRule) {
        const response = await sopProblemRuleApi.updateRule(editingRule.id, request);
        if (response.status === 'ok') {
          message.success('更新规则成功');
        }
      } else {
        const response = await sopProblemRuleApi.createRule(request);
        if (response.status === 'ok') {
          message.success('创建规则成功');
        }
      }

      setModalVisible(false);
      form.resetFields();
      loadRules();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 删除规则
  const handleDelete = async (id: number) => {
    try {
      const response = await sopProblemRuleApi.deleteRule(id);
      if (response.status === 'ok') {
        message.success('删除成功');
        loadRules();
      }
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 切换启用状态
  const handleToggleEnabled = async (id: number, enabled: boolean) => {
    try {
      const response = await sopProblemRuleApi.updateRule(id, {
        is_enabled: enabled
      });
      if (response.status === 'ok') {
        message.success(enabled ? '启用成功' : '禁用成功');
        loadRules();
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 打开编辑模态框
  const openEditModal = (rule: SOPProblemRule) => {
    setEditingRule(rule);
    const ruleInfo = parseRuleInfo(rule.rules_info);
    form.setFieldsValue({
      rule_name: rule.rule_name,
      sop_id: rule.sop_id,
      source_type: ruleInfo.source_type,
      item_keys: ruleInfo.item_keys || [],
      is_enabled: rule.is_enabled
    });
    setModalVisible(true);
  };

  // 表格列定义
  const columns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 200,
    },
    {
      title: '数据源',
      key: 'source_type',
      width: 100,
      render: (record: SOPProblemRule) => {
        const ruleInfo = parseRuleInfo(record.rules_info);
        return <Tag icon={<ApiOutlined />} color="blue">{ruleInfo.source_type}</Tag>;
      }
    },
    {
      title: '指标名称',
      key: 'item_keys',
      width: 300,
      render: (record: SOPProblemRule) => {
        const ruleInfo = parseRuleInfo(record.rules_info);
        const itemKeys = ruleInfo.item_keys || [];
        return (
          <Space direction="vertical" size="small">
            {itemKeys.map((key, index) => (
              <Tooltip key={index} title={key}>
                <Tag><code style={{ fontSize: '11px' }}>{key}</code></Tag>
              </Tooltip>
            ))}
          </Space>
        );
      }
    },
    {
      title: '关联SOP',
      key: 'sop',
      width: 300,
      render: (record: SOPProblemRule) => (
        <Space>
          <LinkOutlined />
          <span>{record.sop_name || record.sop_id}</span>
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      width: 100,
      render: (enabled: boolean, record: SOPProblemRule) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleEnabled(record.id, checked)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      )
    },
    {
      title: '创建人',
      dataIndex: 'created_by',
      key: 'created_by',
      width: 100,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (record: SOPProblemRule) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => openEditModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这条规则吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <Card 
      title="SOP问题规则管理" 
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            console.log('点击新建规则按钮');
            setEditingRule(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          新建规则
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={rules}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{
          defaultPageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `共 ${total} 条`
        }}
      />

      <Modal
        title={editingRule ? '编辑规则' : '新建规则'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            source_type: 'zabbix',
            is_enabled: true
          }}
        >
          <Form.Item
            name="rule_name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="请输入规则名称，如：MySQL连接数过多" />
          </Form.Item>

          <Form.Item
            name="source_type"
            label="数据源"
            rules={[{ required: true, message: '请选择数据源' }]}
          >
            <Select placeholder="请选择数据源">
              <Option value="zabbix">Zabbix</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="item_keys"
            label={
              <Space>
                指标名称
                <Button
                  type="link"
                  size="small"
                  icon={<ReloadOutlined />}
                  loading={loadingItems}
                  onClick={loadZabbixItems}
                >
                  刷新
                </Button>
              </Space>
            }
            rules={[{ required: true, message: '请选择至少一个指标' }]}
            extra="从Zabbix中选择需要监控的指标，支持多选"
          >
            <Select
              mode="multiple"
              placeholder="请选择Zabbix指标，支持多选"
              style={{ width: '100%' }}
              loading={loadingItems}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase()) ||
                (option?.value ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={zabbixItems}
              notFoundContent={loadingItems ? '加载中...' : '暂无数据'}
              showSearch
              allowClear
              maxTagCount="responsive"
            />
          </Form.Item>

          <Form.Item
            name="sop_id"
            label="关联SOP"
            rules={[{ required: true, message: '请选择关联的SOP' }]}
          >
            <Select
              placeholder="请选择SOP"
              showSearch
              optionFilterProp="children"
            >
              {sops.map(sop => (
                <Option key={sop.sop_id} value={sop.sop_id}>
                  {sop.sop_id} - {sop.sop_title}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="is_enabled"
            label="是否启用"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default SOPProblemRuleManagement;