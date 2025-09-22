// IDC Research 模块统一导出

// 页面组件
export { default as IDCReportManagement } from './IDCReportManagement';
export { default as IDCAnalysisPage } from './IDCAnalysisPage';

// 类型导出
export interface IDCReport {
  id: string;
  reportName: string;
  idcLocation: string;
  reportType: string;
  generateTime: string;
  status: string;
  powerUsage: number;
  energyEfficiency: number;
  availabilityRate: number;
  alertCount: number;
  fileSize: string;
}

// 导出IDC分析相关类型
export * from './types/idc';