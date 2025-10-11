/**
 * 扫描配置相关类型定义
 */

// 示例中的提取项
export interface ExampleExtraction {
  extraction_class: string;
  extraction_text: string;
}

// Few-shot 示例
export interface ScanExample {
  text: string;
  extractions: ExampleExtraction[];
}

// 扫描配置
export interface ScanConfig {
  config_id: string;
  config_name: string;
  config_description?: string;
  prompt_description: string;
  examples?: ScanExample[];
  is_default: boolean;
  status: string;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

// 创建配置请求
export interface ScanConfigCreate {
  config_name: string;
  config_description?: string;
  prompt_description: string;
  examples?: ScanExample[];
  is_default?: boolean;
}

// 更新配置请求
export interface ScanConfigUpdate {
  config_name?: string;
  config_description?: string;
  prompt_description?: string;
  examples?: ScanExample[];
  is_default?: boolean;
  status?: string;
}
