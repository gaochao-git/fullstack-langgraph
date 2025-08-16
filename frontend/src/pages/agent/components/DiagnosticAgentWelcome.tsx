import { useState, useMemo, useEffect } from "react";
import { 
  AlertTriangle, 
  Clock, 
  Server, 
  MessageCircle,
  BarChart3,
  Loader2,
  AlertCircle,
  Building2,
  Users,
  RefreshCw
} from "lucide-react";
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';
import SOPApi from '@/services/sopApi';
import { Tag, App } from 'antd';

// 故障类型定义
type FaultSeverity = "warning" | "error" | "critical";
type FaultStatus = "active" | "analyzing" | "analyzed" | "resolved";

interface Fault {
  id: string;
  title: string;
  description: string;
  ip: string;
  time: string;
  severity?: FaultSeverity;
  status: FaultStatus;
  team?: string; // 动态团队
  room?: string; // 动态机房
  level?: string; // 动态等级
  sopId?: string;
  analysisResult?: string;
  threadId?: string;
  lastUpdated: string;
  tags: string[];
  // Zabbix相关字段
  eventid?: string;
  hostname?: string;
  item_key?: string;
  last_value?: string;
  units?: string;
  trigger_description?: string;
  // 标签信息
  idc_tag?: string;
  team_tag?: string;
  level_tag?: string;
}

// 从Zabbix数据中提取标签值
const extractTagValue = (tags: any[], tagPrefix: string): string | undefined => {
  if (!Array.isArray(tags)) return undefined;
  
  const tag = tags.find(t => 
    t.tag && t.tag.toLowerCase().startsWith(tagPrefix.toLowerCase())
  );
  
  if (tag && tag.value) {
    return tag.value;
  }
  
  // 如果没有value，尝试从tag本身提取（格式如：team_tag:数据库）
  if (tag && tag.tag.includes(':')) {
    return tag.tag.split(':')[1];
  }
  
  return undefined;
};

// 映射报警严重级别到我们的系统
const mapAlarmSeverity = (severity: string): FaultSeverity => {
  // 兼容多种监控系统的严重级别
  const levelStr = severity ? severity.toString().toLowerCase() : '';
  
  // P级别映射
  if (levelStr.includes('p0') || levelStr.includes('p1')) {
    return 'critical';
  }
  if (levelStr.includes('p2') || levelStr.includes('p3')) {
    return 'error';
  }
  if (levelStr.includes('p4') || levelStr.includes('p5')) {
    return 'warning';
  }
  
  // 文字级别映射
  switch (levelStr) {
    case '0': // 未分类
    case '1': // 信息
    case '2': // 警告
    case 'warning':
    case 'low':
    case '低':
    case '提示':
      return 'warning';
    case '3': // 一般
    case '4': // 严重
    case 'error':
    case 'medium':
    case 'high':
    case '中':
    case '高':
      return 'error';
    case '5': // 灾难
    case 'critical':
    case 'disaster':
    case '严重':
    case '紧急':
      return 'critical';
    default:
      return 'warning';
  }
};

// 动态团队和机房列表（从数据中提取）
interface DynamicFilters {
  teams: Set<string>;
  rooms: Set<string>;
  levels: Set<string>;
}

interface DiagnosticAgentWelcomeProps {
  onSwitchToChat: () => void;
}

export default function DiagnosticAgentWelcome({ onSwitchToChat }: DiagnosticAgentWelcomeProps) {
  const { isDark } = useTheme();
  const { message } = App.useApp();
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [timeFilter, setTimeFilter] = useState<string>("all");
  const [teamFilter, setTeamFilter] = useState<string>("all");
  const [roomFilter, setRoomFilter] = useState<string>("all");
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [expandedFault, setExpandedFault] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [faults, setFaults] = useState<Fault[]>([]);
  const [dynamicFilters, setDynamicFilters] = useState<DynamicFilters>({
    teams: new Set(),
    rooms: new Set(),
    levels: new Set()
  });

  // 获取报警数据
  const fetchAlarms = async () => {
    setLoading(true);
    try {
      console.log('开始获取报警数据...');
      const response = await SOPApi.getAlarms({
        page: 1,
        page_size: 500  // 获取更多数据用于前端过滤
      });
      
      console.log('报警API响应:', response);

      if (response.status === 'ok' && response.data) {
        let alarmData: any[] = [];
        
        // 处理分页格式或数组格式
        if (response.data.data && Array.isArray(response.data.data)) {
          // 新的分页格式
          alarmData = response.data.data;
          console.log('总告警数:', response.data.total);
          console.log('当前页:', response.data.page);
          console.log('每页数量:', response.data.page_size);
        } else if (Array.isArray(response.data)) {
          // 兼容旧的数组格式
          alarmData = response.data;
        }
        
        const newTeams = new Set<string>();
        const newRooms = new Set<string>();
        const newLevels = new Set<string>();
        
        console.log('获取到的数据条数:', alarmData.length);
        if (alarmData.length > 0) {
          console.log('第一条数据示例:', alarmData[0]);
        }
        
        // 转换报警数据为Fault格式
        const alarmFaults: Fault[] = alarmData.map((alert: any) => {
          const ip = alert.alarm_ip || '未知IP';
          const hostname = alert.hostname || '未知主机';
          
          // 新格式：直接从字段获取标签信息
          const team = alert.team_tag;
          const room = alert.idc_tag;
          const level = alert.alarm_level;
          
          // 收集动态过滤项（只添加有值的）
          if (team) newTeams.add(team);
          if (room) newRooms.add(room);
          if (level) newLevels.add(level);
          
          return {
            id: `alert-${alert.alarm_id}`,
            title: alert.alarm_name,
            description: alert.alarm_desc,
            ip: ip,
            time: alert.alarm_time || new Date().toLocaleString('zh-CN'),
            severity: mapAlarmSeverity(alert.alarm_level),
            status: 'active',
            team: team || undefined,
            room: room || undefined,
            level: level || undefined,
            lastUpdated: alert.alarm_time || new Date().toLocaleString('zh-CN'),
            tags: [team, room, alert.alarm_source, alert.alarm_key].filter(Boolean),
            // 保留原始监控数据
            eventid: alert.alarm_id,
            hostname: hostname,
            item_key: alert.alarm_key,
            last_value: alert.alarm_value,
            units: alert.alarm_unit,
            trigger_description: alert.alarm_desc,
            // 保存标签信息
            idc_tag: room || undefined,
            team_tag: team || undefined,
            level_tag: level || undefined
          };
        });

        setFaults(alarmFaults);
        setDynamicFilters({
          teams: newTeams,
          rooms: newRooms,
          levels: newLevels
        });
      } else if (response.status === 'error') {
        // 处理后端返回的错误
        console.error('报警服务错误:', response.msg);
        message.error(response.msg || '获取报警数据失败');
        
        // 如果是连接问题，提供更详细的信息
        if (response.msg && response.msg.includes('Cannot send a request')) {
          message.warning('请联系管理员检查报警服务连接');
        }
        
        // 设置空数据，但保留错误状态以显示提示
        setFaults([]);
        setDynamicFilters({
          teams: new Set(['连接失败']),
          rooms: new Set(['连接失败']),
          levels: new Set(['连接失败'])
        });
      } else {
        // 其他未知情况
        console.warn('未知的响应格式:', response);
        message.warning('获取数据格式异常');
        setFaults([]);
      }
    } catch (error) {
      console.error('获取报警数据失败:', error);
      message.error('网络请求失败，请检查网络连接');
      setFaults([]);
    } finally {
      setLoading(false);
    }
  };

  // 组件加载时获取数据
  useEffect(() => {
    fetchAlarms();
  }, []);

  // 统计数据
  const stats = useMemo(() => {
    // 动态统计各团队数据
    const teamStats: Record<string, number> = {};
    dynamicFilters.teams.forEach(team => {
      teamStats[team] = faults.filter(f => f.team === team).length;
    });
    
    // 动态统计各机房数据
    const roomStats: Record<string, number> = {};
    dynamicFilters.rooms.forEach(room => {
      roomStats[room] = faults.filter(f => f.room === room).length;
    });
    
    // 动态统计各等级数据
    const levelStats: Record<string, number> = {};
    dynamicFilters.levels.forEach(level => {
      levelStats[level] = faults.filter(f => f.level === level).length;
    });
    
    const severityStats = {
      warning: faults.filter(f => f.severity === "warning").length,
      error: faults.filter(f => f.severity === "error").length,
      critical: faults.filter(f => f.severity === "critical").length,
    };
    
    return {
      total: faults.length,
      teamStats,
      roomStats,
      levelStats,
      ...severityStats
    };
  }, [faults, dynamicFilters]);

  // 过滤故障列表
  const filteredFaults = useMemo(() => {
    return faults.filter(fault => {
      if (severityFilter !== "all" && fault.severity !== severityFilter) return false;
      if (statusFilter !== "all" && fault.status !== statusFilter) return false;
      if (teamFilter !== "all" && fault.team !== teamFilter) return false;
      if (roomFilter !== "all" && fault.room !== roomFilter) return false;
      if (levelFilter !== "all" && fault.level !== levelFilter) return false;
      if (timeFilter !== "all") {
        // 这里可以根据timeFilter实现时间过滤逻辑
      }
      return true;
    }).slice(0, 50);
  }, [faults, severityFilter, statusFilter, teamFilter, roomFilter, levelFilter, timeFilter]);

  return (
    <div className="space-y-6">
      {/* 统计和过滤区域 - 优化后的3行布局 */}
      <div className={cn(
        "rounded-2xl p-5 border backdrop-blur-sm shadow-xl transition-colors duration-200",
        isDark 
          ? "bg-gradient-to-br from-slate-800/75 via-purple-900/30 to-slate-700/75 border-purple-500/40 shadow-purple-500/20" 
          : "bg-gradient-to-br from-blue-100/75 via-purple-100/30 to-blue-100/75 border-purple-300/40 shadow-purple-500/20"
      )}>
        {/* 第一行：时间过滤 */}
        <div className="mb-4">
          <div className="flex items-start gap-4">
            <h3 className={cn(
              "text-sm font-semibold pt-2 flex items-center gap-2",
              isDark ? "text-slate-300" : "text-gray-700"
            )}>
              <Clock className="w-4 h-4" />
              时间范围
            </h3>
            <div className="flex-1 flex items-center justify-between">
              <div className="flex items-center gap-2">
                {['1小时', '24小时', '7天', '30天'].map((time) => (
                  <button
                    key={time}
                    onClick={() => setTimeFilter(timeFilter === time ? 'all' : time)}
                    className={cn(
                      "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200",
                      timeFilter === time
                        ? isDark
                          ? 'bg-blue-600 border-blue-500 text-white shadow-sm'
                          : 'bg-blue-500 border-blue-400 text-white shadow-sm'
                        : isDark
                          ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50 hover:border-slate-500'
                          : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                    )}
                  >
                    {time}
                  </button>
                ))}
              </div>
              
              <button
                onClick={fetchAlarms}
                disabled={loading}
                className={cn(
                  "px-4 py-1.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2",
                  isDark
                    ? 'bg-blue-900/50 hover:bg-blue-800/50 text-blue-300 border border-blue-700 disabled:opacity-50'
                    : 'bg-blue-100 hover:bg-blue-200 text-blue-700 border border-blue-300 disabled:opacity-50'
                )}
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                刷新
              </button>
            </div>
          </div>
        </div>

        {/* 第二行：等级过滤 */}
        <div className="mb-4">
          <div className="flex items-start gap-4">
            <h3 className={cn(
              "text-sm font-semibold pt-2 flex items-center gap-2",
              isDark ? "text-slate-300" : "text-gray-700"
            )}>
              <AlertTriangle className="w-4 h-4" />
              等级过滤
            </h3>
            <div className="flex-1 flex flex-wrap gap-2">
              <button
                onClick={() => setSeverityFilter(severityFilter === 'warning' ? 'all' : 'warning')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[100px]",
                  severityFilter === 'warning'
                    ? isDark
                      ? 'bg-yellow-600 border-yellow-500 text-white shadow-sm'
                      : 'bg-yellow-500 border-yellow-400 text-white shadow-sm'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-yellow-300 hover:bg-slate-600/50 hover:border-yellow-500'
                      : 'bg-white border-gray-300 text-yellow-700 hover:bg-yellow-50 hover:border-yellow-400'
                )}
              >
                Warning ({stats.warning})
              </button>
              <button
                onClick={() => setSeverityFilter(severityFilter === 'error' ? 'all' : 'error')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[100px]",
                  severityFilter === 'error'
                    ? isDark
                      ? 'bg-orange-600 border-orange-500 text-white shadow-sm'
                      : 'bg-orange-500 border-orange-400 text-white shadow-sm'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-orange-300 hover:bg-slate-600/50 hover:border-orange-500'
                      : 'bg-white border-gray-300 text-orange-700 hover:bg-orange-50 hover:border-orange-400'
                )}
              >
                Error ({stats.error})
              </button>
              <button
                onClick={() => setSeverityFilter(severityFilter === 'critical' ? 'all' : 'critical')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[100px]",
                  severityFilter === 'critical'
                    ? isDark
                      ? 'bg-red-600 border-red-500 text-white shadow-sm'
                      : 'bg-red-500 border-red-400 text-white shadow-sm'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-red-300 hover:bg-slate-600/50 hover:border-red-500'
                      : 'bg-white border-gray-300 text-red-700 hover:bg-red-50 hover:border-red-400'
                )}
              >
                Critical ({stats.critical})
              </button>
            </div>
          </div>
        </div>

        {/* 第三行：等级过滤 - 只在有数据时显示 */}
        {dynamicFilters.levels.size > 0 && (
          <div className="mb-4">
            <div className="flex items-start gap-4">
              <h3 className={cn(
                "text-sm font-semibold pt-2 flex items-center gap-2",
                isDark ? "text-slate-300" : "text-gray-700"
              )}>
                <AlertCircle className="w-4 h-4" />
                等级分类
              </h3>
              <div className="flex-1 flex flex-wrap gap-2">
                {Array.from(dynamicFilters.levels).sort().map((level) => {
                  const levelCount = stats.levelStats[level] || 0;
                  return (
                    <button
                      key={level}
                      onClick={() => setLevelFilter(levelFilter === level ? 'all' : level)}
                      className={cn(
                        "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200",
                        levelFilter === level
                          ? isDark
                            ? 'bg-purple-600 border-purple-500 text-white shadow-sm'
                            : 'bg-purple-500 border-purple-400 text-white shadow-sm'
                          : isDark
                            ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50 hover:border-slate-500'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                      )}
                    >
                      {level} ({levelCount})
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* 第四行：机房选择 - 只在有数据时显示 */}
        {dynamicFilters.rooms.size > 0 && (
          <div className="mb-4">
            <div className="flex items-start gap-4">
              <h3 className={cn(
                "text-sm font-semibold pt-2 flex items-center gap-2",
                isDark ? "text-slate-300" : "text-gray-700"
              )}>
                <Building2 className="w-4 h-4" />
                机房选择
              </h3>
              <div className="flex-1 flex flex-wrap gap-2">
                {Array.from(dynamicFilters.rooms).sort().map((room) => {
                  const roomCount = stats.roomStats[room] || 0;
                  return (
                    <button
                      key={room}
                      onClick={() => setRoomFilter(roomFilter === room ? 'all' : room)}
                      className={cn(
                        "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[80px]",
                        roomFilter === room
                          ? isDark
                            ? 'bg-indigo-600 border-indigo-500 text-white shadow-sm'
                            : 'bg-indigo-500 border-indigo-400 text-white shadow-sm'
                          : isDark
                            ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50 hover:border-slate-500'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400'
                      )}
                    >
                      {room} ({roomCount})
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* 第五行：团队报警统计 - 只在有数据时显示 */}
        {dynamicFilters.teams.size > 0 && (
          <div>
            <div className="flex items-start gap-4">
              <h3 className={cn(
                "text-sm font-semibold pt-2 flex items-center gap-2",
                isDark ? "text-slate-300" : "text-gray-700"
              )}>
                <Users className="w-4 h-4" />
                团队分类
              </h3>
              <div className="flex-1 flex flex-wrap gap-2">
                {Array.from(dynamicFilters.teams).sort().map((team, index) => {
                  const teamCount = stats.teamStats[team] || 0;
                  // 动态颜色映射
                  const colorClasses = [
                    { active: 'bg-blue-500 border-blue-400', inactive: isDark ? 'text-blue-300 hover:bg-blue-900/40 hover:border-blue-500' : 'bg-blue-100/50 border-blue-300 text-blue-700 hover:bg-blue-200/50 hover:border-blue-400' },
                    { active: 'bg-purple-500 border-purple-400', inactive: isDark ? 'text-purple-300 hover:bg-purple-900/40 hover:border-purple-500' : 'bg-purple-100/50 border-purple-300 text-purple-700 hover:bg-purple-200/50 hover:border-purple-400' },
                    { active: 'bg-cyan-500 border-cyan-400', inactive: isDark ? 'text-cyan-300 hover:bg-cyan-900/40 hover:border-cyan-500' : 'bg-cyan-100/50 border-cyan-300 text-cyan-700 hover:bg-cyan-200/50 hover:border-cyan-400' },
                    { active: 'bg-green-500 border-green-400', inactive: isDark ? 'text-green-300 hover:bg-green-900/40 hover:border-green-500' : 'bg-green-100/50 border-green-300 text-green-700 hover:bg-green-200/50 hover:border-green-400' },
                    { active: 'bg-yellow-500 border-yellow-400', inactive: isDark ? 'text-yellow-300 hover:bg-yellow-900/40 hover:border-yellow-500' : 'bg-yellow-100/50 border-yellow-300 text-yellow-700 hover:bg-yellow-200/50 hover:border-yellow-400' },
                    { active: 'bg-pink-500 border-pink-400', inactive: isDark ? 'text-pink-300 hover:bg-pink-900/40 hover:border-pink-500' : 'bg-pink-100/50 border-pink-300 text-pink-700 hover:bg-pink-200/50 hover:border-pink-400' },
                  ];
                  const colorClass = colorClasses[index % colorClasses.length];
                  
                  return (
                    <button
                      key={team}
                      onClick={() => setTeamFilter(teamFilter === team ? 'all' : team)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                        teamFilter === team
                          ? `${colorClass.active} text-white shadow-lg`
                          : isDark
                            ? `bg-slate-700/50 border-slate-600 ${colorClass.inactive}`
                            : colorClass.inactive
                      )}
                    >
                      {team} ({teamCount})
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 故障列表 */}
      <div className={cn(
        "rounded-2xl p-3 border backdrop-blur-sm shadow-xl transition-colors duration-200",
        isDark 
          ? "bg-gradient-to-br from-slate-800/75 via-purple-900/30 to-slate-700/75 border-purple-500/40 shadow-purple-500/20" 
          : "bg-gradient-to-br from-blue-100/75 via-purple-100/30 to-blue-100/75 border-purple-300/40 shadow-purple-500/20"
      )}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={cn(
            "text-xl font-semibold flex items-center gap-2",
            isDark ? "text-white" : "text-gray-900"
          )}>
            <BarChart3 className={cn(
              "w-6 h-6",
              isDark ? "text-blue-400" : "text-blue-600"
            )} />
            当前故障 ({filteredFaults.length})
          </h3>
          {filteredFaults.length >= 50 && (
            <span className={cn(
              "text-sm px-3 py-1 rounded-full",
              isDark 
                ? "text-slate-400 bg-slate-700/50" 
                : "text-gray-600 bg-gray-200/50"
            )}>显示前50条</span>
          )}
        </div>
        
        {faults.length === 0 && dynamicFilters.teams.has('连接失败') ? (
          <div className={cn(
            "p-8 text-center border rounded-2xl",
            isDark 
              ? "bg-slate-700/30 border-slate-600/50" 
              : "bg-gray-100/30 border-gray-300/50"
          )}>
            <AlertCircle className={cn(
              "w-16 h-16 mx-auto mb-4",
              isDark ? "text-orange-400" : "text-orange-500"
            )} />
            <h3 className={cn(
              "text-xl font-medium mb-2",
              isDark ? "text-slate-200" : "text-gray-700"
            )}>报警服务连接失败</h3>
            <p className={cn(
              "mb-4",
              isDark ? "text-slate-400" : "text-gray-600"
            )}>无法连接到报警服务，请联系管理员检查服务状态</p>
            <button
              onClick={fetchAlarms}
              disabled={loading}
              className={cn(
                "px-4 py-2 rounded-lg font-medium transition-all duration-200 inline-flex items-center gap-2",
                isDark
                  ? 'bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50'
                  : 'bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50'
              )}
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              重试连接
            </button>
          </div>
        ) : filteredFaults.length === 0 ? (
          <div className={cn(
            "p-8 text-center border rounded-2xl",
            isDark 
              ? "bg-slate-700/30 border-slate-600/50" 
              : "bg-gray-100/30 border-gray-300/50"
          )}>
            <AlertTriangle className={cn(
              "w-16 h-16 mx-auto mb-4",
              isDark ? "text-slate-400" : "text-gray-500"
            )} />
            <h3 className={cn(
              "text-xl font-medium mb-2",
              isDark ? "text-slate-200" : "text-gray-700"
            )}>暂无故障</h3>
            <p className={cn(
              isDark ? "text-slate-400" : "text-gray-600"
            )}>没有找到符合条件的故障</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredFaults.map((fault) => (
              <div
                key={fault.id}
                className={cn(
                  "border rounded-lg p-3 cursor-pointer transition-all duration-200",
                  expandedFault === fault.id
                    ? isDark
                      ? "border-blue-500 bg-slate-700/50"
                      : "border-blue-400 bg-blue-50/50"
                    : isDark
                      ? "border-slate-600 bg-slate-800/50 hover:bg-slate-700/50"
                      : "border-gray-300 bg-white/50 hover:bg-gray-50/50"
                )}
                onClick={() => setExpandedFault(expandedFault === fault.id ? null : fault.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full",
                        fault.status === "active"
                          ? isDark
                            ? "bg-red-900/50 text-red-300"
                            : "bg-red-100 text-red-700"
                          : fault.status === "analyzing"
                          ? isDark
                            ? "bg-blue-900/50 text-blue-300"
                            : "bg-blue-100 text-blue-700"
                          : fault.status === "analyzed"
                          ? isDark
                            ? "bg-green-900/50 text-green-300"
                            : "bg-green-100 text-green-700"
                          : isDark
                            ? "bg-gray-700 text-gray-400"
                            : "bg-gray-200 text-gray-600"
                      )}>
                        {fault.status === "active" ? "活跃" :
                         fault.status === "analyzing" ? "分析中" :
                         fault.status === "analyzed" ? "已分析" : "已解决"}
                      </span>
                      {fault.team && (
                        <span className={cn(
                          "text-xs px-2 py-0.5 rounded-full",
                          isDark
                            ? "bg-slate-700 text-slate-300"
                            : "bg-gray-200 text-gray-700"
                        )}>
                          {fault.team}
                        </span>
                      )}
                      {fault.room && (
                        <span className={cn(
                          "text-xs px-2 py-0.5 rounded-full",
                          isDark
                            ? "bg-purple-900/50 text-purple-300"
                            : "bg-purple-100 text-purple-700"
                        )}>
                          {fault.room}
                        </span>
                      )}
                      {fault.level && (
                        <span className={cn(
                          "text-xs px-2 py-0.5 rounded-full font-medium",
                          isDark
                            ? "bg-indigo-900/50 text-indigo-300"
                            : "bg-indigo-100 text-indigo-700"
                        )}>
                          {fault.level}
                        </span>
                      )}
                    </div>
                    <h4 className={cn(
                      "mt-2 font-medium",
                      isDark ? "text-white" : "text-gray-900"
                    )}>
                      {fault.title}
                    </h4>
                    <p className={cn(
                      "text-sm mt-1",
                      isDark ? "text-slate-400" : "text-gray-600"
                    )}>
                      {fault.description}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs">
                      <span className={cn(
                        "flex items-center gap-1",
                        isDark ? "text-slate-400" : "text-gray-500"
                      )}>
                        <Server className="w-3 h-3" />
                        {fault.ip}
                      </span>
                      {fault.hostname && (
                        <span className={cn(
                          "text-xs",
                          isDark ? "text-slate-500" : "text-gray-400"
                        )}>
                          ({fault.hostname})
                        </span>
                      )}
                      <span className={cn(
                        "flex items-center gap-1",
                        isDark ? "text-slate-400" : "text-gray-500"
                      )}>
                        <Clock className="w-3 h-3" />
                        {fault.time}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSwitchToChat();
                      }}
                      className={cn(
                        "flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200",
                        isDark
                          ? "bg-blue-600 hover:bg-blue-700 text-white"
                          : "bg-blue-500 hover:bg-blue-600 text-white"
                      )}
                    >
                      <MessageCircle className="w-3 h-3" />
                      开始分析
                    </button>
                  </div>
                </div>
                
                {expandedFault === fault.id && (
                  <div className={cn(
                    "mt-3 pt-3 border-t space-y-2",
                    isDark ? "border-slate-600" : "border-gray-200"
                  )}>
                    {fault.item_key && (
                      <>
                        <div>
                          <span className={cn(
                            "text-xs font-medium",
                            isDark ? "text-slate-300" : "text-gray-700"
                          )}>监控项：</span>
                          <span className={cn(
                            "text-xs ml-2 font-mono",
                            isDark ? "text-slate-400" : "text-gray-600"
                          )}>
                            {fault.item_key}
                          </span>
                        </div>
                        <div>
                          <span className={cn(
                            "text-xs font-medium",
                            isDark ? "text-slate-300" : "text-gray-700"
                          )}>当前值：</span>
                          <span className={cn(
                            "text-xs ml-2 font-mono",
                            isDark ? "text-slate-400" : "text-gray-600"
                          )}>
                            {fault.last_value} {fault.units || ''}
                          </span>
                        </div>
                        <div>
                          <span className={cn(
                            "text-xs font-medium",
                            isDark ? "text-slate-300" : "text-gray-700"
                          )}>数据来源：</span>
                          <Tag color="blue" className="text-xs ml-2">实时报警</Tag>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 加载遮罩 */}
      {loading && (
        <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
          <div className={cn(
            "p-4 rounded-lg shadow-lg",
            isDark ? "bg-slate-800" : "bg-white"
          )}>
            <div className="flex items-center gap-3">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              <span className={isDark ? "text-white" : "text-gray-900"}>
                正在加载报警数据...
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}