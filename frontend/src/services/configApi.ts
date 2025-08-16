import { omind_get } from '@/utils/base_api';

export interface UploadConfig {
  max_upload_size_mb: number;
  allowed_extensions: string[];
}

export interface SystemConfig {
  upload: UploadConfig;
}

class ConfigService {
  private config: SystemConfig | null = null;
  private configPromise: Promise<SystemConfig> | null = null;

  /**
   * 获取系统配置（带缓存）
   */
  async getSystemConfig(): Promise<SystemConfig> {
    // 如果已有配置，直接返回
    if (this.config) {
      return this.config;
    }

    // 如果正在加载，返回同一个Promise避免重复请求
    if (this.configPromise) {
      return this.configPromise;
    }

    // 发起新的请求
    this.configPromise = this.fetchSystemConfig();
    
    try {
      this.config = await this.configPromise;
      return this.config;
    } finally {
      this.configPromise = null;
    }
  }

  /**
   * 强制刷新配置
   */
  async refreshConfig(): Promise<SystemConfig> {
    this.config = null;
    this.configPromise = null;
    return this.getSystemConfig();
  }

  /**
   * 获取上传配置
   */
  async getUploadConfig(): Promise<UploadConfig> {
    const config = await this.getSystemConfig();
    return config.upload;
  }

  private async fetchSystemConfig(): Promise<SystemConfig> {
    const response = await omind_get('/api/v1/config/system');
    if (response.status === 'ok' && response.data) {
      return response.data;
    } else {
      // 如果获取失败，返回默认配置
      console.warn('获取系统配置失败，使用默认配置');
      return {
        upload: {
          max_upload_size_mb: 10,
          allowed_extensions: ['.pdf', '.docx', '.txt', '.md']
        }
      };
    }
  }
}

// 导出单例
export const configService = new ConfigService();