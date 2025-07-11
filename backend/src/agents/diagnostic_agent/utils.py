"""
故障诊断代理工具函数模块
包含各种辅助工具函数
"""

import json
import logging
from langchain_core.messages import ToolMessage
from agents.diagnostic_agent.state import SOPStep

logger = logging.getLogger(__name__)

# 排除的SOP工具名常量
EXCLUDED_SOP_TOOLS = {"get_sop_content", "get_sop_detail", "list_sops", "search_sops"}

# 白名单工具：无需审批的安全工具
SAFE_TOOLS_WHITELIST = {
    "get_sop_content", "get_sop_detail", "list_sops", "search_sops",  # SOP相关工具
    "ping", "nslookup", "dig",  # 基础网络查询工具
    "get_system_info", "get_process_info",  # 只读系统信息工具
    "check_port_status", "get_network_status",  # 网络状态查询
    "get_log_info", "search_logs",  # 日志查询工具
    # 可以根据实际需求添加更多安全工具
}


def merge_field(new_value, old_value, field_name=None):
    # 合并信息：优先使用新信息，无新信息时保持原值
    # 如果新值有效且不是待提取，使用新值
    if new_value and new_value != "待提取" and new_value.strip():
        return new_value
    # 如果旧值有效且不是待提取，保持旧值
    elif old_value and old_value != "待提取" and old_value.strip():
        return old_value
    # 特殊处理：如果是时间字段且没有明确时间，使用当前时间
    elif field_name == "fault_time":
        return current_date
    # 否则返回待提取
    else:
        return "待提取"


def find_matching_sop_step(tool_calls, raw_sop_data):
    """
    查找与工具调用匹配的SOP步骤
    
    Args:
        tool_calls: 工具调用列表
        raw_sop_data: 原始SOP数据
        
    Returns:
        SOPStep对象或None
    """
    if not raw_sop_data or not tool_calls:
        return None
        
    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        
        # 跳过SOP加载相关的工具调用
        if tool_name in EXCLUDED_SOP_TOOLS:
            continue
            
        # 在原始SOP步骤中查找匹配的工具和命令
        for sop_step in raw_sop_data.get("steps", []):
            step_tool = sop_step.get("tool", "")
            step_command = sop_step.get("command", "")
            
            # 检查工具名称是否匹配
            if tool_name == step_tool:
                # 如果有命令参数，检查命令是否匹配
                if "command" in tool_args:
                    if tool_args["command"] == step_command:
                        return _create_sop_step_from_data(sop_step)
                else:
                    # 没有具体命令参数，只根据工具匹配
                    return _create_sop_step_from_data(sop_step)
    
    return None


def _create_sop_step_from_data(sop_step_data):
    """
    从SOP步骤数据创建SOPStep对象
    
    Args:
        sop_step_data: SOP步骤原始数据
        
    Returns:
        SOPStep对象
    """
    return SOPStep(
        title=sop_step_data.get("action", ""),
        description=sop_step_data.get("description", ""),
        action=sop_step_data.get("action", ""),
        requires_approval=sop_step_data.get("requires_approval", False),
        status="pending"
    )


def extract_raw_sop_data(messages):
    """
    从消息中提取原始SOP数据
    
    Args:
        messages: 消息列表
        
    Returns:
        原始SOP数据字典或None
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "get_sop_content":
            try:
                result = json.loads(msg.content)
                if result.get("success") and result.get("sop_content"):
                    return result["sop_content"]
            except (json.JSONDecodeError, TypeError):
                continue
    return None


def check_approval_needed(state):
    """
    检查是否需要审批，返回审批信息或None
    
    Returns:
        dict: 包含审批信息的字典，或None表示无需审批
    """
    messages = state.get("messages", [])
    if not messages:
        return None
    
    last_message = messages[-1]
    if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
        return None
    
    tool_calls = last_message.tool_calls
    question_analysis = state.get("question_analysis")
    
    # 获取原始SOP数据
    raw_sop_data = extract_raw_sop_data(messages)
    current_step_info = None
    
    if raw_sop_data:
        # 有SOP数据，查找匹配的SOP步骤
        current_step_info = find_matching_sop_step(tool_calls, raw_sop_data)
    else:
        # 无SOP数据，检查白名单
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            if tool_name not in SAFE_TOOLS_WHITELIST:
                # 创建虚拟审批步骤
                current_step_info = SOPStep(
                    title=f"执行工具: {tool_name}",
                    description=f"由于无法获取SOP数据且工具不在白名单中，为安全起见需要审批",
                    action=f"execute_{tool_name}",
                    requires_approval=True,
                    status="pending"
                )
                break
    
    # 检查是否需要审批
    if current_step_info and current_step_info.requires_approval:
        sop_id = question_analysis.sop_id if question_analysis else "no_sop"
        step_id = f"{sop_id}:{current_step_info.action}"
        
        return {
            "step_info": current_step_info,
            "step_id": step_id,
            "tool_calls": tool_calls,
            "sop_id": sop_id
        }
    
    return None


def is_already_approved(state, approval_info):
    """检查步骤是否已经审批过"""
    approved_steps = state.get("approved_steps", [])
    return approval_info["step_id"] in approved_steps
