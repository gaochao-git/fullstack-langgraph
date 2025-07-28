import {
  SOPTemplate,
  SOPTemplateRequest,
  SOPQueryParams,
  SOPListResponse,
  ApiResponse,
  SOPStep,
  SOPSeverity
} from '../types/sop';
import { baseFetch } from '../utils/baseFetch';

// Mock数据 - 将来替换为真实API调用
const mockSOPTemplates: SOPTemplate[] = [
  {
    id: 1,
    sop_id: "SOP-DB-001",
    sop_title: "MySQL数据库响应耗时升高诊断",
    sop_category: "database",
    sop_description: "诊断MySQL数据库响应时间过长的标准操作程序",
    sop_severity: "high",
    sop_steps: JSON.stringify([
      {
        step: 1,
        description: "获取慢查询日志配置和阈值设置",
        ai_generated: false,
        tool: "execute_mysql_query",
        args: "SHOW VARIABLES WHERE Variable_name IN ('long_query_time', 'slow_query_log');",
        requires_approval: false
      },
      {
        step: 2,
        description: "确定分析范围",
        ai_generated: true,
        tool: "llm",
        args: "根据用户描述的响应耗时和慢查询阈值，确定分析范围，如果用户告诉了范围用用户的，否则用报警时间前后5分钟",
        requires_approval: false
      },
      {
        step: 3,
        description: "大模型判断是否需要分析慢查询日志",
        ai_generated: true,
        tool: "llm",
        args: "如果响应耗时小于慢查询阈值则跳过慢日志分析直接执行第5步，如果大于阈值则继续第4步",
        requires_approval: false
      },
      {
        step: 4,
        description: "从ES中查询指定时间范围的慢查询日志，分析是写慢查询还是读慢查询，查看扫描行数和锁等待情况",
        ai_generated: true,
        tool: "get_es_data",
        args: "index: mysql-slow-*, start_time: 动态生成, end_time: 动态生成, query: 动态生成",
        requires_approval: false
      },
      {
        step: 5,
        description: "获取指定时间范围内的磁盘IO使用率和CPU使用率，检查是否存在瓶颈或异常波动",
        ai_generated: true,
        tool: "get_zabbix_metric_data",
        args: "metric: [system.cpu.util[,user], disk.io.util[vda]], start_time: 动态生成, end_time: 动态生成",
        requires_approval: false
      },
      {
        step: 6,
        description: "如果CPU或者磁盘IO有瓶颈且当前仍然存在瓶颈，则排查CPU和IO占用前5名进程",
        ai_generated: false,
        tool: "execute_system_command",
        args: "top -b -n1 | head -12; iotop -b -n1 | head -10",
        requires_approval: false
      }
    ]),
    tools_required: JSON.stringify([
      "execute_mysql_query",
      "get_es_data", 
      "get_es_indices",
      "get_es_trends_data",
      "get_zabbix_metric_data",
      "get_zabbix_metrics",
      "execute_system_command"
    ]),
    sop_recommendations: "建议优化识别到的慢查询SQL，为高频查询字段添加索引，重构复杂查询，联系DBA进行查询优化",
    team_name: "ops-team",
    create_by: "admin",
    update_by: "admin",
    create_time: "2025-01-12 10:00:00",
    update_time: "2025-01-12 10:00:00"
  },
  {
    id: 2,
    sop_id: "SOP-SYS-101",
    sop_title: "磁盘空间不足处理",
    sop_category: "system",
    sop_description: "处理磁盘空间不足的标准操作程序",
    sop_severity: "medium",
    sop_steps: JSON.stringify([
      {
        step: 1,
        description: "检查磁盘使用情况",
        ai_generated: false,
        tool: "execute_system_command",
        args: "df -h",
        requires_approval: false
      },
      {
        step: 2,
        description: "查找大文件",
        ai_generated: false,
        tool: "execute_system_command", 
        args: "find /var/log -type f -size +100M -exec ls -lh {} \\;",
        requires_approval: false
      },
      {
        step: 3,
        description: "清理日志文件",
        ai_generated: false,
        tool: "execute_system_command",
        args: "find /var/log -name '*.log' -mtime +7 -delete",
        requires_approval: true
      }
    ]),
    tools_required: JSON.stringify(["execute_system_command"]),
    sop_recommendations: "定期清理日志文件，配置日志轮转，监控磁盘使用率",
    team_name: "ops-team",
    create_by: "admin",
    update_by: "admin",
    create_time: "2025-01-12 09:00:00",
    update_time: "2025-01-12 09:00:00"
  }
];

// 工具函数
export class SOPUtils {
  // 解析步骤JSON字符串
  static parseSteps(stepsJson: string): SOPStep[] {
    try {
      return JSON.parse(stepsJson);
    } catch (error) {
      console.error('Failed to parse SOP steps:', error);
      return [];
    }
  }

  // 将步骤数组转换为JSON字符串
  static stringifySteps(steps: SOPStep[]): string {
    return JSON.stringify(steps, null, 2);
  }

  // 解析工具JSON字符串
  static parseTools(toolsJson: string): string[] {
    try {
      return JSON.parse(toolsJson);
    } catch (error) {
      console.error('Failed to parse tools:', error);
      return [];
    }
  }

  // 将工具数组转换为JSON字符串
  static stringifyTools(tools: string[]): string {
    return JSON.stringify(tools);
  }
}

// 模拟网络延迟
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// 过滤SOP数据
const filterSOPs = (sops: SOPTemplate[], params: SOPQueryParams): SOPTemplate[] => {
  let filtered = [...sops];

  // 搜索过滤
  if (params.search) {
    filtered = filtered.filter(sop => 
      sop.sop_title.toLowerCase().includes(params.search!.toLowerCase()) ||
      sop.sop_description?.toLowerCase().includes(params.search!.toLowerCase()) ||
      sop.sop_id.toLowerCase().includes(params.search!.toLowerCase())
    );
  }

  // 分类过滤
  if (params.category) {
    filtered = filtered.filter(sop => sop.sop_category === params.category);
  }

  // 严重性过滤
  if (params.severity && params.severity !== "all") {
    filtered = filtered.filter(sop => sop.sop_severity === params.severity);
  }

  // 团队过滤
  if (params.team_name) {
    filtered = filtered.filter(sop => sop.team_name === params.team_name);
  }

  // 排序：按更新时间倒序
  filtered.sort((a, b) => new Date(b.update_time).getTime() - new Date(a.update_time).getTime());

  // 分页
  if (params.limit) {
    const offset = params.offset || 0;
    filtered = filtered.slice(offset, offset + params.limit);
  }

  return filtered;
};

// SOP API接口类
export class SOPApi {
  // 获取SOP列表
  static async getSOPs(params: SOPQueryParams = {}): Promise<ApiResponse<SOPListResponse>> {
    try {
      // 模拟网络延迟
      await delay(300);

      // TODO: 替换为真实API调用
      // const response = await fetch(`${API_BASE_URL}/api/sops`, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(params),
      // });
      // const data = await response.json();

      // 使用Mock数据
      const filteredSOPs = filterSOPs(mockSOPTemplates, params);
      const allSOPs = filterSOPs(mockSOPTemplates, { ...params, limit: undefined, offset: undefined });

      return {
        success: true,
        data: {
          data: filteredSOPs,
          total: allSOPs.length
        }
      };
    } catch (error) {
      console.error('Failed to fetch SOPs:', error);
      return {
        success: false,
        error: '获取SOP数据失败'
      };
    }
  }

  // 根据ID获取单个SOP
  static async getSOPById(sopId: string): Promise<ApiResponse<SOPTemplate>> {
    try {
      await delay(200);
      
      // TODO: 替换为真实API调用
      // const response = await fetch(`${API_BASE_URL}/api/sops/${sopId}`);
      // const data = await response.json();

      const sop = mockSOPTemplates.find(s => s.sop_id === sopId);
      if (!sop) {
        return {
          success: false,
          error: 'SOP不存在'
        };
      }

      return {
        success: true,
        data: sop
      };
    } catch (error) {
      console.error('Failed to fetch SOP:', error);
      return {
        success: false,
        error: '获取SOP详情失败'
      };
    }
  }

  // 创建SOP
  static async createSOP(sopData: SOPTemplateRequest): Promise<ApiResponse<SOPTemplate>> {
    try {
      await delay(500);
      
      // TODO: 替换为真实API调用
      // const response = await fetch(`${API_BASE_URL}/api/sops`, {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify(sopData),
      // });
      // const data = await response.json();

      // Mock创建
      const newSOP: SOPTemplate = {
        id: mockSOPTemplates.length + 1,
        sop_id: sopData.sop_id,
        sop_title: sopData.sop_title,
        sop_category: sopData.sop_category,
        sop_description: sopData.sop_description,
        sop_severity: sopData.sop_severity,
        sop_steps: SOPUtils.stringifySteps(sopData.steps),
        tools_required: sopData.tools_required ? SOPUtils.stringifyTools(sopData.tools_required) : undefined,
        sop_recommendations: sopData.sop_recommendations,
        team_name: sopData.team_name,
        create_by: 'current_user', // 实际应该从当前登录用户获取
        update_by: 'current_user',
        create_time: new Date().toISOString().slice(0, 19).replace('T', ' '),
        update_time: new Date().toISOString().slice(0, 19).replace('T', ' ')
      };

      mockSOPTemplates.push(newSOP);

      return {
        success: true,
        data: newSOP
      };
    } catch (error) {
      console.error('Failed to create SOP:', error);
      return {
        success: false,
        error: '创建SOP失败'
      };
    }
  }

  // 更新SOP
  static async updateSOP(sopId: string, sopData: Partial<SOPTemplateRequest>): Promise<ApiResponse<SOPTemplate>> {
    try {
      await delay(500);
      
      // TODO: 替换为真实API调用
      
      // Mock更新
      const sopIndex = mockSOPTemplates.findIndex(s => s.sop_id === sopId);
      if (sopIndex === -1) {
        return {
          success: false,
          error: 'SOP不存在'
        };
      }

      const updatedSOP: SOPTemplate = {
        ...mockSOPTemplates[sopIndex],
        ...(sopData.sop_title && { sop_title: sopData.sop_title }),
        ...(sopData.sop_category && { sop_category: sopData.sop_category }),
        ...(sopData.sop_description !== undefined && { sop_description: sopData.sop_description }),
        ...(sopData.sop_severity && { sop_severity: sopData.sop_severity }),
        ...(sopData.steps && { sop_steps: SOPUtils.stringifySteps(sopData.steps) }),
        ...(sopData.tools_required && { tools_required: SOPUtils.stringifyTools(sopData.tools_required) }),
        ...(sopData.sop_recommendations !== undefined && { sop_recommendations: sopData.sop_recommendations }),
        ...(sopData.team_name && { team_name: sopData.team_name }),
        update_by: 'current_user',
        update_time: new Date().toISOString().slice(0, 19).replace('T', ' ')
      };

      mockSOPTemplates[sopIndex] = updatedSOP;

      return {
        success: true,
        data: updatedSOP
      };
    } catch (error) {
      console.error('Failed to update SOP:', error);
      return {
        success: false,
        error: '更新SOP失败'
      };
    }
  }

  // 删除SOP
  static async deleteSOP(sopId: string): Promise<ApiResponse<boolean>> {
    try {
      await delay(300);
      
      // TODO: 替换为真实API调用
      
      // Mock删除
      const sopIndex = mockSOPTemplates.findIndex(s => s.sop_id === sopId);
      if (sopIndex === -1) {
        return {
          success: false,
          error: 'SOP不存在'
        };
      }

      mockSOPTemplates.splice(sopIndex, 1);

      return {
        success: true,
        data: true
      };
    } catch (error) {
      console.error('Failed to delete SOP:', error);
      return {
        success: false,
        error: '删除SOP失败'
      };
    }
  }

  // 获取分类列表
  static async getCategories(): Promise<ApiResponse<string[]>> {
    try {
      await delay(100);
      
      const categories = Array.from(new Set(mockSOPTemplates.map(sop => sop.sop_category)));
      
      return {
        success: true,
        data: categories
      };
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      return {
        success: false,
        error: '获取分类列表失败'
      };
    }
  }

  // 获取团队列表
  static async getTeams(): Promise<ApiResponse<string[]>> {
    try {
      await delay(100);
      
      const teams = Array.from(new Set(mockSOPTemplates.map(sop => sop.team_name)));
      
      return {
        success: true,
        data: teams
      };
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      return {
        success: false,
        error: '获取团队列表失败'
      };
    }
  }
}

export default SOPApi;