// SOP问题规则相关类型定义

// 规则信息JSON结构
export interface RuleInfo {
  source_type: string;  // 数据源类型，目前只有 'zabbix'
  item_keys: string[];  // Zabbix item keys数组，如 ['mysql.status[Threads_connected]', 'mysql.status[Threads_running]']
}

// SOP问题规则接口 - 匹配 sop_problem_rule 表结构
export interface SOPProblemRule {
  id: number;
  rule_name: string;
  sop_id: string;
  rules_info: string | RuleInfo;  // 可能是JSON字符串或对象
  is_enabled: boolean;
  created_by: string;
  updated_by?: string;
  create_time: string;
  update_time: string;
  // 前端扩展字段
  sop_name?: string;  // 关联的SOP名称，用于显示
}

// 创建/更新规则请求
export interface SOPProblemRuleRequest {
  rule_name: string;
  sop_id: string;
  rules_info: RuleInfo;
  is_enabled?: boolean;
}

// 查询参数
export interface SOPProblemRuleQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  sop_id?: string;
  is_enabled?: boolean;
}

// Zabbix Item 信息
export interface ZabbixItem {
  itemid: string;
  name: string;
  key_: string;  // Zabbix API返回的字段名是 key_
  hostid: string;
  hostname?: string;
  status: string;
  value_type: number;
  units?: string;
  description?: string;
}

// Zabbix Host 信息
export interface ZabbixHost {
  hostid: string;
  host: string;
  name: string;
  status: string;
  groups?: Array<{
    groupid: string;
    name: string;
  }>;
}