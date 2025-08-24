import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Loader2, Copy, CopyCheck, ChevronDown, ChevronRight, Wrench, User, Bot, ArrowDown, Plus, History, Send, FileText, Eye, Download, RefreshCw, Image, FileSpreadsheet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState, ReactNode, useEffect, useRef, useCallback } from "react";
import { cn } from "@/utils/lib-utils";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import DiagnosticAgentWelcome from "./DiagnosticAgentWelcome";
import ZabbixDataRenderer, { canRenderChart } from "./ZabbixDataRenderer";
import { useTheme } from "@/hooks/ThemeContext";
import { theme } from "antd";
import { FileUploadManager, FileListDisplay, fileUploadUtils } from "./FileUploadManager";
import { FilePreviewModal } from "./FilePreviewModal";
import { fileApi } from "@/services/fileApi";
import { App } from "antd";
import { exportToWordWithImages } from "@/services/documentExportApi";

// 黑名单：不显示这些工具调用，便于用户发现和维护
const HIDDEN_TOOLS = [
  'QuestionInfoExtraction',      // 问题信息提取
  'DiagnosisReflectionOutput',   // 诊断反思输出
  'IntentAnalysisOutput'         // 意图分析输出
];

// 支持预览的文件类型
const PREVIEWABLE_EXTENSIONS = ['.txt', '.md', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg', '.pdf'];

// 图片文件扩展名
const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'];

// 统一的文件预览判断函数
const isFilePreviewable = (fileName: string): boolean => {
  const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
  return PREVIEWABLE_EXTENSIONS.includes(ext);
};

// 判断文件是否是图片
const isImageFile = (fileName: string): boolean => {
  const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
  return IMAGE_EXTENSIONS.includes(ext);
};

const isExcelFile = (fileName: string): boolean => {
  const ext = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
  return ['.xlsx', '.xls'].includes(ext);
};

// 诊断消息中的事件类型
export interface ProcessedEvent {
  title: string;
  data: any;
}

// 文档引用信息
interface DocumentReference {
  fileName: string;
  content: string;
  fileId?: string;
}

// 解析系统消息中的文档引用
function parseDocumentReferences(content: string): { 
  documents: DocumentReference[]; 
  hasDocuments: boolean;
} {
  const docPattern = /【文档：([^】]+)】\n([^【]*)/g;
  const documents: DocumentReference[] = [];
  let match;
  
  while ((match = docPattern.exec(content)) !== null) {
    documents.push({
      fileName: match[1],
      content: match[2].trim()
    });
  }
  
  return {
    documents,
    hasDocuments: documents.length > 0
  };
}

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
  const { token } = theme.useToken();
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
    <div 
      className="border rounded-xl mb-1 shadow-sm transition-all duration-300 overflow-hidden"
      style={{
        borderColor: isPending ? token.colorWarningBorder : token.colorPrimaryBorder,
        backgroundColor: isPending ? token.colorWarningBg : token.colorPrimaryBg,
        backgroundImage: isPending 
          ? `linear-gradient(135deg, ${token.colorWarningBg} 0%, ${token.colorWarningBgHover} 100%)`
          : `linear-gradient(135deg, ${token.colorPrimaryBg} 0%, ${token.colorPrimaryBgHover} 100%)`
      }}
    >
      {/* 工具调用头部（合并描述和折叠按钮） */}
      <div 
        className="flex items-center justify-between px-3 py-1.5 cursor-pointer transition-all duration-200"
        style={{
          ':hover': {
            backgroundColor: isPending ? token.colorWarningBgHover : token.colorPrimaryBgHover
          }
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = isPending ? token.colorWarningBgHover : token.colorPrimaryBgHover;
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Wrench className="h-5 w-5" style={{ color: isPending ? token.colorWarning : token.colorPrimary }} />
          <span className="font-mono text-sm font-semibold truncate" style={{ color: token.colorText }}>{toolName}</span>
          <span className="ml-2 text-xs font-bold flex-shrink-0" style={{ color: token.colorTextSecondary }}>工具调用（{toolCount || 1}）</span>
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
          <ChevronDown className="h-4 w-4" style={{ color: token.colorTextSecondary }} />
        ) : (
          <ChevronRight className="h-4 w-4" style={{ color: token.colorTextSecondary }} />
        )}
      </div>
      
      {/* 展开的内容 */}
      {isExpanded && (
        <div 
          className="border-t p-3 space-y-3 overflow-x-auto"
          style={{ borderTopColor: token.colorBorderSecondary }}
        >
          {/* 参数 */}
          <div className="min-w-fit max-w-full">
            <h4 className="text-sm font-bold mb-2" style={{ color: token.colorTextHeading }}>参数:</h4>
            <pre 
              className="p-3 rounded-lg text-xs overflow-x-auto whitespace-pre max-w-full border"
              style={{ 
                backgroundColor: token.colorFillTertiary,
                color: token.colorText,
                borderColor: token.colorBorder
              }}
            >
              {JSON.stringify(toolArgs, null, 2)}
            </pre>
          </div>
          
          
          
          {/* 输出结果 */}
          {toolResultContent && (
            <div className="min-w-fit max-w-full">
              <h4 className="text-sm font-bold mb-2" style={{ color: token.colorTextHeading }}>输出:</h4>
              
              {/* 工具展开后只显示原始JSON数据 */}
              <pre 
                className="p-3 rounded-lg text-xs overflow-x-auto max-h-48 overflow-y-auto whitespace-pre max-w-full border"
                style={{ 
                  backgroundColor: token.colorFillTertiary,
                  color: token.colorText,
                  borderColor: token.colorBorder
                }}
              >
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
  onSubmit: (input: string, fileIds?: string[]) => void;
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
  threadFileIds?: string[]; // 新增：会话关联的文件ID列表
}

// 系统消息组件 - 用于显示文档引用
interface SystemMessageProps {
  message: Message;
  fileIds?: string[];
}

const SystemMessage: React.FC<SystemMessageProps> = ({ message, fileIds }) => {
  const { isDark } = useTheme();
  const { token } = theme.useToken();
  const [previewFile, setPreviewFile] = useState<{fileId: string; fileName: string; fileType: string} | null>(null);
  
  if (message.type !== 'system' || !message.content) return null;
  
  const content = typeof message.content === 'string' ? message.content : JSON.stringify(message.content);
  const { documents, hasDocuments } = parseDocumentReferences(content);
  
  // 如果不是文档引用的系统消息，不显示
  if (!hasDocuments || !content.includes('请参考以下文档内容回答用户问题')) {
    return null;
  }
  
  // 获取文件扩展名
  const getFileExtension = (fileName: string): string => {
    const lastDot = fileName.lastIndexOf('.');
    return lastDot > -1 ? fileName.substring(lastDot) : '';
  };
  
  
  return (
    <>
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          {documents.map((doc, index) => (
            <div 
              key={index}
              className={cn(
                "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                isDark ? "bg-gray-800 text-gray-200" : "bg-gray-100 text-gray-700"
              )}
            >
              {isImageFile(doc.fileName) ? (
                <Image className="h-4 w-4" style={{ color: token.colorTextSecondary }} />
              ) : isExcelFile(doc.fileName) ? (
                <FileSpreadsheet className="h-4 w-4" style={{ color: token.colorTextSecondary }} />
              ) : (
                <FileText className="h-4 w-4" style={{ color: token.colorTextSecondary }} />
              )}
              <span>{doc.fileName}</span>
              {isFilePreviewable(doc.fileName) && fileIds && fileIds[index] && (
                <button
                  type="button"
                  onClick={() => setPreviewFile({
                    fileId: fileIds[index],
                    fileName: doc.fileName,
                    fileType: getFileExtension(doc.fileName)
                  })}
                  className={cn(
                    "ml-1 p-0.5 rounded hover:opacity-70 transition-opacity",
                    isDark ? "text-gray-400 hover:text-gray-200" : "text-gray-500 hover:text-gray-700"
                  )}
                  title="预览"
                >
                  <Eye className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {previewFile && (
        <FilePreviewModal
          visible={!!previewFile}
          fileId={previewFile.fileId}
          fileName={previewFile.fileName}
          fileType={previewFile.fileType}
          onClose={() => setPreviewFile(null)}
        />
      )}
    </>
  );
};

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
  threadFileIds = [],
}: ChatMessagesProps) {
  const { isDark } = useTheme();
  const { token } = theme.useToken();
  const { message } = App.useApp();
  const [inputValue, setInputValue] = useState<string>("");
  const [uploadingClipboard, setUploadingClipboard] = useState<boolean>(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [downloadingMessageId, setDownloadingMessageId] = useState<string | null>(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState<boolean>(true);
  const [showScrollButton, setShowScrollButton] = useState<boolean>(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const isScrollingRef = useRef<boolean>(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<Array<{ file: File; fileId: string; status: 'uploading' | 'success' | 'failed' }>>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [currentFileIds, setCurrentFileIds] = useState<string[]>([]);
  const [previewFile, setPreviewFile] = useState<{fileId: string; fileName: string; fileType: string} | null>(null);
  
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 获取成功上传的文件ID
    const successFileIds = uploadedFiles
      .filter(f => f.status === 'success' && f.fileId)
      .map(f => f.fileId);
    
    if (inputValue.trim() || successFileIds.length > 0) {
      // 存储当前文件IDs以便在系统消息中使用
      if (successFileIds.length > 0) {
        setCurrentFileIds(successFileIds);
      }
      
      // 提交消息和文件ID
      onSubmit(inputValue.trim(), successFileIds.length > 0 ? successFileIds : undefined);
      setInputValue("");
      setUploadedFiles([]); // 清空已上传文件
    }
  };

  // 处理粘贴事件，支持文件粘贴
  const handlePaste = async (e: React.ClipboardEvent<HTMLInputElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    const files: File[] = [];
    
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      // 检查是否是文件类型
      if (item.kind === 'file') {
        e.preventDefault(); // 阻止默认粘贴行为
        
        const blob = item.getAsFile();
        if (!blob) continue;

        // 根据类型生成合适的文件名
        let fileName = `paste-${Date.now()}`;
        if (item.type.startsWith('image/')) {
          fileName += '.png';
        } else if (item.type === 'text/plain') {
          fileName += '.txt';
        } else if (item.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
          fileName += '.docx';
        } else if (item.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
          fileName += '.xlsx';
        } else if (item.type === 'application/pdf') {
          fileName += '.pdf';
        } else {
          // 尝试从blob中获取扩展名或使用默认
          const ext = blob.name?.split('.').pop();
          fileName += ext ? `.${ext}` : '.dat';
        }

        // 创建File对象
        const file = new File([blob], fileName, { type: blob.type });
        files.push(file);
      }
    }
    
    if (files.length > 0) {
      // 使用现有的文件处理逻辑
      await handleFilesSelect(files);
      message.success(`已粘贴 ${files.length} 个文件`);
    }
  };

  // 拖放状态
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);

  // 处理拖入事件
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  // 处理拖动悬停事件
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  // 处理拖离事件
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  // 处理拖放事件
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      // 验证文件类型
      const validFiles = files.filter(file => {
        // 使用 fileUploadUtils 中的验证函数
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        return fileUploadUtils.isValidFileType(file);
      });

      if (validFiles.length > 0) {
        await handleFilesSelect(validFiles);
        message.success(`已拖入 ${validFiles.length} 个文件`);
      }

      if (validFiles.length < files.length) {
        message.warning(`${files.length - validFiles.length} 个文件类型不支持`);
      }
    }
  };

  // 处理文件选择 - 选择后立即上传
  const handleFilesSelect = async (files: File[]) => {
    // 为每个文件创建上传状态
    const newUploadedFiles = files.map(file => ({
      file,
      fileId: '',
      status: 'uploading' as const
    }));
    
    setUploadedFiles(prev => [...prev, ...newUploadedFiles]);
    setIsUploading(true);
    
    // 并行上传所有文件
    const uploadPromises = files.map(async (file, index) => {
      const currentIndex = uploadedFiles.length + index;
      try {
        const result = await fileApi.uploadFile(file);
        
        // 等待文件处理完成
        await fileApi.waitForFileReady(result.file_id);
        
        // 更新状态为成功
        setUploadedFiles(prev => {
          const updated = [...prev];
          if (updated[currentIndex]) {
            updated[currentIndex] = {
              ...updated[currentIndex],
              fileId: result.file_id,
              status: 'success'
            };
          }
          return updated;
        });
        
        return result.file_id;
      } catch (error) {
        // 更新状态为失败
        setUploadedFiles(prev => {
          const updated = [...prev];
          if (updated[currentIndex]) {
            updated[currentIndex] = {
              ...updated[currentIndex],
              status: 'failed'
            };
          }
          return updated;
        });
        
        const errorMsg = error instanceof Error ? error.message : '未知错误';
        message.error(`文件 ${file.name} 上传失败: ${errorMsg}`);
        throw error;
      }
    });
    
    try {
      const results = await Promise.allSettled(uploadPromises);
      
      // 统计成功和失败的数量
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      const failedCount = results.filter(r => r.status === 'rejected').length;
      
      if (successCount > 0 && failedCount === 0) {
        message.success(`成功上传 ${successCount} 个文件`);
      } else if (successCount > 0 && failedCount > 0) {
        message.warning(`${successCount} 个文件上传成功，${failedCount} 个文件上传失败`);
      } else if (failedCount > 0 && successCount === 0) {
        message.error(`所有文件上传失败`);
      }
    } finally {
      setIsUploading(false);
    }
  };

  // 移除选中的文件
  const handleRemoveFile = (index: number) => {
    setUploadedFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
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
    <div 
      className="flex flex-col relative w-full overflow-hidden h-full" 
      style={{ backgroundColor: token.colorBgContainer }}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* 全屏拖放提示 */}
      {isDragging && (
        <div className={cn(
          "absolute inset-0 flex items-center justify-center z-50 pointer-events-none",
          isDark ? "bg-gray-900/90" : "bg-white/90"
        )}>
          <div className={cn(
            "flex flex-col items-center gap-4 p-8 rounded-lg",
            isDark ? "bg-gray-800 shadow-2xl" : "bg-white shadow-2xl"
          )}>
            <div className={cn(
              "w-16 h-16 rounded-full flex items-center justify-center",
              isDark ? "bg-cyan-900" : "bg-cyan-100"
            )}>
              <Image className={cn(
                "w-8 h-8",
                isDark ? "text-cyan-400" : "text-cyan-600"
              )} />
            </div>
            <div className={cn(
              "text-xl font-medium",
              isDark ? "text-cyan-400" : "text-cyan-600"
            )}>
              释放以上传文件
            </div>
            <div className={cn(
              "text-sm",
              isDark ? "text-gray-400" : "text-gray-600"
            )}>
              支持图片、文档、表格等多种格式
            </div>
          </div>
        </div>
      )}
      
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
          {dialogRounds.map((round, idx) => {
            // 查找这一轮之前的系统消息（文档引用）
            const roundIndex = messages.findIndex(m => m.id === round.user.id);
            let systemMessage = null;
            let systemFileIds = null;
            
            if (roundIndex > 0) {
              // 检查前一条消息是否是系统消息
              const prevMessage = messages[roundIndex - 1];
              if (prevMessage.type === 'system' && prevMessage.content) {
                const content = typeof prevMessage.content === 'string' ? prevMessage.content : JSON.stringify(prevMessage.content);
                if (content.includes('请参考以下文档内容回答用户问题')) {
                  systemMessage = prevMessage;
                  // 使用会话关联的文件IDs（优先使用线程文件ID，如果没有则使用当前文件ID）
                  systemFileIds = threadFileIds.length > 0 ? threadFileIds : currentFileIds;
                }
              }
            }
            
            return (
              <div key={round.user.id || idx}>
                {/* 用户消息 */}
                <div className="flex flex-col items-end mb-6 pl-4">
                  <div className="flex items-center justify-end max-w-[90%] w-full" style={{ gap: '5px' }}>
                    <div className="flex flex-col items-end gap-2">
                      {/* 文档附件 - 显示在消息上方 */}
                      {systemMessage && (() => {
                        const content = typeof systemMessage.content === 'string' ? systemMessage.content : JSON.stringify(systemMessage.content);
                        const { documents, hasDocuments } = parseDocumentReferences(content);
                        if (hasDocuments) {
                          return (
                            <div className="flex flex-wrap gap-2 justify-end">
                              {documents.map((doc, index) => (
                                <div 
                                  key={index}
                                  className={cn(
                                    "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm",
                                    isDark ? "bg-gray-700 text-gray-200" : "bg-gray-100 text-gray-700"
                                  )}
                                >
                                  {isImageFile(doc.fileName) ? (
                                    <Image className="h-4 w-4" />
                                  ) : isExcelFile(doc.fileName) ? (
                                    <FileSpreadsheet className="h-4 w-4" />
                                  ) : (
                                    <FileText className="h-4 w-4" />
                                  )}
                                  <span>{doc.fileName}</span>
                                  {(() => {
                                    const ext = doc.fileName.substring(doc.fileName.lastIndexOf('.')).toLowerCase();
                                    return isFilePreviewable(doc.fileName) && systemFileIds && systemFileIds[index] && (
                                      <button
                                        type="button"
                                        onClick={() => setPreviewFile({
                                          fileId: systemFileIds[index],
                                          fileName: doc.fileName,
                                          fileType: ext
                                        })}
                                        className={cn(
                                          "ml-1 p-0.5 rounded hover:opacity-70 transition-opacity",
                                          isDark ? "text-gray-400 hover:text-gray-200" : "text-gray-500 hover:text-gray-700"
                                        )}
                                        title="预览"
                                      >
                                        <Eye className="h-3.5 w-3.5" />
                                      </button>
                                    );
                                  })()}
                                </div>
                              ))}
                            </div>
                          );
                        }
                        return null;
                      })()}
                      
                      {/* 用户消息内容 */}
                      <div 
                        className="rounded-2xl break-words min-h-7 overflow-x-auto min-w-fit px-4 py-2.5 border"
                        style={{ 
                          backgroundColor: token.colorPrimary,
                          borderColor: token.colorPrimaryBorder,
                          color: token.colorTextLightSolid
                        }}
                      >
                        <span className="whitespace-pre-wrap">
                          {typeof round.user.content === "string" ? round.user.content : JSON.stringify(round.user.content)}
                        </span>
                      </div>
                    </div>
                    <div 
                      className="rounded-full p-2 flex-shrink-0 flex items-center justify-center"
                      style={{ backgroundColor: token.colorFillSecondary }}
                    >
                      <User className="h-5 w-5" style={{ color: token.colorPrimary }} />
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
                    <div 
                      className="rounded-full p-2 flex-shrink-0 flex items-center justify-center"
                      style={{ backgroundColor: token.colorFillSecondary }}
                    >
                      <Bot className="h-5 w-5" style={{ color: token.colorPrimary }} />
                    </div>
                    <div 
                      className="relative flex flex-col rounded-xl p-4 shadow-lg min-w-0 flex-1 overflow-hidden border"
                      style={{ 
                        backgroundColor: token.colorBgContainer,
                        borderColor: token.colorBorder
                      }}
                    >
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
                      {/* 合并区域只显示最后一条 AI 消息的操作按钮 */}
                    </div>
                  </div>
                  {/* 操作按钮 - 放在左下角 */}
                  {(() => {
                    // 找到最后一条有内容的 AI 消息
                    const lastAiMsg = [...round.assistant].reverse().find(m => m.type === 'ai' && m.content && String(m.content).trim().length > 0);
                    if (!lastAiMsg) return null;
                    const aiContent = typeof lastAiMsg.content === 'string' ? lastAiMsg.content : JSON.stringify(lastAiMsg.content);
                    return (
                      <div className="flex gap-1 mt-2 ml-12">
                        <Button
                          variant="ghost"
                          size="small"
                          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
                          onClick={() => handleCopy(aiContent, lastAiMsg.id!)}
                          title={copiedMessageId === lastAiMsg.id ? "已复制" : "复制"}
                        >
                          {copiedMessageId === lastAiMsg.id ? <CopyCheck className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                        </Button>
                        <Button
                          variant="ghost"
                          size="small"
                          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
                          onClick={async () => {
                            try {
                              setDownloadingMessageId(lastAiMsg.id!);
                              // 使用新的导出函数，传入isDark参数以匹配主题
                              await exportToWordWithImages(aiContent, `对话导出_${new Date().toLocaleDateString()}`, isDark);
                            } catch (error) {
                              // 错误已在 exportToWordWithImages 中处理
                            } finally {
                              setDownloadingMessageId(null);
                            }
                          }}
                          disabled={downloadingMessageId === lastAiMsg.id}
                          title="下载Word"
                        >
                          {downloadingMessageId === lastAiMsg.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Download className="h-3.5 w-3.5" />
                          )}
                        </Button>
                        {idx === dialogRounds.length - 1 && (
                          <Button
                            variant="ghost"
                            size="small"
                            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
                            onClick={() => {
                              // 重新生成回复 - 使用当前轮次的用户消息
                              if (round.user && round.user.content) {
                                const content = typeof round.user.content === 'string' 
                                  ? round.user.content 
                                  : JSON.stringify(round.user.content);
                                // 直接调用 onSubmit 重新生成
                                onSubmit(content);
                              }
                            }}
                            disabled={isLoading}
                            title="重新生成"
                          >
                            <RefreshCw className={cn("h-3.5 w-3.5", isLoading && "animate-spin")} />
                          </Button>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}
              </div>
            );
          })}
          
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
                <div 
                  className="rounded-full p-2 flex-shrink-0 flex items-center justify-center"
                  style={{ backgroundColor: token.colorFillSecondary }}
                >
                  <Bot className="h-5 w-5" style={{ color: token.colorPrimary }} />
                </div>
                <div className="flex items-center gap-2" style={{ color: token.colorTextDescription }}>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  思考中...
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
          "relative flex-shrink-0 border-t-2 transition-colors duration-200",
          isDark 
            ? "bg-gradient-to-r from-gray-800 to-gray-700 border-gray-600" 
            : "bg-gradient-to-r from-white to-gray-50 border-gray-300"
        )}
      >
        
        {/* 已上传文件显示区域 */}
        <FileListDisplay 
          files={uploadedFiles}
          onRemove={handleRemoveFile}
          isDark={isDark}
        />
        
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
              "flex items-center border-r px-1 sm:px-3 py-2 sm:py-2.5 flex-shrink-0",
              isDark 
                ? "border-gray-600" 
                : "border-gray-300"
            )}>
              <select
                value={currentModel || ''}
                onChange={(e) => onModelChange?.(e.target.value)}
                className={cn(
                  "bg-transparent text-xs sm:text-sm font-medium cursor-pointer focus:outline-none",
                  "w-16 sm:w-[120px] truncate", // 手机端更窄的宽度
                  isDark ? "text-gray-200" : "text-gray-700"
                )}
                disabled={isLoading || !!interrupt || availableModels.length === 0}
                title={availableModels.length > 0 ? `当前模型: ${availableModels.find(m => m.type === currentModel)?.name || '未选择'}` : '正在加载模型...'}
              >
                {availableModels.length > 0 ? (
                  availableModels.map((model) => {
                    return (
                      <option 
                        key={model.id} 
                        value={model.type}
                        title={model.name} // 添加 title 以显示完整名称
                      >
                        {model.name}
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
              onPaste={handlePaste}
              placeholder={interrupt ? "请先确认或取消..." : "请描述问题..."}
              className={cn(
                "flex-1 min-w-0 px-2 sm:px-3 py-2 sm:py-2.5 bg-transparent focus:outline-none text-sm sm:text-base",
                isDark 
                  ? "text-gray-100 placeholder-gray-400" 
                  : "text-gray-900 placeholder-gray-500"
              )}
              disabled={false}
            />
            
            {/* 操作按钮区域 - 包含上传文件和发送按钮 */}
            <div className={cn(
              "flex items-center border-l flex-shrink-0",
              isDark 
                ? "border-gray-600" 
                : "border-gray-300"
            )}>
              {/* 上传文件按钮 */}
              {!(isLoading || interrupt) && (
                <FileUploadManager
                  selectedFiles={uploadedFiles.map(f => f.file)}
                  onFilesSelect={handleFilesSelect}
                  onFileRemove={handleRemoveFile}
                  isDark={isDark}
                  disabled={isLoading || !!interrupt}
                />
              )}
              
              {/* 分隔线 - 手机端隐藏 */}
              {!(isLoading || interrupt) && (
                <div className={cn(
                  "hidden sm:block h-6 w-px mx-1",
                  isDark ? "bg-gray-600" : "bg-gray-300"
                )} />
              )}
              
              {/* 发送/取消按钮 */}
              {(isLoading || interrupt) ? (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onCancel();
                  }}
                  className={cn(
                    "p-2 rounded hover:bg-opacity-80 transition-colors duration-200 flex items-center gap-1 mx-1",
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
                  disabled={(!inputValue.trim() && selectedFiles.length === 0) || isLoading || isUploading || !!interrupt}
                  className={cn(
                    "p-2 rounded transition-colors duration-200 mr-1",
                    ((!inputValue.trim() && selectedFiles.length === 0) || isLoading || isUploading || !!interrupt)
                      ? "text-gray-400 cursor-not-allowed"
                      : "text-cyan-500 hover:bg-cyan-50 hover:text-cyan-600"
                  )}
                  title={
                    isLoading ? "等待AI响应中..." : 
                    isUploading ? "文件上传中..." : 
                    interrupt ? "请先处理人工确认..." :
                    (!inputValue.trim() && selectedFiles.length === 0) ? "请输入消息或选择文件" :
                    "发送消息"
                  }
                >
                  <Send className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
      
      {/* 文件预览模态框 */}
      {previewFile && (
        <FilePreviewModal
          visible={!!previewFile}
          fileId={previewFile.fileId}
          fileName={previewFile.fileName}
          fileType={previewFile.fileType}
          onClose={() => setPreviewFile(null)}
        />
      )}
    </div>
  );
}

export default ChatMessages;