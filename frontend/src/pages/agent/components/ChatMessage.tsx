import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Wrench, User, Bot, ArrowDown, Plus, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState, ReactNode, useEffect, useRef, useCallback } from "react";
import { cn } from "@/utils/lib-utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import DiagnosticAgentWelcome from "./DiagnosticAgentWelcome";
import ZabbixDataRenderer, { canRenderChart } from "./ZabbixDataRenderer";
import { useTheme } from "@/hooks/ThemeContext";

// 黑名单：不显示这些工具调用，便于用户发现和维护
const HIDDEN_TOOLS = [
  'QuestionInfoExtraction',      // 问题信息提取
  'DiagnosisReflectionOutput',   // 诊断反思输出
  'IntentAnalysisOutput'         // 意图分析输出
];

// 诊断消息中的事件类型
export interface ProcessedEvent {
  title: string;
  data: any;
}


// 动态按钮文字组件
const DiagnosisButtonText: React.FC<{ text?: string }> = ({ text = "诊断中" }) => {
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => {
        if (prev.length >= 3) return "";
        return prev + ".";
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <span className="flex items-center gap-2">
      <Loader2 className="h-4 w-4 animate-spin text-cyan-100" />
      {text}
      <span className="inline-block w-6 text-left">{dots}</span>
    </span>
  );
};

// 工具调用组件 props
interface ToolCallProps {
  toolCall: any;
  toolResult?: any;
  isPending?: boolean; // 是否为待确认状态
  onApprove?: () => void; // 确认回调
  onReject?: () => void; // 拒绝回调
  toolCount?: number; // 新增：工具调用总数
}

// 工具调用组件
const ToolCall: React.FC<ToolCallProps> = ({ toolCall, toolResult, isPending, onApprove, onReject, toolCount }) => {
  const [isExpanded, setIsExpanded] = useState(isPending || false); // 待确认状态默认展开
  
  // 当工具变为待审批状态时，自动展开
  useEffect(() => {
    if (isPending) {
      setIsExpanded(true);
    }
  }, [isPending]);
  
  const toolName = toolCall?.name || "Unknown Tool";
  const toolArgs = toolCall?.args || {};
  const toolResultContent = toolResult?.content || "";
  
  
  return (
    <div className={`border rounded-xl mb-1 shadow-sm transition-all duration-300 overflow-hidden ${isPending ? 'border-orange-400 bg-gradient-to-r from-orange-100 to-yellow-100' : 'border-cyan-400 bg-gradient-to-r from-blue-800 to-blue-900'}`}>
      {/* 工具调用头部（合并描述和折叠按钮） */}
      <div 
        className={`flex items-center justify-between px-3 py-1.5 cursor-pointer transition-all duration-200 ${isPending ? 'hover:bg-gradient-to-r hover:from-orange-200 hover:to-yellow-200' : 'hover:bg-gradient-to-r hover:from-blue-700 hover:to-blue-800'}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Wrench className={`h-5 w-5 ${isPending ? 'text-orange-600' : 'text-cyan-300'}`} />
          <span className={`font-mono text-sm font-semibold truncate ${isPending ? 'text-orange-800' : 'text-yellow-400'}`}>{toolName}</span>
          <span className={`ml-2 text-xs font-bold flex-shrink-0 ${isPending ? 'text-orange-700' : 'text-yellow-400'}`}>工具调用（{toolCount || 1}）</span>
        </div>
        
        {/* 待确认状态的操作按钮 - 放在头部 */}
        {isPending && (
          <div className="flex gap-2 mr-2" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="default"
              size="sm"
              onClick={() => {
                // 确认工具: toolCall.name
                // 传递详细的审批信息给后端
                onApprove?.();
              }}
              className="bg-green-500 hover:bg-green-600 text-white font-medium text-xs px-2 py-1 h-6"
            >
              ✅ 确认
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // 拒绝工具: toolCall.name
                onReject?.();
              }}
              className="border-red-400 text-red-600 hover:bg-red-50 font-medium text-xs px-2 py-1 h-6"
            >
              ❌ 拒绝
            </Button>
          </div>
        )}
        
        {isExpanded ? (
          <ChevronDown className={`h-4 w-4 ${isPending ? 'text-orange-600' : 'text-cyan-300'}`} />
        ) : (
          <ChevronRight className={`h-4 w-4 ${isPending ? 'text-orange-600' : 'text-cyan-300'}`} />
        )}
      </div>
      
      {/* 展开的内容 */}
      {isExpanded && (
        <div className={`border-t-2 p-3 space-y-3 overflow-x-auto ${isPending ? 'border-orange-400' : 'border-cyan-400'}`}>
          {/* 参数 */}
          <div className="min-w-fit max-w-full">
            <h4 className={`text-sm font-bold mb-2 ${isPending ? 'text-cyan-300' : 'text-cyan-300'}`}>参数:</h4>
            <pre className={`p-3 rounded-lg text-xs overflow-x-auto whitespace-pre max-w-full border ${isPending ? 'bg-gray-900 text-cyan-300 border-cyan-500' : 'bg-gray-900 text-cyan-300 border-cyan-500'}`}>
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
          
          
          
          {/* 输出结果 */}
          {toolResultContent && (
            <div className="min-w-fit max-w-full">
              <h4 className={`text-sm font-bold mb-2 ${isPending ? 'text-cyan-300' : 'text-cyan-300'}`}>输出:</h4>
              
              {/* 工具展开后只显示原始JSON数据 */}
              <pre className={`p-3 rounded-lg text-xs overflow-x-auto max-h-48 overflow-y-auto whitespace-pre max-w-full border ${isPending ? 'bg-gray-900 text-cyan-300 border-cyan-500' : 'bg-gray-900 text-cyan-300 border-cyan-500'}`}>
                {typeof toolResultContent === 'string' 
                  ? toolResultContent 
                  : JSON.stringify(toolResultContent, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// SOP执行确认组件 props
interface SOPExecutionApprovalProps {
  interrupt: any;
  onInterruptResume: (approved: boolean) => void;
}

// SOP执行确认组件
const SOPExecutionApproval: React.FC<SOPExecutionApprovalProps> = ({ interrupt, onInterruptResume }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const sopInfo = interrupt.value;
  
  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      onInterruptResume(true);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      onInterruptResume(false);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="border border-orange-300 rounded-lg p-4 bg-gradient-to-r from-orange-50 to-yellow-50">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-orange-800 mb-2">
          SOP执行确认
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          {sopInfo.message}
        </p>
      </div>
      
      {/* SOP信息 */}
      <div className="mb-4 p-3 bg-white border border-orange-200 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium text-orange-800">SOP ID: {sopInfo.sop_id || '未知'}</span>
          <Badge 
            variant="outline" 
            className="text-xs border-orange-500 text-orange-700"
          >
            SOP执行
          </Badge>
        </div>
        <div className="text-xs text-gray-600 mb-2">
          <strong>当前步骤:</strong> {sopInfo.current_sop_step || '未知'}
        </div>
        {sopInfo.tool_calls && sopInfo.tool_calls.length > 0 && (
          <div>
            <div className="text-xs text-gray-600 mb-2">
              <strong>计划执行的操作:</strong>
            </div>
            <pre className="text-xs bg-gray-100 p-2 rounded border overflow-x-auto">
              {sopInfo.tool_calls.map((call: any, index: number) => 
                `${index + 1}. ${call.name}: ${JSON.stringify(call.args, null, 2)}`
              ).join('\n')}
            </pre>
          </div>
        )}
      </div>
      
      {/* 操作按钮 */}
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleReject}
          className="border-gray-400 text-gray-600 hover:bg-gray-100 rounded-md"
          disabled={isSubmitting}
        >
          取消
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={handleApprove}
          className="bg-green-500 hover:bg-green-600 text-white"
          disabled={isSubmitting}
        >
          {isSubmitting ? "处理中..." : "确认执行"}
        </Button>
      </div>
    </div>
  );
};

// 工具调用列表组件 props
interface ToolCallsProps {
  message: Message;
  allMessages: Message[];
  interrupt?: any; // 添加interrupt数据
  onInterruptResume?: (approved: boolean | string[]) => void; // 添加interrupt处理函数
}

// 工具调用列表组件
const ToolCalls: React.FC<ToolCallsProps> = ({ message, allMessages, interrupt, onInterruptResume }) => {
  const allToolCalls = (message as any).tool_calls || [];
  
  // 使用全局定义的黑名单过滤工具调用
  const toolCalls = allToolCalls.filter((call: any) => {
    const toolName = call.name || call.function?.name;
    return toolName && !HIDDEN_TOOLS.includes(toolName);
  });
  
  if (!toolCalls.length) return null;
  
  // 查找对应的工具结果
  const findToolResult = (toolCallId: string) => {
    const messageIndex = allMessages.findIndex(msg => msg.id === message.id);
    if (messageIndex === -1) return null;
    
    // 查找下一个 ToolMessage
    for (let i = messageIndex + 1; i < allMessages.length; i++) {
      const nextMessage = allMessages[i];
      if (nextMessage.type === 'tool' && (nextMessage as any).tool_call_id === toolCallId) {
        return nextMessage;
      }
    }
    return null;
  };
  
  // 检查工具调用是否为待确认状态
  const isPendingToolCall = (toolCall: any) => {
    if (!interrupt || !interrupt.value) {
      return false;
    }
    
    const interruptValue = interrupt.value;
    
    // 工具审批：使用工具名+参数精确匹配
    if (interruptValue.suggestion_type === "tool_approval") {
      return interruptValue.tool_name === toolCall.name && 
             JSON.stringify(interruptValue.tool_args) === JSON.stringify(toolCall.args || {});
    }
    
    // SOP执行：检查工具调用列表中是否包含当前工具
    if (interruptValue.suggestion_type === "sop_execution" && interruptValue.tool_calls) {
      return interruptValue.tool_calls.some((sopToolCall: any) => 
        sopToolCall.name === toolCall.name && 
        JSON.stringify(sopToolCall.args || {}) === JSON.stringify(toolCall.args || {})
      );
    }
    
    return false;
  };
  
  return (
    <div className="mb-1">
      <div className="space-y-2">
        {toolCalls.map((toolCall: any, index: number) => {
          const toolResult = findToolResult(toolCall.id);
          const isPending = isPendingToolCall(toolCall);
          return (
            <ToolCall 
              key={toolCall.id || index} 
              toolCall={toolCall}
              toolResult={toolResult}
              isPending={isPending}
              onApprove={() => {
                // 确认工具: toolCall.name
                // 传递详细的审批信息给后端
                onInterruptResume?.({
                  "工具名": toolCall.name,
                  "工具参数": toolCall.args,
                  "审批结果": true
                });
              }}
              onReject={() => {
                // 拒绝工具: toolCall.name
                // 传递详细的审批信息给后端
                onInterruptResume?.({
                  "工具名": toolCall.name,
                  "工具参数": toolCall.args,
                  "审批结果": false
                });
              }}
              toolCount={toolCalls.length}
            />
          );
        })}
      </div>
    </div>
  );
};

// 批量工具审批组件 props
interface BatchToolApprovalProps {
  interrupt: any;
  onInterruptResume: (approvedTools: string[]) => void;
}

// 批量工具审批组件
const BatchToolApproval: React.FC<BatchToolApprovalProps> = ({ interrupt, onInterruptResume }) => {
  const [approvedTools, setApprovedTools] = useState<Set<string>>(new Set());
  const [submittedTools, setSubmittedTools] = useState<Set<string>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // 从interrupt中获取待审批的工具列表
  const pendingTools = interrupt?.pending_tools || [];
  const approvedToolsFromBackend = interrupt?.approved_tools || [];
  const totalTools = interrupt?.total_tools || 0;
  
  // 处理单个工具的审批状态变化
  const handleToolApprovalChange = (toolCallId: string, approved: boolean) => {
    setApprovedTools(prev => {
      const newSet = new Set(prev);
      if (approved) {
        newSet.add(toolCallId);
      } else {
        newSet.delete(toolCallId);
      }
      return newSet;
    });
  };
  
  // 计算剩余待审批的工具
  const remainingTools = pendingTools.filter((tool: any) => !submittedTools.has(tool.tool_call_id));
  
  // 处理全选/取消全选
  const handleSelectAll = (selectAll: boolean) => {
    if (selectAll) {
      const allToolIds = remainingTools.map((tool: any) => tool.tool_call_id);
      setApprovedTools(new Set(allToolIds));
    } else {
      setApprovedTools(new Set());
    }
  };
  
  // 提交当前选中的工具
  const handleSubmitSelected = async () => {
    const approvedToolIds = Array.from(approvedTools);
    if (approvedToolIds.length > 0) {
      setIsSubmitting(true);
      try {
        // 将当前选中的工具标记为已提交
        setSubmittedTools(prev => new Set([...prev, ...approvedToolIds]));
        // 清空当前选择
        setApprovedTools(new Set());
        // 提交选中的工具
        onInterruptResume(approvedToolIds);
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  // 提交所有剩余工具
  const handleSubmitAll = async () => {
    const allToolIds = remainingTools.map((tool: any) => tool.tool_call_id);
    if (allToolIds.length > 0) {
      setIsSubmitting(true);
      try {
        // 将所有剩余工具标记为已提交
        setSubmittedTools(prev => new Set([...prev, ...allToolIds]));
        // 清空当前选择
        setApprovedTools(new Set());
        // 提交所有剩余工具
        onInterruptResume(allToolIds);
      } finally {
        setIsSubmitting(false);
      }
    }
  };
  
  // 拒绝所有工具
  const handleRejectAll = async () => {
    setIsSubmitting(true);
    try {
      // 拒绝所有工具
      onInterruptResume([]);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="border border-orange-300 rounded-lg p-4 bg-gradient-to-r from-orange-50 to-yellow-50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-orange-800">
          批量工具审批 ({pendingTools.length} 个待审批)
        </h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSelectAll(true)}
            className="text-xs"
          >
            全选
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSelectAll(false)}
            className="text-xs"
          >
            取消全选
          </Button>
        </div>
      </div>
      
      {/* 已自动批准的工具 */}
      {approvedToolsFromBackend.length > 0 && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm font-medium text-green-700">
              已自动批准 ({approvedToolsFromBackend.length} 个)
            </span>
          </div>
          <div className="text-xs text-green-600">
            {approvedToolsFromBackend.map((tool: any, index: number) => (
              <span key={index} className="inline-block bg-green-100 px-2 py-1 rounded mr-2 mb-1">
                {tool.name || 'Unknown Tool'}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* 已提交的工具 */}
      {submittedTools.size > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="text-sm font-medium text-blue-700">
              已提交执行 ({submittedTools.size} 个)
            </span>
          </div>
          <div className="text-xs text-blue-600">
            {pendingTools
              .filter((tool: any) => submittedTools.has(tool.tool_call_id))
              .map((tool: any, index: number) => (
                <span key={tool.tool_call_id} className="inline-block bg-blue-100 px-2 py-1 rounded mr-2 mb-1">
                  {tool.tool_name || 'Unknown Tool'}
                </span>
              ))}
          </div>
        </div>
      )}
      
      {/* 待确认的工具列表 */}
      <div className="space-y-3">
        {remainingTools.map((tool: any) => (
          <div key={tool.tool_call_id} className="border border-orange-200 rounded-lg p-3 bg-white">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-orange-800">{tool.tool_name}</span>
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${
                      tool.risk_level === 'high' ? 'border-red-500 text-red-700' :
                      tool.risk_level === 'medium' ? 'border-orange-500 text-orange-700' :
                      'border-yellow-500 text-yellow-700'
                    }`}
                  >
                    {tool.risk_level?.toUpperCase() || 'MEDIUM'} 风险
                  </Badge>
                </div>
                <div className="text-xs text-gray-600 mb-2">
                  <strong>参数:</strong>
                </div>
                <pre className="text-xs bg-gray-100 p-2 rounded border overflow-x-auto">
                  {JSON.stringify(tool.tool_args, null, 2)}
                </pre>
                {tool.reason && (
                  <div className="text-xs text-gray-500 mt-1">
                    <strong>原因:</strong> {tool.reason}
                  </div>
                )}
              </div>
              <div className="ml-4">
                <input
                  type="checkbox"
                  checked={approvedTools.has(tool.tool_call_id)}
                  onChange={(e) => handleToolApprovalChange(tool.tool_call_id, e.target.checked)}
                  className="w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500"
                  disabled={isSubmitting}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* 操作按钮 */}
      <div className="flex justify-between items-center mt-4 pt-4 border-t border-orange-200">
        <div className="text-sm text-gray-600">
          已选择 {approvedTools.size} / {remainingTools.length} 个工具
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRejectAll}
            className="border-gray-400 text-gray-600 hover:bg-gray-100"
            disabled={isSubmitting}
          >
            拒绝全部
          </Button>
          <Button
            onClick={handleSubmitSelected}
            disabled={approvedTools.size === 0 || isSubmitting}
            className="bg-blue-500 hover:bg-blue-600 text-white disabled:opacity-50"
          >
            {isSubmitting ? "提交中..." : `提交选中 (${approvedTools.size} 个)`}
          </Button>
          {remainingTools.length > 0 && (
            <Button
              onClick={handleSubmitAll}
              className="bg-orange-500 hover:bg-orange-600 text-white"
              disabled={isSubmitting}
            >
              {isSubmitting ? "提交中..." : `提交剩余 (${remainingTools.length} 个)`}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

// 单个工具审批组件 props
interface SingleToolApprovalProps {
  interrupt: any;
  onInterruptResume: (approved: boolean) => void;
}

// 单个工具审批组件
const SingleToolApproval: React.FC<SingleToolApprovalProps> = ({ interrupt, onInterruptResume }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const toolInfo = interrupt.value;
  
  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      onInterruptResume(true);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      onInterruptResume(false);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="border border-orange-300 rounded-lg p-4 bg-gradient-to-r from-orange-50 to-yellow-50">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-orange-800 mb-2">
          工具审批
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          {toolInfo.message}
        </p>
      </div>
      
      {/* 工具信息 */}
      <div className="mb-4 p-3 bg-white border border-orange-200 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium text-orange-800">{toolInfo.tool_name}</span>
          <Badge 
            variant="outline" 
            className={`text-xs ${
              toolInfo.risk_level === 'high' ? 'border-red-500 text-red-700' :
              toolInfo.risk_level === 'medium' ? 'border-orange-500 text-orange-700' :
              'border-yellow-500 text-yellow-700'
            }`}
          >
            {toolInfo.risk_level?.toUpperCase() || 'MEDIUM'} 风险
          </Badge>
        </div>
        <div className="text-xs text-gray-600 mb-2">
          <strong>参数:</strong>
        </div>
        <pre className="text-xs bg-gray-100 p-2 rounded border overflow-x-auto">
          {JSON.stringify(toolInfo.tool_args, null, 2)}
        </pre>
      </div>
      
      {/* 操作按钮 */}
      <div className="flex justify-end gap-2">
        <Button
          variant="outline"
          onClick={handleReject}
          className="border-gray-400 text-gray-600 hover:bg-gray-100"
          disabled={isSubmitting}
        >
          拒绝
        </Button>
        <Button
          onClick={handleApprove}
          className="bg-green-500 hover:bg-green-600 text-white"
          disabled={isSubmitting}
        >
          {isSubmitting ? "处理中..." : "批准执行"}
        </Button>
      </div>
    </div>
  );
};

// 诊断聊天视图 props
interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (inputValue: string) => void;
  onCancel: () => void;
  liveActivityEvents: ProcessedEvent[];
  historicalActivities: Record<string, ProcessedEvent[]>;
  interrupt?: any; // 添加interrupt属性
  onInterruptResume?: (approved: boolean | string[]) => void; // 添加interrupt处理函数
}

// 新增：对话轮分组（每轮：用户消息+本轮所有助手消息）
interface DialogRound {
  user: Message;
  assistant: Message[];
}

// 智能体信息类型
interface Agent {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_description: string;
  agent_capabilities: string[];
  agent_status: string;
  agent_enabled: string;
  is_builtin: string;
}

// 自定义欢迎组件接口
interface WelcomeComponentProps {
  agent: Agent | null;
  onSubmit: (message: string) => void;
}

// 诊断聊天视图组件 Props 扩展
interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  onSubmit: (input: string) => void;
  onCancel: () => void;
  liveActivityEvents: ProcessedEvent[];
  historicalActivities: Record<string, ProcessedEvent[]>;
  interrupt?: any;
  onInterruptResume?: (approved: boolean) => void;
  onNewSession?: () => void; // 新增：新建会话回调
  onHistoryToggle?: () => void; // 新增：历史会话抽屉切换回调
  availableModels?: Array<{id: string, name: string, provider: string, type: string}>; // 新增：可用模型列表
  currentModel?: string; // 新增：当前选中的模型
  onModelChange?: (modelType: string) => void; // 新增：模型切换回调
  WelcomeComponent?: React.ComponentType<WelcomeComponentProps>; // 新增：自定义欢迎组件
  agent?: Agent | null; // 新增：智能体信息
}

// 诊断聊天视图组件
function ChatMessages({
  messages,
  isLoading,
  onSubmit,
  onCancel,
  liveActivityEvents,
  historicalActivities,
  interrupt,
  onInterruptResume,
  onNewSession,
  onHistoryToggle,
  availableModels = [],
  currentModel,
  onModelChange,
  WelcomeComponent,
  agent,
}: ChatMessagesProps) {
  const { isDark } = useTheme();
  const [inputValue, setInputValue] = useState<string>("");
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState<boolean>(true);
  const [showScrollButton, setShowScrollButton] = useState<boolean>(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isScrollingRef = useRef<boolean>(false);
  
  // 处理故障诊断开始 - 将诊断消息设置到输入框
  const handleStartDiagnosis = (message: string) => {
    setInputValue(message);
  };
  
  
  const handleCopy = async (text: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 1500);
    } catch {}
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSubmit(inputValue.trim());
      setInputValue("");
    }
  };

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (messagesContainerRef.current) {
      isScrollingRef.current = true;
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      setTimeout(() => {
        isScrollingRef.current = false;
      }, 100);
    }
  }, []);

  // 检查是否已滚动到底部
  const isAtBottom = useCallback(() => {
    if (!messagesContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    return scrollHeight - scrollTop - clientHeight < 10; // 10px 容差
  }, []);

  // 处理手动滚动
  const handleScroll = useCallback(() => {
    if (isScrollingRef.current) return; // 忽略程序化滚动
    
    const atBottom = isAtBottom();
    setIsAutoScrollEnabled(atBottom);
    setShowScrollButton(!atBottom);
  }, [isAtBottom]);

  // 点击滚动按钮
  const handleScrollButtonClick = useCallback(() => {
    setIsAutoScrollEnabled(true);
    setShowScrollButton(false);
    scrollToBottom();
  }, [scrollToBottom]);

  // 监听消息变化，自动滚动
  useEffect(() => {
    if (isAutoScrollEnabled && messages.length > 0) {
      scrollToBottom();
    }
  }, [messages, isAutoScrollEnabled, scrollToBottom]);

  // 监听加载状态变化，自动滚动
  useEffect(() => {
    if (isAutoScrollEnabled && isLoading) {
      scrollToBottom();
    }
  }, [isLoading, isAutoScrollEnabled, scrollToBottom]);

  // 分组：每个人类消息+其后的所有助手消息为一轮
  const dialogRounds: DialogRound[] = [];
  let currentRound: DialogRound | null = null;
  messages.forEach((msg) => {
    if (msg.type === 'human') {
      if (currentRound) dialogRounds.push(currentRound);
      currentRound = { user: msg, assistant: [] };
    } else if (currentRound) {
      currentRound.assistant.push(msg);
    }
  });
  if (currentRound) dialogRounds.push(currentRound);

  return (
    <div className="flex flex-col relative w-full overflow-hidden h-full" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 50%, #1E3A8A 100%)' }}>
      <style>
        {`
          @keyframes buttonSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes buttonPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.02); }
          }
        `}
      </style>
      
      {/* 头部工具栏 - 固定高度 */}
      <div className={cn(
        "flex-shrink-0 flex items-center justify-between px-4 border-b transition-colors duration-200",
        isDark 
          ? "bg-gray-800 border-gray-700" 
          : "bg-white border-gray-200"
      )}
      style={{ paddingTop: '5px', paddingBottom: '5px' }}>
        <div className="flex items-center gap-2">
          <Bot className={cn("h-5 w-5", isDark ? "text-cyan-400" : "text-blue-600")} />
          <span className={cn("font-semibold", isDark ? "text-white" : "text-gray-900")}>
            {agent?.agent_name || agent?.display_name || null}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            onClick={onNewSession}
            variant="outline"
            size="sm"
            className={cn(
              "text-xs px-3 py-1.5 h-7 transition-colors duration-200",
              isDark 
                ? "bg-blue-600/20 hover:bg-blue-600/40 border-blue-500 text-blue-200 hover:text-white" 
                : "bg-blue-50 hover:bg-blue-100 border-blue-300 text-blue-700 hover:text-blue-800"
            )}
          >
            <Plus className="h-3 w-3 mr-1" />
            新建会话
          </Button>
          <Button
            onClick={onHistoryToggle}
            variant="outline"
            size="sm"
            className={cn(
              "text-xs px-3 py-1.5 h-7 transition-colors duration-200",
              isDark 
                ? "bg-purple-600/20 hover:bg-purple-600/40 border-purple-500 text-purple-200 hover:text-white" 
                : "bg-purple-50 hover:bg-purple-100 border-purple-300 text-purple-700 hover:text-purple-800"
            )}
          >
            <History className="h-3 w-3 mr-1" />
            历史会话
          </Button>
        </div>
      </div>
      
      {/* 消息区 - 可滚动的flex-1区域 */}
      <div
        ref={messagesContainerRef}
        className={cn(
          "flex-1 overflow-y-auto overflow-x-hidden pt-1 pb-0 relative transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-b from-gray-900 to-gray-800" 
            : "bg-gradient-to-b from-white to-gray-50"
        )}
        style={{ minHeight: 0, paddingLeft: '5px', paddingRight: '5px' }}
        onScroll={handleScroll}
      >
        <div className="flex flex-col overflow-x-hidden">
          {messages.length === 0 && (
            <div className="w-full">
              {WelcomeComponent ? (
                <WelcomeComponent 
                  agent={agent || null}
                  onSubmit={onSubmit}
                />
              ) : (
                <DiagnosticAgentWelcome 
                  onDiagnose={() => {}} 
                  onContinueChat={() => {}}
                  onStartDiagnosis={handleStartDiagnosis}
                />
              )}
            </div>
          )}
          {dialogRounds.map((round, idx) => (
            <div key={round.user.id || idx}>
              {/* 用户消息 */}
              <div className="flex flex-col items-end mb-6 pl-4">
                <div className="flex items-center justify-end max-w-[90%] w-full" style={{ gap: '5px' }}>
                  <div className="text-white rounded-2xl break-words min-h-7 overflow-x-auto min-w-fit px-4 py-2.5 border border-cyan-400" style={{ backgroundColor: '#1D4ED8' }}>
                    <span className="whitespace-pre-wrap">
                      {typeof round.user.content === "string" ? round.user.content : JSON.stringify(round.user.content)}
                    </span>
                  </div>
                  <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: '#1E3A8A' }}>
                    <User className="h-5 w-5 text-blue-200" />
                  </div>
                </div>
              </div>
              {/* 助手合并输出区域 - 只有当有实际可显示内容时才显示 */}
              {(() => {
                // 检查是否有任何实际要渲染的内容
                let hasRenderableContent = false;
                
                round.assistant.forEach((msg) => {
                  if (msg.type === 'ai') {
                    // 检查AI内容
                    if (msg.content && String(msg.content).trim()) {
                      hasRenderableContent = true;
                    }
                    
                    // 检查工具调用（排除黑名单中的工具）
                    const toolCalls = (msg as any).tool_calls || [];
                    const visibleToolCalls = toolCalls.filter((call: any) => {
                      const toolName = call.name || call.function?.name;
                      return toolName && !HIDDEN_TOOLS.includes(toolName);
                    });
                    if (visibleToolCalls.length > 0) {
                      hasRenderableContent = true;
                    }
                  }
                });
                
                return hasRenderableContent;
              })() && (
                <div className="flex flex-col items-start mb-6 mr-2">
                  <div className="flex items-start w-full" style={{ gap: '5px' }}>
                    <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: '#374151' }}>
                      <Bot className="h-5 w-5 text-blue-200" />
                    </div>
                    <div className="relative flex flex-col rounded-xl p-4 shadow-lg min-w-0 flex-1 overflow-hidden border border-cyan-400" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 100%)' }}>
                      {(() => {
                        // 按时间顺序渲染所有消息和图表
                        const renderItems: React.ReactNode[] = [];
                        
                        round.assistant.forEach((msg, i) => {
                          if (msg.type === 'ai') {
                            const activityForThisMessage = historicalActivities[msg.id!] || [];
                            
                            // AI 消息内容
                            renderItems.push(
                              <div key={msg.id || `ai-${i}`} className="min-w-0 w-full mb-3">
                                {activityForThisMessage.length > 0 && (
                                  <div className="mb-3 border-b border-blue-300 pb-3 text-xs overflow-x-auto">
                                    <ActivityTimeline
                                      processedEvents={activityForThisMessage}
                                      isLoading={false}
                                    />
                                  </div>
                                )}
                                {/* AI 内容 - 过滤空内容 */}
                                {msg.content && String(msg.content).trim() && (
                                  <div className="mb-2 overflow-x-auto min-w-0">
                                    <div className="min-w-fit max-w-none">
                                      <MarkdownRenderer content={typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)} />
                                    </div>
                                  </div>
                                )}
                                
                                {/* 工具调用 */}
                                {(msg as any).tool_calls && (msg as any).tool_calls.length > 0 && (
                                  <div className="overflow-x-auto">
                                    <div className="min-w-fit">
                                      <ToolCalls 
                                        key={msg.id || i} 
                                        message={msg} 
                                        allMessages={messages} 
                                        interrupt={interrupt}
                                        onInterruptResume={onInterruptResume}
                                      />
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                            
                            // 为每个工具调用添加对应的图表
                            const toolCalls = (msg as any).tool_calls || [];
                            toolCalls.forEach((toolCall: any) => {
                              if (toolCall.name === 'get_zabbix_metric_data') {
                                // 查找工具调用的结果
                                const messageIndex = messages.findIndex(m => m.id === msg.id);
                                if (messageIndex !== -1) {
                                  for (let j = messageIndex + 1; j < messages.length; j++) {
                                    const nextMessage = messages[j];
                                    if (nextMessage.type === 'tool' && (nextMessage as any).tool_call_id === toolCall.id) {
                                      const toolResult = nextMessage.content;
                                      if (canRenderChart(toolResult, toolCall.name)) {
                                        renderItems.push(
                                          <div key={`chart-${toolCall.id}`} className="min-w-0 w-full mb-3">
                                            <ZabbixDataRenderer data={toolResult} toolName={toolCall.name} />
                                          </div>
                                        );
                                      }
                                      break;
                                    }
                                  }
                                }
                              }
                            });
                          }
                        });
                        
                        return renderItems;
                      })()}
                      {/* 合并区域只显示最后一条 AI 消息的复制按钮 */}
                      {(() => {
                        // 找到最后一条有内容的 AI 消息
                        const lastAiMsg = [...round.assistant].reverse().find(m => m.type === 'ai' && m.content && String(m.content).trim().length > 0);
                        if (!lastAiMsg) return null;
                        const aiContent = typeof lastAiMsg.content === 'string' ? lastAiMsg.content : JSON.stringify(lastAiMsg.content);
                        return (
                          <Button
                            variant="default"
                            className="cursor-pointer bg-blue-200 border-blue-300 text-blue-800 hover:bg-blue-300 self-end mt-2"
                            onClick={() => handleCopy(aiContent, lastAiMsg.id!)}
                          >
                            {copiedMessageId === lastAiMsg.id ? "已复制" : "复制"}
                            {copiedMessageId === lastAiMsg.id ? <CopyCheck /> : <Copy />}
                          </Button>
                        );
                      })()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {/* 调试信息 */}
          {/* {interrupt && (
            <div className="mb-6 p-4 bg-red-100 border border-red-300 rounded">
              <h3 className="text-red-800 font-bold">调试信息:</h3>
              <pre className="text-xs text-red-700 overflow-auto">
                {JSON.stringify(interrupt, null, 2)}
              </pre>
              <div className="mt-2">
                <strong>batch_mode:</strong> {String(interrupt.value?.batch_mode)}
              </div>
            </div>
          )} */}
          
          
          {/* 加载状态 - 当正在加载且最后一轮没有助手气泡时显示 */}
          {isLoading && (() => {
            const lastRound = dialogRounds[dialogRounds.length - 1];
            if (!lastRound || lastRound.assistant.length === 0) return true;
            
            // 检查最后一轮是否会显示助手气泡（使用与上面气泡相同的逻辑）
            let hasRenderableContent = false;
            lastRound.assistant.forEach((msg) => {
              if (msg.type === 'ai') {
                // 检查AI内容
                if (msg.content && String(msg.content).trim()) {
                  hasRenderableContent = true;
                }
                
                // 检查工具调用（排除黑名单中的工具）
                const toolCalls = (msg as any).tool_calls || [];
                const visibleToolCalls = toolCalls.filter((call: any) => {
                  const toolName = call.name || call.function?.name;
                  return toolName && !HIDDEN_TOOLS.includes(toolName);
                });
                if (visibleToolCalls.length > 0) {
                  hasRenderableContent = true;
                }
              }
            });
            
            return !hasRenderableContent;
          })() && (
            <div className="flex flex-col items-start mb-6 mr-2">
              <div className="flex items-start gap-2 w-full">
                <div className="rounded-full p-2 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: '#374151' }}>
                  <Bot className="h-5 w-5 text-blue-200" />
                </div>
                <div className="flex items-center gap-2 text-gray-300">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  诊断中...
                </div>
              </div>
            </div>
          )}
          

          {/* 保证自动滚动到底部 */}
          <div id="chat-messages-end" />
        </div>
        
      </div>
      
      {/* 输入区 - 固定高度 */}
      <div
        className={cn(
          "flex-shrink-0 border-t-2 transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-r from-gray-800 to-gray-700 border-gray-600" 
            : "bg-gradient-to-r from-white to-gray-50 border-gray-300"
        )}
      >
        <form onSubmit={handleSubmit} style={{ paddingLeft: '5px', paddingRight: '5px', paddingTop: '5px', paddingBottom: '5px' }}>
          {/* 地址栏样式的输入容器 */}
          <div className={cn(
            "flex items-center border-2 rounded-md overflow-hidden shadow-sm transition-all duration-200 focus-within:ring-2 focus-within:ring-cyan-400",
            isDark 
              ? "bg-gray-800 border-gray-600" 
              : "bg-white border-gray-300"
          )}>
            {/* 模型选择器 - 作为地址栏的协议部分 */}
            <div className={cn(
              "flex items-center border-r px-3 py-2.5",
              isDark 
                ? "border-gray-600" 
                : "border-gray-300"
            )}>
              <select
                value={currentModel || ''}
                onChange={(e) => onModelChange?.(e.target.value)}
                className={cn(
                  "bg-transparent text-sm font-medium cursor-pointer focus:outline-none",
                  isDark ? "text-gray-200" : "text-gray-700"
                )}
                disabled={isLoading || !!interrupt || availableModels.length === 0}
                title={availableModels.length > 0 ? `当前模型: ${availableModels.find(m => m.type === currentModel)?.name || '未选择'}` : '正在加载模型...'}
              >
                {availableModels.length > 0 ? (
                  availableModels.map((model) => {
                    // 简化模型名称显示
                    const getShortName = (name: string) => {
                      if (name.includes('deepseek')) return 'DeepSeek';
                      if (name.includes('qwen2.5')) return 'Qwen2.5';
                      if (name.includes('qwen')) return 'Qwen';
                      if (name.includes('gpt')) return 'GPT';
                      if (name.includes('claude')) return 'Claude';
                      return name.substring(0, 10);
                    };
                    
                    return (
                      <option 
                        key={model.id} 
                        value={model.type}
                      >
                        {getShortName(model.name)}
                      </option>
                    );
                  })
                ) : (
                  <option value="" disabled>
                    加载中...
                  </option>
                )}
              </select>
            </div>
            
            {/* 输入框 - 作为地址栏的主体部分 */}
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={interrupt ? "请先确认或取消工具执行..." : (window.innerWidth < 640 ? "请描述问题..." : "请描述您遇到的问题...")}
              className={cn(
                "flex-1 px-3 py-2.5 bg-transparent focus:outline-none text-sm sm:text-base",
                isDark 
                  ? "text-gray-100 placeholder-gray-400" 
                  : "text-gray-900 placeholder-gray-500"
              )}
              disabled={isLoading || !!interrupt}
            />
            
            {/* 发送/取消按钮 - 作为地址栏的操作部分 */}
            <div className={cn(
              "flex items-center border-l px-2",
              isDark 
                ? "border-gray-600" 
                : "border-gray-300"
            )}>
              {(isLoading || interrupt) ? (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onCancel();
                  }}
                  className={cn(
                    "p-2 rounded hover:bg-opacity-80 transition-colors duration-200 flex items-center gap-1",
                    "text-orange-500 hover:bg-orange-100"
                  )}
                  style={{
                    animation: 'buttonPulse 1.5s ease-in-out infinite'
                  }}
                >
                  <span 
                    style={{
                      display: 'inline-block',
                      width: '12px',
                      height: '12px',
                      border: '2px solid currentColor',
                      borderTop: '2px solid transparent',
                      borderRadius: '50%',
                      animation: 'buttonSpin 1s linear infinite'
                    }}
                  />
                  <span className="hidden sm:inline text-sm">取消</span>
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!inputValue.trim()}
                  className={cn(
                    "p-2 rounded transition-colors duration-200 flex items-center gap-1",
                    !inputValue.trim()
                      ? "text-gray-400 cursor-not-allowed"
                      : "text-cyan-500 hover:bg-cyan-50 hover:text-cyan-600"
                  )}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                  </svg>
                  <span className="hidden sm:inline text-sm">发送</span>
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ChatMessages;