"""
使用官方人工干预机制实现选择性工具审批
"""

from typing import Callable, List
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt 
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt

from .tools import all_tools
from .tool_permissions import is_tool_requiring_approval, get_tool_config


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review.""" 
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
        }

    @create_tool(  
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    def call_tool_with_interrupt(**tool_input):
        # 获取工具配置信息
        tool_config = get_tool_config(tool.name)
        
        # 构建前端期望的中断数据格式
        interrupt_info = {
            "suggestion_type": "tool_approval",
            "tool_name": tool.name,
            "tool_args": tool_input,
            "tool_description": tool_config.get("description", tool.description),
            "message": f"需要确认执行工具: {tool.name}",
            "risk_level": tool_config.get("risk_level", "medium"),
            "category": tool_config.get("category", "unknown")
        }
        
        # 触发中断，等待用户审批
        approval_result = interrupt(interrupt_info)
        
        print(f"🔍 收到审批结果: {approval_result}")
        print(f"🔍 审批结果类型: {type(approval_result)}")
        
        # 解析前端传递的审批数据
        if isinstance(approval_result, dict):
            # 前端传递了详细的审批信息: {"工具名": xx, "工具参数": xxx, "审批结果": xxxx}
            approved_tool_name = approval_result.get("工具名") or approval_result.get("tool_name")
            approved_tool_args = approval_result.get("工具参数") or approval_result.get("tool_args")
            user_approved = approval_result.get("审批结果") or approval_result.get("approved")
            
            print(f"🔍 解析审批信息:")
            print(f"  - 审批工具: {approved_tool_name}")
            print(f"  - 审批参数: {approved_tool_args}")
            print(f"  - 审批结果: {user_approved}")
            
            # 验证工具名称和参数是否匹配
            if (approved_tool_name == tool.name and approved_tool_args == tool_input):
                print(f"✅ 审批验证通过: {tool.name}")
                if user_approved:
                    return tool.invoke(tool_input)
                else:
                    return f"工具 {tool.name} 执行被用户拒绝"
            else:
                error_msg = f"❌ 审批验证失败: 请求工具 {tool.name}，审批工具 {approved_tool_name}"
                print(error_msg)
                return error_msg
        else:
            # 简单的布尔值审批
            user_approved = bool(approval_result)
            print(f"🔍 简单审批模式: {user_approved}")
            
            if user_approved:
                return tool.invoke(tool_input)
            else:
                return f"工具 {tool.name} 执行被用户拒绝"

    return call_tool_with_interrupt


def get_tools_with_selective_approval() -> List[BaseTool]:
    """
    获取选择性审批的工具列表
    
    Returns:
        工具列表，其中需要审批的工具添加了人工干预包装器
    """
    wrapped_tools = []
    
    approval_count = 0
    
    for tool in all_tools:
        if is_tool_requiring_approval(tool.name):
            # 需要审批的工具 - 添加人工干预包装器
            wrapped_tool = add_human_in_the_loop(tool)
            wrapped_tools.append(wrapped_tool)
            approval_count += 1
            tool_config = get_tool_config(tool.name)
            print(f"🔒 工具 {tool.name} 已添加审批机制 (风险等级: {tool_config.get('risk_level', 'medium')})")
        else:
            # 安全工具 - 直接使用，无需审批
            wrapped_tools.append(tool)
            tool_config = get_tool_config(tool.name)
            print(f"✅ 工具 {tool.name} 为安全工具，直接执行 (类别: {tool_config.get('category', 'unknown')})")
    
    print(f"📊 总计: {len(wrapped_tools)} 个工具，{approval_count} 个需要审批")
    return wrapped_tools