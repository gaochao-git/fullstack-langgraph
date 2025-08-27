/**
 * 知识库 API服务 - API层透传，不处理业务逻辑
 */

import { omind_get, omind_post, omind_put, omind_del } from '@/utils/base_api';

// 知识库类型定义
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
}

export interface KBFolder {
  folder_id: string;
  kb_id: string;
  parent_folder_id?: string;
  folder_name: string;
  folder_description?: string;
  folder_type: string;
  sort_order: number;
  create_by: string;
  create_time: string;
  children?: KBFolder[];
}

export interface KBDocument {
  file_id: string;
  file_name: string;
  doc_title?: string;
  doc_category?: string;
  doc_status: number;
  file_size: number;
  file_type: string;
  process_status: number;
  display_name?: string;
  is_pinned: boolean;
  sort_order: number;
  create_time: string;
}

// 请求参数类型
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
  file_id: string;
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

export interface ListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

// 知识库 API接口类
export class KBApi {
  private baseUrl = '/api/v1/kb';

  // ==================== 知识库管理 ====================
  
  /**
   * 创建知识库
   */
  async createKnowledgeBase(data: KBCreateRequest) {
    return await omind_post('/api/v1/kb/knowledge-bases', data);
  }

  /**
   * 获取知识库列表
   */
  async getKnowledgeBases(params: ListParams = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());
    if (params.search) queryParams.append('search', params.search);

    const url = `/api/v1/kb/knowledge-bases${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  /**
   * 获取知识库详情
   */
  async getKnowledgeBase(kbId: string) {
    return await omind_get(`/api/v1/kb/knowledge-bases/${kbId}`);
  }

  /**
   * 更新知识库
   */
  async updateKnowledgeBase(kbId: string, data: KBUpdateRequest) {
    return await omind_put(`/api/v1/kb/knowledge-bases/${kbId}`, data);
  }

  /**
   * 删除知识库
   */
  async deleteKnowledgeBase(kbId: string) {
    return await omind_del(`/api/v1/kb/knowledge-bases/${kbId}`);
  }

  // ==================== 知识库文档管理 ====================

  /**
   * 添加文档到知识库
   */
  async addDocumentToKB(kbId: string, data: DocumentAddRequest) {
    return await omind_post(`/api/v1/kb/knowledge-bases/${kbId}/documents`, data);
  }

  /**
   * 从知识库移除文档
   */
  async removeDocumentFromKB(kbId: string, fileId: string) {
    return await omind_del(`/api/v1/kb/knowledge-bases/${kbId}/documents/${fileId}`);
  }

  /**
   * 获取知识库文档列表
   */
  async getKBDocuments(kbId: string, params: ListParams = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());

    const url = `/api/v1/kb/knowledge-bases/${kbId}/documents${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  // ==================== 知识库目录管理 ====================

  /**
   * 创建目录
   */
  async createFolder(kbId: string, data: FolderCreateRequest) {
    return await omind_post(`/api/v1/kb/knowledge-bases/${kbId}/folders`, data);
  }

  /**
   * 获取目录树
   */
  async getFolderTree(kbId: string) {
    return await omind_get(`/api/v1/kb/knowledge-bases/${kbId}/folders/tree`);
  }

  /**
   * 更新目录
   */
  async updateFolder(folderId: string, data: FolderUpdateRequest) {
    return await omind_put(`/api/v1/kb/folders/${folderId}`, data);
  }

  /**
   * 移动目录
   */
  async moveFolder(folderId: string, targetParentId?: string) {
    const data = targetParentId ? { target_parent_id: targetParentId } : {};
    return await omind_post(`/api/v1/kb/folders/${folderId}/move`, data);
  }

  /**
   * 删除目录
   */
  async deleteFolder(folderId: string) {
    return await omind_del(`/api/v1/kb/folders/${folderId}`);
  }

  // ==================== 目录文档管理 ====================

  /**
   * 获取目录下的文档列表
   * @param kbId 知识库ID
   * @param folderId 目录ID，null表示根目录
   * @param params 分页参数
   */
  async getFolderDocuments(kbId: string, folderId: string | null = null, params: ListParams = {}) {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', params.page.toString());
    if (params.page_size) queryParams.append('page_size', params.page_size.toString());

    const folderPath = folderId || 'root';
    const url = `/api/v1/kb/knowledge-bases/${kbId}/folders/${folderPath}/documents${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return await omind_get(url);
  }

  /**
   * 添加文档到目录（拖拽功能）
   */
  async addDocumentToFolder(kbId: string, folderId: string | null, data: DocumentMoveRequest) {
    const folderPath = folderId || 'root';
    return await omind_post(`/api/v1/kb/knowledge-bases/${kbId}/folders/${folderPath}/documents`, data);
  }

  // ==================== 权限管理 ====================

  /**
   * 授予知识库权限
   */
  async grantPermission(kbId: string, data: PermissionGrantRequest) {
    return await omind_post(`/api/v1/kb/knowledge-bases/${kbId}/permissions`, data);
  }

  // ==================== 搜索 ====================

  /**
   * 知识库搜索
   */
  async searchKnowledgeBase(params: {
    query: string;
    kb_ids?: string[];
    limit?: number;
    score_threshold?: number;
  }) {
    return await omind_post('/api/v1/kb/search', params);
  }

  // ==================== 统计信息 ====================

  /**
   * 获取知识库统计信息
   */
  async getKBStats() {
    return await omind_get('/api/v1/kb/stats');
  }
}

// 导出实例
export const kbApi = new KBApi();

export default KBApi;