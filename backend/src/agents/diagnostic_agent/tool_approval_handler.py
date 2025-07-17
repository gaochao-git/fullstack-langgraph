"""
工具审批处理模块
处理工具调用的权限检查和用户确认流程
"""

import logging
from typing import Dict, Any, List, Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from .state import DiagnosticState
from .tool_permissions import check_tool_permission, get_approval_message

logger = logging.getLogger(__name__)

def tool_approval_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    工具审批节点 - 检查工具调用权限并处理用户确认
    """
    print(f"✅ 执行节点: tool_approval_node")
    print(f"🔍 tool_approval_node - 输入状态: {list(state.keys())}")
    
    messages = state.get("messages", [])
    print(f"🔍 tool_approval_node - 消息数量: {len(messages)}")
    
    if not messages:
        print("❌ 没有消息，无法处理工具审批")
        return {"approval_status": "error", "approval_message": "没有工具调用需要审批"}
    
    last_message = messages[-1]
    
    # 检查是否有工具调用
    if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
        print("❌ 没有工具调用，无需审批")
        return {"approval_status": "no_tools", "approval_message": "没有工具调用需要审批"}
    
    tool_calls = last_message.tool_calls
    print(f"🔍 检测到 {len(tool_calls)} 个工具调用")
    
    # 检查每个工具调用的权限
    approval_results = []
    pending_approvals = []
    approved_tools = []
    
    for i, tool_call in enumerate(tool_calls):
        tool_name = tool_call.get("name", "unknown")
        tool_args = tool_call.get("args", {})
        
        print(f"🔍 检查工具 {i+1}: {tool_name} - {tool_args}")
        
        # 检查权限
        permission_result = check_tool_permission(tool_name, tool_args)
        approval_results.append({
            "tool_call": tool_call,
            "permission_result": permission_result
        })
        
        if permission_result["approved"]:
            approved_tools.append(tool_call)
            print(f"✅ 工具 {tool_name} 已自动批准: {permission_result['reason']}")
        elif permission_result["requires_approval"]:
            pending_approvals.append({
                "tool_call": tool_call,
                "approval_message": get_approval_message(tool_name, tool_args, permission_result["risk_level"])
            })
            print(f"⏳ 工具 {tool_name} 需要用户确认: {permission_result['reason']}")
    
    # 处理结果
    if not pending_approvals:
        # 所有工具都已批准，可以直接执行
        print(f"✅ 所有 {len(approved_tools)} 个工具调用都已自动批准")
        return {
            "approval_status": "all_approved",
            "approved_tool_calls": approved_tools,
            "approval_message": f"所有 {len(approved_tools)} 个工具调用都已通过安全检查，可以执行"
        }
    elif approved_tools:
        # 部分工具需要确认
        approval_message = f"检测到 {len(tool_calls)} 个工具调用：\n"
        approval_message += f"- ✅ {len(approved_tools)} 个已自动批准\n"
        approval_message += f"- ⏳ {len(pending_approvals)} 个需要确认\n\n"
        
        for pending in pending_approvals:
            approval_message += pending["approval_message"] + "\n\n"
        
        print(f"⏳ 部分工具需要确认: {len(approved_tools)} 已批准, {len(pending_approvals)} 待确认")
        return {
            "approval_status": "partial_approval",
            "approved_tool_calls": approved_tools,
            "pending_tool_calls": [p["tool_call"] for p in pending_approvals],
            "approval_message": approval_message
        }
    else:
        # 所有工具都需要确认
        approval_message = f"检测到 {len(pending_approvals)} 个工具调用需要确认：\n\n"
        for pending in pending_approvals:
            approval_message += pending["approval_message"] + "\n\n"
        
        print(f"⏳ 所有工具都需要确认: {len(pending_approvals)} 个")
        return {
            "approval_status": "all_pending",
            "pending_tool_calls": [p["tool_call"] for p in pending_approvals],
            "approval_message": approval_message
        }

def user_confirmation_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    用户确认节点 - 处理用户的确认回复
    """
    print(f"✅ 执行节点: user_confirmation_node")
    print(f"🔍 user_confirmation_node - 输入状态: {list(state.keys())}")
    
    messages = state.get("messages", [])
    approval_status = state.get("approval_status", "")
    pending_tool_calls = state.get("pending_tool_calls", [])
    approved_tool_calls = state.get("approved_tool_calls", [])
    
    print(f"🔍 approval_status: {approval_status}")
    print(f"🔍 pending_tool_calls: {len(pending_tool_calls)}")
    print(f"🔍 approved_tool_calls: {len(approved_tool_calls)}")
    
    if not pending_tool_calls:
        print("❌ 没有待确认的工具调用")
        return {"confirmation_result": "no_pending"}
    
    # 获取用户最新回复
    if not messages:
        print("❌ 没有用户回复")
        return {"confirmation_result": "no_response"}
    
    # 查找最新的用户回复
    user_response = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_response = msg.content.strip().lower()
            break
    
    if not user_response:
        print("❌ 没有找到用户回复")
        return {"confirmation_result": "no_response"}
    
    print(f"🔍 用户回复: {user_response}")
    
    # 解析用户回复
    if user_response in ["确认", "y", "yes", "同意", "执行", "ok"]:
        # 用户确认，将待确认的工具加入已批准列表
        all_approved = approved_tool_calls + pending_tool_calls
        print(f"✅ 用户确认执行，总共批准 {len(all_approved)} 个工具调用")
        
        return {
            "confirmation_result": "approved",
            "approved_tool_calls": all_approved,
            "pending_tool_calls": [],
            "approval_status": "all_approved"
        }
    
    elif user_response in ["拒绝", "n", "no", "取消", "不执行", "cancel"]:
        # 用户拒绝
        print(f"❌ 用户拒绝执行工具调用")
        
        response_message = "用户已拒绝执行相关工具调用。"
        if approved_tool_calls:
            response_message += f"但仍可执行 {len(approved_tool_calls)} 个已批准的安全工具。"
        
        return {
            "confirmation_result": "rejected",
            "approved_tool_calls": approved_tool_calls,  # 只保留已批准的
            "pending_tool_calls": [],
            "approval_status": "partial_approved" if approved_tool_calls else "all_rejected",
            "rejection_message": response_message
        }
    
    elif user_response in ["详情", "details", "detail", "说明", "info"]:
        # 用户请求详情
        detail_message = "**工具调用详细信息**：\n\n"
        
        for i, tool_call in enumerate(pending_tool_calls):
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            
            detail_message += f"**工具 {i+1}**: {tool_name}\n"
            detail_message += f"**参数**: {tool_args}\n"
            detail_message += f"**说明**: {_get_tool_description(tool_name)}\n\n"
        
        detail_message += "请回复 `确认` 或 `拒绝`"
        
        print(f"ℹ️ 用户请求详情")
        return {
            "confirmation_result": "request_details",
            "detail_message": detail_message
        }
    
    else:
        # 无法识别的回复
        print(f"❓ 无法识别用户回复: {user_response}")
        help_message = "无法识别您的回复。请回复：\n"
        help_message += "- `确认` 或 `y` - 同意执行\n"
        help_message += "- `拒绝` 或 `n` - 拒绝执行\n"
        help_message += "- `详情` - 查看详细说明"
        
        return {
            "confirmation_result": "invalid_response",
            "help_message": help_message
        }

def _get_tool_description(tool_name: str) -> str:
    """获取工具的描述信息"""
    descriptions = {
        "get_system_info": "获取系统基本信息（CPU、内存、磁盘等）",
        "analyze_processes": "分析系统进程状态",
        "check_service_status": "检查系统服务状态",
        "analyze_system_logs": "分析系统日志",
        "execute_system_command": "执行系统命令",
        "execute_mysql_query": "执行MySQL查询",
        "search_elasticsearch": "搜索Elasticsearch数据",
        "get_zabbix_alerts": "获取Zabbix告警信息",
    }
    return descriptions.get(tool_name, f"执行 {tool_name} 工具")

def check_approval_routing(state: DiagnosticState, config: RunnableConfig) -> Literal["execute_approved_tools", "wait_user_confirmation", "handle_confirmation", "END"]:
    """
    检查审批状态并路由到相应节点
    """
    print(f"✅ 执行路由函数: check_approval_routing")
    
    approval_status = state.get("approval_status", "")
    confirmation_result = state.get("confirmation_result", "")
    
    print(f"🔍 approval_status: {approval_status}")
    print(f"🔍 confirmation_result: {confirmation_result}")
    
    # 处理确认结果
    if confirmation_result:
        if confirmation_result == "approved":
            print("✅ 用户确认，执行工具")
            return "execute_approved_tools"
        elif confirmation_result in ["rejected", "partial_approved"]:
            print("❌ 用户拒绝或部分拒绝")
            approved_tools = state.get("approved_tool_calls", [])
            if approved_tools:
                print(f"✅ 仍有 {len(approved_tools)} 个已批准工具可执行")
                return "execute_approved_tools"
            else:
                print("❌ 没有可执行的工具，结束")
                return "END"
        elif confirmation_result in ["request_details", "invalid_response"]:
            print("ℹ️ 需要继续等待用户确认")
            return "wait_user_confirmation"
        else:
            print("❓ 未知确认结果，等待用户确认")
            return "wait_user_confirmation"
    
    # 处理初始审批状态
    if approval_status == "all_approved":
        print("✅ 所有工具都已批准，直接执行")
        return "execute_approved_tools"
    elif approval_status in ["partial_approval", "all_pending"]:
        print("⏳ 需要等待用户确认")
        return "wait_user_confirmation"
    elif approval_status == "no_tools":
        print("❌ 没有工具调用，结束")
        return "END"
    else:
        print("❓ 未知审批状态，结束")
        return "END"

# 导出主要函数
__all__ = [
    "tool_approval_node", 
    "user_confirmation_node",
    "check_approval_routing"
]