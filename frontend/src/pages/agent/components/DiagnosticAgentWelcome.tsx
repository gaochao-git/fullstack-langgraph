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
  Loader2
} from "lucide-react";
import ReactEcharts from 'echarts-for-react';
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';

// 故障类型定义
type FaultPriority = "P1" | "P2" | "P3";
type FaultStatus = "active" | "analyzing" | "analyzed" | "resolved";

interface Fault {
  id: string;
  title: string;
  description: string;
  ip: string;
  time: string;
  priority: FaultPriority;
  status: FaultStatus;
  sopId?: string;
  analysisResult?: string;
  threadId?: string;
  lastUpdated: string;
  tags: string[];
}

// 优先级和状态配置
const PRIORITY_CONFIG = {
  P1: { color: "bg-red-400", textColor: "text-red-300", borderColor: "border-red-600" },
  P2: { color: "bg-orange-400", textColor: "text-orange-300", borderColor: "border-orange-600" },
  P3: { color: "bg-yellow-400", textColor: "text-yellow-300", borderColor: "border-yellow-600" }
};

const STATUS_CONFIG = {
  active: { label: "待处理", textColor: "text-red-300", tagBg: "bg-red-900/50", tagText: "text-red-300", tagBorder: "border-red-600" },
  analyzing: { label: "分析中", textColor: "text-blue-300", tagBg: "bg-blue-900/50", tagText: "text-blue-300", tagBorder: "border-blue-600" },
  analyzed: { label: "已分析", textColor: "text-green-300", tagBg: "bg-green-900/50", tagText: "text-green-300", tagBorder: "border-green-600" },
  resolved: { label: "已解决", textColor: "text-purple-300", tagBg: "bg-purple-900/50", tagText: "text-purple-300", tagBorder: "border-purple-600" }
};

// Mock数据
const mockFaults: Fault[] = [
  {
    id: "fault-001",
    title: "磁盘空间不足",
    description: "/var/log分区使用率达到95%，系统日志写入异常",
    ip: "192.168.1.101",
    time: "2025-01-12 14:30:25",
    priority: "P3",
    status: "active",
    sopId: "SOP-SYS-101",
    lastUpdated: "2025-01-12 14:35:00",
    tags: ["磁盘空间", "系统", "日志"]
  },
  {
    id: "fault-002", 
    title: "MySQL写入耗时大于200ms",
    description: "MySQL数据库写入耗时大于200ms",
    ip: "192.168.1.102",
    time: "2025-07-24 15:26:01",
    priority: "P2",
    status: "active",
    sopId: "SOP-DB-001",
    lastUpdated: "2025-01-12 15:20:00", 
    tags: ["数据库", "响应耗时", "MySQL"]
  },
  {
    id: "fault-003",
    title: "内存不足",
    description: "服务器内存使用率持续超过90%，应用响应缓慢",
    ip: "192.168.1.103", 
    time: "2025-01-12 12:45:30",
    priority: "P3",
    status: "analyzing",
    sopId: "SOP-SYS-103",
    threadId: "thread-def456",
    lastUpdated: "2025-01-12 16:10:00",
    tags: ["内存", "性能", "系统"]
  },
  {
    id: "fault-004",
    title: "系统负载过高",
    description: "系统负载平均值过高，响应缓慢",
    ip: "192.168.1.104",
    time: "2025-01-12 11:20:15",
    priority: "P3", 
    status: "resolved",
    sopId: "SOP-SYS-102",
    analysisResult: "高CPU进程导致负载过高，已优化相关服务配置",
    threadId: "thread-ghi789",
    lastUpdated: "2025-01-12 16:45:00",
    tags: ["系统", "负载", "性能"]
  },
  {
    id: "fault-005",
    title: "MySQL连接问题",
    description: "MySQL数据库连接超时，Too many connections错误",
    ip: "192.168.1.105",
    time: "2025-01-12 10:30:45",
    priority: "P3",
    status: "resolved", 
    sopId: "SOP-DB-002",
    lastUpdated: "2025-01-12 10:35:00",
    tags: ["数据库", "连接", "MySQL"]
  },
  {
    id: "fault-006",
    title: "MySQL慢查询",
    description: "MySQL数据库查询响应时间长，影响用户体验",
    ip: "192.168.1.106",
    time: "2025-01-12 09:15:20",
    priority: "P3",
    status: "resolved",
    sopId: "SOP-DB-003", 
    analysisResult: "多个复杂查询未使用索引，已优化SQL并添加索引",
    threadId: "thread-jkl012",
    lastUpdated: "2025-01-12 17:00:00",
    tags: ["数据库", "慢查询", "MySQL"]
  },
  {
    id: "fault-007",
    title: "MySQL死锁问题",
    description: "MySQL数据库发生死锁，事务超时影响业务",
    ip: "192.168.1.107",
    time: "2025-01-12 08:00:00",
    priority: "P2",
    status: "analyzed",
    sopId: "SOP-DB-004",
    lastUpdated: "2025-01-12 08:05:00",
    tags: ["数据库", "死锁", "MySQL"]
  },
  {
    id: "fault-008",
    title: "系统负载过高",
    description: "应用服务器负载平均值过高，CPU和IO等待时间长",
    ip: "192.168.1.108", 
    time: "2025-01-12 16:45:10",
    priority: "P3",
    status: "analyzed",
    sopId: "SOP-SYS-102",
    threadId: "thread-mno345",
    lastUpdated: "2025-01-12 17:30:00",
    tags: ["系统", "负载", "性能"]
  }
];

// 故障诊断场景配置
const DIAGNOSIS_SCENARIOS = {
  "fault-001": {
    title: "磁盘空间不足",
    description: `我遇到一个磁盘空间不足的故障，具体情况如下：

**故障现象：** /var/log分区使用率达到95%，系统日志写入异常
**故障IP：** 192.168.1.101  
**故障时间：** 2025-01-12 14:30:25
**希望排查的SOP：** SOP-SYS-101

请帮我进行故障诊断排查。`
  },
  "fault-005": {
    title: "MySQL连接问题", 
    description: `我遇到一个MySQL连接问题的故障，具体情况如下：

**故障现象：** MySQL数据库连接超时，Too many connections错误
**故障IP：** 192.168.1.105
**故障时间：** 2025-01-12 10:30:45  
**希望排查的SOP：** SOP-DB-002

请帮我进行故障诊断排查。`
  },
  "fault-007": {
    title: "MySQL死锁问题",
    description: `我遇到一个MySQL死锁问题的故障，具体情况如下：

**故障现象：** MySQL数据库发生死锁，事务超时影响业务
**故障IP：** 192.168.1.107
**故障时间：** 2025-01-12 08:00:00
**希望排查的SOP：** SOP-DB-004

请帮我进行故障诊断排查。`
  }
};

interface FaultWelcomeProps {
  onDiagnose: (fault: Fault) => void;
  onContinueChat: (fault: Fault) => void;
  onEndDiagnosis?: (fault: Fault) => void;
  onStartDiagnosis?: (message: string) => void; // 新增：直接发送诊断消息
}

function DiagnosticAgentWelcome({ onDiagnose, onContinueChat, onEndDiagnosis, onStartDiagnosis }: FaultWelcomeProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [timeFilter, setTimeFilter] = useState<string>("all");
  const [expandedFault, setExpandedFault] = useState<string | null>(null);

  // 将故障四要素组合成一句话提问
  const formatDiagnosisQuestion = (fault: Fault): string => {
    // 验证四要素是否完整
    if (!fault.time || !fault.ip || !fault.description || !fault.sopId) {
      // 故障四要素不完整
      return `故障信息不完整，无法进行诊断排查。`;
    }
    
    return `${fault.time}，服务器${fault.ip}出现了${fault.description}，请使用SOP编号${fault.sopId}进行诊断排查。`;
  };

  // 计算统计数据
  const stats = useMemo(() => {
    // 临时调试：打印当前mockFaults的实际内容
    // 当前mockFaults数据
    
    const activeFaults = mockFaults.filter(f => f.status === "active").length;
    const analyzingFaults = mockFaults.filter(f => f.status === "analyzing").length;
    const analyzedFaults = mockFaults.filter(f => f.status === "analyzed").length;
    const resolvedFaults = mockFaults.filter(f => f.status === "resolved").length;
    const p1Faults = mockFaults.filter(f => f.priority === "P1").length;
    const p2Faults = mockFaults.filter(f => f.priority === "P2").length;
    const p3Faults = mockFaults.filter(f => f.priority === "P3").length;
    
    const result = {
      total: mockFaults.length,
      active: activeFaults,
      analyzing: analyzingFaults,
      analyzed: analyzedFaults,
      resolved: resolvedFaults,
      p1: p1Faults,
      p2: p2Faults,
      p3: p3Faults
    };
    
    // 统计结果
    return result;
  }, []);

  // 过滤故障数据
  const filteredFaults = useMemo(() => {
    let filtered = [...mockFaults];

    // 搜索过滤
    if (searchTerm) {
      filtered = filtered.filter(fault => 
        fault.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        fault.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        fault.ip.includes(searchTerm)
      );
    }

    // 优先级过滤
    if (priorityFilter !== "all") {
      filtered = filtered.filter(fault => fault.priority === priorityFilter);
    }

    // 状态过滤
    if (statusFilter !== "all") {
      filtered = filtered.filter(fault => fault.status === statusFilter);
    }

    // 时间过滤
    if (timeFilter !== "all") {
      const now = new Date();
      
      filtered = filtered.filter(fault => {
        const faultDate = new Date(fault.time);
        const timeDiff = now.getTime() - faultDate.getTime();
        
        switch (timeFilter) {
          case '10min':
            return timeDiff <= 10 * 60 * 1000; // 10分钟
          case '30min':
            return timeDiff <= 30 * 60 * 1000; // 30分钟
          case '1hour':
            return timeDiff <= 60 * 60 * 1000; // 1小时
          case 'today':
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            return faultDate >= today;
          case 'week':
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return faultDate >= weekAgo;
          default:
            return true;
        }
      });
    }

    // 按状态和时间排序
    filtered.sort((a, b) => {
      const statusOrder = { "active": 4, "analyzing": 3, "analyzed": 2, "resolved": 1 };
      const statusDiff = statusOrder[b.status] - statusOrder[a.status];
      if (statusDiff !== 0) return statusDiff;
      return new Date(b.time).getTime() - new Date(a.time).getTime();
    });

    return filtered.slice(0, 50); // 限制显示数量
  }, [searchTerm, priorityFilter, statusFilter, timeFilter]);

  const { isDark } = useTheme();

  return (
    <div className={cn(
      "max-w-4xl mx-auto p-4 space-y-4 min-h-screen transition-colors duration-200",
      isDark 
        ? "bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900" 
        : "bg-gradient-to-br from-blue-50 via-white to-blue-50"
    )}>
      {/* 标题和搜索区域 */}
      <div className={cn(
        "flex items-center justify-between rounded-lg border backdrop-blur-sm py-1.5 px-3 shadow-xl transition-colors duration-200",
        isDark 
          ? "bg-gradient-to-r from-slate-800/75 via-cyan-900/30 to-slate-800/75 border-cyan-500/40 shadow-cyan-500/25" 
          : "bg-gradient-to-r from-blue-100/75 via-purple-100/30 to-blue-100/75 border-blue-300/40 shadow-blue-500/25"
      )}>
        <div className="text-center flex-1">
          <h1 className={cn(
            "text-lg md:text-xl font-bold bg-gradient-to-r bg-clip-text text-transparent",
            isDark 
              ? "from-blue-400 to-purple-400" 
              : "from-blue-600 to-purple-600"
          )}>
            故障诊断助手
          </h1>
        </div>
        <div className="ml-8">
          <div className="relative">
            <Search className={cn(
              "absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4",
              isDark ? "text-slate-400" : "text-gray-500"
            )} />
            <input
              placeholder="搜索故障标题、描述或IP..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={cn(
                "w-full pl-9 pr-4 py-1 text-xs md:text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-400 shadow-lg transition-all duration-200",
                isDark 
                  ? "bg-slate-700/60 border-slate-600 text-slate-100 placeholder-slate-400 focus:bg-slate-700" 
                  : "bg-white/60 border-gray-300 text-gray-900 placeholder-gray-500 focus:bg-white"
              )}
            />
          </div>
          {/* 时间筛选按钮 */}
          <div className="flex flex-wrap gap-2 mt-2">
            <button 
              onClick={() => setTimeFilter(timeFilter === '10min' ? 'all' : '10min')}
              className={cn(
                "px-3 py-1 rounded-lg text-xs md:text-sm font-medium border transition-all duration-200",
                timeFilter === '10min' 
                  ? isDark
                    ? 'bg-cyan-500 border-cyan-400 text-white shadow-md' 
                    : 'bg-blue-500 border-blue-400 text-white shadow-md'
                  : isDark
                    ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50'
                    : 'bg-gray-100/50 border-gray-300 text-gray-700 hover:bg-gray-200/50'
              )}
            >
              最近10分钟
            </button>
            <button 
              onClick={() => setTimeFilter(timeFilter === '30min' ? 'all' : '30min')}
              className={cn(
                "px-3 py-1 rounded-lg text-xs md:text-sm font-medium border transition-all duration-200",
                timeFilter === '30min' 
                  ? isDark
                    ? 'bg-cyan-500 border-cyan-400 text-white shadow-md' 
                    : 'bg-blue-500 border-blue-400 text-white shadow-md'
                  : isDark
                    ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50'
                    : 'bg-gray-100/50 border-gray-300 text-gray-700 hover:bg-gray-200/50'
              )}
            >
              最近30分钟
            </button>
            <button 
              onClick={() => setTimeFilter(timeFilter === '1hour' ? 'all' : '1hour')}
              className={cn(
                "px-3 py-1 rounded-lg text-xs md:text-sm font-medium border transition-all duration-200",
                timeFilter === '1hour' 
                  ? isDark
                    ? 'bg-cyan-500 border-cyan-400 text-white shadow-md' 
                    : 'bg-blue-500 border-blue-400 text-white shadow-md'
                  : isDark
                    ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50'
                    : 'bg-gray-100/50 border-gray-300 text-gray-700 hover:bg-gray-200/50'
              )}
            >
              最近1小时
            </button>
            <button 
              onClick={() => setTimeFilter(timeFilter === 'today' ? 'all' : 'today')}
              className={cn(
                "px-3 py-1 rounded-lg text-xs md:text-sm font-medium border transition-all duration-200",
                timeFilter === 'today' 
                  ? isDark
                    ? 'bg-cyan-500 border-cyan-400 text-white shadow-md' 
                    : 'bg-blue-500 border-blue-400 text-white shadow-md'
                  : isDark
                    ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50'
                    : 'bg-gray-100/50 border-gray-300 text-gray-700 hover:bg-gray-200/50'
              )}
            >
              今天
            </button>
            <button 
              onClick={() => setTimeFilter(timeFilter === 'week' ? 'all' : 'week')}
              className={cn(
                "px-3 py-1 rounded-lg text-xs md:text-sm font-medium border transition-all duration-200",
                timeFilter === 'week' 
                  ? isDark
                    ? 'bg-cyan-500 border-cyan-400 text-white shadow-md' 
                    : 'bg-blue-500 border-blue-400 text-white shadow-md'
                  : isDark
                    ? 'bg-slate-700/50 border-slate-600 text-slate-300 hover:bg-slate-600/50'
                    : 'bg-gray-100/50 border-gray-300 text-gray-700 hover:bg-gray-200/50'
              )}
            >
              本周
            </button>
          </div>
        </div>
      </div>

      {/* 双栏统计仪表板 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 第一栏：优先级统计 */}
        <div className={cn(
          "rounded-xl p-2 border backdrop-blur-sm shadow-xl transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-br from-slate-800/75 via-blue-900/35 to-slate-700/75 border-blue-500/40 shadow-blue-500/20" 
            : "bg-gradient-to-br from-blue-100/75 via-purple-100/35 to-blue-100/75 border-blue-300/40 shadow-blue-500/20"
        )}>
          <h3 className={cn(
            "text-xs md:text-sm font-semibold mb-1 flex items-center gap-1",
            isDark ? "text-white" : "text-gray-900"
          )}>
            <AlertTriangle className={cn(
              "w-4 h-4",
              isDark ? "text-red-400" : "text-red-600"
            )} />
            报警等级
          </h3>
          <div className="flex items-center gap-2">
            {/* 总数环形图+数字 */}
            <div className="relative flex-shrink-0">
              <ReactEcharts
                option={{
                  series: [{
                    type: 'pie',
                    radius: ['75%', '99%'],
                    center: ['50%', '50%'],
                    label: { show: false },
                    labelLine: { show: false },
                    silent: true,
                    data: [
                      { value: stats.p1, name: 'P1', itemStyle: { color: '#ef4444', borderWidth: 0 } },
                      { value: stats.p2, name: 'P2', itemStyle: { color: '#f97316', borderWidth: 0 } },
                      { value: stats.p3, name: 'P3', itemStyle: { color: '#eab308', borderWidth: 0 } },
                    ]
                  }]
                }}
                style={{ width: 90, height: 90 }}
                opts={{ renderer: 'canvas', devicePixelRatio: window.devicePixelRatio }}
                notMerge={true}
                lazyUpdate={true}
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className={cn(
                  "text-xs md:text-sm font-bold leading-none",
                  isDark ? "text-yellow-400" : "text-blue-600"
                )}>{stats.total}</span>
                <span className={cn(
                  "text-xs md:text-sm leading-tight",
                  isDark ? "text-slate-300" : "text-gray-600"
                )}>总数</span>
              </div>
            </div>
            {/* P1/P2/P3按钮 */}
            <div className="flex flex-col gap-2 flex-1">
              <button onClick={() => { 
                  if (priorityFilter === 'P1') {
                    setPriorityFilter('all');
                  } else {
                    setPriorityFilter('P1');
                  }
                }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition-all duration-200",
                  priorityFilter === 'P1' 
                    ? 'bg-red-500 border-red-400 text-white shadow-lg transform scale-105' 
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-red-300 hover:bg-red-900/40 hover:border-red-500'
                      : 'bg-red-100/50 border-red-300 text-red-700 hover:bg-red-200/50 hover:border-red-400'
                )}
              >
                <AlertTriangle className="w-3.5 h-3.5" />P1 紧急 ({stats.p1})
              </button>
              <button onClick={() => { 
                  if (priorityFilter === 'P2') {
                    setPriorityFilter('all');
                  } else {
                    setPriorityFilter('P2');
                  }
                }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition-all duration-200",
                  priorityFilter === 'P2' 
                    ? 'bg-orange-500 border-orange-400 text-white shadow-lg transform scale-105' 
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-orange-300 hover:bg-orange-900/40 hover:border-orange-500'
                      : 'bg-orange-100/50 border-orange-300 text-orange-700 hover:bg-orange-200/50 hover:border-orange-400'
                )}
              >
                <Clock className="w-3.5 h-3.5" />P2 重要 ({stats.p2})
              </button>
              <button onClick={() => { 
                  if (priorityFilter === 'P3') {
                    setPriorityFilter('all');
                  } else {
                    setPriorityFilter('P3');
                  }
                }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition-all duration-200",
                  priorityFilter === 'P3' 
                    ? 'bg-yellow-500 border-yellow-400 text-gray-900 shadow-lg transform scale-105' 
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-yellow-300 hover:bg-yellow-900/40 hover:border-yellow-500'
                      : 'bg-yellow-100/50 border-yellow-300 text-yellow-700 hover:bg-yellow-200/50 hover:border-yellow-400'
                )}
              >
                <Server className="w-3.5 h-3.5" />P3 一般 ({stats.p3})
              </button>
            </div>
          </div>
        </div>
        {/* 第二栏：状态统计 */}
        <div className={cn(
          "rounded-xl p-2 border backdrop-blur-sm shadow-xl transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-br from-slate-800/75 via-blue-900/35 to-slate-700/75 border-blue-500/40 shadow-blue-500/20" 
            : "bg-gradient-to-br from-blue-100/75 via-purple-100/35 to-blue-100/75 border-blue-300/40 shadow-blue-500/20"
        )}>
          <h3 className={cn(
            "text-xs md:text-sm font-semibold mb-1 flex items-center gap-1",
            isDark ? "text-white" : "text-gray-900"
          )}>
            <Activity className={cn(
              "w-4 h-4",
              isDark ? "text-blue-400" : "text-blue-600"
            )} />
            处理状态
          </h3>
          <div className="flex items-center gap-2">
            {/* 已解决占比环形图+数字 */}
            <div className="relative flex-shrink-0">
              <ReactEcharts
                option={{
                  series: [{
                    type: 'pie',
                    radius: ['75%', '99%'],
                    center: ['50%', '50%'],
                    label: { show: false },
                    labelLine: { show: false },
                    silent: true,
                    data: [
                      { value: stats.active, name: '待处理', itemStyle: { color: '#ef4444', borderWidth: 0 } },
                      { value: stats.analyzing, name: '分析中', itemStyle: { color: '#3b82f6', borderWidth: 0 } },
                      { value: stats.analyzed, name: '已分析', itemStyle: { color: '#10b981', borderWidth: 0 } },
                      { value: stats.resolved, name: '已解决', itemStyle: { color: '#a855f7', borderWidth: 0 } },
                    ]
                  }]
                }}
                style={{ width: 90, height: 90 }}
                opts={{ renderer: 'canvas', devicePixelRatio: window.devicePixelRatio }}
                notMerge={true}
                lazyUpdate={true}
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className={cn(
                  "text-sm font-bold leading-none",
                  isDark ? "text-red-400" : "text-red-600"
                )}>{stats.total > 0 ? Math.round(stats.active / stats.total * 100) : 0}%</span>
                <span className={cn(
                  "text-xs leading-tight",
                  isDark ? "text-slate-300" : "text-gray-600"
                )}>待处理</span>
              </div>
            </div>
            {/* 状态按钮组 */}
            <div className="flex flex-col gap-2 flex-1">
              <button onClick={() => { 
                  if (statusFilter === 'active') {
                    setStatusFilter('all');
                  } else {
                    setStatusFilter('active');
                  }
                }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition-all duration-200",
                  statusFilter === 'active' 
                    ? 'bg-red-500 border-red-400 text-white shadow-lg transform scale-105' 
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-red-300 hover:bg-red-900/40 hover:border-red-500'
                      : 'bg-red-100/50 border-red-300 text-red-700 hover:bg-red-200/50 hover:border-red-400'
                )}
              >
                <AlertTriangle className="w-3.5 h-3.5" />待处理 ({stats.active})
              </button>
              <button onClick={() => { 
                  if (statusFilter === 'analyzing') {
                    setStatusFilter('all');
                  } else {
                    setStatusFilter('analyzing');
                  }
                }}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition-all duration-200",
                  statusFilter === 'analyzing' 
                    ? 'bg-blue-500 border-blue-400 text-white shadow-lg transform scale-105' 
                    : isDark
                      ? 'bg-slate-700/50 border-slate-600 text-blue-300 hover:bg-blue-900/40 hover:border-blue-500'
                      : 'bg-blue-100/50 border-blue-300 text-blue-700 hover:bg-blue-200/50 hover:border-blue-400'
                )}
              >
                <Activity className="w-3.5 h-3.5" />分析中 ({stats.analyzing})
              </button>
              <div className="flex gap-2">
                <button onClick={() => { 
                    if (statusFilter === 'analyzed') {
                      setStatusFilter('all');
                    } else {
                      setStatusFilter('analyzed');
                    }
                  }}
                  className={cn(
                    "flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200 flex-1",
                    statusFilter === 'analyzed' 
                      ? 'bg-green-500 border-green-400 text-white shadow-lg transform scale-105' 
                      : isDark
                        ? 'bg-slate-700/50 border-slate-600 text-green-300 hover:bg-green-900/40 hover:border-green-500'
                        : 'bg-green-100/50 border-green-300 text-green-700 hover:bg-green-200/50 hover:border-green-400'
                  )}
                >
                  <CheckCircle className="w-3.5 h-3.5" />已分析 ({stats.analyzed})
                </button>
                <button onClick={() => { 
                    if (statusFilter === 'resolved') {
                      setStatusFilter('all');
                    } else {
                      setStatusFilter('resolved');
                    }
                  }}
                  className={cn(
                    "flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs font-semibold border-2 transition-all duration-200 flex-1",
                    statusFilter === 'resolved' 
                      ? 'bg-purple-500 border-purple-400 text-white shadow-lg transform scale-105' 
                      : isDark
                        ? 'bg-slate-700/50 border-slate-600 text-purple-300 hover:bg-purple-900/40 hover:border-purple-500'
                        : 'bg-purple-100/50 border-purple-300 text-purple-700 hover:bg-purple-200/50 hover:border-purple-400'
                  )}
                >
                  <CheckCircle className="w-3.5 h-3.5" />已解决 ({stats.resolved})
                </button>
              </div>
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
            {filteredFaults.map((fault) => {
              const priorityConfig = PRIORITY_CONFIG[fault.priority] || PRIORITY_CONFIG.P3;
              const statusConfig = STATUS_CONFIG[fault.status] || STATUS_CONFIG.active;
              const canContinueChat = fault.status === "analyzed" || fault.status === "analyzing";
              const canStartDiagnosis = fault.status === "active";
              const hasFourElements = fault.time && fault.ip && fault.description && fault.sopId;
              const isExpanded = expandedFault === fault.id;
              
              return (
                <div 
                  key={fault.id} 
                  className={cn(
                    "relative px-3 py-2 border-l-4 border rounded-xl text-sm transition-all duration-200 hover:shadow-lg",
                    isDark
                      ? "hover:bg-slate-600/30 border-l-blue-500 border-slate-600/50 bg-slate-700/40"
                      : "hover:bg-blue-100/30 border-l-blue-400 border-blue-200/50 bg-blue-50/40",
                    isExpanded 
                      ? isDark
                        ? "bg-slate-600/50 border-slate-500/60" 
                        : "bg-blue-100/50 border-blue-300/60"
                      : ''
                  )}
                >
                  {/* 主要信息行 - 可点击展开 */}
                  <div 
                    className="cursor-pointer"
                    onClick={() => setExpandedFault(isExpanded ? null : fault.id)}
                  >
                    <div>
                      {/* 桌面端：完整信息显示 */}
                      <div className="hidden md:flex items-center justify-between gap-2 w-full overflow-x-auto">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <div className={`w-2.5 h-2.5 rounded-full ${priorityConfig.color} flex-shrink-0 shadow-sm`}></div>
                          <span className={cn(
                            "font-medium whitespace-nowrap",
                            isDark ? "text-white" : "text-gray-900"
                          )}>{fault.title}</span>
                          <span className={cn(
                            "font-mono text-xs whitespace-nowrap",
                            isDark ? "text-slate-300" : "text-gray-600"
                          )}>{fault.ip}</span>
                          <span className={cn(
                            "text-xs whitespace-nowrap",
                            isDark ? "text-slate-400" : "text-gray-500"
                          )}>{fault.time}</span>
                          {/* 展开/折叠图标 */}
                          <svg 
                            className={cn(
                              "w-4 h-4 transition-transform duration-200",
                              isDark ? "text-slate-400" : "text-gray-500",
                              isExpanded ? 'rotate-90' : ''
                            )}
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                        
                        {/* 桌面端按钮区域 */}
                        <div className="flex gap-1.5 flex-shrink-0">
                          {fault.status === "active" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                // 点击开始排查按钮
                                
                                if (!hasFourElements) {
                                  alert('故障信息不完整，无法进行诊断排查。请确保包含：故障时间、故障IP、故障现象、SOP编号。');
                                  return;
                                }
                                
                                if (onStartDiagnosis) {
                                  const question = formatDiagnosisQuestion(fault);
                                  // 调用onStartDiagnosis
                                  onStartDiagnosis(question);
                                } else {
                                  // onStartDiagnosis未定义，使用回退逻辑
                                  const scenario = DIAGNOSIS_SCENARIOS[fault.id as keyof typeof DIAGNOSIS_SCENARIOS];
                                  if (scenario) {
                                    const faultWithDescription = {
                                      ...fault,
                                      diagnosisDescription: scenario.description
                                    };
                                    onDiagnose(faultWithDescription);
                                  } else {
                                    onDiagnose(fault);
                                  }
                                }
                              }}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-all duration-200 whitespace-nowrap ${
                                hasFourElements 
                                  ? 'bg-red-600 hover:bg-red-700 cursor-pointer' 
                                  : 'bg-gray-600 cursor-not-allowed opacity-60'
                              }`}
                              disabled={!hasFourElements}
                              title={hasFourElements ? '开始排查' : '故障信息不完整，无法开始排查'}
                            >
                              开始排查
                            </button>
                          )}
                          
                          {fault.status === "analyzing" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onContinueChat(fault);
                              }}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all duration-200 whitespace-nowrap"
                            >
                              <Loader2 className="w-3 h-3 animate-spin" />
                              查看进度
                            </button>
                          )}
                          
                          {fault.status === "analyzed" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onContinueChat(fault);
                              }}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap"
                            >
                              查看结果
                            </button>
                          )}
                          
                          {fault.status === "analyzed" && onEndDiagnosis && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onEndDiagnosis(fault);
                              }}
                              className="bg-green-700 hover:bg-green-800 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap"
                            >
                              结束排查
                            </button>
                          )}
                          
                          {fault.status === "resolved" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onContinueChat(fault);
                              }}
                              className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap"
                            >
                              解决详情
                            </button>
                          )}
                        </div>
                      </div>
                      
                      {/* 手机端：简化显示 */}
                      <div className="flex md:hidden items-center justify-between gap-2 w-full">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <div className={`w-2.5 h-2.5 rounded-full ${priorityConfig.color} flex-shrink-0 shadow-sm`}></div>
                          <span className="font-medium text-white truncate">
                            {fault.title.length > 10 ? fault.title.substring(0, 10) + '...' : fault.title}
                          </span>
                          {/* 展开/折叠图标 */}
                          <svg 
                            className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''} flex-shrink-0`}
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                        
                        {/* 手机端按钮区域 */}
                        <div className="flex gap-1.5 flex-shrink-0">
                          {fault.status === "active" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                // 点击开始排查按钮
                                
                                if (!hasFourElements) {
                                  alert('故障信息不完整，无法进行诊断排查。请确保包含：故障时间、故障IP、故障现象、SOP编号。');
                                  return;
                                }
                                
                                if (onStartDiagnosis) {
                                  const question = formatDiagnosisQuestion(fault);
                                  // 调用onStartDiagnosis
                                  onStartDiagnosis(question);
                                } else {
                                  // onStartDiagnosis未定义，使用回退逻辑
                                  const scenario = DIAGNOSIS_SCENARIOS[fault.id as keyof typeof DIAGNOSIS_SCENARIOS];
                                  if (scenario) {
                                    const faultWithDescription = {
                                      ...fault,
                                      diagnosisDescription: scenario.description
                                    };
                                    onDiagnose(faultWithDescription);
                                  } else {
                                    onDiagnose(fault);
                                  }
                                }
                              }}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-all duration-200 whitespace-nowrap ${
                                hasFourElements 
                                  ? 'bg-red-600 hover:bg-red-700 cursor-pointer' 
                                  : 'bg-gray-600 cursor-not-allowed opacity-60'
                              }`}
                              disabled={!hasFourElements}
                              title={hasFourElements ? '开始排查' : '故障信息不完整，无法开始排查'}
                            >
                              开始排查
                            </button>
                          )}
                          
                          {fault.status === "analyzing" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onContinueChat(fault);
                              }}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all duration-200 whitespace-nowrap"
                            >
                              <Loader2 className="w-3 h-3 animate-spin" />
                              查看进度
                            </button>
                          )}
                          
                          {fault.status === "analyzed" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onContinueChat(fault);
                              }}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap"
                            >
                              查看结果
                            </button>
                          )}
                          
                          {fault.status === "analyzed" && onEndDiagnosis && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onEndDiagnosis(fault);
                              }}
                              className="bg-green-700 hover:bg-green-800 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap"
                            >
                              结束排查
                            </button>
                          )}
                          
                          {fault.status === "resolved" && (
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                onContinueChat(fault);
                              }}
                              className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 whitespace-nowrap"
                            >
                              解决详情
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 展开的详细信息 */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-slate-600/50 space-y-3">
                      <div className="space-y-2 text-xs">
                        {/* 故障描述行 */}
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400 flex-shrink-0">故障描述：</span>
                          <div className="text-slate-200 bg-slate-800/30 px-2 py-1 rounded overflow-x-auto whitespace-nowrap" style={{width: 'calc(100% - 80px)'}}>{fault.description}</div>
                        </div>
                        {/* 其他信息行 */}
                        <div className="pr-28">
                          <div className="flex flex-wrap gap-4">
                            <div className="whitespace-nowrap">
                              <span className="text-slate-400">SOP编号：</span>
                              <span className="text-cyan-300 font-mono">{fault.sopId}</span>
                            </div>
                            <div className="whitespace-nowrap">
                              <span className="text-slate-400">优先级：</span>
                              <span className={`${priorityConfig.textColor} font-medium`}>{fault.priority}</span>
                            </div>
                            <div className="whitespace-nowrap">
                              <span className="text-slate-400">状态：</span>
                              <span className={`${statusConfig.textColor} font-medium`}>{statusConfig.label}</span>
                            </div>
                            <div className="whitespace-nowrap">
                              <span className="text-slate-400">最后更新：</span>
                              <span className="text-slate-200">{fault.lastUpdated}</span>
                            </div>
                          </div>
                        </div>
                        {fault.analysisResult && (
                          <div className="pr-28">
                            <span className="text-slate-400 text-xs">分析结果：</span>
                            <div className="text-slate-200 text-xs mt-1 bg-slate-800/30 p-2 rounded">
                              {fault.analysisResult}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="text-center pt-6 mt-6 border-t border-slate-600/50">
        <p className="text-slate-400 bg-slate-700/30 inline-block px-6 py-3 rounded-2xl border border-slate-600/30">
          💡 也可直接在下方输入框描述新故障进行智能诊断
        </p>
      </div>
    </div>
  );
}

export default DiagnosticAgentWelcome;