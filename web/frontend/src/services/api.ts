import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 系统管理 API
export const systemApi = {
  getStatus: () => apiClient.get('/api/status'),
  start: () => apiClient.post('/api/start'),
  stop: () => apiClient.post('/api/stop'),
  restart: () => apiClient.post('/api/restart'),
  getConfig: () => apiClient.get('/api/config'),
  updateConfig: (config: any) => apiClient.put('/api/config', config),
};

// 账户管理 API
export const accountsApi = {
  getAll: () => apiClient.get('/api/accounts'),
  getBalance: (name: string) => apiClient.get(`/api/accounts/${name}/balance`),
  getPositions: (name: string) => apiClient.get(`/api/accounts/${name}/positions`),
  setLeverage: (name: string, leverage: number) =>
    apiClient.post(`/api/accounts/${name}/leverage`, { leverage }),
  toggleEnable: (name: string, enabled: boolean) =>
    apiClient.put(`/api/accounts/${name}/enable`, { enabled }),
};

// 交易监控 API
export const tradesApi = {
  getRecent: (params?: { page?: number; size?: number }) =>
    apiClient.get('/api/trades/recent', { params }),
  getHistory: (params?: any) => apiClient.get('/api/trades/history', { params }),
  getStats: () => apiClient.get('/api/trades/stats'),
  getById: (id: string) => apiClient.get(`/api/trades/${id}`),
};

// 性能监控 API
export const metricsApi = {
  getRateLimit: () => apiClient.get('/api/metrics/rate-limit'),
  getCircuitBreaker: () => apiClient.get('/api/metrics/circuit-breaker'),
  getPerformance: () => apiClient.get('/api/metrics/performance'),
  getSystem: () => apiClient.get('/api/metrics/system'),
};

// 风险管理 API
export const riskApi = {
  getSummary: () => apiClient.get('/api/risk/summary'),
  emergencyStop: () => apiClient.post('/api/risk/emergency-stop'),
  getAlerts: (params?: any) => apiClient.get('/api/risk/alerts', { params }),
  ackAlert: (id: string) => apiClient.post(`/api/risk/alerts/${id}/ack`),
};

// 日志管理 API
export const logsApi = {
  getSystem: (params?: any) => apiClient.get('/api/logs/system', { params }),
  getTrades: (params?: any) => apiClient.get('/api/logs/trades', { params }),
  getErrors: (params?: any) => apiClient.get('/api/logs/errors', { params }),
  clear: (logType: string) => apiClient.delete(`/api/logs/clear?type=${logType}`),
};

export default apiClient;
