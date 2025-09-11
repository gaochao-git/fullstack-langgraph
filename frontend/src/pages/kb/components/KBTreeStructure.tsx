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
  Tooltip,
  App
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
  hasChildren?: boolean; // 是否有子元素
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
  // 使用 App.useApp 获取 modal 实例
  const { modal } = App.useApp();
  // 目录最大层级深度配置（支持3级目录）
  const MAX_FOLDER_DEPTH = 3;
  const [treeData, setTreeData] = useState<TreeNodeData[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [hoveredNodeKey, setHoveredNodeKey] = useState<string>('');
  const [autoExpandParent, setAutoExpandParent] = useState(true);
  const [loadedKBs, setLoadedKBs] = useState<Set<string>>(new Set()); // 已加载的知识库缓存
  const [nodeChildrenInfo, setNodeChildrenInfo] = useState<Map<string, boolean>>(new Map()); // 节点子元素信息缓存
  
  // Modal状态
  const [createFolderVisible, setCreateFolderVisible] = useState(false);
  const [renameFolderVisible, setRenameFolderVisible] = useState(false);
  const [selectedNode, setSelectedNode] = useState<TreeNodeData | null>(null);
  const [newFolderName, setNewFolderName] = useState('');

  // 检查节点是否有子目录（不包括文档）
  const checkNodeHasChildren = async (kbId: string, folderId: string | null): Promise<boolean> => {
    const cacheKey = `${kbId}-${folderId || 'root'}`;
    
    if (nodeChildrenInfo.has(cacheKey)) {
      return nodeChildrenInfo.get(cacheKey)!;
    }
    
    try {
      const response = await kbApi.checkHasChildren(kbId, folderId);
      if (response.status === 'ok') {
        // 只检查是否有子目录，不考虑文档
        const hasFolders = response.data.has_folders || false;
        setNodeChildrenInfo(prev => new Map(prev.set(cacheKey, hasFolders)));
        return hasFolders;
      }
    } catch (error) {
      console.error(`检查子元素失败: ${cacheKey}`, error);
    }
    
    return false;
  };

  // 构建树形数据 - 基于实际内容决定是否可展开
  const buildTreeData = (kbs: KnowledgeBase[]): TreeNodeData[] => {
    if (kbs.length === 0) return [];
    
    const treeNodes: TreeNodeData[] = [];

    // 为每个知识库创建基础节点
    for (const kb of kbs) {
      // 使用后端返回的has_folders信息决定是否显示展开按钮
      const hasChildren = kb.has_folders || false;
      
      const kbNode: TreeNodeData = {
        key: `kb-${kb.kb_id}`,
        title: `${kb.kb_name}${kb.file_count ? ` (${kb.file_count})` : ''}`,
        icon: <BookOutlined />,
        type: 'kb',
        data: kb,
        kbId: kb.kb_id,
        hasChildren: hasChildren, // 根据后端数据决定
        isLeaf: !hasChildren, // 没有子目录则为叶子节点
      };

      treeNodes.push(kbNode);
    }

    return treeNodes;
  };

  // 延迟加载指定知识库的目录结构
  const loadKBChildren = async (kbId: string): Promise<TreeNodeData[]> => {
    try {
      const children: TreeNodeData[] = [];
      
      // 获取目录树（只获取目录，不获取文档）
      const folderResponse = await kbApi.getFolderTree(kbId);
      if (folderResponse.status === 'ok' && folderResponse.data.tree) {
        const folderNodes = await buildFolderNodes(folderResponse.data.tree, kbId);
        children.push(...folderNodes);
      }

      // 不再在树形结构中显示文档，文档将在选中目录后显示
      return children;
    } catch (error) {
      console.error(`获取知识库 ${kbId} 的目录结构失败:`, error);
      return [];
    }
  };

  // 构建目录节点 - 不再递归调用API，只构建结构
  const buildFolderNodes = async (folders: KBFolder[], kbId: string): Promise<TreeNodeData[]> => {
    const folderNodes: TreeNodeData[] = [];

    for (const folder of folders) {
      // 构建子节点
      const childrenNodes: TreeNodeData[] = [];
      
      // 递归构建子目录结构（不调用API）
      if (folder.children && folder.children.length > 0) {
        const subFolderNodes = await buildFolderNodes(folder.children, kbId);
        childrenNodes.push(...subFolderNodes);
      }

      // 检查目录是否有子目录（不考虑文档）
      const hasChildren = childrenNodes.length > 0 || (folder.children && folder.children.length > 0);

      const folderNode: TreeNodeData = {
        key: `${kbId}-folder-${folder.folder_id}`,
        title: `${folder.folder_name}${folder.file_count ? ` (${folder.file_count})` : ''}`,
        icon: expandedKeys.includes(`${kbId}-folder-${folder.folder_id}`) ? <FolderOpenOutlined /> : <FolderOutlined />,
        children: childrenNodes.length > 0 ? childrenNodes : undefined, // 如果有子节点就设置，否则不设置
        isLeaf: !hasChildren, // 根据是否有子元素来设置叶子节点标记
        type: 'folder',
        data: folder,
        kbId: kbId,
        hasChildren,
      };

      folderNodes.push(folderNode);
    }

    return folderNodes;
  };

  // 加载树形数据 - 优化版本，减少API调用
  const loadTreeData = () => {
    try {
      const data = buildTreeData(knowledgeBases);
      setTreeData(data);
      
      // 清空已加载缓存，因为知识库列表可能已变化
      setLoadedKBs(new Set());
      setNodeChildrenInfo(new Map()); // 清空子元素信息缓存
      
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

  // 计算节点的文件夹层级深度（从1开始计算）
  const getFolderDepth = (node: TreeNodeData): number => {
    if (node.type === 'kb') return 0;
    
    const fullPath = findNodeFullPath(node.key as string, treeData);
    // 返回文件夹层级深度，从1开始
    return fullPath.length - 1;
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
      const kbNode = {
        ...node,
        data: latestKB || node.data
      };
      // 只调用 onNodeSelect，由父组件统一处理
      onNodeSelect?.(kbNode, nodePath);
    } else if (node.type === 'folder') {
      // 选中目录时，直接通知父组件
      onNodeSelect?.(node, nodePath);
    } else if (node.type === 'document') {
      // 选中文档时，直接通知父组件
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
                children: children.length > 0 ? children : [],
                isLeaf: children.length === 0, // 根据实际children数量设置叶子节点状态
                hasChildren: children.length > 0 // 根据实际加载的children数量设置hasChildren
              };
            }
            return node;
          });
        });
        
        // 标记为已加载
        setLoadedKBs(prev => new Set([...prev, kbId]));
      } catch (error) {
        console.error(`加载知识库 ${kbId} 内容失败:`, error);
        // 加载失败时，将节点标记为叶子节点
        setTreeData(prevTreeData => {
          return prevTreeData.map(node => {
            if (node.key === nodeData.key) {
              return {
                ...node,
                children: [],
                isLeaf: true,
                hasChildren: false
              };
            }
            return node;
          });
        });
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
      // 知识库总是可以创建目录，不依赖hasChildren
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
      const currentDepth = getFolderDepth(node);
      const canCreateSubFolder = currentDepth < MAX_FOLDER_DEPTH;
      
      items.push(
        {
          key: 'create-folder',
          icon: <FolderAddOutlined />,
          label: '新建子目录',
          onClick: () => {
            console.log('点击新建子目录');
            handleCreateFolder(node);
          },
          disabled: !canCreateSubFolder,
        },
        {
          key: 'rename',
          icon: <EditOutlined />,
          label: '重命名',
          onClick: () => {
            console.log('点击重命名');
            handleRenameFolder(node);
          },
        },
        {
          type: 'divider' as const,
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除目录',
          onClick: () => {
            console.log('点击删除目录', node);
            handleDeleteFolder(node);
          },
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
    // 检查层级深度限制
    if (parentNode.type === 'folder') {
      const currentDepth = getFolderDepth(parentNode);
      if (currentDepth >= MAX_FOLDER_DEPTH) {
        message.warning(`目录层级深度不能超过${MAX_FOLDER_DEPTH}层`);
        return;
      }
    }
    
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
    console.log('handleDeleteFolder called with node:', node);
    if (node.type !== 'folder') {
      console.log('Node type is not folder:', node.type);
      return;
    }
    
    const folder = node.data as KBFolder;
    console.log('Folder data:', folder);
    
    const folderName = node.title as string;
    const kbId = node.kbId!;
    
    // 使用 App.useApp 提供的 modal 实例，并通过 setTimeout 避免与 Dropdown 冲突
    setTimeout(() => {
      modal.confirm({
        title: '确认删除',
        content: `确定要删除目录"${folderName}"吗？目录下的所有内容也会被删除。`,
        okText: '确定',
        okType: 'danger',
        cancelText: '取消',
        onOk: async () => {
          try {
            console.log('Deleting folder with ID:', folder.folder_id);
            const response = await kbApi.deleteFolder(folder.folder_id);
            console.log('Delete response:', response);
            
            if (response.status === 'ok') {
              message.success('目录删除成功');
              // 只刷新相关知识库的数据
              await refreshKBData(kbId);
            } else {
              message.error(response.msg || '删除失败');
            }
          } catch (error) {
            console.error('删除目录失败:', error);
            message.error('删除失败，请重试');
          }
        },
        onCancel: () => {
          console.log('取消删除');
        },
      });
    }, 100); // 延迟 100ms，给 Dropdown 足够的时间关闭
  };

  // 刷新特定知识库的数据
  const refreshKBData = async (kbId: string) => {
    try {
      // 清除相关缓存
      const keysToRemove = Array.from(nodeChildrenInfo.keys()).filter(key => key.startsWith(`${kbId}-`));
      const newChildrenInfo = new Map(nodeChildrenInfo);
      keysToRemove.forEach(key => newChildrenInfo.delete(key));
      setNodeChildrenInfo(newChildrenInfo);
      
      const children = await loadKBChildren(kbId);
      
      // 检查知识库是否有子目录（children 只包含目录，不包含文档）
      const hasChildren = children.length > 0;
      
      // 更新树数据
      setTreeData(prevTreeData => {
        return prevTreeData.map(node => {
          if (node.key === `kb-${kbId}`) {
            return {
              ...node,
              children: hasChildren ? children : [],
              isLeaf: !hasChildren,
              hasChildren
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
                    {/* 知识库和目录可以新建子目录，但要检查层级限制和是否应该显示按钮 */}
                    {(() => {
                      const node = nodeData as TreeNodeData;
                      const isKB = node.type === 'kb';
                      const isFolder = node.type === 'folder';
                      const canCreateInFolder = isFolder && getFolderDepth(node) < MAX_FOLDER_DEPTH;
                      
                      // 知识库管理场景的+按钮显示逻辑
                      let shouldShowButton = false;
                      if (isKB) {
                        // 知识库节点：用户有写权限就显示+按钮（允许创建目录）
                        const kbData = node.data as KnowledgeBase;
                        const hasWritePermission = ['write', 'admin', 'owner'].includes(kbData.user_permission || '');
                        shouldShowButton = hasWritePermission;
                      } else if (canCreateInFolder) {
                        // 目录节点：在层级限制内就显示+按钮（允许创建子目录）
                        shouldShowButton = true;
                      }
                      
                      return shouldShowButton;
                    })() && (
                      <Tooltip title={
                        (nodeData as TreeNodeData).type === 'folder' && getFolderDepth(nodeData as TreeNodeData) >= MAX_FOLDER_DEPTH 
                          ? `已达到最大层级深度（${MAX_FOLDER_DEPTH}层）` 
                          : "新建目录"
                      }>
                        <Button
                          type="text"
                          size="small"
                          icon={<PlusOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCreateFolder(nodeData as TreeNodeData);
                          }}
                          style={{ padding: '2px 4px' }}
                          disabled={(nodeData as TreeNodeData).type === 'folder' && getFolderDepth(nodeData as TreeNodeData) >= MAX_FOLDER_DEPTH}
                        />
                      </Tooltip>
                    )}
                    {/* 更多操作按钮 */}
                    <Dropdown
                      menu={{
                        items: getContextMenuItems(nodeData as TreeNodeData)
                      }}
                      trigger={['click']}
                      placement="bottomRight"
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