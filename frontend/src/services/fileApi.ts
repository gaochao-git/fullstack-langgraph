import { omind_get, omind_post } from '@/utils/base_api';

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
  // 上传文件（支持进度回调）
  async uploadFile(
    file: File, 
    onProgress?: (percent: number) => void
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await omind_post('/api/v1/agents/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent: any) => {
        if (progressEvent.total && onProgress) {
          const percentComplete = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentComplete);
        }
      }
    });
    
    // response 已经是处理后的数据
    if (response.status === 'ok' && response.data) {
      return response.data;
    } else {
      // 业务错误，使用返回的错误消息
      throw new Error(response.msg || '上传失败');
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
    const response = await omind_get(`/api/v1/agents/files/${fileId}/status`, { showLoading: false });
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
  },

  // 下载文档
  async downloadDocument(fileId: string): Promise<Blob> {
    const token = localStorage.getItem('access_token');
    const headers: any = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`/api/v1/agents/files/${fileId}/download`, {
      method: 'GET',
      headers: headers
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`下载失败: ${errorText || response.statusText}`);
    }

    return response.blob();
  }
};