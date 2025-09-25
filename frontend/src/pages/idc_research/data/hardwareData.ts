import { HardwareProduct, DomesticSubstitutionMetrics, BrandDistribution, SubstitutionPlan } from '../types/idc';

// 生成硬件产品数据的辅助函数
function generateHardwareProduct(
  category: HardwareProduct['category'],
  brand: string,
  isDomestic: boolean,
  idcId: string,
  baseQuantity: number = 10
): HardwareProduct[] {
  const products: HardwareProduct[] = [];
  const quantity = Math.floor(baseQuantity * (0.8 + Math.random() * 0.4)); // 80%-120%的变化
  
  const product: HardwareProduct = {
    id: `${category}-${brand}-${idcId}-${Date.now()}`,
    category,
    name: getProductName(category, brand),
    brand,
    isDomestic: isDomestic,
    model: getProductModel(category, brand),
    quantity,
    idcId,
    installDate: getRandomDate(2020, 2024),
    warrantyEndDate: getRandomDate(2025, 2027),
    status: Math.random() > 0.1 ? 'normal' : (Math.random() > 0.5 ? 'warning' : 'fault'),
    failureCount: Math.floor(Math.random() * (isDomestic ? 3 : 2)), // 国产产品故障稍多
    mtbf: Math.floor(8760 * (isDomestic ? 0.85 + Math.random() * 0.3 : 0.9 + Math.random() * 0.2)), // 国产MTBF稍低
  };
  
  products.push(product);
  return products;
}

function getProductName(category: string, brand: string): string {
  const names: Record<string, Record<string, string>> = {
    server: {
      '华为': '华为FusionServer',
      '浪潮': '浪潮英信服务器',
      '联想': '联想ThinkSystem',
      '曙光': '曙光TC4600',
      'Dell': 'Dell PowerEdge',
      'HP': 'HP ProLiant',
      'IBM': 'IBM Power Systems',
    },
    network: {
      '华为': '华为CloudEngine',
      '中兴': '中兴ZXR10',
      '锐捷': '锐捷RG-N18000',
      'Cisco': 'Cisco Catalyst',
      'Juniper': 'Juniper EX Series',
      'Arista': 'Arista 7050X',
    },
    storage: {
      '华为': '华为OceanStor',
      '海康威视': '海康存储',
      '同有科技': '同有NetStor',
      'NetApp': 'NetApp FAS',
      'Dell EMC': 'Dell EMC Unity',
      'HPE': 'HPE 3PAR',
    },
    os: {
      '统信': '统信UOS',
      '麒麟': '银河麒麟',
      '中科方德': '方德Linux',
      'RedHat': 'Red Hat Enterprise Linux',
      'SUSE': 'SUSE Linux Enterprise',
      'Ubuntu': 'Ubuntu Server',
    },
    database: {
      '达梦': '达梦数据库',
      '人大金仓': 'KingbaseES',
      '南大通用': 'GBase',
      'Oracle': 'Oracle Database',
      'Microsoft': 'SQL Server',
      'IBM': 'IBM Db2',
    },
    middleware: {
      '东方通': '东方通TongWeb',
      '金蝶': '金蝶Apusic',
      '宝兰德': '宝兰德BES',
      'IBM': 'IBM WebSphere',
      'Oracle': 'Oracle WebLogic',
      'Red Hat': 'Red Hat JBoss',
    },
    security: {
      '奇安信': '奇安信防火墙',
      '绿盟': '绿盟安全网关',
      '启明星辰': '启明防护系统',
      'Palo Alto': 'Palo Alto Networks',
      'Fortinet': 'FortiGate',
      'Check Point': 'Check Point Firewall',
    },
  };
  
  return names[category]?.[brand] || `${brand} ${category}`;
}

function getProductModel(category: string, brand: string): string {
  const models: Record<string, string[]> = {
    server: ['R4900', 'R5300', 'R740', 'DL380', 'x3650'],
    network: ['S12700', 'S9300', 'C9500', 'EX4600', '7280R'],
    storage: ['5300', '6800', 'VNX5400', '3PAR8400', 'FAS8200'],
    os: ['V20', 'V10', 'RHEL8', 'SLES15', '20.04LTS'],
    database: ['DM8', 'V8R6', 'GBase8a', '19c', '2019', 'v11.5'],
    middleware: ['7.0', 'AS7', 'BES9', 'WAS9', 'WLS14c', 'EAP7'],
    security: ['SG6000', 'NF3180', 'NGFW4600', 'PA3200', 'FG600E', '15600'],
  };
  
  const categoryModels = models[category] || ['Model-1000'];
  return categoryModels[Math.floor(Math.random() * categoryModels.length)];
}

function getRandomDate(startYear: number, endYear: number): string {
  const start = new Date(startYear, 0, 1);
  const end = new Date(endYear, 11, 31);
  const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
  return date.toISOString().split('T')[0];
}

// 品牌定义
const brands = {
  server: {
    domestic: ['华为', '浪潮', '联想', '曙光'],
    imported: ['Dell', 'HP', 'IBM'],
  },
  network: {
    domestic: ['华为', '中兴', '锐捷'],
    imported: ['Cisco', 'Juniper', 'Arista'],
  },
  storage: {
    domestic: ['华为', '海康威视', '同有科技'],
    imported: ['NetApp', 'Dell EMC', 'HPE'],
  },
  os: {
    domestic: ['统信', '麒麟', '中科方德'],
    imported: ['RedHat', 'SUSE', 'Ubuntu'],
  },
  database: {
    domestic: ['达梦', '人大金仓', '南大通用'],
    imported: ['Oracle', 'Microsoft', 'IBM'],
  },
  middleware: {
    domestic: ['东方通', '金蝶', '宝兰德'],
    imported: ['IBM', 'Oracle', 'Red Hat'],
  },
  security: {
    domestic: ['奇安信', '绿盟', '启明星辰'],
    imported: ['Palo Alto', 'Fortinet', 'Check Point'],
  },
};

// 生成所有硬件产品数据
const idcIds = ['idc-beijing-001', 'idc-shanghai-001', 'idc-guangzhou-001', 'idc-shenzhen-001', 'idc-chengdu-001'];

export const mockHardwareProducts: HardwareProduct[] = [];

// 为每个IDC生成硬件产品
idcIds.forEach(idcId => {
  Object.entries(brands).forEach(([category, brandTypes]) => {
    // 国产品牌
    brandTypes.domestic.forEach(brand => {
      const baseQuantity = category === 'server' ? 20 : category === 'network' ? 8 : 5;
      mockHardwareProducts.push(...generateHardwareProduct(
        category as HardwareProduct['category'], 
        brand, 
        true, 
        idcId, 
        baseQuantity
      ));
    });
    
    // 进口品牌
    brandTypes.imported.forEach(brand => {
      const baseQuantity = category === 'server' ? 15 : category === 'network' ? 6 : 4;
      mockHardwareProducts.push(...generateHardwareProduct(
        category as HardwareProduct['category'], 
        brand, 
        false, 
        idcId, 
        baseQuantity
      ));
    });
  });
});

// 计算国产替代率指标
export const domesticSubstitutionMetrics: DomesticSubstitutionMetrics[] = Object.keys(brands).map(category => {
  const categoryProducts = mockHardwareProducts.filter(p => p.category === category);
  const totalCount = categoryProducts.reduce((sum, p) => sum + p.quantity, 0);
  const domesticCount = categoryProducts.filter(p => p.isDomestic).reduce((sum, p) => sum + p.quantity, 0);
  const substitutionRate = totalCount > 0 ? (domesticCount / totalCount) * 100 : 0;
  
  // 计算品牌分布
  const brandStats = new Map<string, { count: number; isDomestic: boolean; mtbfSum: number; productCount: number }>();
  
  categoryProducts.forEach(product => {
    const existing = brandStats.get(product.brand) || { count: 0, isDomestic: product.isDomestic, mtbfSum: 0, productCount: 0 };
    existing.count += product.quantity;
    existing.mtbfSum += product.mtbf;
    existing.productCount += 1;
    brandStats.set(product.brand, existing);
  });
  
  const brandDistributions: BrandDistribution[] = Array.from(brandStats.entries()).map(([brand, stats]) => ({
    brand,
    isDomestic: stats.isDomestic,
    count: stats.count,
    percentage: (stats.count / totalCount) * 100,
    avgMtbf: Math.round(stats.mtbfSum / stats.productCount),
  }));
  
  // 计算故障率
  const domesticProducts = categoryProducts.filter(p => p.isDomestic);
  const importedProducts = categoryProducts.filter(p => !p.isDomestic);
  
  const domesticFailureRate = domesticProducts.length > 0 
    ? domesticProducts.reduce((sum, p) => sum + p.failureCount, 0) / domesticProducts.length 
    : 0;
  const importedFailureRate = importedProducts.length > 0 
    ? importedProducts.reduce((sum, p) => sum + p.failureCount, 0) / importedProducts.length 
    : 0;
  const avgFailureRate = categoryProducts.length > 0 
    ? categoryProducts.reduce((sum, p) => sum + p.failureCount, 0) / categoryProducts.length 
    : 0;
  
  return {
    category: getCategoryName(category),
    totalCount,
    domesticCount,
    substitutionRate: Math.round(substitutionRate * 10) / 10,
    brands: brandDistributions,
    avgFailureRate: Math.round(avgFailureRate * 100) / 100,
    domesticFailureRate: Math.round(domesticFailureRate * 100) / 100,
    importedFailureRate: Math.round(importedFailureRate * 100) / 100,
  };
});

// 替代计划数据
export const substitutionPlans: SubstitutionPlan[] = [
  {
    category: '操作系统',
    currentRate: 45.2,
    targetRate: 80.0,
    timeline: '2025年底',
    priority: 'high',
    challenges: ['兼容性问题', '运维人员培训', '应用程序适配'],
    recommendations: ['建立测试环境', '制定迁移计划', '加强技术培训'],
  },
  {
    category: '数据库',
    currentRate: 32.1,
    targetRate: 70.0,
    timeline: '2026年中',
    priority: 'high',
    challenges: ['数据迁移复杂', '性能调优', '业务连续性'],
    recommendations: ['选择合适的迁移工具', '制定回滚方案', '分阶段实施'],
  },
  {
    category: '服务器',
    currentRate: 58.7,
    targetRate: 85.0,
    timeline: '2025年中',
    priority: 'medium',
    challenges: ['供应链稳定性', '性能差异', '成本控制'],
    recommendations: ['多供应商策略', '性能基准测试', '总体拥有成本分析'],
  },
  {
    category: '网络设备',
    currentRate: 41.3,
    targetRate: 75.0,
    timeline: '2026年底',
    priority: 'medium',
    challenges: ['技术标准差异', '互操作性', '网络稳定性'],
    recommendations: ['标准化网络架构', '渐进式替换', '加强监控'],
  },
  {
    category: '中间件',
    currentRate: 28.5,
    targetRate: 60.0,
    timeline: '2027年中',
    priority: 'low',
    challenges: ['应用依赖复杂', '开发工具链', '技术支持'],
    recommendations: ['应用现代化改造', '容器化部署', '建立技术支持体系'],
  },
];

function getCategoryName(category: string): string {
  const names: Record<string, string> = {
    server: '服务器',
    network: '网络设备',
    storage: '存储设备',
    os: '操作系统',
    database: '数据库',
    middleware: '中间件',
    security: '安全设备',
  };
  return names[category] || category;
}

// IDC名称映射
export const hardwareIdcNameMap: Record<string, string> = {
  'idc-beijing-001': '北京数据中心',
  'idc-shanghai-001': '上海数据中心',
  'idc-guangzhou-001': '广州数据中心',
  'idc-shenzhen-001': '深圳数据中心',
  'idc-chengdu-001': '成都数据中心',
};

// 产品类别映射
export const categoryNames: Record<string, string> = {
  server: '服务器',
  network: '网络设备',
  storage: '存储设备',
  os: '操作系统',
  database: '数据库',
  middleware: '中间件',
  security: '安全设备',
};