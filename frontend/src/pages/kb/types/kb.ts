/**
 * 知识库模块类型定义
 */

// 知识库基础类型
export interface KnowledgeBase {
  kb_id: string;
  kb_name: string;
  kb_description?: string;
  kb_type: string;
  kb_status: number;
  visibility: 'private' | 'internal' | 'public';
  owner_id: string;
  department?: string;
  tags: string[];
  doc_count: number;
  total_chunks: number;
  create_by: string;
  create_time: string;
  update_time: string;
  user_permission?: 'read' | 'write' | 'admin' | 'owner';
  has_folders?: boolean; // 是否有子目录
}

// 目录类型
export interface KBFolder {
  folder_id: string;
  kb_id: string;
  parent_folder_id?: string;
  folder_name: string;
  folder_description?: string;
  folder_type: string;
  sort_order: number;
  inherit_permissions: boolean;
  custom_permissions?: Record<string, any>;
  create_by: string;
  create_time: string;
  update_time: string;
  // 树结构相关属性（后端返回时包含）
  children?: KBFolder[]; // 子目录列表，由后端的邻接列表模型构造
}

// 文档类型
export interface KBDocument {
  file_id: string;
  file_name: string;
  doc_title?: string;
  doc_category?: string;
  doc_status: number;
  file_size: number;
  file_type: string;
  process_status: number;
  vector_status?: number;
  display_name?: string;
  is_pinned: boolean;
  sort_order: number;
  create_time: string;
  add_by: string;
}

// 权限类型
export interface KBPermission {
  kb_id: string;
  user_id: string;
  permission_type: 'read' | 'write' | 'admin';
  granted_by: string;
  granted_time: string;
  expire_time?: string;
}

// 搜索结果类型
export interface SearchResult {
  file_id: string;
  file_name: string;
  kb_id: string;
  kb_name: string;
  chunk_text: string;
  similarity: number;
  chunk_metadata?: Record<string, any>;
}

// 统计信息类型
export interface KBStats {
  total_kbs: number;
  total_docs: number;
  total_chunks: number;
  kb_types: Record<string, number>;
}

// 表单请求类型
export interface KBCreateRequest {
  kb_name: string;
  kb_description?: string;
  kb_type?: string;
  visibility?: 'private' | 'internal' | 'public';
  department?: string;
  tags?: string[];
}

export interface KBUpdateRequest {
  kb_name?: string;
  kb_description?: string;
  kb_type?: string;
  visibility?: 'private' | 'internal' | 'public';
  department?: string;
  tags?: string[];
}

export interface FolderCreateRequest {
  folder_name: string;
  parent_folder_id?: string;
  folder_description?: string;
}

export interface FolderUpdateRequest {
  folder_name?: string;
  folder_description?: string;
  sort_order?: number;
}

export interface DocumentAddRequest {
  file_id: string;
  doc_title?: string;
  doc_category?: string;
  folder_id?: string;
}

export interface DocumentMoveRequest {
  file_id?: string;
  target_folder_id?: string;
  display_name?: string;
  sort_order?: number;
  is_pinned?: boolean;
}

export interface PermissionGrantRequest {
  user_id: string;
  permission_type: 'read' | 'write' | 'admin';
  expire_time?: string;
}

export interface SearchRequest {
  query: string;
  kb_ids?: string[];
  limit?: number;
  score_threshold?: number;
}

// 列表参数类型
export interface ListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// 树节点类型（用于拖拽）
export interface TreeNode {
  key: string;
  title: string;
  children?: TreeNode[];
  isLeaf?: boolean;
  icon?: React.ReactNode;
  data?: KBFolder | KBDocument;
  type: 'folder' | 'document';
}

// 拖拽信息类型
export interface DragInfo {
  node: TreeNode;
  dragNode: TreeNode;
  dragNodesKeys: string[];
  dropPosition: number;
  dropToGap: boolean;
}

// Modal 属性类型
export interface KBModalProps {
  open: boolean;
  onCancel: () => void;
  onSuccess?: (data?: KnowledgeBase) => void;
  initialData?: Partial<KnowledgeBase>;
}

export interface FolderModalProps {
  open: boolean;
  onCancel: () => void;
  onSuccess?: () => void;
  kbId: string;
  parentFolderId?: string;
  initialData?: Partial<KBFolder>;
}

// 常量定义
export const KB_TYPES = {
  GENERAL: 'general',
  TECHNICAL: 'technical',
  FAQ: 'faq',
  TRAINING: 'training',
} as const;

export const VISIBILITY_OPTIONS = {
  PRIVATE: 'private',
  INTERNAL: 'internal',
  PUBLIC: 'public',
} as const;

export const VISIBILITY_COLORS = {
  private: 'default',
  internal: 'processing',
  public: 'success',
} as const;

export const VISIBILITY_TEXTS = {
  private: '私有',
  internal: '内部',
  public: '公开',
} as const;

export const PERMISSION_TYPES = {
  READ: 'read',
  WRITE: 'write',
  ADMIN: 'admin',
} as const;

export const DOCUMENT_STATUS = {
  ACTIVE: 1,
  INACTIVE: 0,
} as const;

export const PROCESS_STATUS = {
  PENDING: 0,
  PROCESSING: 1,
  COMPLETED: 2,
  FAILED: 3,
} as const;