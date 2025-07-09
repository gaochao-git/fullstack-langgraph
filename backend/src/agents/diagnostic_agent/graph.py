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
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek



from agents.diagnostic_agent.state import (
    DiagnosticOverallState,
    ToolExecutionState,
    DiagnosisReflectionState,
)
from agents.diagnostic_agent.configuration import Configuration
from agents.diagnostic_agent.prompts import (
    get_current_date,
    reflection_instructions,
    default_info_insufficient_prompt,
    default_diagnosis_plan_prompt,
)
from agents.diagnostic_agent.tools_and_schemas import QuestionInfoExtraction


# 导入工具
from tools import ssh_tool
from tools import sop_tool

from dotenv import load_dotenv



load_dotenv()

if os.getenv("DEEPSEEK_API_KEY") is None:
    raise ValueError("DEEPSEEK_API_KEY is not set")

logger = logging.getLogger(__name__)

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

# 问题分析节点，判断信息是否充足
def question_analysis(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    configurable = Configuration.from_runnable_config(config)
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    messages = state.get("messages", [])
    user_question = messages[-1].content if messages else ""
    
    # 使用结构化输出判断四要素是否充足
    
    # 构建提示词
    prompt = default_info_insufficient_prompt.format(user_question=user_question)
    
    # 使用结构化输出解析用户输入
    result = llm.with_structured_output(QuestionInfoExtraction).invoke(prompt)
    
    # 根据解析出的四要素判断信息是否充足
    # 检查四要素是否都有有效值（不为空或"待提取"等占位符）
    info_sufficient = (
        result.fault_ip and result.fault_ip.strip() and result.fault_ip != "待提取" and
        result.fault_time and result.fault_time.strip() and result.fault_time != "待提取" and
        result.fault_info and result.fault_info.strip() and result.fault_info != "待提取" and
        result.sop_id and result.sop_id.strip() and result.sop_id != "待提取"
    )
    
    # 如果信息不足，生成缺失字段列表和用户提示
    if not info_sufficient:
        missing_fields = []
        if not result.fault_ip or result.fault_ip.strip() == "" or result.fault_ip == "待提取":
            missing_fields.append("故障IP")
        if not result.fault_time or result.fault_time.strip() == "" or result.fault_time == "待提取":
            missing_fields.append("故障时间")
        if not result.fault_info or result.fault_info.strip() == "" or result.fault_info == "待提取":
            missing_fields.append("故障现象")
        if not result.sop_id or result.sop_id.strip() == "" or result.sop_id == "待提取":
            missing_fields.append("排查SOP编号")
        
        user_tip = f"请补充以下信息：{', '.join(missing_fields)}"
    else:
        missing_fields = []
        user_tip = ""
    
    if info_sufficient:
        # 信息充足，构建格式化的诊断提示词
        formatted_prompt = default_diagnosis_plan_prompt.format(
            fault_ip=result.fault_ip,
            fault_time=result.fault_time,
            fault_info=result.fault_info,
            sop_id=result.sop_id
        )
        # 返回格式化的用户消息，供后续节点使用
        formatted_message = HumanMessage(content=formatted_prompt)
        return {
            "messages": [formatted_message],
            "current_step": "question_analysis",
            "info_sufficient": True
        }
    else:
        # 信息不足，返回AI消息提示用户补充信息
        ai_response = f"信息不足，需要补充：{', '.join(missing_fields)}"
        return {
            "messages": [AIMessage(content=ai_response)],
            "current_step": "question_analysis",
            "info_sufficient": False
        }

# 节点：SOP提取和验证
def sop_extraction(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """SOP提取节点：根据sop_id获取SOP详情并更新状态"""
    configurable = Configuration.from_runnable_config(config)
    
    # 从消息中提取sop_id
    messages = state.get("messages", [])
    sop_id = None
    
    # 从最后一条消息中提取sop_id
    if messages:
        last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
        # 从格式化的消息中提取sop_id
        # 根据 default_diagnosis_plan_prompt 的格式提取
        import re
        sop_match = re.search(r'排查SOP编号：(\S+)', last_message)
        if sop_match:
            sop_id = sop_match.group(1)
        else:
            # 如果没有找到，尝试其他可能的格式
            sop_match = re.search(r'SOP编号[：:]\s*(\S+)', last_message)
            if sop_match:
                sop_id = sop_match.group(1)
            else:
                sop_id = None
    
    # 尝试根据sop_id获取SOP详情
    sop_detail = None
    sop_state = "none"
    sop_message = ""
    
    if sop_id and sop_id.strip() and sop_id != "待提取":
        try:
            # 使用sop_tool获取SOP详情，注意参数名是sop_key
            sop_response_str = sop_tool.get_sop_detail({"sop_key": sop_id})
            # 解析JSON响应
            import json
            sop_response = json.loads(sop_response_str)
            
            if sop_response and sop_response.get("success"):
                sop_detail = sop_response.get("sop")
                sop_state = "loaded"
                sop_message = f"SOP加载成功：{sop_id}"
            else:
                sop_state = "invalid"
                error_msg = sop_response.get("error", "SOP不存在或ID错误")
                sop_message = f"SOP验证失败：{sop_id} - {error_msg}"
        except Exception as e:
            sop_state = "error"
            sop_message = f"SOP验证异常：{sop_id} - {str(e)}"
    else:
        sop_message = "未提供有效的SOP ID"
    
    # 构建响应消息
    response_content = f"SOP提取结果：{sop_message}"
    if sop_detail:
        response_content += f"\n\nSOP详情：{sop_detail}"
    
    return {
        "messages": [AIMessage(content=response_content)],
        "current_step": "sop_extraction",
        "sop_state": sop_state,
        "sop_detail": sop_detail
    }

# 节点：工具节点（包含SOP选择和工具规划）
def tools(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """工具节点：生成工具调用计划。"""
    configurable = Configuration.from_runnable_config(config)
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 绑定工具到LLM
    ssh_tools = [
        ssh_tool.get_system_info,
        ssh_tool.analyze_processes,
        ssh_tool.check_service_status,
        ssh_tool.analyze_system_logs,
        ssh_tool.execute_system_command
    ]
    llm_with_tools = llm.bind_tools(ssh_tools)
    
    # 构建系统提示
    system_prompt = """你是专业的故障诊断专家，需要执行诊断工具来收集系统信息。

【诊断工具执行】
1. 根据SOP步骤选择合适的诊断工具
2. 执行工具并分析结果
3. 根据结果决定下一步操作

【可用工具】
- get_system_info: 获取系统信息
- analyze_processes: 分析进程
- check_service_status: 检查服务状态
- analyze_system_logs: 分析系统日志
- execute_system_command: 执行系统命令

请根据当前情况选择合适的诊断工具执行。"""

    # 构建消息
    messages = state.get("messages", [])
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        messages = [SystemMessage(content=system_prompt)] + messages
    
    # 调用LLM生成工具调用
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response],
        "current_step": "tools"
    }



# 节点：工具执行审批
def approval_node(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """审批节点：在工具执行前进行人工或自动审批。"""
    # 这里可以实现人工审批、自动审批或模拟审批逻辑
    # 简单实现：默认审批通过，实际可集成前端交互或审批系统
    # 可以在state中加入审批意见、审批人等信息
    return {
        "current_step": "approval"
    }

# 节点：诊断反思
def reflect_diagnosis(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosisReflectionState:
    """LangGraph 节点，反思诊断进度并决定下一步。"""
    configurable = Configuration.from_runnable_config(config)
    
    # 计算当前诊断步骤数
    current_steps = sum(state.get("diagnosis_step_count", [0]))
    max_steps = state.get("max_diagnosis_steps", 10)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.reflection_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 使用反思指令模板
    formatted_prompt = reflection_instructions.format(
        current_steps=current_steps,
        max_steps=max_steps,
        tools_used=state.get('tools_used', []),
        diagnosis_results=chr(10).join(state.get('diagnosis_results', []))
    )
    
    # 调用LLM进行反思
    response = llm.invoke(formatted_prompt)
    
    # 解析响应（这里简化处理，实际可以使用结构化输出）
    content = response.content if hasattr(response, 'content') else str(response)
    
    # 简单的完成判断逻辑
    is_complete = (
        current_steps >= max_steps or
        "诊断完成" in content or
        "问题已解决" in content
    )
    
    return {
        "is_complete": is_complete,
        "next_steps": [content],  # 简化处理
        "confidence_score": 0.8 if is_complete else 0.5,  # 简化处理
        "diagnosis_step_count": [0],  # 反思不算作新步骤
        "knowledge_gaps": [],
        "recommendations": [content]
    }

# 路由函数：评估诊断进度
def evaluate_diagnosis_progress(state: DiagnosisReflectionState, config: RunnableConfig) -> str:
    """LangGraph 路由函数，确定诊断流程中的下一步。"""
    configurable = Configuration.from_runnable_config(config)
    max_steps = configurable.max_diagnosis_steps
    
    # 计算当前步骤数
    current_steps = sum(state.get("diagnosis_step_count", [0]))
    
    if state["is_complete"] or current_steps >= max_steps:
        return "finalize_diagnosis"
    else:
        return "continue_diagnosis"

# 节点：完成诊断
def finalize_diagnosis(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """LangGraph 节点，完成诊断并生成最终报告。"""
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.answer_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 信息充足时，输出排查方案
    user_question = ""
    messages = state.get("messages", [])
    if messages:
        user_question = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    
    # 使用信息充足的提示词模板
    final_prompt = default_diagnosis_plan_prompt.format(
        fault_ip="待提取",  # 实际应该从用户输入中提取
        fault_time="待提取",
        fault_info="待提取", 
        sop_id="待提取"
    )
    
    # 调用LLM
    response = llm.invoke(final_prompt)
    
    return {
        "messages": [AIMessage(content=response.content)],
        "current_step": "completed",
        "diagnosis_step_count": [0],  # 完成不算作新步骤
        "confidence_score": 0.9
    }

# 创建诊断Agent图
builder = StateGraph(DiagnosticOverallState, config_schema=Configuration)

# 添加节点
builder.add_node("question_analysis", question_analysis)
builder.add_node("sop_extraction", sop_extraction)
builder.add_node("tools", tools)
builder.add_node("approval", approval_node)

# 使用 ToolNode 来处理工具调用
ssh_tools = [
    ssh_tool.get_system_info,
    ssh_tool.analyze_processes,
    ssh_tool.check_service_status,
    ssh_tool.analyze_system_logs,
    ssh_tool.execute_system_command
]
tool_node = ToolNode(ssh_tools)
builder.add_node("execute_tool", tool_node)

builder.add_node("reflection", reflect_diagnosis)
builder.add_node("finalize_answer", finalize_diagnosis)

# 添加边
builder.add_edge(START, "question_analysis")
builder.add_conditional_edges("question_analysis", lambda state, config: (
    "sop_extraction" if state.get("info_sufficient") else END
), ["sop_extraction", END])
builder.add_edge("sop_extraction", "tools")
builder.add_edge("tools", "approval")
builder.add_edge("approval", "execute_tool")
builder.add_conditional_edges("execute_tool", tools_condition, {
    "tools": "execute_tool",
    "__end__": "reflection"
})
builder.add_conditional_edges("reflection", evaluate_diagnosis_progress, {
    "continue_diagnosis": "tools",
    "finalize_answer": "finalize_answer"
})
builder.add_edge("finalize_answer", END)

# 编译图
graph = builder.compile(name="diagnostic-agent")

# 将图保存到当前路径
graph_image = graph.get_graph().draw_mermaid_png()
with open("diagnostic_agent_graph.png", "wb") as f: 
    f.write(graph_image)
print("图已保存到: diagnostic_agent_graph.png")
