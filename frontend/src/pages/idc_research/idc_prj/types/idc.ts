export interface IDCData {
  id: string;
  name: string;
  location: string;
  serverCount: number;
  cpuUsage: number;
  memoryUsage: number;
  networkLoad: number;
  stabilityScore: number;
  powerUsage: number;
  temperature: number;
  uptime: number;
  status: 'healthy' | 'warning' | 'critical';
  lastUpdated: string;
  performanceHistory: PerformanceMetric[];
}

export interface PerformanceMetric {
  timestamp: string;
  cpu: number;
  memory: number;
  network: number;
  temperature: number;
}

export interface ComparisonReport {
  idcs: string[];
  metrics: {
    avgCpuUsage: number[];
    avgMemoryUsage: number[];
    avgNetworkLoad: number[];
    stabilityScores: number[];
    uptimePercentage: number[];
  };
  recommendations: string[];
}

// 新增应用程序相关类型
export interface Application {
  id: string;
  name: string;
  businessType: string; // 业务类型：支付、备付金、风控等
  version: string;
  deployedIDCs: string[]; // 部署的数据中心ID列表
  services: ApplicationService[];
  isShared: boolean; // 是否为跨数据中心共享业务
  status: 'healthy' | 'warning' | 'critical';
}

export interface ApplicationService {
  id: string;
  name: string;
  type: 'app' | 'database' | 'cache' | 'mq' | 'gateway'; // 服务类型
  idcId: string;
  instances: number;
  metrics: ServiceMetrics;
  dependencies: string[]; // 依赖的其他服务ID
}

export interface ServiceMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkIO: number;
  responseTime: number;
  throughput: number;
  errorRate: number;
  availability: number;
  connections: number;
}

export interface BusinessComparison {
  businessType: string;
  applications: Application[];
  crossIDCMetrics: {
    avgResponseTime: number[];
    avgThroughput: number[];
    avgErrorRate: number[];
    avgAvailability: number[];
  };
  recommendations: string[];
}

// 新增国产替代相关类型
export interface HardwareProduct {
  id: string;
  category: 'server' | 'network' | 'storage' | 'os' | 'database' | 'middleware' | 'security';
  name: string;
  brand: string;
  isDomestic: boolean; // 是否为国产
  model: string;
  quantity: number;
  idcId: string;
  installDate: string;
  warrantyEndDate: string;
  status: 'normal' | 'warning' | 'fault';
  failureCount: number; // 故障次数
  mtbf: number; // 平均故障间隔时间(小时)
}

export interface DomesticSubstitutionMetrics {
  category: string;
  totalCount: number;
  domesticCount: number;
  substitutionRate: number; // 替代率
  brands: BrandDistribution[];
  avgFailureRate: number; // 平均故障率
  domesticFailureRate: number; // 国产产品故障率
  importedFailureRate: number; // 进口产品故障率
}

export interface BrandDistribution {
  brand: string;
  isDomestic: boolean;
  count: number;
  percentage: number;
  avgMtbf: number; // 平均故障间隔时间
}

export interface SubstitutionPlan {
  category: string;
  currentRate: number;
  targetRate: number;
  timeline: string;
  priority: 'high' | 'medium' | 'low';
  challenges: string[];
  recommendations: string[];
}