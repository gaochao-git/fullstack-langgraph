// SOP严重性级别
export type SOPSeverity = "low" | "medium" | "high" | "critical";

// SOP步骤接口 - 支持树形结构
export interface SOPStep {
  id?: string; // 节点唯一标识
  step: number;
  description: string;
  ai_generated: boolean;
  tool: string;
  args: string;
  requires_approval: boolean;
  timeout?: number;
  retry_count?: number;
  on_failure?: "continue" | "stop" | "branch";
  status?: string; // 节点状态
  children?: SOPStep[]; // 子步骤
}

// SOP模板接口 - 匹配 sop_prompt_templates 表结构
export interface SOPTemplate {
  id: number;
  sop_id: string;
  sop_title: string;
  sop_category: string;
  sop_description?: string;
  sop_severity: SOPSeverity;
  sop_steps: SOPStep[] | string; // 可能是对象数组或JSON字符串
  tools_required?: string[] | string; // 可能是字符串数组或JSON字符串
  sop_recommendations: string;
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
  sop_severity?: SOPSeverity; // 后端默认 "high"
  steps: SOPStep[]; // 前端传递的步骤数组
  tools_required?: string[];
  sop_recommendations?: string; // 后端默认 ""
  team_name?: string; // 后端自动从用户信息获取
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

// SOP查询参数接口（更新为GET请求参数）
export interface SOPListParams {
  page?: number;
  size?: number;
  search?: string;
  category?: string;
  severity?: SOPSeverity | "all";
  team_name?: string;
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