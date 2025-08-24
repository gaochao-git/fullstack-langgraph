import React, { useCallback, useRef, useState, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  Handle,
  Position,
  NodeProps,
  ReactFlowProvider,
} from 'reactflow';
import { Button, Space, Modal, Form, Input, Select, Dropdown, Menu } from 'antd';
import { Save, Undo, Redo, Plus, Edit, Trash2 } from 'lucide-react';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined } from '@ant-design/icons';
import 'reactflow/dist/style.css';
import { FaultTreeData } from '../types/faultTree';

const { TextArea } = Input;
const { Option } = Select;

// 自定义节点组件
const CustomNode: React.FC<NodeProps> = ({ data, isConnectable }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  
  const getNodeStyle = () => {
    // 优先根据健康状态返回颜色
    if (data.healthStatus) {
      switch (data.healthStatus) {
        case 'healthy':
          return { background: '#f6ffed', borderColor: '#52c41a' };
        case 'warning':
          return { background: '#fffbe6', borderColor: '#faad14' };
        case 'critical':
          return { background: '#fff2e8', borderColor: '#ff4d4f' };
        case 'error':
          return { background: '#ffebe6', borderColor: '#ff4d4f' };
        case 'unknown':
        default:
          return { background: '#f0f0f0', borderColor: '#d9d9d9' };
      }
    }
    
    // 如果没有健康状态，使用类型颜色
    switch (data.type) {
      case 'fault':
        return { background: '#ffd6d6', borderColor: '#ff4444' };
      case 'step':
        return { background: '#d6e7ff', borderColor: '#4444ff' };
      case 'analysis':
        return { background: '#ffe6d6', borderColor: '#ff8844' };
      case 'rootCause':
        return { background: '#d6ffd6', borderColor: '#44ff44' };
      default:
        return { background: '#f0f0f0', borderColor: '#888888' };
    }
  };

  const style = getNodeStyle();

  
  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return '#1890ff';
      case 'success':
        return '#52c41a';
      case 'failed':
        return '#ff4d4f';
      case 'warning':
        return '#faad14';
      default:
        return '#d9d9d9';
    }
  };
  
  // 获取执行状态文本
  const getStatusText = (status: string) => {
    const statusTexts: { [key: string]: string } = {
      'pending': '待执行',
      'running': '执行中',
      'success': '成功',
      'failed': '失败',
      'skipped': '跳过',
    };
    return statusTexts[status] || status;
  };
  
  // 获取健康状态文本
  const getHealthStatusText = (status: string) => {
    const statusTexts: { [key: string]: string } = {
      'unknown': '未知',
      'healthy': '健康',
      'warning': '警告',
      'critical': '严重',
      'error': '错误',
    };
    return statusTexts[status] || status;
  };

  return (
    <div
      style={{
        padding: '10px 20px',
        borderRadius: '8px',
        border: `2px solid ${style.borderColor}`,
        background: style.background,
        minWidth: '150px',
        textAlign: 'center',
        position: 'relative',
        cursor: 'pointer',
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#555' }}
        isConnectable={isConnectable}
      />
      
      <div style={{ fontWeight: 'bold' }}>{data.label}</div>
      
      {/* 执行状态指示器 */}
      {data.executionStatus && data.executionStatus !== 'pending' && (
        <div style={{ 
          position: 'absolute', 
          top: '-8px', 
          right: '-8px',
          width: '16px',
          height: '16px',
          borderRadius: '50%',
          background: getStatusColor(data.executionStatus),
          border: '2px solid white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }} />
      )}
      
      {/* 悬浮提示框 */}
      {showTooltip && (data.description || data.executionStatus || data.healthStatus) && (
        <div
          style={{
            position: 'absolute',
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            marginBottom: '10px',
            padding: '12px 16px',
            background: 'rgba(0, 0, 0, 0.85)',
            color: 'white',
            borderRadius: '6px',
            fontSize: '13px',
            whiteSpace: 'pre-wrap',
            minWidth: '200px',
            maxWidth: '400px',
            zIndex: 10000,
            pointerEvents: 'none',
            boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
          }}
        >
          {data.executionStatus && (
            <div style={{ marginBottom: '8px' }}>
              <strong>执行状态:</strong> {getStatusText(data.executionStatus)}
            </div>
          )}
          {data.healthStatus && data.healthStatus !== 'unknown' && (
            <div style={{ marginBottom: '8px' }}>
              <strong>健康状态:</strong> {getHealthStatusText(data.healthStatus)}
            </div>
          )}
          {data.description && (
            <div>
              {data.description}
            </div>
          )}
          {/* 小三角箭头 */}
          <div
            style={{
              position: 'absolute',
              bottom: '-6px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: 0,
              height: 0,
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: '6px solid rgba(0, 0, 0, 0.85)',
            }}
          />
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#555' }}
        isConnectable={isConnectable}
      />
    </div>
  );
};

const nodeTypes = {
  faultNode: CustomNode,
};

interface FaultTreeEditorProps {
  initialData?: FaultTreeData;
  onSave?: (data: FaultTreeData) => void;
  readOnly?: boolean;
}

const FaultTreeEditorContent: React.FC<FaultTreeEditorProps> = ({
  initialData,
  onSave,
  readOnly = false,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialData?.nodes || []);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialData?.edges || []);
  const [nodeModalVisible, setNodeModalVisible] = useState(false);
  const [editingNode, setEditingNode] = useState<any>(null);
  const [contextMenuNode, setContextMenuNode] = useState<Node | null>(null);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [form] = Form.useForm();

  // 处理节点右键菜单
  const onNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      event.preventDefault();
      if (readOnly) return;
      setContextMenuNode(node);
      setContextMenuPosition({ x: event.clientX, y: event.clientY });
    },
    [readOnly]
  );

  // 添加子节点
  const handleAddNode = useCallback((parentNode: Node) => {
    // 找到该父节点的现有子节点
    const childEdges = edges.filter(edge => edge.source === parentNode.id);
    const childCount = childEdges.length;
    
    // 根据已有子节点数量计算新节点位置
    // 使用扇形布局，子节点分布在父节点下方
    const baseY = parentNode.position.y + 150;
    const spacing = 200; // 节点之间的水平间距
    
    let newX, newY;
    
    if (childCount === 0) {
      // 第一个子节点直接放在父节点下方
      newX = parentNode.position.x;
      newY = baseY;
    } else if (childCount === 1) {
      // 第二个子节点放在左侧
      newX = parentNode.position.x - spacing;
      newY = baseY;
    } else if (childCount === 2) {
      // 第三个子节点放在右侧
      newX = parentNode.position.x + spacing;
      newY = baseY;
    } else {
      // 更多子节点时，交替向左右扩展
      const side = childCount % 2 === 0 ? -1 : 1; // 偶数在左，奇数在右
      const offset = Math.ceil((childCount - 2) / 2);
      newX = parentNode.position.x + (side * spacing * (offset + 1));
      newY = baseY;
    }
    
    const newNodeId = `node-${Date.now()}`;
    const newNode: Node = {
      id: newNodeId,
      type: 'faultNode',
      position: {
        x: newX,
        y: newY,
      },
      data: {
        label: '新步骤',
        type: 'step',
        status: 'pending',
        description: '请输入步骤描述',
      },
    };

    const newEdge: Edge = {
      id: `edge-${parentNode.id}-${newNodeId}`,
      source: parentNode.id,
      target: newNodeId,
      type: 'smoothstep',
    };

    setNodes(nds => [...nds, newNode]);
    setEdges(eds => [...eds, newEdge]);
  }, [edges, setNodes, setEdges]);

  // 编辑节点
  const handleEditNode = useCallback((node: Node) => {
    setEditingNode({ id: node.id, ...node.data });
    form.setFieldsValue({
      label: node.data.label,
      description: node.data.description,
      executionStatus: node.data.executionStatus || 'pending',
      healthStatus: node.data.healthStatus || 'unknown',
    });
    setNodeModalVisible(true);
  }, [form]);

  // 删除节点
  const handleDeleteNode = useCallback((nodeId: string) => {
    setNodes(nds => nds.filter(node => node.id !== nodeId));
    setEdges(eds => eds.filter(edge => edge.source !== nodeId && edge.target !== nodeId));
  }, [setNodes, setEdges]);

  // 复制节点
  const handleCopyNode = useCallback((node: Node) => {
    const newNodeId = `node-${Date.now()}`;
    const newNode: Node = {
      ...node,
      id: newNodeId,
      position: {
        x: node.position.x + 50,
        y: node.position.y + 50,
      },
      data: {
        ...node.data,
        label: `${node.data.label} (副本)`,
      },
    };
    
    setNodes(nds => [...nds, newNode]);
  }, [setNodes]);

  // 创建右键菜单
  const createContextMenu = useCallback((node: Node) => {
    const menuItems = [
      {
        key: 'add',
        icon: <PlusOutlined />,
        label: '添加子节点',
        onClick: () => {
          handleAddNode(node);
          setContextMenuNode(null);
        },
      },
      {
        key: 'edit',
        icon: <EditOutlined />,
        label: '编辑节点',
        onClick: () => {
          handleEditNode(node);
          setContextMenuNode(null);
        },
      },
      {
        key: 'copy',
        icon: <CopyOutlined />,
        label: '复制节点',
        onClick: () => {
          handleCopyNode(node);
          setContextMenuNode(null);
        },
      },
    ];

    // 根节点不能删除
    if (node.data.type !== 'fault') {
      menuItems.push({
        key: 'delete',
        icon: <DeleteOutlined />,
        label: '删除节点',
        danger: true,
        onClick: () => {
          handleDeleteNode(node.id);
          setContextMenuNode(null);
        },
      });
    }

    return <Menu items={menuItems} />;
  }, [handleAddNode, handleEditNode, handleCopyNode, handleDeleteNode]);

  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return;
      setEdges((eds) => addEdge(params, eds));
    },
    [readOnly, setEdges]
  );

  // 保存节点编辑
  const handleNodeSave = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingNode) {
        setNodes(nds =>
          nds.map(node => {
            if (node.id === editingNode.id) {
              return {
                ...node,
                data: {
                  ...node.data,
                  ...values,
                },
              };
            }
            return node;
          })
        );
      }
      setNodeModalVisible(false);
      setEditingNode(null);
      form.resetFields();
    } catch (error) {
      // 表单验证失败，不做任何操作
    }
  };

  // 暂存
  const handleSave = () => {
    if (onSave) {
      onSave({ nodes, edges });
    }
  };


  // 自动布局
  const autoLayout = () => {
    const layoutedNodes = [...nodes];
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const childrenMap = new Map<string, string[]>();
    const levelMap = new Map<string, number>();
    
    edges.forEach(edge => {
      const children = childrenMap.get(edge.source) || [];
      children.push(edge.target);
      childrenMap.set(edge.source, children);
    });

    const rootNodes = nodes.filter(node => 
      !edges.some(edge => edge.target === node.id)
    );

    const queue = rootNodes.map(n => ({ id: n.id, level: 0 }));
    while (queue.length > 0) {
      const { id, level } = queue.shift()!;
      levelMap.set(id, level);
      
      const children = childrenMap.get(id) || [];
      children.forEach(childId => {
        queue.push({ id: childId, level: level + 1 });
      });
    }

    const levels = new Map<number, string[]>();
    levelMap.forEach((level, nodeId) => {
      const nodesAtLevel = levels.get(level) || [];
      nodesAtLevel.push(nodeId);
      levels.set(level, nodesAtLevel);
    });

    const yGap = 150;
    const xGap = 200;
    
    levels.forEach((nodeIds, level) => {
      const totalWidth = (nodeIds.length - 1) * xGap;
      const startX = 400 - totalWidth / 2;
      
      nodeIds.forEach((nodeId, index) => {
        const node = nodeMap.get(nodeId);
        if (node) {
          node.position = {
            x: startX + index * xGap,
            y: 50 + level * yGap,
          };
        }
      });
    });

    setNodes(layoutedNodes);
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px', background: '#f5f5f5', borderBottom: '1px solid #e0e0e0' }}>
        <Space>
          {!readOnly && (
            <>
              <Button type="primary" icon={<Save size={16} />} onClick={handleSave}>
                暂存
              </Button>
              <Button onClick={autoLayout}>
                自动布局
              </Button>
            </>
          )}
          <span style={{ marginLeft: 16, color: '#666', fontSize: 12 }}>
            提示：右键点击节点进行操作
          </span>
        </Space>
      </div>
      
      <div style={{ flex: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeContextMenu={onNodeContextMenu}
          nodeTypes={nodeTypes}
          fitView
          deleteKeyCode={readOnly ? null : 'Delete'}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
        
        {/* 右键菜单 */}
        {contextMenuNode && (
          <>
            <div
              style={{
                position: 'fixed',
                left: 0,
                top: 0,
                width: '100%',
                height: '100%',
                zIndex: 999,
              }}
              onClick={() => setContextMenuNode(null)}
              onContextMenu={(e) => e.preventDefault()}
            />
            <div
              style={{
                position: 'fixed',
                left: contextMenuPosition.x,
                top: contextMenuPosition.y,
                zIndex: 1000,
              }}
            >
              {createContextMenu(contextMenuNode)}
            </div>
          </>
        )}
      </div>

      {/* 节点编辑模态框 */}
      <Modal
        title="编辑节点"
        open={nodeModalVisible}
        onOk={handleNodeSave}
        onCancel={() => {
          setNodeModalVisible(false);
          setEditingNode(null);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="label" label="节点名称" rules={[{ required: true, message: '请输入节点名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述" rules={[{ required: true, message: '请输入节点描述' }]}>
            <TextArea rows={3} placeholder="请输入节点描述" />
          </Form.Item>
          <Form.Item name="executionStatus" label="执行状态">
            <Select placeholder="请选择执行状态">
              <Option value="pending">待执行</Option>
              <Option value="running">执行中</Option>
              <Option value="success">成功</Option>
              <Option value="failed">失败</Option>
              <Option value="skipped">跳过</Option>
            </Select>
          </Form.Item>
          <Form.Item name="healthStatus" label="健康状态">
            <Select placeholder="请选择健康状态">
              <Option value="unknown">未知</Option>
              <Option value="healthy">健康</Option>
              <Option value="warning">警告</Option>
              <Option value="critical">严重</Option>
              <Option value="error">错误</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

const FaultTreeEditor: React.FC<FaultTreeEditorProps> = (props) => {
  return (
    <ReactFlowProvider>
      <FaultTreeEditorContent {...props} />
    </ReactFlowProvider>
  );
};

export default FaultTreeEditor;