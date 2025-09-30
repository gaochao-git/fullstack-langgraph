// @ts-nocheck

/**
 * 硬件资源管理API客户端
 * 通过主项目后端代理转发到独立的硬件资源管理服务
 */

// 使用代理路径，通过主项目后端（8000端口）转发到硬件服务（8888端口）
const API_BASE_URL = '/api/v1/hardware-proxy';

type RequestMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS';

type RequestOptions = {
  method?: RequestMethod;
  headers?: Record<string, string>;
  body?: any;
  params?: Record<string, any>;
};

const resolveUrl = (endpoint: string) => {
  if (!endpoint) return API_BASE_URL;
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  // 移除开头的斜杠，避免重复
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

/**
 * 获取认证令牌
 * 从主项目的存储中获取
 */
const getAuthToken = () => {
  // 尝试多个可能的存储键
  return localStorage.getItem('access_token') ||
         localStorage.getItem('token') ||
         localStorage.getItem('auth_token');
};

async function request(endpoint: string, options: RequestOptions = {}) {
  const { method = 'GET', headers = {}, body, params } = options;
  let url = resolveUrl(endpoint);

  const finalHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // 添加认证令牌
  const token = getAuthToken();
  if (token) {
    finalHeaders['Authorization'] = `Bearer ${token}`;
  }

  const init: RequestInit = {
    method,
    headers: finalHeaders,
    credentials: 'include', // 包含cookies
  };

  // 处理查询参数
  if (params && Object.keys(params).length > 0) {
    const queryString = new URLSearchParams(params).toString();
    url = `${url}${url.includes('?') ? '&' : '?'}${queryString}`;
  }

  // 处理请求体
  if (body !== undefined && body !== null && method !== 'GET' && method !== 'DELETE') {
    if (body instanceof FormData) {
      init.body = body;
      delete finalHeaders['Content-Type'];
    } else {
      init.body = JSON.stringify(body);
    }
  }

  try {
    const response = await fetch(url, init);

    // 处理认证错误
    if (response.status === 401) {
      // 清理本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('token');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');

      // 跳转到登录页
      window.location.href = '/login';
      throw new Error('认证失败，请重新登录');
    }

    // 处理其他错误
    if (!response.ok) {
      let errorMessage = `请求失败 (${response.status})`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        const errorText = await response.text();
        if (errorText) errorMessage = errorText;
      }
      throw new Error(errorMessage);
    }

    // 解析响应
    const data = await response.json().catch(() => ({}));
    return {
      data,
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    };
  } catch (error) {
    console.error('API请求错误:', error);
    throw error;
  }
}

const apiClient = {
  request,

  get(endpoint: string, params: Record<string, any> = {}) {
    return request(endpoint, { method: 'GET', params });
  },

  post(endpoint: string, data: any = {}, config: RequestOptions = {}) {
    return request(endpoint, { method: 'POST', body: data, headers: config.headers });
  },

  put(endpoint: string, data: any = {}, config: RequestOptions = {}) {
    return request(endpoint, { method: 'PUT', body: data, headers: config.headers });
  },

  delete(endpoint: string, data: any = {}, config: RequestOptions = {}) {
    return request(endpoint, { method: 'DELETE', body: data, headers: config.headers });
  },

  patch(endpoint: string, data: any = {}, config: RequestOptions = {}) {
    return request(endpoint, { method: 'PATCH', body: data, headers: config.headers });
  },

  // 兼容旧的方法
  axiosGet(endpoint: string, config: RequestOptions & { params?: Record<string, any> } = {}) {
    return this.get(endpoint, config.params || {});
  },

  axiosPost(endpoint: string, data: any, config: RequestOptions = {}) {
    return this.post(endpoint, data, config);
  },

  // 硬件资源管理特定API（这些将通过代理转发到8888端口）
  // 注意：不要在路径前面加 /api，因为resolveUrl会自动添加代理前缀

  // 资源池相关
  getHostsPoolDetail() {
    return this.get('cmdb/v1/get_hosts_pool_detail');
  },

  // 集群相关
  getClusterGroups() {
    return this.get('cmdb/v1/cluster-groups');
  },

  getClusterResourcesMax(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/cluster-resources-max', params);
  },

  getClusterResources(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/cluster-resources', params);
  },

  getClusterConfirmSummary(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/cluster-confirm-summary', params);
  },

  getClusterGroupReport(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/cluster-group-report', params);
  },

  // 服务器资源相关
  getServerResourcesMax(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/server-resources-max', params);
  },

  getServerResources(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/server-resources', params);
  },

  // 硬件验证相关
  getHardwareResourceVerificationStatus(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/hardware-resource-verification-status', params);
  },

  getHardwareResourceVerificationHistory(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/hardware-resource-verification-history', params);
  },

  postHardwareResourceVerification(data: any) {
    return this.post('cmdb/v1/hardware-resource-verification', data);
  },

  // 监控相关
  verifyMonitoringData(data: any) {
    return this.post('cmdb/v1/verify-monitoring-data', data);
  },

  fetchHostsHardwareInfo(data: any) {
    return this.post('cmdb/v1/fetch-hosts-hardware-info', data);
  },

  // 备份恢复相关
  getBackupRestoreCheckInfo(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/backup-restore-check-info', params);
  },

  // 任务相关
  getScheduledTaskExecutionDetails(taskId: string) {
    return this.get(`cmdb/v1/scheduled-tasks/execution-details/${taskId}`);
  },

  // 磁盘预测
  getDiskPrediction(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/disk-prediction', params);
  },

  // 邮件发送
  sendEmail(data: any) {
    return this.post('cmdb/v1/send-email', data);
  },

  // 其他原有方法保持兼容
  getHardwareResources(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/hardware-resources', params);
  },

  getHostList(params: Record<string, any> = {}) {
    return this.get('cmdb/v1/hosts', params);
  },

  getClusterInfo(clusterId: string) {
    return this.get(`cmdb/v1/clusters/${clusterId}`);
  },
};

export default apiClient;
