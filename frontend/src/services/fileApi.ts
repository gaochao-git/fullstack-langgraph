import { omind_post, omind_get } from '@/utils/base_api';

export interface FileUploadResponse {
  file_id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  upload_time: string;
  status: string;
  message?: string;
}

export interface DocumentContent {
  file_id: string;
  file_name: string;
  content: string;
  metadata?: any;
  chunks?: any[];
}

export interface FileProcessStatus {
  file_id: string;
  status: string;
  progress?: number;
  message?: string;
  processed_at?: string;
}

export const fileApi = {
  // 上传文件
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    // 使用原生 fetch，因为 omind_post 可能不支持 FormData
    // 获取 token（如果需要认证）
    const token = localStorage.getItem('access_token');
    const headers: any = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch('/api/v1/agents/files/upload', {
      method: 'POST',
      body: formData,
      headers: headers
      // 不要设置 Content-Type，让浏览器自动设置 multipart/form-data
    });
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.statusText}`);
    }
    
    const result = await response.json();
    if (result.status === 'ok' && result.data) {
      return result.data;
    } else {
      throw new Error(result.msg || '上传失败');
    }
  },

  // 获取文档内容
  async getDocumentContent(fileId: string): Promise<DocumentContent> {
    const response = await omind_get(`/api/v1/agents/files/${fileId}/content`);
    if (response.status === 'ok' && response.data) {
      return response.data;
    } else {
      throw new Error(response.msg || '获取文档内容失败');
    }
  },

  // 获取文件处理状态
  async getFileStatus(fileId: string): Promise<FileProcessStatus> {
    const response = await omind_get(`/api/v1/agents/files/${fileId}/status`);
    if (response.status === 'ok' && response.data) {
      return response.data;
    } else {
      throw new Error(response.msg || '获取文件状态失败');
    }
  },

  // 等待文件处理完成
  async waitForFileReady(fileId: string, maxRetries: number = 30, interval: number = 1000): Promise<void> {
    for (let i = 0; i < maxRetries; i++) {
      const status = await this.getFileStatus(fileId);
      if (status.status === 'ready') {
        return;
      } else if (status.status === 'failed') {
        throw new Error(status.message || '文件处理失败');
      }
      // 等待一段时间后重试
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    throw new Error('文件处理超时');
  }
};