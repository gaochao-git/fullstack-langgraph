"""
故障诊断代理 - 使用LangGraph架构，基于SOP知识库和智能工具选择
"""

import os
import json
import requests
from typing import Annotated, Dict, Any, List, Optional
from typing_extensions import TypedDict
from datetime import datetime
import logging

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek

from agents.diagnostic_agent.tools_and_schemas import SearchQueryList, Reflection
from agents.diagnostic_agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agents.diagnostic_agent.configuration import Configuration
from agents.diagnostic_agent.prompts import (
    get_current_date,
    query_writer_instructions,
    reflection_instructions,
    answer_instructions,
)
from agents.diagnostic_agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

# 导入工具
from tools import ssh_tool
from tools import sop_tool

from dotenv import load_dotenv

load_dotenv()

if os.getenv("DEEPSEEK_API_KEY") is None:
    raise ValueError("DEEPSEEK_API_KEY is not set")

logger = logging.getLogger(__name__)

# 定义诊断状态
class DiagnosticState(TypedDict):
    """诊断代理的状态"""
    messages: Annotated[list, add_messages]  # LangGraph特殊注解，用于消息累积
    sop_key: Optional[str]  # 用户提供的SOP键
    sop_validated: bool  # SOP与问题的相关性是否已验证
    sop_loaded: bool  # SOP是否已加载
    tools_used: List[str]  # 已使用的工具列表
    system_diagnosis_result: Annotated[list, lambda x, y: x + y]  # 诊断结果

# 收集所有工具
def collect_all_tools():
    """收集所有可用的诊断工具"""
    all_tools = []
    
    # 添加SOP工具
    all_tools.extend(sop_tool.sop_tools)
    
    # 添加SSH工具 - 直接使用工具函数
    ssh_tools = [
        ssh_tool.get_system_info,
        ssh_tool.analyze_processes,
        ssh_tool.check_service_status,
        ssh_tool.analyze_system_logs,
        ssh_tool.execute_system_command
    ]
    all_tools.extend(ssh_tools)
    
    logger.info(f"收集到 {len(all_tools)} 个工具")
    return all_tools

# 节点：分析故障信息并选择SOP
def analyze_fault_and_select_sop(state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
    """LangGraph 节点，分析用户输入的故障信息并选择合适的SOP。"""
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化 DeepSeek Chat
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 构建系统提示 - 不在节点中直接调用工具
    system_prompt = """你是专业的故障诊断专家，需要根据用户描述的问题选择合适的SOP进行诊断。

【诊断流程】
1. 分析用户描述的问题
2. 调用list_sops获取可用的SOP列表
3. 从可用SOP中选择最相关的SOP
4. 调用get_sop_detail获取SOP详情
5. 按照SOP步骤进行诊断

【工具使用规则】
- 每次只调用一个工具
- 根据SOP步骤和前一个工具结果选择下一个工具
- 避免重复调用相同功能的工具
- 所有工具自动连接到目标服务器

【可用工具】
- list_sops: 列出所有可用的SOP
- get_sop_detail: 获取SOP详情
- get_system_info: 获取系统信息
- analyze_processes: 分析进程
- check_service_status: 检查服务状态
- analyze_system_logs: 分析系统日志
- execute_system_command: 执行系统命令

请分析用户问题并开始诊断流程。"""

    # 构建消息
    messages = state.get("messages", [])
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # 绑定工具到LLM
    all_tools = collect_all_tools()
    llm_with_tools = llm.bind_tools(all_tools)
    
    # 调用LLM
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response],
        "sop_key": state.get("sop_key"),
        "sop_validated": state.get("sop_validated", False),
        "sop_loaded": state.get("sop_loaded", False),
        "tools_used": state.get("tools_used", []),
        "system_diagnosis_result": state.get("system_diagnosis_result", [])
    }

# 状态更新节点
def update_diagnostic_state(state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
    """更新诊断状态"""
    messages = state.get("messages", [])
    current_sop_key = state.get("sop_key")
    current_sop_validated = state.get("sop_validated", False)
    current_sop_loaded = state.get("sop_loaded", False)
    tools_used = state.get("tools_used", [])
    
    # 提取SOP键名
    sop_key = current_sop_key
    if not sop_key:
        for msg in messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                import re
                sop_matches = re.findall(r'sop_\w+', msg.content.lower())
                if sop_matches:
                    sop_key = sop_matches[0]
                    break
    
    # 检查最近的工具调用
    recent_tools = []
    for msg in messages[-2:]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get("name"):
                    recent_tools.append(tool_call["name"])
    
    all_tools_used = list(set(tools_used + recent_tools))
    
    # SOP验证逻辑
    sop_validated = current_sop_validated
    sop_loaded = current_sop_loaded
    
    if sop_key and not sop_validated and "get_sop_detail" in recent_tools:
        sop_validated = True
        sop_loaded = True
    elif sop_validated and "get_sop_detail" in recent_tools:
        sop_loaded = True
    
    return {
        "sop_key": sop_key,
        "sop_validated": sop_validated,
        "sop_loaded": sop_loaded,
        "tools_used": all_tools_used,
        "system_diagnosis_result": state.get("system_diagnosis_result", [])
    }

# 路由函数
def should_continue_diagnosis(state: DiagnosticState) -> str:
    """检查是否应该继续诊断"""
    sop_key = state.get("sop_key")
    sop_validated = state.get("sop_validated", False)
    sop_loaded = state.get("sop_loaded", False)
    tools_used = state.get("tools_used", [])
    messages = state.get("messages", [])
    
    # 检查最近的工具调用
    recent_tools = []
    for msg in messages[-2:]:
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get("name"):
                    recent_tools.append(tool_call["name"])
    
    # 1. 如果没有SOP键名，继续
    if not sop_key:
        return "update_state"
    
    # 2. 如果有SOP但未验证，继续
    if sop_key and not sop_validated:
        return "update_state"
    
    # 3. SOP已验证但未加载详情，继续
    if sop_validated and not sop_loaded:
        return "update_state"
    
    # 4. 完成条件：SOP已验证且已加载，使用了足够的工具且最近没有工具调用
    if sop_validated and sop_loaded and len(tools_used) >= 3:
        if not recent_tools:  # 没有最近的工具调用，说明在做分析
            return END
    
    return "update_state"

# 直接创建图
builder = StateGraph(DiagnosticState)

# 收集所有工具
all_tools = collect_all_tools()

# 添加节点
builder.add_node("analyze_fault", analyze_fault_and_select_sop)
builder.add_node("tools", ToolNode(all_tools))
builder.add_node("update_state", update_diagnostic_state)

# 添加边
builder.add_edge(START, "analyze_fault")
builder.add_conditional_edges("analyze_fault", tools_condition)
builder.add_edge("tools", "update_state")
builder.add_conditional_edges("update_state", should_continue_diagnosis, {
    "update_state": "analyze_fault", 
    END: END
})

# 编译图
graph = builder.compile(name="diagnostic-agent")
