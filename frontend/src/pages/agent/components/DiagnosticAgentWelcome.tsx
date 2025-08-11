import { useState, useMemo } from "react";
import { 
  AlertTriangle, 
  Clock, 
  Server, 
  Play, 
  MessageCircle,
  Search,
  BarChart3,
  Activity,
  CheckCircle,
  Loader2,
  AlertCircle,
  Building2,
  Users
} from "lucide-react";
import ReactEcharts from 'echarts-for-react';
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';
import ZabbixProblemsModal from './ZabbixProblemsModal';

// 故障类型定义
type FaultPriority = "P1" | "P2" | "P3";
type FaultSeverity = "warning" | "error" | "critical";
type FaultStatus = "active" | "analyzing" | "analyzed" | "resolved";
type FaultTeam = "系统" | "网络" | "组件" | "数据库" | "云管" | "机房";

interface Fault {
  id: string;
  title: string;
  description: string;
  ip: string;
  time: string;
  priority: FaultPriority;
  severity: FaultSeverity;
  status: FaultStatus;
  team: FaultTeam;
  room?: string;
  components?: string[];
  affectedServices?: string;
  possibleCauses?: string[];
  suggestedSolutions?: string[];
  relatedFaults?: string[];
  analysisProgress?: number;
}

// 模拟数据
const mockFaults: Fault[] = [
  {
    id: "1",
    title: "数据库连接超时",
    description: "MySQL主库连接池耗尽，导致应用无法获取连接",
    ip: "192.168.1.10",
    time: "2024-01-15 14:30:00",
    priority: "P1",
    severity: "critical",
    status: "active",
    team: "数据库",
    room: "10",
    components: ["MySQL", "连接池", "应用服务"],
    affectedServices: "订单服务、用户服务",
    possibleCauses: ["连接数配置过低", "慢查询导致连接占用", "应用未正确释放连接"],
    suggestedSolutions: ["增加最大连接数", "优化慢查询", "检查应用连接池配置"]
  },
  {
    id: "2",
    title: "API网关响应缓慢",
    description: "网关平均响应时间超过3秒，影响用户体验",
    ip: "192.168.1.20",
    time: "2024-01-15 14:25:00",
    priority: "P2",
    severity: "error",
    status: "analyzing",
    team: "系统",
    room: "20",
    analysisProgress: 65,
    components: ["API网关", "负载均衡", "后端服务"],
    affectedServices: "所有API服务",
    possibleCauses: ["流量突增", "后端服务响应慢", "网关配置不当"],
    suggestedSolutions: ["扩容网关实例", "优化后端服务", "调整网关缓存策略"],
    relatedFaults: ["3"]
  },
  {
    id: "3",
    title: "缓存服务内存使用率高",
    description: "Redis内存使用率达到85%，有OOM风险",
    ip: "192.168.1.30",
    time: "2024-01-15 14:20:00",
    priority: "P2",
    severity: "warning",
    status: "analyzed",
    team: "系统",
    room: "10",
    components: ["Redis", "缓存服务"],
    affectedServices: "缓存依赖服务",
    possibleCauses: ["缓存数据未设置过期时间", "大key占用过多内存", "缓存雪崩"],
    suggestedSolutions: ["清理过期数据", "优化大key", "增加Redis节点"],
    relatedFaults: ["2"]
  },
  {
    id: "4",
    title: "磁盘空间不足告警",
    description: "/data分区使用率达到90%",
    ip: "192.168.1.40",
    time: "2024-01-15 14:15:00",
    priority: "P3",
    severity: "warning",
    status: "resolved",
    team: "系统",
    room: "30",
    components: ["存储", "日志系统"],
    affectedServices: "日志收集服务",
    possibleCauses: ["日志文件过大", "未配置日志轮转", "临时文件未清理"],
    suggestedSolutions: ["配置日志轮转", "清理临时文件", "扩容磁盘"]
  },
  {
    id: "5",
    title: "应用服务CPU使用率高",
    description: "用户服务CPU使用率持续在80%以上",
    ip: "192.168.1.50",
    time: "2024-01-15 14:10:00",
    priority: "P2",
    severity: "error",
    status: "active",
    team: "系统",
    room: "20",
    components: ["应用服务", "JVM"],
    affectedServices: "用户服务",
    possibleCauses: ["代码死循环", "GC频繁", "请求量突增"],
    suggestedSolutions: ["分析线程堆栈", "优化JVM参数", "服务扩容"]
  }
];

interface DiagnosticAgentWelcomeProps {
  onSwitchToChat: () => void;
}

export default function DiagnosticAgentWelcome({ onSwitchToChat }: DiagnosticAgentWelcomeProps) {
  const { isDark } = useTheme();
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [timeFilter, setTimeFilter] = useState<string>("all");
  const [teamFilter, setTeamFilter] = useState<string>("all");
  const [roomFilter, setRoomFilter] = useState<string>("all");
  const [expandedFault, setExpandedFault] = useState<string | null>(null);
  const [showZabbixModal, setShowZabbixModal] = useState(false);

  const rooms = ['10', '11', '12', '20', '21', '30', '31', '32'];

  // 统计数据
  const stats = useMemo(() => {
    const teamStats = {
      system: mockFaults.filter(f => f.team === "系统").length,
      network: mockFaults.filter(f => f.team === "网络").length,
      component: mockFaults.filter(f => f.team === "组件").length,
      database: mockFaults.filter(f => f.team === "数据库").length,
      cloud: mockFaults.filter(f => f.team === "云管").length,
      room: mockFaults.filter(f => f.team === "机房").length,
    };
    
    const severityStats = {
      warning: mockFaults.filter(f => f.severity === "warning").length,
      error: mockFaults.filter(f => f.severity === "error").length,
      critical: mockFaults.filter(f => f.severity === "critical").length,
    };
    
    return {
      total: mockFaults.length,
      ...teamStats,
      ...severityStats
    };
  }, []);

  // 过滤故障列表
  const filteredFaults = useMemo(() => {
    return mockFaults.filter(fault => {
      if (priorityFilter !== "all" && fault.severity !== priorityFilter) return false;
      if (statusFilter !== "all" && fault.status !== statusFilter) return false;
      if (teamFilter !== "all" && fault.team !== teamFilter) return false;
      if (roomFilter !== "all" && fault.room !== roomFilter) return false;
      if (timeFilter !== "all") {
        // 这里可以根据timeFilter实现时间过滤逻辑
      }
      return true;
    }).slice(0, 50);
  }, [priorityFilter, statusFilter, teamFilter, roomFilter, timeFilter]);

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
                onClick={() => setShowZabbixModal(true)}
                className={cn(
                  "px-4 py-1.5 rounded-lg font-medium transition-all duration-200 flex items-center gap-2",
                  isDark
                    ? 'bg-red-900/50 hover:bg-red-800/50 text-red-300 border border-red-700'
                    : 'bg-red-100 hover:bg-red-200 text-red-700 border border-red-300'
                )}
              >
                <AlertCircle className="w-4 h-4" />
                Zabbix异常
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
                onClick={() => setPriorityFilter(priorityFilter === 'warning' ? 'all' : 'warning')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[100px]",
                  priorityFilter === 'warning'
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
                onClick={() => setPriorityFilter(priorityFilter === 'error' ? 'all' : 'error')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[100px]",
                  priorityFilter === 'error'
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
                onClick={() => setPriorityFilter(priorityFilter === 'critical' ? 'all' : 'critical')}
                className={cn(
                  "px-4 py-1.5 rounded-lg text-sm font-medium border transition-all duration-200 min-w-[100px]",
                  priorityFilter === 'critical'
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

        {/* 第三行：机房选择 */}
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
              {rooms.map((room) => {
                const roomCount = mockFaults.filter(f => f.room === room).length;
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

        {/* 第四行：团队报警统计 */}
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
              <button
                onClick={() => setTeamFilter(teamFilter === '系统' ? 'all' : '系统')}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                  teamFilter === '系统'
                    ? 'bg-blue-500 border-blue-400 text-white shadow-lg'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-blue-300 hover:bg-blue-900/40 hover:border-blue-500'
                      : 'bg-blue-100/50 border-blue-300 text-blue-700 hover:bg-blue-200/50 hover:border-blue-400'
                )}
              >
                系统 ({stats.system || 3})
              </button>
              <button
                onClick={() => setTeamFilter(teamFilter === '网络' ? 'all' : '网络')}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                  teamFilter === '网络'
                    ? 'bg-purple-500 border-purple-400 text-white shadow-lg'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-purple-300 hover:bg-purple-900/40 hover:border-purple-500'
                      : 'bg-purple-100/50 border-purple-300 text-purple-700 hover:bg-purple-200/50 hover:border-purple-400'
                )}
              >
                网络 ({stats.network || 0})
              </button>
              <button
                onClick={() => setTeamFilter(teamFilter === '组件' ? 'all' : '组件')}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                  teamFilter === '组件'
                    ? 'bg-cyan-500 border-cyan-400 text-white shadow-lg'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-cyan-300 hover:bg-cyan-900/40 hover:border-cyan-500'
                      : 'bg-cyan-100/50 border-cyan-300 text-cyan-700 hover:bg-cyan-200/50 hover:border-cyan-400'
                )}
              >
                组件 ({stats.component || 0})
              </button>
              <button
                onClick={() => setTeamFilter(teamFilter === '数据库' ? 'all' : '数据库')}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                  teamFilter === '数据库'
                    ? 'bg-green-500 border-green-400 text-white shadow-lg'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-green-300 hover:bg-green-900/40 hover:border-green-500'
                      : 'bg-green-100/50 border-green-300 text-green-700 hover:bg-green-200/50 hover:border-green-400'
                )}
              >
                数据库 ({stats.database || 5})
              </button>
              <button
                onClick={() => setTeamFilter(teamFilter === '云管' ? 'all' : '云管')}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                  teamFilter === '云管'
                    ? 'bg-yellow-500 border-yellow-400 text-gray-900 shadow-lg'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-yellow-300 hover:bg-yellow-900/40 hover:border-yellow-500'
                      : 'bg-yellow-100/50 border-yellow-300 text-yellow-700 hover:bg-yellow-200/50 hover:border-yellow-400'
                )}
              >
                云管 ({stats.cloud || 0})
              </button>
              <button
                onClick={() => setTeamFilter(teamFilter === '机房' ? 'all' : '机房')}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200",
                  teamFilter === '机房'
                    ? 'bg-pink-500 border-pink-400 text-white shadow-lg'
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-pink-300 hover:bg-pink-900/40 hover:border-pink-500'
                      : 'bg-pink-100/50 border-pink-300 text-pink-700 hover:bg-pink-200/50 hover:border-pink-400'
                )}
              >
                机房 ({stats.room || 0})
              </button>
            </div>
          </div>
        </div>
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
        
        {filteredFaults.length === 0 ? (
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
                        "text-xs px-2 py-0.5 rounded-full font-semibold",
                        fault.priority === "P1"
                          ? "bg-red-500 text-white"
                          : fault.priority === "P2"
                          ? "bg-orange-500 text-white"
                          : "bg-yellow-500 text-gray-900"
                      )}>
                        {fault.priority}
                      </span>
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
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full",
                        isDark
                          ? "bg-slate-700 text-slate-300"
                          : "bg-gray-200 text-gray-700"
                      )}>
                        {fault.team}
                      </span>
                      {fault.room && (
                        <span className={cn(
                          "text-xs px-2 py-0.5 rounded-full",
                          isDark
                            ? "bg-purple-900/50 text-purple-300"
                            : "bg-purple-100 text-purple-700"
                        )}>
                          机房{fault.room}
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
                    {fault.status === "analyzing" && fault.analysisProgress && (
                      <div className="flex items-center gap-2">
                        <Loader2 className={cn(
                          "w-4 h-4 animate-spin",
                          isDark ? "text-blue-400" : "text-blue-600"
                        )} />
                        <span className={cn(
                          "text-xs",
                          isDark ? "text-blue-400" : "text-blue-600"
                        )}>
                          {fault.analysisProgress}%
                        </span>
                      </div>
                    )}
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
                    {fault.components && (
                      <div>
                        <span className={cn(
                          "text-xs font-medium",
                          isDark ? "text-slate-300" : "text-gray-700"
                        )}>涉及组件：</span>
                        <span className={cn(
                          "text-xs ml-2",
                          isDark ? "text-slate-400" : "text-gray-600"
                        )}>
                          {fault.components.join("、")}
                        </span>
                      </div>
                    )}
                    {fault.affectedServices && (
                      <div>
                        <span className={cn(
                          "text-xs font-medium",
                          isDark ? "text-slate-300" : "text-gray-700"
                        )}>影响服务：</span>
                        <span className={cn(
                          "text-xs ml-2",
                          isDark ? "text-slate-400" : "text-gray-600"
                        )}>
                          {fault.affectedServices}
                        </span>
                      </div>
                    )}
                    {fault.possibleCauses && (
                      <div>
                        <span className={cn(
                          "text-xs font-medium",
                          isDark ? "text-slate-300" : "text-gray-700"
                        )}>可能原因：</span>
                        <ul className={cn(
                          "text-xs mt-1 ml-4 list-disc",
                          isDark ? "text-slate-400" : "text-gray-600"
                        )}>
                          {fault.possibleCauses.map((cause, index) => (
                            <li key={index}>{cause}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Zabbix异常弹窗 */}
      {showZabbixModal && (
        <ZabbixProblemsModal
          open={showZabbixModal}
          onClose={() => setShowZabbixModal(false)}
          onSelect={(problem) => {
            console.log('选中的问题:', problem);
            setShowZabbixModal(false);
          }}
        />
      )}
    </div>
  );
}