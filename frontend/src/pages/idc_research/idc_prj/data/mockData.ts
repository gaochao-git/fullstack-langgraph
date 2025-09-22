import { IDCData, PerformanceMetric } from '../types/idc';

// 生成性能历史数据
function generatePerformanceHistory(): PerformanceMetric[] {
  const history: PerformanceMetric[] = [];
  const now = new Date();
  
  for (let i = 23; i >= 0; i--) {
    const timestamp = new Date(now.getTime() - i * 60 * 60 * 1000).toISOString();
    history.push({
      timestamp,
      cpu: Math.floor(Math.random() * 40 + 30), // 30-70%
      memory: Math.floor(Math.random() * 30 + 50), // 50-80%
      network: Math.floor(Math.random() * 60 + 20), // 20-80%
      temperature: Math.floor(Math.random() * 10 + 45), // 45-55°C
    });
  }
  
  return history;
}

export const mockIDCData: IDCData[] = [
  {
    id: 'idc-beijing-001',
    name: '北京数据中心',
    location: '北京市海淀区',
    serverCount: 1250,
    cpuUsage: 65,
    memoryUsage: 72,
    networkLoad: 45,
    stabilityScore: 98.5,
    powerUsage: 850,
    temperature: 22,
    uptime: 99.9,
    status: 'healthy',
    lastUpdated: new Date().toISOString(),
    performanceHistory: generatePerformanceHistory(),
  },
  {
    id: 'idc-shanghai-001',
    name: '上海数据中心',
    location: '上海市浦东新区',
    serverCount: 980,
    cpuUsage: 58,
    memoryUsage: 68,
    networkLoad: 52,
    stabilityScore: 97.8,
    powerUsage: 720,
    temperature: 24,
    uptime: 99.7,
    status: 'healthy',
    lastUpdated: new Date().toISOString(),
    performanceHistory: generatePerformanceHistory(),
  },
  {
    id: 'idc-guangzhou-001',
    name: '广州数据中心',
    location: '广州市天河区',
    serverCount: 760,
    cpuUsage: 78,
    memoryUsage: 85,
    networkLoad: 71,
    stabilityScore: 95.2,
    powerUsage: 640,
    temperature: 26,
    uptime: 99.2,
    status: 'warning',
    lastUpdated: new Date().toISOString(),
    performanceHistory: generatePerformanceHistory(),
  },
  {
    id: 'idc-shenzhen-001',
    name: '深圳数据中心',
    location: '深圳市南山区',
    serverCount: 1120,
    cpuUsage: 42,
    memoryUsage: 55,
    networkLoad: 38,
    stabilityScore: 99.1,
    powerUsage: 780,
    temperature: 21,
    uptime: 99.8,
    status: 'healthy',
    lastUpdated: new Date().toISOString(),
    performanceHistory: generatePerformanceHistory(),
  },
  {
    id: 'idc-chengdu-001',
    name: '成都数据中心',
    location: '成都市高新区',
    serverCount: 650,
    cpuUsage: 88,
    memoryUsage: 92,
    networkLoad: 89,
    stabilityScore: 89.5,
    powerUsage: 580,
    temperature: 28,
    uptime: 98.1,
    status: 'critical',
    lastUpdated: new Date().toISOString(),
    performanceHistory: generatePerformanceHistory(),
  },
];

export const chatMessages = [
  {
    id: '1',
    type: 'system' as const,
    content: '您好！我是IDC监控分析助手。您可以询问关于数据中心运行状况、性能分析、机房比对等问题。',
    timestamp: new Date().toISOString(),
  },
];