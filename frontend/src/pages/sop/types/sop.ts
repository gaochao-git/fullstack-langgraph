// SOP模板接口 - 简化版
export interface SOPTemplate {
  id: number;
  sop_id: string;
  sop_title: string;
  sop_description: string; // 包含所有步骤的文本描述
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

// SOP模板创建/更新请求接口
export interface SOPTemplateRequest {
  sop_id: string;
  sop_title: string;
  sop_description: string; // 包含所有步骤的文本描述（必填）
}

// SOP查询参数接口
export interface SOPQueryParams {
  search?: string;
  limit?: number;
  offset?: number;
}

// SOP查询参数接口（更新为GET请求参数）
export interface SOPListParams {
  page?: number;
  size?: number;
  search?: string;
}