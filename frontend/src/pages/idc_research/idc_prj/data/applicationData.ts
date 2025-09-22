import { Application, ApplicationService, ServiceMetrics } from '../types/idc';

// 生成服务指标的辅助函数
function generateServiceMetrics(baseLoad: number = 50): ServiceMetrics {
  const variance = Math.random() * 30 - 15; // -15% to +15% variance
  const load = Math.max(0, Math.min(100, baseLoad + variance));
  
  return {
    cpuUsage: Math.floor(load),
    memoryUsage: Math.floor(load + Math.random() * 20 - 10),
    diskUsage: Math.floor(Math.random() * 60 + 20),
    networkIO: Math.floor(Math.random() * 80 + 20),
    responseTime: Math.floor(Math.random() * 200 + 50),
    throughput: Math.floor(Math.random() * 1000 + 500),
    errorRate: Math.random() * 2,
    availability: 95 + Math.random() * 4.8,
    connections: Math.floor(Math.random() * 500 + 100),
  };
}

// 支付业务应用
const paymentApplication: Application = {
  id: 'app-payment',
  name: '支付系统',
  businessType: '支付业务',
  version: '2.3.1',
  deployedIDCs: ['idc-beijing-001', 'idc-shanghai-001', 'idc-guangzhou-001', 'idc-shenzhen-001'],
  isShared: true,
  status: 'healthy',
  services: [
    // 北京数据中心服务
    {
      id: 'payment-app-bj',
      name: '支付应用服务器',
      type: 'app',
      idcId: 'idc-beijing-001',
      instances: 8,
      metrics: generateServiceMetrics(45),
      dependencies: ['payment-db-bj', 'payment-cache-bj'],
    },
    {
      id: 'payment-db-bj',
      name: '支付数据库',
      type: 'database',
      idcId: 'idc-beijing-001',
      instances: 3,
      metrics: generateServiceMetrics(65),
      dependencies: [],
    },
    {
      id: 'payment-cache-bj',
      name: '支付缓存服务',
      type: 'cache',
      idcId: 'idc-beijing-001',
      instances: 4,
      metrics: generateServiceMetrics(35),
      dependencies: [],
    },
    // 上海数据中心服务
    {
      id: 'payment-app-sh',
      name: '支付应用服务器',
      type: 'app',
      idcId: 'idc-shanghai-001',
      instances: 6,
      metrics: generateServiceMetrics(52),
      dependencies: ['payment-db-sh', 'payment-cache-sh'],
    },
    {
      id: 'payment-db-sh',
      name: '支付数据库',
      type: 'database',
      idcId: 'idc-shanghai-001',
      instances: 2,
      metrics: generateServiceMetrics(58),
      dependencies: [],
    },
    {
      id: 'payment-cache-sh',
      name: '支付缓存服务',
      type: 'cache',
      idcId: 'idc-shanghai-001',
      instances: 3,
      metrics: generateServiceMetrics(40),
      dependencies: [],
    },
    // 广州数据中心服务
    {
      id: 'payment-app-gz',
      name: '支付应用服务器',
      type: 'app',
      idcId: 'idc-guangzhou-001',
      instances: 4,
      metrics: generateServiceMetrics(75),
      dependencies: ['payment-db-gz', 'payment-cache-gz'],
    },
    {
      id: 'payment-db-gz',
      name: '支付数据库',
      type: 'database',
      idcId: 'idc-guangzhou-001',
      instances: 2,
      metrics: generateServiceMetrics(82),
      dependencies: [],
    },
    {
      id: 'payment-cache-gz',
      name: '支付缓存服务',
      type: 'cache',
      idcId: 'idc-guangzhou-001',
      instances: 2,
      metrics: generateServiceMetrics(68),
      dependencies: [],
    },
    // 深圳数据中心服务
    {
      id: 'payment-app-sz',
      name: '支付应用服务器',
      type: 'app',
      idcId: 'idc-shenzhen-001',
      instances: 5,
      metrics: generateServiceMetrics(38),
      dependencies: ['payment-db-sz', 'payment-cache-sz'],
    },
    {
      id: 'payment-db-sz',
      name: '支付数据库',
      type: 'database',
      idcId: 'idc-shenzhen-001',
      instances: 2,
      metrics: generateServiceMetrics(45),
      dependencies: [],
    },
    {
      id: 'payment-cache-sz',
      name: '支付缓存服务',
      type: 'cache',
      idcId: 'idc-shenzhen-001',
      instances: 3,
      metrics: generateServiceMetrics(32),
      dependencies: [],
    },
  ],
};

// 备付金业务应用
const reserveFundApplication: Application = {
  id: 'app-reserve-fund',
  name: '备付金系统',
  businessType: '备付金业务',
  version: '1.8.2',
  deployedIDCs: ['idc-beijing-001', 'idc-shanghai-001', 'idc-shenzhen-001'],
  isShared: true,
  status: 'warning',
  services: [
    // 北京数据中心服务
    {
      id: 'reserve-app-bj',
      name: '备付金应用服务器',
      type: 'app',
      idcId: 'idc-beijing-001',
      instances: 4,
      metrics: generateServiceMetrics(55),
      dependencies: ['reserve-db-bj', 'reserve-cache-bj'],
    },
    {
      id: 'reserve-db-bj',
      name: '备付金数据库',
      type: 'database',
      idcId: 'idc-beijing-001',
      instances: 2,
      metrics: generateServiceMetrics(70),
      dependencies: [],
    },
    {
      id: 'reserve-cache-bj',
      name: '备付金缓存服务',
      type: 'cache',
      idcId: 'idc-beijing-001',
      instances: 2,
      metrics: generateServiceMetrics(42),
      dependencies: [],
    },
    // 上海数据中心服务
    {
      id: 'reserve-app-sh',
      name: '备付金应用服务器',
      type: 'app',
      idcId: 'idc-shanghai-001',
      instances: 3,
      metrics: generateServiceMetrics(62),
      dependencies: ['reserve-db-sh', 'reserve-cache-sh'],
    },
    {
      id: 'reserve-db-sh',
      name: '备付金数据库',
      type: 'database',
      idcId: 'idc-shanghai-001',
      instances: 2,
      metrics: generateServiceMetrics(68),
      dependencies: [],
    },
    {
      id: 'reserve-cache-sh',
      name: '备付金缓存服务',
      type: 'cache',
      idcId: 'idc-shanghai-001',
      instances: 2,
      metrics: generateServiceMetrics(48),
      dependencies: [],
    },
    // 深圳数据中心服务
    {
      id: 'reserve-app-sz',
      name: '备付金应用服务器',
      type: 'app',
      idcId: 'idc-shenzhen-001',
      instances: 3,
      metrics: generateServiceMetrics(35),
      dependencies: ['reserve-db-sz', 'reserve-cache-sz'],
    },
    {
      id: 'reserve-db-sz',
      name: '备付金数据库',
      type: 'database',
      idcId: 'idc-shenzhen-001',
      instances: 1,
      metrics: generateServiceMetrics(41),
      dependencies: [],
    },
    {
      id: 'reserve-cache-sz',
      name: '备付金缓存服务',
      type: 'cache',
      idcId: 'idc-shenzhen-001',
      instances: 2,
      metrics: generateServiceMetrics(28),
      dependencies: [],
    },
  ],
};

// 风控系统（仅部分数据中心）
const riskControlApplication: Application = {
  id: 'app-risk-control',
  name: '风控系统',
  businessType: '风险控制',
  version: '3.1.0',
  deployedIDCs: ['idc-beijing-001', 'idc-shanghai-001'],
  isShared: false,
  status: 'healthy',
  services: [
    // 北京数据中心服务
    {
      id: 'risk-app-bj',
      name: '风控应用服务器',
      type: 'app',
      idcId: 'idc-beijing-001',
      instances: 6,
      metrics: generateServiceMetrics(48),
      dependencies: ['risk-db-bj', 'risk-cache-bj', 'risk-mq-bj'],
    },
    {
      id: 'risk-db-bj',
      name: '风控数据库',
      type: 'database',
      idcId: 'idc-beijing-001',
      instances: 3,
      metrics: generateServiceMetrics(62),
      dependencies: [],
    },
    {
      id: 'risk-cache-bj',
      name: '风控缓存服务',
      type: 'cache',
      idcId: 'idc-beijing-001',
      instances: 4,
      metrics: generateServiceMetrics(38),
      dependencies: [],
    },
    {
      id: 'risk-mq-bj',
      name: '风控消息队列',
      type: 'mq',
      idcId: 'idc-beijing-001',
      instances: 2,
      metrics: generateServiceMetrics(44),
      dependencies: [],
    },
    // 上海数据中心服务
    {
      id: 'risk-app-sh',
      name: '风控应用服务器',
      type: 'app',
      idcId: 'idc-shanghai-001',
      instances: 4,
      metrics: generateServiceMetrics(52),
      dependencies: ['risk-db-sh', 'risk-cache-sh', 'risk-mq-sh'],
    },
    {
      id: 'risk-db-sh',
      name: '风控数据库',
      type: 'database',
      idcId: 'idc-shanghai-001',
      instances: 2,
      metrics: generateServiceMetrics(58),
      dependencies: [],
    },
    {
      id: 'risk-cache-sh',
      name: '风控缓存服务',
      type: 'cache',
      idcId: 'idc-shanghai-001',
      instances: 3,
      metrics: generateServiceMetrics(41),
      dependencies: [],
    },
    {
      id: 'risk-mq-sh',
      name: '风控消息队列',
      type: 'mq',
      idcId: 'idc-shanghai-001',
      instances: 2,
      metrics: generateServiceMetrics(47),
      dependencies: [],
    },
  ],
};

// 数据分析系统（成都独有）
const analyticsApplication: Application = {
  id: 'app-analytics',
  name: '数据分析系统',
  businessType: '数据分析',
  version: '2.0.5',
  deployedIDCs: ['idc-chengdu-001'],
  isShared: false,
  status: 'critical',
  services: [
    {
      id: 'analytics-app-cd',
      name: '分析应用服务器',
      type: 'app',
      idcId: 'idc-chengdu-001',
      instances: 8,
      metrics: generateServiceMetrics(85),
      dependencies: ['analytics-db-cd', 'analytics-cache-cd'],
    },
    {
      id: 'analytics-db-cd',
      name: '分析数据库',
      type: 'database',
      idcId: 'idc-chengdu-001',
      instances: 4,
      metrics: generateServiceMetrics(92),
      dependencies: [],
    },
    {
      id: 'analytics-cache-cd',
      name: '分析缓存服务',
      type: 'cache',
      idcId: 'idc-chengdu-001',
      instances: 6,
      metrics: generateServiceMetrics(88),
      dependencies: [],
    },
  ],
};

// API网关（所有数据中心）
const gatewayApplication: Application = {
  id: 'app-gateway',
  name: 'API网关',
  businessType: '基础设施',
  version: '1.5.3',
  deployedIDCs: ['idc-beijing-001', 'idc-shanghai-001', 'idc-guangzhou-001', 'idc-shenzhen-001', 'idc-chengdu-001'],
  isShared: true,
  status: 'healthy',
  services: [
    {
      id: 'gateway-bj',
      name: 'API网关',
      type: 'gateway',
      idcId: 'idc-beijing-001',
      instances: 4,
      metrics: generateServiceMetrics(42),
      dependencies: [],
    },
    {
      id: 'gateway-sh',
      name: 'API网关',
      type: 'gateway',
      idcId: 'idc-shanghai-001',
      instances: 3,
      metrics: generateServiceMetrics(38),
      dependencies: [],
    },
    {
      id: 'gateway-gz',
      name: 'API网关',
      type: 'gateway',
      idcId: 'idc-guangzhou-001',
      instances: 2,
      metrics: generateServiceMetrics(65),
      dependencies: [],
    },
    {
      id: 'gateway-sz',
      name: 'API网关',
      type: 'gateway',
      idcId: 'idc-shenzhen-001',
      instances: 3,
      metrics: generateServiceMetrics(31),
      dependencies: [],
    },
    {
      id: 'gateway-cd',
      name: 'API网关',
      type: 'gateway',
      idcId: 'idc-chengdu-001',
      instances: 2,
      metrics: generateServiceMetrics(78),
      dependencies: [],
    },
  ],
};

export const mockApplications: Application[] = [
  paymentApplication,
  reserveFundApplication,
  riskControlApplication,
  analyticsApplication,
  gatewayApplication,
];

// 业务类型映射
export const businessTypes = [
  '支付业务',
  '备付金业务',
  '风险控制',  
  '数据分析',
  '基础设施',
];

// IDC名称映射
export const idcNameMap: Record<string, string> = {
  'idc-beijing-001': '北京数据中心',
  'idc-shanghai-001': '上海数据中心',
  'idc-guangzhou-001': '广州数据中心',
  'idc-shenzhen-001': '深圳数据中心',
  'idc-chengdu-001': '成都数据中心',
};