/**
 * 知识库树形目录结构组件
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Tree,
  Button,
  Space,
  Dropdown,
  Modal,
  message,
  Spin,
  Empty,
  Tooltip
} from 'antd';
import {
  BookOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderAddOutlined,
  EyeOutlined,
  UsergroupAddOutlined
} from '@ant-design/icons';
import type { DataNode } from 'antd/es/tree';

import { KnowledgeBase, KBFolder, KBDocument } from '../types/kb';
import { kbApi } from '@/services/kbApi';

interface TreeNodeData extends DataNode {
  type: 'kb' | 'folder' | 'document';
  data?: KnowledgeBase | KBFolder | KBDocument;
  kbId?: string; // 所属知识库ID
}

interface KBTreeStructureProps {
  knowledgeBases: KnowledgeBase[];
  loading: boolean;
  onKBSelect: (kb: KnowledgeBase | null) => void;
  selectedKB: KnowledgeBase | null;
  onCreateKB: () => void;
  onEditKB: (kb: KnowledgeBase) => void;
  onDeleteKB: (kb: KnowledgeBase) => void;
  onManageContent: (kb: KnowledgeBase) => void;
  onRefresh: () => void; // 添加刷新回调
  onNodeSelect?: (node: TreeNodeData | null, path: string[]) => void; // 添加节点选择回调
  searchText: string;
}

const KBTreeStructure: React.FC<KBTreeStructureProps> = ({
  knowledgeBases,
  loading,
  onKBSelect,
  selectedKB,
  onCreateKB,
  onEditKB,
  onDeleteKB,
  onManageContent,
  onRefresh,
  onNodeSelect,
  searchText
}) => {
  const [treeData, setTreeData] = useState<TreeNodeData[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [hoveredNodeKey, setHoveredNodeKey] = useState<string>('');
  const [autoExpandParent, setAutoExpandParent] = useState(true);
  const [loadedKBs, setLoadedKBs] = useState<Set<string>>(new Set()); // 已加载的知识库缓存
  
  // Modal状态
  const [createFolderVisible, setCreateFolderVisible] = useState(false);
  const [renameFolderVisible, setRenameFolderVisible] = useState(false);
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [newFolderName, setNewFolderName] = useState('');

  // 构建树形数据 - 优化版本，减少API调用
  const buildTreeData = async (kbs: KnowledgeBase[]): Promise<TreeNodeData[]> => {
    if (kbs.length === 0) return [];
    
    const treeNodes: TreeNodeData[] = [];

    // 为每个知识库创建基础节点，延迟加载子节点
    for (const kb of kbs) {
      const kbNode: TreeNodeData = {
        key: `kb-${kb.kb_id}`,
        title: kb.kb_name,
        icon: <BookOutlined />,
        // 不设置 children 属性，让 Tree 组件认为这是一个可展开的节点
        type: 'kb',
        data: kb,
        kbId: kb.kb_id,
      };

      treeNodes.push(kbNode);
    }

    return treeNodes;
  };

  // 延迟加载指定知识库的目录结构
  const loadKBChildren = async (kbId: string): Promise<TreeNodeData[]> => {
    try {
      const children: TreeNodeData[] = [];
      
      // 获取目录树
      const folderResponse = await kbApi.getFolderTree(kbId);
      if (folderResponse.status === 'ok' && folderResponse.data.tree) {
        const folderNodes = buildFolderNodes(folderResponse.data.tree, kbId);
        children.push(...folderNodes);
      }

      // 获取根目录下的文档
      const docsResponse = await kbApi.getFolderDocuments(kbId, null, { page: 1, page_size: 100 });
      if (docsResponse.status === 'ok' && docsResponse.data.items) {
        const docNodes: TreeNodeData[] = docsResponse.data.items.map((doc) => ({
          key: `${kbId}-doc-${doc.file_id}`,
          title: doc.display_name || doc.file_name,
          icon: <FileTextOutlined />,
          isLeaf: true,
          type: 'document',
          data: doc,
          kbId: kbId,
        }));
        children.push(...docNodes);
      }

      return children;
    } catch (error) {
      console.error(`获取知识库 ${kbId} 的目录结构失败:`, error);
      return [];
    }
  };

  // 构建目录节点 - 不再递归调用API，只构建结构
  const buildFolderNodes = (folders: KBFolder[], kbId: string): TreeNodeData[] => {
    const folderNodes: TreeNodeData[] = [];

    for (const folder of folders) {
      // 构建子节点
      const childrenNodes: TreeNodeData[] = [];
      
      // 递归构建子目录结构（不调用API）
      if (folder.children && folder.children.length > 0) {
        const subFolderNodes = buildFolderNodes(folder.children, kbId);
        childrenNodes.push(...subFolderNodes);
      }

      const folderNode: TreeNodeData = {
        key: `${kbId}-folder-${folder.folder_id}`,
        title: folder.folder_name,
        icon: expandedKeys.includes(`${kbId}-folder-${folder.folder_id}`) ? <FolderOpenOutlined /> : <FolderOutlined />,
        children: childrenNodes.length > 0 ? childrenNodes : undefined,
        type: 'folder',
        data: folder,
        kbId: kbId,
      };

      folderNodes.push(folderNode);
    }

    return folderNodes;
  };

  // 加载树形数据 - 优化版本，只加载基础结构
  const loadTreeData = async () => {
    try {
      const data = await buildTreeData(knowledgeBases);
      setTreeData(data);
      
      // 清空已加载缓存，因为知识库列表可能已变化
      setLoadedKBs(new Set());
      
      // 不再默认展开，让用户按需展开以减少API调用
    } catch (error) {
      console.error('加载树形数据失败:', error);
    }
  };

  // 监听知识库变化 - 包括名称、描述等内容变化
  const kbDataString = knowledgeBases.map(kb => 
    `${kb.kb_id}-${kb.kb_name}-${kb.update_time}`
  ).sort().join('|');
  
  useEffect(() => {
    if (knowledgeBases.length > 0) {
      loadTreeData();
    } else {
      setTreeData([]);
      setExpandedKeys([]);
    }
  }, [kbDataString]); // 监听知识库数据的实际变化

  // 递归构建完整的节点路径
  const buildNodePath = (node: TreeNodeData): string[] => {
    const path: string[] = [];
    
    // 找到所属知识库
    const kb = knowledgeBases.find(k => k.kb_id === node.kbId);
    if (kb) {
      path.push(kb.kb_name);
    }
    
    // 如果是目录或文档，需要构建完整路径
    if (node.type === 'folder' || node.type === 'document') {
      const fullPath = findNodeFullPath(node.key as string, treeData);
      if (fullPath.length > 0) {
        // 排除知识库节点，只添加目录路径
        const directoryPath = fullPath.slice(1); // 去掉知识库节点
        path.push(...directoryPath);
      }
    }
    
    return path;
  };

  // 递归查找节点的完整路径
  const findNodeFullPath = (targetKey: string, nodes: TreeNodeData[], currentPath: string[] = []): string[] => {
    for (const node of nodes) {
      const newPath = [...currentPath, node.title as string];
      
      if (node.key === targetKey) {
        return newPath;
      }
      
      if (node.children && node.children.length > 0) {
        const foundPath = findNodeFullPath(targetKey, node.children, newPath);
        if (foundPath.length > 0) {
          return foundPath;
        }
      }
    }
    return [];
  };

  // 选择节点处理
  const handleSelect = (selectedKeys: React.Key[], info: any) => {
    const key = selectedKeys[0] as string;
    setSelectedKeys(selectedKeys as string[]);
    
    if (!key) {
      onKBSelect(null);
      onNodeSelect?.(null, []);
      return;
    }
    
    const node = info.node as TreeNodeData;
    const nodePath = buildNodePath(node);
    
    if (node.type === 'kb') {
      // 选中知识库时，使用最新的知识库数据
      const latestKB = knowledgeBases.find(kb => kb.kb_id === (node.data as KnowledgeBase).kb_id);
      onKBSelect(latestKB || (node.data as KnowledgeBase));
      onNodeSelect?.(node, nodePath);
    } else if (node.type === 'folder') {
      // 选中目录时，同时选中所属的知识库
      const kb = knowledgeBases.find(k => k.kb_id === node.kbId);
      if (kb) {
        onKBSelect(kb);
      }
      onNodeSelect?.(node, nodePath);
    } else if (node.type === 'document') {
      // 选中文档时，同时选中所属的知识库
      const kb = knowledgeBases.find(k => k.kb_id === node.kbId);
      if (kb) {
        onKBSelect(kb);
      }
      onNodeSelect?.(node, nodePath);
    }
  };

  // 异步加载数据
  const handleLoadData = async (treeNode: any): Promise<void> => {
    const nodeData = treeNode as TreeNodeData;
    
    if (nodeData.type === 'kb') {
      const kbId = (nodeData.data as KnowledgeBase).kb_id;
      
      // 如果已经加载过，直接返回
      if (loadedKBs.has(kbId)) {
        return;
      }
      
      try {
        const children = await loadKBChildren(kbId);
        
        // 更新树数据
        setTreeData(prevTreeData => {
          return prevTreeData.map(node => {
            if (node.key === nodeData.key) {
              return {
                ...node,
                children: children.length > 0 ? children : []
              };
            }
            return node;
          });
        });
        
        // 标记为已加载
        setLoadedKBs(prev => new Set([...prev, kbId]));
      } catch (error) {
        console.error(`加载知识库 ${kbId} 内容失败:`, error);
        throw error;
      }
    }
  };

  // 展开/收起处理
  const handleExpand = (expandedKeys: React.Key[]) => {
    setExpandedKeys(expandedKeys as string[]);
    setAutoExpandParent(false);
  };

  // 获取节点操作菜单
  const getContextMenuItems = (node: TreeNodeData) => {
    const items = [];
    
    if (node.type === 'kb') {
      const kb = node.data as KnowledgeBase;
      items.push(
        {
          key: 'create-folder',
          icon: <FolderAddOutlined />,
          label: '新建目录',
          onClick: () => handleCreateFolder(node),
        },
        {
          key: 'manage',
          icon: <FolderOutlined />,
          label: '管理内容',
          onClick: () => onManageContent(kb),
        },
        {
          type: 'divider' as const,
        },
        {
          key: 'edit',
          icon: <EditOutlined />,
          label: '编辑知识库',
          onClick: () => onEditKB(kb),
        },
        {
          key: 'permissions',
          icon: <UsergroupAddOutlined />,
          label: '权限管理',
          onClick: () => message.info('权限管理功能开发中'),
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除知识库',
          onClick: () => onDeleteKB(kb),
          danger: true,
        }
      );
    } else if (node.type === 'folder') {
      items.push(
        {
          key: 'create-folder',
          icon: <FolderAddOutlined />,
          label: '新建子目录',
          onClick: () => handleCreateFolder(node),
        },
        {
          key: 'rename',
          icon: <EditOutlined />,
          label: '重命名',
          onClick: () => handleRenameFolder(node),
        },
        {
          type: 'divider' as const,
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除目录',
          onClick: () => handleDeleteFolder(node),
          danger: true,
        }
      );
    } else if (node.type === 'document') {
      items.push({
        key: 'view',
        icon: <EyeOutlined />,
        label: '查看详情',
        onClick: () => message.info('文档详情功能开发中'),
      });
    }
    
    return items;
  };

  // 创建目录
  const handleCreateFolder = (parentNode: TreeNodeData) => {
    setSelectedNode(parentNode);
    setNewFolderName('');
    setCreateFolderVisible(true);
  };

  // 重命名目录
  const handleRenameFolder = (node: TreeNodeData) => {
    setSelectedNode(node);
    setNewFolderName(node.title as string);
    setRenameFolderVisible(true);
  };

  // 删除目录
  const handleDeleteFolder = (node: TreeNodeData) => {
    if (node.type !== 'folder') return;
    
    const folder = node.data as KBFolder;
    const folderName = node.title as string;
    const kbId = node.kbId!;
    
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除目录"${folderName}"吗？目录下的所有内容也会被删除。`,
      onOk: async () => {
        try {
          await kbApi.deleteFolder(folder.folder_id);
          message.success('目录删除成功');
          
          // 只刷新相关知识库的数据
          await refreshKBData(kbId);
        } catch (error) {
          console.error('删除目录失败:', error);
          message.error('删除失败，请重试');
        }
      },
    });
  };

  // 刷新特定知识库的数据
  const refreshKBData = async (kbId: string) => {
    try {
      const children = await loadKBChildren(kbId);
      
      // 更新树数据
      setTreeData(prevTreeData => {
        return prevTreeData.map(node => {
          if (node.key === `kb-${kbId}`) {
            return {
              ...node,
              children: children.length > 0 ? children : undefined
            };
          }
          return node;
        });
      });
      
      // 确保知识库保持展开状态
      setExpandedKeys(prev => {
        const kbKey = `kb-${kbId}`;
        if (!prev.includes(kbKey)) {
          return [...prev, kbKey];
        }
        return prev;
      });
      
    } catch (error) {
      console.error(`刷新知识库 ${kbId} 数据失败:`, error);
    }
  };

  // 确认创建目录
  const handleCreateFolderConfirm = async () => {
    if (!newFolderName.trim()) {
      message.error('请输入目录名称');
      return;
    }
    
    if (!selectedNode) return;
    
    try {
      let parentFolderId: string | undefined;
      let kbId: string;
      
      if (selectedNode.type === 'kb') {
        // 在知识库根目录下创建
        kbId = (selectedNode.data as KnowledgeBase).kb_id;
        parentFolderId = undefined;
      } else if (selectedNode.type === 'folder') {
        // 在子目录下创建
        kbId = selectedNode.kbId!;
        parentFolderId = (selectedNode.data as KBFolder).folder_id;
      } else {
        return;
      }
      
      await kbApi.createFolder(kbId, {
        folder_name: newFolderName.trim(),
        parent_folder_id: parentFolderId,
      });
      
      message.success('目录创建成功');
      setCreateFolderVisible(false);
      setNewFolderName('');
      
      // 只刷新相关知识库的数据，而不是全部刷新
      await refreshKBData(kbId);
    } catch (error) {
      console.error('创建目录失败:', error);
      message.error('创建失败，请重试');
    }
  };

  // 确认重命名目录
  const handleRenameFolderConfirm = async () => {
    if (!newFolderName.trim()) {
      message.error('请输入目录名称');
      return;
    }
    
    if (!selectedNode || selectedNode.type !== 'folder') return;
    
    try {
      const folder = selectedNode.data as KBFolder;
      const kbId = selectedNode.kbId!;
      
      await kbApi.updateFolder(folder.folder_id, {
        folder_name: newFolderName.trim(),
      });
      
      message.success('目录重命名成功');
      setRenameFolderVisible(false);
      setNewFolderName('');
      
      // 只刷新相关知识库的数据
      await refreshKBData(kbId);
    } catch (error) {
      console.error('重命名失败:', error);
      message.error('重命名失败，请重试');
    }
  };

  // 过滤树数据
  const filterTreeData = (data: TreeNodeData[]): TreeNodeData[] => {
    if (!searchText) return data;
    
    return data.reduce((acc: TreeNodeData[], node) => {
      const title = node.title as string;
      const isMatch = title.toLowerCase().includes(searchText.toLowerCase());
      
      let children: TreeNodeData[] = [];
      if (node.children) {
        children = filterTreeData(node.children);
      }
      
      if (isMatch || children.length > 0) {
        acc.push({
          ...node,
          children: children.length > 0 ? children : node.children,
        });
      }
      
      return acc;
    }, []);
  };

  const filteredTreeData = useMemo(() => filterTreeData(treeData), [treeData, searchText]);

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin />
      </div>
    );
  }

  return (
    <div style={{ flex: 1, padding: '8px', overflow: 'hidden' }}>
      <div style={{ height: '100%', overflow: 'auto' }}>
        {filteredTreeData.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无知识库"
            style={{ padding: '20px 0' }}
          >
            <Button type="primary" onClick={onCreateKB}>
              创建知识库
            </Button>
          </Empty>
        ) : (
          <Tree
            treeData={filteredTreeData}
            selectedKeys={selectedKeys}
            expandedKeys={expandedKeys}
            autoExpandParent={autoExpandParent}
            onSelect={handleSelect}
            onExpand={handleExpand}
            loadData={handleLoadData}
            showLine={{ showLeafIcon: false }}
            blockNode
            titleRender={(nodeData) => (
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  width: '100%',
                }}
                onMouseEnter={() => setHoveredNodeKey(nodeData.key as string)}
                onMouseLeave={() => setHoveredNodeKey('')}
              >
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {nodeData.title}
                </span>
                {/* 所有节点在悬停或选中时显示操作按钮 */}
                {(hoveredNodeKey === nodeData.key || nodeData.key === selectedKeys[0]) && (
                  <Space size={2}>
                    {/* 知识库和目录可以新建子目录 */}
                    {((nodeData as TreeNodeData).type === 'kb' || (nodeData as TreeNodeData).type === 'folder') && (
                      <Tooltip title="新建目录">
                        <Button
                          type="text"
                          size="small"
                          icon={<PlusOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateFolder(nodeData as TreeNodeData);
                          }}
                          style={{ padding: '2px 4px' }}
                        />
                      </Tooltip>
                    )}
                    {/* 更多操作按钮 */}
                    <Dropdown
                      menu={{
                        items: getContextMenuItems(nodeData as TreeNodeData)
                      }}
                      trigger={['click']}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<MoreOutlined />}
                        onClick={(e) => e.stopPropagation()}
                        style={{ padding: '2px 4px' }}
                      />
                    </Dropdown>
                  </Space>
                )}
              </div>
            )}
          />
        )}
      </div>

      {/* 创建目录弹窗 */}
      <Modal
        title="新建目录"
        open={createFolderVisible}
        onOk={handleCreateFolderConfirm}
        onCancel={() => {
          setCreateFolderVisible(false);
          setNewFolderName('');
        }}
        okText="创建"
        cancelText="取消"
      >
        <div style={{ margin: '16px 0' }}>
          <input
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              fontSize: '14px',
            }}
            placeholder="请输入目录名称"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleCreateFolderConfirm();
              }
            }}
            maxLength={100}
          />
        </div>
      </Modal>

      {/* 重命名目录弹窗 */}
      <Modal
        title="重命名目录"
        open={renameFolderVisible}
        onOk={handleRenameFolderConfirm}
        onCancel={() => {
          setRenameFolderVisible(false);
          setNewFolderName('');
        }}
        okText="确定"
        cancelText="取消"
      >
        <div style={{ margin: '16px 0' }}>
          <input
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: '4px',
              fontSize: '14px',
            }}
            placeholder="请输入新的目录名称"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleRenameFolderConfirm();
              }
            }}
            maxLength={100}
          />
        </div>
      </Modal>
    </div>
  );
};

export default KBTreeStructure;