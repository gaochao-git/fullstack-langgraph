"""
基于 create_react_agent 的新通用智能体
用于替代原有的 general_qa_subgraph
"""

import logging
from typing import Dict, Any, Callable
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.types import interrupt
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt

from .configuration import Configuration
from .tools import all_tools
from .state import DiagnosticState
from .tool_permissions import TOOL_PERMISSIONS

logger = logging.getLogger(__name__)

# 通用智能体的系统提示词
GENERAL_AGENT_PROMPT = """你是一个专业的运维技术助手，专门帮助用户解答各种技术问题和提供运维支持。

你的核心能力：
1. 技术问答 - 回答各种运维、开发、系统管理相关问题
2. 故障排查 - 协助用户进行基础的故障分析和排查
3. 配置指导 - 提供系统配置、软件部署的建议和指导
4. 最佳实践 - 分享行业最佳实践和经验
5. 工具使用 - 灵活使用各种运维工具来解决问题

可用工具类型：
- SSH工具：系统信息查询、进程分析、服务状态检查、日志分析、命令执行
- SOP工具：查找和参考标准操作程序
- MySQL工具：数据库连接、查询执行、性能监控
- Elasticsearch工具：集群状态查询、索引管理、数据分析
- Zabbix工具：监控数据获取、告警信息查询
- 通用工具：时间获取等实用功能

工作原则：
1. 理解用户问题的核心需求
2. 选择合适的工具来获取必要信息
3. 基于获取的信息提供准确、实用的建议
4. 如果问题复杂，提供分步骤的解决方案
5. 始终考虑安全性和最佳实践

注意事项：
- 优先提供安全可靠的解决方案
- 对于复杂操作，建议用户先在测试环境验证
- 如果涉及数据安全，提醒用户注意备份
- 提供具体可执行的操作步骤
- 如果需要更多信息才能准确回答，主动询问

请以友好、专业的态度协助用户解决技术问题。"""


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review."""
    from typing import Callable
    from langchain_core.tools import BaseTool, tool as create_tool
    from langchain_core.runnables import RunnableConfig
    from langgraph.types import interrupt
    from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt
    
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
    def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        # 构建兼容的中断信息（用于前端显示）
        # 使用工具名+参数进行匹配，这是最可靠的方案
        interrupt_info = {
            "message": f"检测到工具调用需要确认: {tool.name}",
            "tool_name": tool.name,
            "tool_args": tool_input,
            "description": f"请审批工具调用: {tool.name}",
            "suggestion_type": "tool_approval",
            "risk_level": "medium",
            "batch_mode": False,  # 单个工具模式
        }
        
        # 调用interrupt并获取用户确认结果
        user_approved = interrupt(interrupt_info)
        
        if user_approved:
            tool_response = tool.invoke(tool_input, config)
        else:
            tool_response = f"工具 {tool.name} 执行被用户拒绝"

        return tool_response

    return call_tool_with_interrupt


def create_batch_approval_interrupt_handler():
    """
    创建批量审批的中断处理器
    基于官方文档的 interrupt() 实现
    当检测到多个工具需要审批时，统一处理
    """
    def batch_approval_handler(state: DiagnosticState, config: RunnableConfig):
        """批量审批处理器"""
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        last_message = messages[-1]
        
        # 检查是否有工具调用
        if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
            return {}
        
        tool_calls = last_message.tool_calls
        pending_tools = []
        approved_tools = []
        
        # 检查每个工具调用的权限
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            
            # 生成唯一ID（如果还没有的话）
            if "id" not in tool_call:
                import uuid
                tool_call_id = str(uuid.uuid4())
                tool_call["id"] = tool_call_id
            
            # 检查权限
            from .tool_permissions import check_tool_permission
            permission_result = check_tool_permission(tool_name, tool_args)
            
            if permission_result["approved"]:
                approved_tools.append(tool_call)
            else:
                pending_tools.append({
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "tool_call_id": tool_call["id"],
                    "risk_level": permission_result["risk_level"],
                    "reason": permission_result["reason"]
                })
        
        # 如果有需要审批的工具，触发中断
        if pending_tools:
            # 构建中断信息
            interrupt_info = {
                "message": f"检测到 {len(pending_tools)} 个工具调用需要确认",
                "batch_mode": True,  # 批量模式
                "pending_tools": pending_tools,
                "approved_tools": approved_tools,
                "total_tools": len(tool_calls),
                "suggestion_type": "batch_tool_approval",
                "interrupt_type": "batch_tool_approval"  # 添加明确的类型标识
            }
            
            # 调用interrupt
            user_approved_tools = interrupt(interrupt_info)
            
            # 处理用户审批结果
            if isinstance(user_approved_tools, list):
                # 用户返回了具体的审批列表
                approved_tool_ids = set(user_approved_tools)
                final_approved = approved_tools + [
                    tool_call for tool_call in tool_calls 
                    if tool_call.get("id") in approved_tool_ids
                ]
                
                # 检查是否还有未审批的工具
                remaining_tools = [
                    tool_call for tool_call in tool_calls 
                    if tool_call.get("id") not in approved_tool_ids and 
                    not any(tc.get("id") == tool_call.get("id") for tc in approved_tools)
                ]
                
                if remaining_tools:
                    # 更新消息，只包含已批准的工具
                    from langchain_core.messages import AIMessage
                    updated_message = AIMessage(
                        content=last_message.content,
                        tool_calls=final_approved
                    )
                    return {"messages": messages[:-1] + [updated_message]}
                else:
                    # 更新消息，包含所有工具
                    from langchain_core.messages import AIMessage
                    updated_message = AIMessage(
                        content=last_message.content,
                        tool_calls=final_approved
                    )
                    return {"messages": messages[:-1] + [updated_message]}
                    
            elif user_approved_tools:
                # 用户批准所有工具
                final_approved = tool_calls
                
                # 更新消息，包含所有工具
                from langchain_core.messages import AIMessage
                updated_message = AIMessage(
                    content=last_message.content,
                    tool_calls=final_approved
                )
                return {"messages": messages[:-1] + [updated_message]}
            else:
                # 用户拒绝所有工具
                final_approved = approved_tools
                
                # 更新消息，只包含已自动批准的工具
                from langchain_core.messages import AIMessage
                updated_message = AIMessage(
                    content=last_message.content,
                    tool_calls=final_approved
                )
                return {"messages": messages[:-1] + [updated_message]}
        
        return {}
    
    return batch_approval_handler


def create_selective_approval_tools():
    """
    创建选择性审批的工具列表
    根据 TOOL_PERMISSIONS 配置，对需要审批的工具添加人工干预
    """
    from copy import deepcopy
    
    # 创建工具副本，避免修改原始工具
    selective_tools = []
    
    for tool in all_tools:
        tool_name = tool.name
        
        # 检查工具是否需要审批
        if tool_name in TOOL_PERMISSIONS["approval_required"]:
            # 需要审批的工具：添加人工干预
            wrapped_tool = add_human_in_the_loop(
                tool,
                interrupt_config={
                    "allow_accept": True,
                    "allow_edit": True,
                    "allow_respond": True,
                }
            )
            selective_tools.append(wrapped_tool)
        else:
            # 安全工具：直接使用
            selective_tools.append(tool)
    
    return selective_tools


def create_react_general_subgraph():
    """
    创建基于 create_react_agent 的通用智能体子图
    包装在我们自己的状态图中，以保持兼容性
    支持批量工具审批
    """
    # 从配置中获取LLM实例
    def get_llm_from_config(config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=configurable.model_temperature
        )
    
    # 创建带工具审批的 react agent 节点
    def create_react_agent_node(state: DiagnosticState, config: RunnableConfig):
        """创建 react agent 节点"""
        
        # 动态获取LLM
        llm = get_llm_from_config(config)
        
        # 创建选择性审批的工具列表
        selective_tools = create_selective_approval_tools()
        
        # 创建 react agent，使用选择性审批的工具
        # 不使用 interrupt_before，让我们的批量审批处理器来处理
        react_agent = create_react_agent(
            model=llm,
            tools=selective_tools,  # 使用选择性审批的工具
            prompt=GENERAL_AGENT_PROMPT,
        )
        
        # 准备消息 - 转换为 react agent 需要的格式
        messages = state.get("messages", [])
        react_state = {"messages": messages}
        
        # 调用 react agent
        result = react_agent.invoke(react_state, config)
        
        # 返回更新的消息，保持与原有状态的兼容
        return {"messages": result.get("messages", [])}
    
    # 创建工具调用预处理器
    def create_tool_calls_preprocessor():
        """创建工具调用预处理器，在工具执行前检查权限"""
        def preprocess_tool_calls(state: DiagnosticState, config: RunnableConfig):
            """预处理工具调用，检查权限并触发批量审批"""
            messages = state.get("messages", [])
            if not messages:
                return {}
            
            last_message = messages[-1]
            
            # 检查是否有工具调用
            if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
                return {}
            
            tool_calls = last_message.tool_calls
            pending_tools = []
            approved_tools = []
            
            # 检查每个工具调用的权限
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
                
                # 生成唯一ID（如果还没有的话）
                if "id" not in tool_call:
                    import uuid
                    tool_call_id = str(uuid.uuid4())
                    tool_call["id"] = tool_call_id
                
                # 检查权限
                from .tool_permissions import check_tool_permission
                permission_result = check_tool_permission(tool_name, tool_args)
                
                if permission_result["approved"]:
                    approved_tools.append(tool_call)
                else:
                    pending_tools.append({
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "tool_call_id": tool_call["id"],
                        "risk_level": permission_result["risk_level"],
                        "reason": permission_result["reason"]
                    })
            
            # 如果有需要审批的工具，触发中断
            if pending_tools:
                # 构建中断信息
                interrupt_info = {
                    "message": f"检测到 {len(pending_tools)} 个工具调用需要确认",
                    "batch_mode": True,  # 批量模式
                    "pending_tools": pending_tools,
                    "approved_tools": approved_tools,
                    "total_tools": len(tool_calls),
                    "suggestion_type": "batch_tool_approval",
                    "interrupt_type": "batch_tool_approval"  # 添加明确的类型标识
                }
                
                # 调用interrupt
                user_approved_tools = interrupt(interrupt_info)
                
                # 处理用户审批结果
                if isinstance(user_approved_tools, list):
                    # 用户返回了具体的审批列表
                    approved_tool_ids = set(user_approved_tools)
                    final_approved = approved_tools + [
                        tool_call for tool_call in tool_calls 
                        if tool_call.get("id") in approved_tool_ids
                    ]
                    
                    # 更新消息，只包含已批准的工具
                    from langchain_core.messages import AIMessage
                    updated_message = AIMessage(
                        content=last_message.content,
                        tool_calls=final_approved
                    )
                    return {"messages": messages[:-1] + [updated_message]}
                        
                elif user_approved_tools:
                    # 用户批准所有工具
                    final_approved = tool_calls
                    
                    # 更新消息，包含所有工具
                    from langchain_core.messages import AIMessage
                    updated_message = AIMessage(
                        content=last_message.content,
                        tool_calls=final_approved
                    )
                    return {"messages": messages[:-1] + [updated_message]}
                else:
                    # 用户拒绝所有工具
                    final_approved = approved_tools
                    
                    # 更新消息，只包含已自动批准的工具
                    from langchain_core.messages import AIMessage
                    updated_message = AIMessage(
                        content=last_message.content,
                        tool_calls=final_approved
                    )
                    return {"messages": messages[:-1] + [updated_message]}
            
            return {}
        
        return preprocess_tool_calls
    
    # 创建包装的状态图
    from langgraph.graph import StateGraph, START, END
    builder = StateGraph(DiagnosticState)
    
    # 添加工具调用预处理器
    tool_calls_preprocessor = create_tool_calls_preprocessor()
    builder.add_node("tool_calls_preprocessor", tool_calls_preprocessor)
    
    # 添加 react agent 节点
    builder.add_node("react_general_agent", create_react_agent_node)
    
    # 添加批量审批节点
    batch_approval_handler = create_batch_approval_interrupt_handler()
    builder.add_node("batch_approval", batch_approval_handler)
    
    # 设置边 - 在react_agent之前添加工具调用预处理器
    builder.add_edge(START, "tool_calls_preprocessor")
    builder.add_edge("tool_calls_preprocessor", "react_general_agent")
    builder.add_edge("react_general_agent", "batch_approval")
    builder.add_edge("batch_approval", END)
    
    return builder.compile()