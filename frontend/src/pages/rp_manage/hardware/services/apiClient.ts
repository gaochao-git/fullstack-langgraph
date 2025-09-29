// @ts-nocheck

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '';

type RequestMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS';

type RequestOptions = {
  method?: RequestMethod;
  headers?: Record<string, string>;
  body?: any;
};

const resolveUrl = (endpoint: string) => {
  if (!endpoint) return API_BASE_URL;
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  return `${API_BASE_URL}${endpoint}`;
};

async function request(endpoint: string, options: RequestOptions = {}) {
  const { method = 'GET', headers = {}, body } = options;
  const url = resolveUrl(endpoint);

  const finalHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  const init: RequestInit = {
    method,
    headers: finalHeaders,
    credentials: 'include',
  };

  if (body !== undefined && body !== null) {
    if (body instanceof FormData) {
      init.body = body;
      delete finalHeaders['Content-Type'];
    } else if (method === 'GET' || method === 'DELETE') {
      const params = new URLSearchParams(body).toString();
      endpoint = params ? `${endpoint}?${params}` : endpoint;
      init.body = undefined;
      init.headers = finalHeaders;
      return request(endpoint, { method, headers });
    } else {
      init.body = JSON.stringify(body);
    }
  }

  const response = await fetch(url, init);

  if (response.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    throw new Error('未授权访问，请重新登录');
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  const data = await response.json().catch(() => ({}));
  return {
    data,
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  };
}

const apiClient = {
  request,
  get(endpoint: string, params: Record<string, any> = {}) {
    return request(endpoint, { method: 'GET', body: params });
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
  options(endpoint: string, config: RequestOptions = {}) {
    return request(endpoint, { method: 'OPTIONS', headers: config.headers });
  },
  axiosGet(endpoint: string, config: RequestOptions & { params?: Record<string, any> } = {}) {
    const params = config.params || {};
    const query = new URLSearchParams(params).toString();
    const target = query ? `${endpoint}?${query}` : endpoint;
    return request(target, { method: 'GET', headers: config.headers });
  },
  axiosPost(endpoint: string, data: any, config: RequestOptions = {}) {
    return request(endpoint, { method: 'POST', body: data, headers: config.headers });
  },
  getDiskPrediction(params: Record<string, any> = {}) {
    return this.axiosGet('/api/cmdb/v1/disk-prediction', { params });
  },
};

export default apiClient;
