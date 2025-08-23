import React, { useState, useEffect } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  App,
  Tabs,
  Row,
  Col,
  Space
} from 'antd';
import { InfoCircleOutlined, PartitionOutlined } from '@ant-design/icons';
import { SOPTemplate, SOPTemplateRequest, SOPStep } from '../types/sop';
import { SOPApi, SOPUtils } from '@/services/sopApi';
import FaultTreeEditor from './FaultTreeEditor';
import { FaultTreeData } from '../types/faultTree';
import { Node, Edge } from 'reactflow';

const { TextArea } = Input;
const { Option } = Select;

interface SOPFormWithTreeModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  editData?: SOPTemplate | null;
}

// 将SOP步骤转换为故障树节点（支持树形结构）
const convertSOPToFaultTree = (sop: Partial<SOPTemplate>): FaultTreeData => {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  
  // 创建根节点
  nodes.push({
    id: 'root',
    type: 'faultNode',
    position: { x: 400, y: 50 },
    data: {
      label: sop.sop_title || '新SOP流程',
      type: 'fault',
      status: 'pending',
      description: sop.sop_description || '',
      onAdd: undefined,
      onDelete: undefined,
      onEdit: undefined,
    },
  });
  
  // 如果有步骤，递归创建步骤节点
  if (sop.sop_steps) {
    const steps = typeof sop.sop_steps === 'string' 
      ? JSON.parse(sop.sop_steps) 
      : sop.sop_steps;
    
    // 递归创建节点和边
    const createNodesFromSteps = (
      steps: SOPStep[], 
      parentId: string, 
      level: number = 0,
      xOffset: number = 0
    ) => {
      const levelY = 150 + level * 150;
      const stepCount = steps.length;
      const totalWidth = (stepCount - 1) * 200;
      
      steps.forEach((step, index) => {
        const nodeId = step.id || `step-${Date.now()}-${Math.random()}`;
        const x = 400 + xOffset + (index * 200) - (totalWidth / 2);
        
        nodes.push({
          id: nodeId,
          type: 'faultNode',
          position: { x, y: levelY },
          data: {
            label: step.step, // 直接使用step作为label
            type: 'step',
            status: step.status || 'pending',
            executionStatus: step.executionStatus,
            healthStatus: step.healthStatus,
            description: step.description,
            onAdd: undefined,
            onDelete: undefined,
            onEdit: undefined,
          },
        });
        
        // 创建到父节点的边
        edges.push({
          id: `edge-${parentId}-${nodeId}`,
          source: parentId,
          target: nodeId,
          type: 'smoothstep',
        });
        
        // 递归处理子步骤
        if (step.children && step.children.length > 0) {
          createNodesFromSteps(step.children, nodeId, level + 1, 0);
        }
      });
    };
    
    // 从根节点开始创建
    createNodesFromSteps(steps, 'root');
  }
  
  return { nodes, edges };
};

// 将故障树转换回SOP步骤（树形结构）
const convertFaultTreeToSOPSteps = (treeData: FaultTreeData): SOPStep[] => {
  const { nodes, edges } = treeData;
  
  // 构建节点关系图
  const nodeMap = new Map(nodes.map(n => [n.id, n]));
  const childrenMap = new Map<string, string[]>();
  
  edges.forEach(edge => {
    const children = childrenMap.get(edge.source) || [];
    children.push(edge.target);
    childrenMap.set(edge.source, children);
  });
  
  // 递归构建树形结构
  const buildStepTree = (nodeId: string): SOPStep[] => {
    const childIds = childrenMap.get(nodeId) || [];
    const steps: SOPStep[] = [];
    
    childIds.forEach(childId => {
      const node = nodeMap.get(childId);
      if (node && node.data.type !== 'fault') {
        const step: SOPStep = {
          id: node.id,
          step: node.data.label || '新步骤', // 使用节点名称作为step
          description: node.data.description || '步骤描述', // 确保有默认值
          status: node.data.status,
          executionStatus: node.data.executionStatus,
          healthStatus: node.data.healthStatus,
        };
        
        // 递归获取子步骤
        const childSteps = buildStepTree(childId);
        if (childSteps.length > 0) {
          step.children = childSteps;
        }
        
        steps.push(step);
      }
    });
    
    return steps;
  };
  
  // 从根节点开始构建
  const rootSteps = buildStepTree('root');
  
  // 如果没有步骤，返回一个默认步骤
  if (rootSteps.length === 0) {
    return [{
      step: '初始化步骤',
      description: '请编辑步骤描述', // 确保描述不为空
      status: 'pending',
    }];
  }
  
  return rootSteps;
};

const SOPFormWithTreeModal: React.FC<SOPFormWithTreeModalProps> = ({
  visible,
  onCancel,
  onSuccess,
  editData
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('basic');
  const [treeData, setTreeData] = useState<FaultTreeData | null>(null);
  const { message } = App.useApp();

  // 初始化表单数据
  useEffect(() => {
    if (visible) {
      if (editData) {
        // 编辑模式
        form.setFieldsValue({
          sop_id: editData.sop_id,
          sop_title: editData.sop_title,
          sop_category: editData.sop_category,
          sop_description: editData.sop_description
        });
        
        // 初始化故障树数据
        const faultTreeData = convertSOPToFaultTree(editData);
        setTreeData(faultTreeData);
      } else {
        // 新建模式
        form.resetFields();
        // 设置默认的故障树数据
        setTreeData({
          nodes: [{
            id: 'root',
            type: 'faultNode',
            position: { x: 400, y: 50 },
            data: {
              label: '新SOP流程',
              type: 'fault',
              status: 'pending',
              description: '点击编辑SOP描述',
              onAdd: undefined,
              onDelete: undefined,
              onEdit: undefined,
            },
          }],
          edges: []
        });
      }
    }
  }, [visible, editData, form]);

  // 当基础信息更新时，同步更新故障树根节点
  const syncTreeRootNode = () => {
    const values = form.getFieldsValue();
    if (treeData && values.sop_title) {
      const updatedTreeData = {
        ...treeData,
        nodes: treeData.nodes.map(node => {
          if (node.id === 'root') {
            return {
              ...node,
              data: {
                ...node.data,
                label: values.sop_title,
                description: values.sop_description || '',
              }
            };
          }
          return node;
        })
      };
      setTreeData(updatedTreeData);
    }
  };

  // 保存故障树
  const handleSaveTree = (data: FaultTreeData) => {
    setTreeData(data);
    message.success('暂存成功');
  };

  // 表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (!treeData) {
        message.error('请编辑执行流程');
        return;
      }

      // 从故障树转换为步骤
      const steps = convertFaultTreeToSOPSteps(treeData);
      
      // 验证步骤
      if (steps.length === 0) {
        message.error('至少需要一个执行步骤');
        return;
      }
      
      // 验证所有步骤的描述不为空
      const validateSteps = (stepList: SOPStep[]): boolean => {
        for (const step of stepList) {
          if (!step.description || step.description.trim() === '') {
            message.error(`步骤 ${step.step} 的描述不能为空`);
            return false;
          }
          if (step.children && step.children.length > 0) {
            if (!validateSteps(step.children)) {
              return false;
            }
          }
        }
        return true;
      };
      
      if (!validateSteps(steps)) {
        return;
      }

      setLoading(true);

      if (editData) {
        // 更新模式
        const updateData: Partial<SOPTemplateRequest> = {
          sop_title: values.sop_title,
          sop_category: values.sop_category,
          sop_description: values.sop_description,
          steps: steps
        };

        const response = await SOPApi.updateSOP(editData.sop_id, updateData);
        
        if (response.status === 'error') {
          message.error(response.msg || '更新失败');
          return;
        }
        
        message.success('更新成功');
        onSuccess();
      } else {
        // 创建模式
        const requestData: SOPTemplateRequest = {
          sop_id: values.sop_id,
          sop_title: values.sop_title,
          sop_category: values.sop_category,
          sop_description: values.sop_description,
          steps: steps
        };

        const response = await SOPApi.createSOP(requestData);
        
        if (response.status === 'error') {
          message.error(response.msg || '创建失败');
          return;
        }
        
        message.success('创建成功');
        onSuccess();
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
      width="95%"
      style={{ top: 20 }}
      bodyStyle={{ height: 'calc(100vh - 200px)' }}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {editData ? '更新' : '创建'}
        </Button>
      ]}
      destroyOnClose
    >
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        style={{ height: '100%' }}
        items={[
          {
            key: 'basic',
            label: (
              <span>
                <InfoCircleOutlined />
                基础信息
              </span>
            ),
            children: (
              <Form
                form={form}
                layout="vertical"
                initialValues={{}}
                onValuesChange={syncTreeRootNode}
                style={{ maxWidth: 800, margin: '0 auto' }}
              >
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="sop_id"
                      label="SOP ID"
                      rules={[{ required: true, message: '请输入SOP ID' }]}
                    >
                      <Input placeholder="如：SOP-DB-001" disabled={!!editData} />
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

              </Form>
            ),
          },
          {
            key: 'flow',
            label: (
              <span>
                <PartitionOutlined />
                执行流程
              </span>
            ),
            children: (
              <div style={{ height: 'calc(100vh - 350px)' }}>
                {treeData && (
                  <FaultTreeEditor
                    initialData={treeData}
                    onSave={handleSaveTree}
                    readOnly={false}
                  />
                )}
              </div>
            ),
          },
        ]}
      />
    </Modal>
  );
};

export default SOPFormWithTreeModal;