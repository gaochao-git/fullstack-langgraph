// SOP严重性级别
export type SOPSeverity = "low" | "medium" | "high" | "critical";

// SOP步骤接口
export interface SOPStep {
  step: number;
  description: string;
  ai_generated: boolean;
  tool: string;
  args: string;
  requires_approval: boolean;
  timeout?: number;
  retry_count?: number;
  on_failure?: "continue" | "stop" | "branch";
}

// SOP模板接口 - 匹配 sop_prompt_templates 表结构
export interface SOPTemplate {
  id: number;
  sop_id: string;
  sop_title: string;
  sop_category: string;
  sop_description?: string;
  sop_severity: SOPSeverity;
  sop_steps: string; // JSON字符串，解析后为SOPStep[]
  tools_required?: string; // JSON字符串，解析后为string[]
  sop_recommendations?: string;
  team_name: string;
  create_by: string;
  update_by?: string;
  create_time: string;
  update_time: string;
}

// SOP模板创建/更新请求接口
export interface SOPTemplateRequest {
  sop_id: string;
  sop_title: string;
  sop_category: string;
  sop_description?: string;
  sop_severity: SOPSeverity;
  steps: SOPStep[]; // 前端传递的步骤数组
  tools_required?: string[];
  sop_recommendations?: string;
  team_name: string;
}

// SOP查询参数接口
export interface SOPQueryParams {
  search?: string;
  category?: string;
  severity?: SOPSeverity | "all";
  team_name?: string;
  limit?: number;
  offset?: number;
}

// SOP列表响应接口
export interface SOPListResponse {
  data: SOPTemplate[];
  total: number;
}

// 通用API响应接口
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// SOP执行相关接口
export interface SOPExecution {
  id: string;
  sop_id: string;
  sop_title: string;
  steps: SOPStep[];
  current_step: number;
  status: "pending" | "running" | "paused" | "completed" | "failed" | "cancelled";
  started_at?: string;
  completed_at?: string;
  execution_log: SOPStepResult[];
}

export interface SOPStepResult {
  step: number;
  status: "pending" | "running" | "success" | "failed" | "skipped";
  output?: string;
  error?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
}

// 工具辅助函数类型
export type SOPStepsParser = (stepsJson: string) => SOPStep[];
export type SOPStepsStringifier = (steps: SOPStep[]) => string;
export type ToolsParser = (toolsJson: string) => string[];
export type ToolsStringifier = (tools: string[]) => string;