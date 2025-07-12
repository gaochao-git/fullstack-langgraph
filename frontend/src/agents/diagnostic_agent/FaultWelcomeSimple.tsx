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
  P1: { color: "bg-red-500", textColor: "text-red-500", borderColor: "border-red-200" },
  P2: { color: "bg-orange-500", textColor: "text-orange-500", borderColor: "border-orange-200" },
  P3: { color: "bg-yellow-500", textColor: "text-yellow-600", borderColor: "border-yellow-200" }
};

const STATUS_CONFIG = {
  active: { label: "待处理", textColor: "text-red-600", tagBg: "bg-red-100", tagText: "text-red-600", tagBorder: "border-red-300" },
  analyzing: { label: "分析中", textColor: "text-blue-600", tagBg: "bg-blue-100", tagText: "text-blue-600", tagBorder: "border-blue-300" },
  analyzed: { label: "已分析", textColor: "text-green-600", tagBg: "bg-green-100", tagText: "text-green-600", tagBorder: "border-green-300" },
  resolved: { label: "已解决", textColor: "text-purple-600", tagBg: "bg-purple-100", tagText: "text-purple-600", tagBorder: "border-purple-300" }
};

// Mock数据
const mockFaults: Fault[] = [
  {
    id: "fault-001",
    title: "磁盘空间不足",
    description: "/var/log分区使用率达到95%，系统日志写入异常",
    ip: "192.168.1.101",
    time: "2025-01-12 14:30:25",
    priority: "P1",
    status: "active",
    sopId: "SOP-SYS-101",
    lastUpdated: "2025-01-12 14:35:00",
    tags: ["磁盘空间", "系统", "日志"]
  },
  {
    id: "fault-002", 
    title: "MySQL高CPU使用率",
    description: "MySQL数据库CPU使用率过高，查询响应缓慢",
    ip: "192.168.1.102",
    time: "2025-01-12 13:15:10",
    priority: "P2",
    status: "analyzed",
    sopId: "SOP-DB-001",
    analysisResult: "慢查询导致CPU使用率过高，已优化相关SQL",
    threadId: "thread-abc123",
    lastUpdated: "2025-01-12 15:20:00", 
    tags: ["数据库", "CPU", "MySQL"]
  },
  {
    id: "fault-003",
    title: "内存不足",
    description: "服务器内存使用率持续超过90%，应用响应缓慢",
    ip: "192.168.1.103", 
    time: "2025-01-12 12:45:30",
    priority: "P2",
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
    priority: "P2",
    status: "active", 
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
    priority: "P2",
    status: "analyzed",
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
    priority: "P1",
    status: "active",
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
    priority: "P1",
    status: "analyzing",
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

export function FaultWelcomeSimple({ onDiagnose, onContinueChat, onEndDiagnosis, onStartDiagnosis }: FaultWelcomeProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // 将故障四要素组合成一句话提问
  const formatDiagnosisQuestion = (fault: Fault): string => {
    // 验证四要素是否完整
    if (!fault.time || !fault.ip || !fault.description || !fault.sopId) {
      console.error('故障四要素不完整:', { 
        time: fault.time, 
        ip: fault.ip, 
        description: fault.description, 
        sopId: fault.sopId 
      });
      return `故障信息不完整，无法进行诊断排查。`;
    }
    
    return `我需要排查一个故障：在${fault.time}，服务器${fault.ip}出现了${fault.description}，希望使用SOP编号${fault.sopId}进行诊断排查。`;
  };

  // 计算统计数据
  const stats = useMemo(() => {
    const activeFaults = mockFaults.filter(f => f.status === "active").length;
    const analyzingFaults = mockFaults.filter(f => f.status === "analyzing").length;
    const analyzedFaults = mockFaults.filter(f => f.status === "analyzed").length;
    const resolvedFaults = mockFaults.filter(f => f.status === "resolved").length;
    const p1Faults = mockFaults.filter(f => f.priority === "P1").length;
    const p2Faults = mockFaults.filter(f => f.priority === "P2").length;
    const p3Faults = mockFaults.filter(f => f.priority === "P3").length;
    
    return {
      total: mockFaults.length,
      active: activeFaults,
      analyzing: analyzingFaults,
      analyzed: analyzedFaults,
      resolved: resolvedFaults,
      p1: p1Faults,
      p2: p2Faults,
      p3: p3Faults
    };
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

    // 按优先级和时间排序
    filtered.sort((a, b) => {
      const priorityOrder = { "P1": 3, "P2": 2, "P3": 1 };
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
      if (priorityDiff !== 0) return priorityDiff;
      return new Date(b.time).getTime() - new Date(a.time).getTime();
    });

    return filtered.slice(0, 50); // 限制显示数量
  }, [searchTerm, priorityFilter, statusFilter]);

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-3">
      {/* 欢迎标题 */}
      <div className="text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-1">故障诊断助手</h1>
        <p className="text-sm text-gray-600">选择故障开始诊断，或直接输入描述</p>
      </div>

      {/* 统计概览、搜索和过滤合并 */}
      <div className="flex gap-1 items-center text-xs flex-wrap">
        {/* 统计标签 - 可点击过滤 */}
        <div 
          onClick={() => {
            setStatusFilter("all");
            setPriorityFilter("all");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            statusFilter === "all" && priorityFilter === "all" 
              ? "bg-gray-200 border-gray-400" 
              : "bg-gray-50 border-gray-300 hover:bg-gray-100"
          }`}
        >
          <BarChart3 className="w-3 h-3 text-gray-500" />
          <span className="text-gray-600">总数</span>
          <span className="font-bold text-gray-900">{stats.total}</span>
        </div>
        
        <div 
          onClick={() => {
            setStatusFilter("active");
            setPriorityFilter("all");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            statusFilter === "active" 
              ? "bg-red-200 border-red-400" 
              : "bg-red-50 border-red-300 hover:bg-red-100"
          }`}
        >
          <AlertTriangle className="w-3 h-3 text-red-500" />
          <span className="text-red-600">待处理</span>
          <span className="font-bold text-red-700">{stats.active}</span>
        </div>

        <div 
          onClick={() => {
            setStatusFilter("analyzing");
            setPriorityFilter("all");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            statusFilter === "analyzing" 
              ? "bg-blue-200 border-blue-400" 
              : "bg-blue-50 border-blue-300 hover:bg-blue-100"
          }`}
        >
          <Activity className="w-3 h-3 text-blue-500" />
          <span className="text-blue-600">分析中</span>
          <span className="font-bold text-blue-700">{stats.analyzing}</span>
        </div>

        <div 
          onClick={() => {
            setStatusFilter("analyzed");
            setPriorityFilter("all");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            statusFilter === "analyzed" 
              ? "bg-green-200 border-green-400" 
              : "bg-green-50 border-green-300 hover:bg-green-100"
          }`}
        >
          <CheckCircle className="w-3 h-3 text-green-500" />
          <span className="text-green-600">已分析</span>
          <span className="font-bold text-green-700">{stats.analyzed}</span>
        </div>

        <div 
          onClick={() => {
            setStatusFilter("resolved");
            setPriorityFilter("all");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            statusFilter === "resolved" 
              ? "bg-purple-200 border-purple-400" 
              : "bg-purple-50 border-purple-300 hover:bg-purple-100"
          }`}
        >
          <CheckCircle className="w-3 h-3 text-purple-500" />
          <span className="text-purple-600">已解决</span>
          <span className="font-bold text-purple-700">{stats.resolved}</span>
        </div>

        <div 
          onClick={() => {
            setStatusFilter("all");
            setPriorityFilter("P1");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            priorityFilter === "P1" 
              ? "bg-red-200 border-red-400" 
              : "bg-red-50 border-red-300 hover:bg-red-100"
          }`}
        >
          <div className="w-2 h-2 rounded-full bg-red-500"></div>
          <span className="text-red-600">P1</span>
          <span className="font-bold text-red-700">{stats.p1}</span>
        </div>

        <div 
          onClick={() => {
            setStatusFilter("all");
            setPriorityFilter("P2");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            priorityFilter === "P2" 
              ? "bg-orange-200 border-orange-400" 
              : "bg-orange-50 border-orange-300 hover:bg-orange-100"
          }`}
        >
          <div className="w-2 h-2 rounded-full bg-orange-500"></div>
          <span className="text-orange-600">P2</span>
          <span className="font-bold text-orange-700">{stats.p2}</span>
        </div>

        <div 
          onClick={() => {
            setStatusFilter("all");
            setPriorityFilter("P3");
          }}
          className={`flex items-center gap-1 px-1.5 py-1 rounded border cursor-pointer transition-colors ${
            priorityFilter === "P3" 
              ? "bg-yellow-200 border-yellow-400" 
              : "bg-yellow-50 border-yellow-300 hover:bg-yellow-100"
          }`}
        >
          <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
          <span className="text-yellow-600">P3</span>
          <span className="font-bold text-yellow-700">{stats.p3}</span>
        </div>

        {/* 搜索框 */}
        <div className="relative ml-2 w-32">
          <Search className="absolute left-2 top-1.5 w-3 h-3 text-gray-400" />
          <input
            placeholder="搜索故障..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-7 pr-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* 故障列表 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-800">
            当前故障 ({filteredFaults.length})
          </h3>
          {filteredFaults.length >= 50 && (
            <span className="text-xs text-gray-500">显示前50条</span>
          )}
        </div>
        
        {filteredFaults.length === 0 ? (
          <div className="p-6 text-center border border-gray-200 rounded">
            <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">暂无故障</h3>
            <p className="text-gray-600">没有找到符合条件的故障</p>
          </div>
        ) : (
          <div className="grid gap-0.5">
            {filteredFaults.map((fault) => {
              const priorityConfig = PRIORITY_CONFIG[fault.priority];
              const statusConfig = STATUS_CONFIG[fault.status];
              const canContinueChat = fault.status === "analyzed" || fault.status === "analyzing";
              const canStartDiagnosis = fault.status === "active";
              const hasFourElements = fault.time && fault.ip && fault.description && fault.sopId;

              return (
                <div 
                  key={fault.id} 
                  className={`flex items-center justify-between gap-1 px-2 py-1 hover:bg-gray-50 border-l-2 ${priorityConfig.borderColor} bg-white border border-gray-200 rounded text-xs`}
                >
                  <div className="flex items-center gap-1 flex-1 min-w-0">
                    <span className={`${statusConfig.tagBg} ${statusConfig.tagText} ${statusConfig.tagBorder} px-1.5 py-0.5 rounded border text-xs flex-shrink-0`}>
                      {statusConfig.label}
                    </span>
                    <div className={`w-2 h-2 rounded-full ${priorityConfig.color} flex-shrink-0`}></div>
                    <span className="font-medium text-gray-800 truncate">{fault.title}</span>
                    <span className="text-blue-600 font-mono text-xs">{fault.sopId}</span>
                    <span className="text-gray-500 font-mono">{fault.ip}</span>
                    <span className="text-gray-400 text-xs">{fault.time}</span>
                  </div>
                  
                  <div className="flex gap-1 flex-shrink-0">
                    {/* 开始排查按钮 - 仅对待处理状态显示 */}
                    {fault.status === "active" && (
                      <button 
                        onClick={() => {
                          console.log('点击开始排查按钮', fault.id, fault.title);
                          
                          if (!hasFourElements) {
                            alert('故障信息不完整，无法进行诊断排查。请确保包含：故障时间、故障IP、故障现象、SOP编号。');
                            return;
                          }
                          
                          if (onStartDiagnosis) {
                            // 使用四要素组合的一句话提问
                            const question = formatDiagnosisQuestion(fault);
                            console.log('调用onStartDiagnosis:', question);
                            onStartDiagnosis(question);
                          } else {
                            console.log('onStartDiagnosis未定义，使用回退逻辑');
                            // 回退到原有逻辑
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
                        className={`px-2 py-0 rounded text-xs h-4 text-white ${
                          hasFourElements 
                            ? 'bg-red-600 hover:bg-red-700 cursor-pointer' 
                            : 'bg-gray-400 cursor-not-allowed opacity-60'
                        }`}
                        disabled={!hasFourElements}
                        title={hasFourElements ? '开始排查' : '故障信息不完整，无法开始排查'}
                      >
                        开始排查
                      </button>
                    )}
                    
                    {/* 查看进度按钮 - 对分析中状态显示 */}
                    {fault.status === "analyzing" && (
                      <button 
                        onClick={() => onContinueChat(fault)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-0 rounded text-xs h-4 flex items-center gap-1"
                      >
                        <Loader2 className="w-2.5 h-2.5 animate-spin" />
                        查看进度
                      </button>
                    )}
                    
                    {/* 查看结果按钮 - 对已分析状态显示 */}
                    {fault.status === "analyzed" && (
                      <button 
                        onClick={() => onContinueChat(fault)}
                        className="bg-green-600 hover:bg-green-700 text-white px-2 py-0 rounded text-xs h-4"
                      >
                        查看结果
                      </button>
                    )}
                    
                    {/* 结束排查按钮 - 对已分析状态显示 */}
                    {fault.status === "analyzed" && onEndDiagnosis && (
                      <button 
                        onClick={() => onEndDiagnosis(fault)}
                        className="bg-green-700 hover:bg-green-800 text-white px-2 py-0 rounded text-xs h-4"
                      >
                        结束排查
                      </button>
                    )}
                    
                    {/* 查看详情按钮 - 对已解决状态显示 */}
                    {fault.status === "resolved" && (
                      <button 
                        onClick={() => onContinueChat(fault)}
                        className="bg-purple-600 hover:bg-purple-700 text-white px-2 py-0 rounded text-xs h-4"
                      >
                        解决详情
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="text-center pt-2 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          💡 也可直接在下方输入框描述新故障
        </p>
      </div>
    </div>
  );
}