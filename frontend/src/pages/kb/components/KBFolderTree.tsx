/**
 * 知识库拖拽目录树组件
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Tree,
  Card,
  Button,
  Space,
  Input,
  Dropdown,
  Modal,
  message,
  Spin,
  Empty
} from 'antd';
import {
  FolderOutlined,
  FolderOpenOutlined,
  FileTextOutlined,
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  DeleteOutlined,
  ScissorOutlined,
  FolderAddOutlined
} from '@ant-design/icons';
import type { DataNode, TreeProps } from 'antd/es/tree';

import { KBFolder, KBDocument, TreeNode, DragInfo } from '../types/kb';
import { kbApi } from '@/services/kbApi';

const { Search } = Input;

interface KBFolderTreeProps {
  kbId: string;
  onFolderSelect?: (folderId: string | null, folderInfo: KBFolder | null) => void;
  onDocumentSelect?: (document: KBDocument) => void;
  selectedFolderId?: string | null;
}

const KBFolderTree: React.FC<KBFolderTreeProps> = ({
  kbId,
  onFolderSelect,
  onDocumentSelect,
  selectedFolderId
}) => {
  const [loading, setLoading] = useState(false);
  const [treeData, setTreeData] = useState<DataNode[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>(['root']);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  // Modal状态
  const [createFolderVisible, setCreateFolderVisible] = useState(false);
  const [renameFolderVisible, setRenameFolderVisible] = useState(false);
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [newFolderName, setNewFolderName] = useState('');

  // 加载目录树
  const loadFolderTree = async () => {
    try {
      setLoading(true);
      const [folderResponse, rootDocsResponse] = await Promise.all([
        kbApi.getFolderTree(kbId),
        kbApi.getFolderDocuments(kbId, null, { page: 1, page_size: 100 })
      ]);

      if (folderResponse.status === 'ok' && rootDocsResponse.status === 'ok') {
        const folders = folderResponse.data.tree || [];
        const rootDocuments = rootDocsResponse.data.items || [];
        
        const treeData = await buildTreeData(folders, rootDocuments);
        setTreeData(treeData);
        
        // 默认选中根目录
        if (!selectedKeys.length) {
          setSelectedKeys(['root']);
          onFolderSelect?.(null, null);
        }
      }
    } catch (error) {
      console.error('加载目录树失败:', error);
      message.error('加载失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  // 构建树形数据
  const buildTreeData = async (folders: KBFolder[], rootDocs: KBDocument[] = []): Promise<DataNode[]> => {
    const folderNodes = await Promise.all(
      folders.map(async (folder) => {
        // 获取文件夹下的文档
        let documents: KBDocument[] = [];
        try {
          const docsResponse = await kbApi.getFolderDocuments(kbId, folder.folder_id, { page: 1, page_size: 100 });
          if (docsResponse.status === 'ok') {
            documents = docsResponse.data.items || [];
          }
        } catch (error) {
          console.error(`获取目录 ${folder.folder_id} 下的文档失败:`, error);
        }

        // 构建子节点（子目录 + 文档）
        const childrenNodes: DataNode[] = [];
        
        // 子目录
        if (folder.children && folder.children.length > 0) {
          const subFolderNodes = await buildTreeData(folder.children);
          childrenNodes.push(...subFolderNodes);
        }
        
        // 文档节点
        const documentNodes: DataNode[] = documents.map((doc) => ({
          key: `doc-${doc.file_id}`,
          title: doc.display_name || doc.file_name,
          icon: <FileTextOutlined />,
          isLeaf: true,
          data: doc,
          type: 'document',
          className: doc.is_pinned ? 'pinned-document' : undefined,
        }));
        
        childrenNodes.push(...documentNodes);

        return {
          key: `folder-${folder.folder_id}`,
          title: folder.folder_name,
          icon: <FolderOutlined />,
          children: childrenNodes.length > 0 ? childrenNodes : undefined,
          data: folder,
          type: 'folder',
        };
      })
    );

    // 根目录文档节点
    const rootDocumentNodes: DataNode[] = rootDocs.map((doc) => ({
      key: `doc-${doc.file_id}`,
      title: doc.display_name || doc.file_name,
      icon: <FileTextOutlined />,
      isLeaf: true,
      data: doc,
      type: 'document',
      className: doc.is_pinned ? 'pinned-document' : undefined,
    }));

    // 构建根节点
    const rootNode: DataNode = {
      key: 'root',
      title: '根目录',
      icon: <FolderOpenOutlined />,
      children: [...folderNodes, ...rootDocumentNodes],
      type: 'folder',
      data: null,
    };

    return [rootNode];
  };

  // 初始加载
  useEffect(() => {
    if (kbId) {
      loadFolderTree();
    }
  }, [kbId]);

  // 选择节点处理
  const handleSelect = (selectedKeys: React.Key[], info: any) => {
    const key = selectedKeys[0] as string;
    setSelectedKeys(selectedKeys as string[]);
    
    if (!key) return;
    
    if (key === 'root') {
      onFolderSelect?.(null, null);
    } else if (key.startsWith('folder-')) {
      const folderId = key.replace('folder-', '');
      const folderInfo = info.node.data as KBFolder;
      onFolderSelect?.(folderId, folderInfo);
    } else if (key.startsWith('doc-')) {
      const document = info.node.data as KBDocument;
      onDocumentSelect?.(document);
    }
  };

  // 展开/收起处理
  const handleExpand = (expandedKeys: React.Key[]) => {
    setExpandedKeys(expandedKeys as string[]);
    setAutoExpandParent(false);
  };

  // 暂时移除拖拽功能
  // TODO: 后续实现拖拽功能

  // 右键菜单处理
  const getContextMenuItems = (node: TreeNode) => {
    const items = [];
    
    if (node.type === 'folder') {
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
          disabled: node.key === 'root',
        },
        {
          key: 'delete',
          icon: <DeleteOutlined />,
          label: '删除',
          onClick: () => handleDeleteFolder(node),
          disabled: node.key === 'root',
          danger: true,
        }
      );
    } else {
      items.push(
        {
          key: 'remove',
          icon: <ScissorOutlined />,
          label: '从知识库移除',
          onClick: () => handleRemoveDocument(node),
          danger: true,
        }
      );
    }
    
    return items;
  };

  // 创建目录
  const handleCreateFolder = (parentNode: TreeNode) => {
    setSelectedNode(parentNode);
    setNewFolderName('');
    setCreateFolderVisible(true);
  };

  // 重命名目录
  const handleRenameFolder = (node: TreeNode) => {
    setSelectedNode(node);
    setNewFolderName(node.title as string);
    setRenameFolderVisible(true);
  };

  // 删除目录
  const handleDeleteFolder = (node: TreeNode) => {
    if (node.key === 'root') return;
    
    const folderId = (node.key as string).replace('folder-', '');
    const folderName = node.title as string;
    
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除目录"${folderName}"吗？目录下的所有内容也会被删除。`,
      onOk: async () => {
        try {
          await kbApi.deleteFolder(folderId);
          message.success('目录删除成功');
          loadFolderTree();
        } catch (error) {
          console.error('删除目录失败:', error);
          message.error('删除失败，请重试');
        }
      },
    });
  };

  // 移除文档
  const handleRemoveDocument = (node: TreeNode) => {
    const fileId = (node.key as string).replace('doc-', '');
    const fileName = node.title as string;
    
    Modal.confirm({
      title: '确认移除',
      content: `确定要从知识库中移除文档"${fileName}"吗？`,
      onOk: async () => {
        try {
          await kbApi.removeDocumentFromKB(kbId, fileId);
          message.success('文档移除成功');
          loadFolderTree();
        } catch (error) {
          console.error('移除文档失败:', error);
          message.error('移除失败，请重试');
        }
      },
    });
  };

  // 确认创建目录
  const handleCreateFolderConfirm = async () => {
    if (!newFolderName.trim()) {
      message.error('请输入目录名称');
      return;
    }
    
    try {
      const parentFolderId = selectedNode?.key === 'root' ? undefined : 
                           (selectedNode?.key as string)?.replace('folder-', '');
      
      await kbApi.createFolder(kbId, {
        folder_name: newFolderName.trim(),
        parent_folder_id: parentFolderId,
      });
      
      message.success('目录创建成功');
      setCreateFolderVisible(false);
      setNewFolderName('');
      loadFolderTree();
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
    
    try {
      const folderId = (selectedNode?.key as string)?.replace('folder-', '');
      
      await kbApi.updateFolder(folderId, {
        folder_name: newFolderName.trim(),
      });
      
      message.success('目录重命名成功');
      setRenameFolderVisible(false);
      setNewFolderName('');
      loadFolderTree();
    } catch (error) {
      console.error('重命名失败:', error);
      message.error('重命名失败，请重试');
    }
  };

  // 搜索处理
  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (value) {
      // 展开所有匹配的节点
      const expandKeys: string[] = [];
      const searchInTree = (nodes: DataNode[]) => {
        nodes.forEach(node => {
          if ((node.title as string).toLowerCase().includes(value.toLowerCase())) {
            expandKeys.push(node.key as string);
          }
          if (node.children) {
            searchInTree(node.children);
          }
        });
      };
      searchInTree(treeData);
      setExpandedKeys(expandKeys);
      setAutoExpandParent(true);
    }
  };

  // 过滤树节点
  const filterTreeData = (data: DataNode[]): DataNode[] => {
    if (!searchValue) return data;
    
    return data.reduce((acc: DataNode[], node) => {
      const title = node.title as string;
      const isMatch = title.toLowerCase().includes(searchValue.toLowerCase());
      
      let children: DataNode[] = [];
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

  const filteredTreeData = useMemo(() => filterTreeData(treeData), [treeData, searchValue]);

  return (
    <Card
      title="目录结构"
      size="small"
      extra={
        <Button
          type="text"
          size="small"
          icon={<PlusOutlined />}
          onClick={() => handleCreateFolder({ key: 'root', title: '根目录', type: 'folder' } as TreeNode)}
        >
          新建目录
        </Button>
      }
      style={{ height: '100%' }}
      bodyStyle={{ height: 'calc(100% - 57px)', padding: '8px' }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="small">
        {/* 搜索框 */}
        <Search
          placeholder="搜索目录或文档"
          allowClear
          size="small"
          onSearch={handleSearch}
          style={{ marginBottom: 8 }}
        />
        
        {/* 目录树 */}
        <div style={{ height: 'calc(100vh - 300px)', overflow: 'auto' }}>
          <Spin spinning={loading}>
            {filteredTreeData.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无目录"
                style={{ padding: '20px 0' }}
              />
            ) : (
              <Tree
                treeData={filteredTreeData}
                selectedKeys={selectedKeys}
                expandedKeys={expandedKeys}
                autoExpandParent={autoExpandParent}
                onSelect={handleSelect}
                onExpand={handleExpand}
                // 暂时移除拖拽功能
                // draggable={{
                //   icon: false,
                //   nodeDraggable: (node) => node.key !== 'root',
                // }}
                titleRender={(nodeData) => (
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      width: '100%',
                    }}
                  >
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {nodeData.title}
                    </span>
                    {nodeData.key !== 'root' && (
                      <Dropdown
                        menu={{
                          items: getContextMenuItems(nodeData as TreeNode)
                        }}
                        trigger={['click']}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          type="text"
                          size="small"
                          icon={<MoreOutlined />}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </Dropdown>
                    )}
                  </div>
                )}
              />
            )}
          </Spin>
        </div>
      </Space>

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
        <Input
          placeholder="请输入目录名称"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          onPressEnter={handleCreateFolderConfirm}
          maxLength={100}
        />
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
        <Input
          placeholder="请输入新的目录名称"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          onPressEnter={handleRenameFolderConfirm}
          maxLength={100}
        />
      </Modal>
    </Card>
  );
};

export default KBFolderTree;