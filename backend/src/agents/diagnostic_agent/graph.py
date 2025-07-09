"""
故障诊断代理 - 使用LangGraph架构，基于SOP知识库和智能工具选择
重构版本：参考调研agent的结构，优化状态管理和节点职责
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Send, interrupt

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek

from agents.diagnostic_agent.state import (
    DiagnosticOverallState,
    QuestionAnalysisState,
    DiagnosisReflectionState,
    ToolPlanningState,
)
from agents.diagnostic_agent.configuration import Configuration
from agents.diagnostic_agent.prompts import (
    get_current_date,
    question_analysis_instructions,
    tool_planning_instructions,
    reflection_instructions,
    final_diagnosis_instructions,
)
from agents.diagnostic_agent.tools_and_schemas import QuestionInfoExtraction

# 导入工具
from tools import ssh_tool, sop_tool
from dotenv import load_dotenv

load_dotenv()

if os.getenv("DEEPSEEK_API_KEY") is None:
    raise ValueError("DEEPSEEK_API_KEY is not set")

logger = logging.getLogger(__name__)


# 节点函数 - 参考调研agent的清晰结构
def analyze_question(state: DiagnosticOverallState, config: RunnableConfig) -> QuestionAnalysisState:
    """问题分析节点 - 类似调研agent的generate_query"""
    configurable = Configuration.from_runnable_config(config)
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    messages = state.get("messages", [])
    user_question = messages[-1].content if messages else ""
    
    # 格式化提示词
    current_date = get_current_date()
    formatted_prompt = question_analysis_instructions.format(
        current_date=current_date,
        user_question=user_question
    )
    
    # 使用结构化输出解析用户输入
    result = llm.with_structured_output(QuestionInfoExtraction).invoke(formatted_prompt)
    
    # 检查四要素是否都有有效值
    info_sufficient = (
        result.fault_ip and result.fault_ip.strip() and result.fault_ip != "待提取" and
        result.fault_time and result.fault_time.strip() and result.fault_time != "待提取" and
        result.fault_info and result.fault_info.strip() and result.fault_info != "待提取" and
        result.sop_id and result.sop_id.strip() and result.sop_id != "待提取"
    )
    
    # 生成缺失字段列表
    missing_fields = []
    if not result.fault_ip or result.fault_ip.strip() == "" or result.fault_ip == "待提取":
        missing_fields.append("故障IP")
    if not result.fault_time or result.fault_time.strip() == "" or result.fault_time == "待提取":
        missing_fields.append("故障时间")
    if not result.fault_info or result.fault_info.strip() == "" or result.fault_info == "待提取":
        missing_fields.append("故障现象")
    if not result.sop_id or result.sop_id.strip() == "" or result.sop_id == "待提取":
        missing_fields.append("排查SOP编号")
    
    return {
        "fault_ip": result.fault_ip,
        "fault_time": result.fault_time,
        "fault_info": result.fault_info,
        "sop_id": result.sop_id,
        "info_sufficient": info_sufficient,
        "missing_fields": missing_fields,
    }


def plan_diagnosis_tools(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """工具规划节点 - 专门负责工具选择和规划"""
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
    sop_tools = [
        sop_tool.get_sop_content,
        sop_tool.get_sop_detail,
        sop_tool.list_sops,
        sop_tool.search_sops
    ]
    all_tools = ssh_tools + sop_tools
    llm_with_tools = llm.bind_tools(all_tools)
    
    # 构建工具规划提示
    sop_content = state.get("sop_detail", "")
    formatted_prompt = tool_planning_instructions.format(
        fault_ip=state.get("fault_ip", ""),
        fault_time=state.get("fault_time", ""),
        fault_info=state.get("fault_info", ""),
        sop_id=state.get("sop_id", ""),
        sop_content=sop_content
    )
    
    # 构建消息
    messages = state.get("messages", [])
    system_message = SystemMessage(content=formatted_prompt)
    messages_with_system = [system_message] + messages
    
    # 调用LLM生成工具调用
    response = llm_with_tools.invoke(messages_with_system)
    
    # 更新状态
    new_state = {
        "messages": [response],
        "diagnosis_step_count": state.get("diagnosis_step_count", 0) + 1
    }
    
    return sync_sop_state_from_messages(new_state)


def approval_node(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """审批节点 - 在工具执行前进行审批"""
    # 获取最新的工具调用消息
    messages = state.get("messages", [])
    if not messages:
        return state
    
    last_message = messages[-1]
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return state
    
    # 检查是否有高风险工具调用
    high_risk_tools = ["execute_system_command"]
    tool_calls = last_message.tool_calls
    
    for tool_call in tool_calls:
        if tool_call.get("name") in high_risk_tools:
            # 对于高风险工具，询问用户是否继续
            user_response = interrupt({
                "message": f"即将执行高风险工具：{tool_call.get('name')}\n参数：{tool_call.get('args')}\n是否继续？",
                "tool_call": tool_call,
            })
            
            if not user_response:
                return {
                    "messages": [AIMessage(content="用户取消了工具执行操作，诊断过程已结束。")]
                }
    
    return state


def execute_diagnosis_tools(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """工具执行节点 - 使用ToolNode执行工具"""
    # 这个节点会被ToolNode替代，但我们需要在这里处理工具执行后的状态更新
    return state


def reflect_diagnosis_progress(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosisReflectionState:
    """诊断反思节点 - 类似调研agent的reflection"""
    # 同步SOP状态
    state = sync_sop_state_from_messages(state)
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.reflection_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 格式化反思提示
    formatted_prompt = reflection_instructions.format(
        diagnosis_step_count=state.get("diagnosis_step_count", 0),
        max_diagnosis_steps=state.get("max_diagnosis_steps", 10),
        tools_used=state.get("tools_used", []),
        diagnosis_results="\n".join(state.get("diagnosis_results", [])),
        sop_state=state.get("sop_state", "none"),
        fault_info=state.get("fault_info", "")
    )
    
    # 调用LLM进行反思
    try:
        from agents.diagnostic_agent.tools_and_schemas import DiagnosisReflectionOutput
        result = llm.with_structured_output(DiagnosisReflectionOutput).invoke(formatted_prompt)
        
        return {
            "is_complete": result.is_complete,
            "confidence_score": result.confidence_score,
            "next_steps": result.next_steps,
            "knowledge_gaps": result.knowledge_gaps,
            "recommendations": result.recommendations,
            "diagnosis_step_count": state.get("diagnosis_step_count", 0)
        }
    except Exception as e:
        logger.error(f"反思节点执行失败: {e}")
        # 降级处理
        return {
            "is_complete": True,
            "confidence_score": 0.5,
            "next_steps": ["诊断异常结束"],
            "knowledge_gaps": ["反思处理失败"],
            "recommendations": ["请检查系统状态"],
            "diagnosis_step_count": state.get("diagnosis_step_count", 0)
        }


def finalize_diagnosis_report(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """完成诊断报告节点 - 类似调研agent的finalize_answer"""
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.answer_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 格式化最终诊断提示
    current_date = get_current_date()
    formatted_prompt = final_diagnosis_instructions.format(
        fault_ip=state.get("fault_ip", ""),
        fault_time=state.get("fault_time", ""),
        fault_info=state.get("fault_info", ""),
        sop_id=state.get("sop_id", ""),
        current_date=current_date,
        diagnosis_results="\n".join(state.get("diagnosis_results", []))
    )
    
    # 调用LLM生成最终诊断报告
    response = llm.invoke(formatted_prompt)
    
    return {
        "messages": [AIMessage(content=response.content)],
        "diagnosis_step_count": state.get("diagnosis_step_count", 0)
    }


# 辅助函数
def sync_sop_state_from_messages(state: DiagnosticOverallState) -> DiagnosticOverallState:
    """同步SOP状态 - 从消息中提取SOP信息"""
    for msg in reversed(state.get("messages", [])):
        if hasattr(msg, "tool_call") and getattr(msg.tool_call, "name", None) == "get_sop_content":
            try:
                result = json.loads(msg.content)
                state["sop_state"] = result.get("sop_state", "none")
                state["sop_detail"] = result.get("sop_content")
            except Exception:
                pass
            break
    return state


# 路由函数 - 参考调研agent的条件路由
def check_info_sufficient(state: QuestionAnalysisState, config: RunnableConfig) -> str:
    """检查信息是否充足"""
    return "plan_tools" if state.get("info_sufficient") else "finalize_answer"


def evaluate_diagnosis_progress(state: DiagnosisReflectionState, config: RunnableConfig) -> str:
    """评估诊断进度，决定下一步"""
    configurable = Configuration.from_runnable_config(config)
    max_steps = configurable.max_diagnosis_steps
    
    current_steps = state.get("diagnosis_step_count", 0)
    
    if state["is_complete"] or current_steps >= max_steps:
        return "finalize_answer"
    else:
        return "plan_tools"


# 创建诊断Agent图 - 参考调研agent的图构建方式
builder = StateGraph(DiagnosticOverallState, config_schema=Configuration)

# 添加节点
builder.add_node("analyze_question", analyze_question)
builder.add_node("plan_tools", plan_diagnosis_tools)
builder.add_node("approval", approval_node)

# 创建工具执行节点
ssh_tools = [
    ssh_tool.get_system_info,
    ssh_tool.analyze_processes,
    ssh_tool.check_service_status,
    ssh_tool.analyze_system_logs,
    ssh_tool.execute_system_command
]
sop_tools = [
    sop_tool.get_sop_content,
    sop_tool.get_sop_detail,
    sop_tool.list_sops,
    sop_tool.search_sops
]
all_tools = ssh_tools + sop_tools
tool_node = ToolNode(all_tools)
builder.add_node("execute_tools", tool_node)

builder.add_node("reflection", reflect_diagnosis_progress)
builder.add_node("finalize_answer", finalize_diagnosis_report)

# 添加边 - 参考调研agent的清晰边连接
builder.add_edge(START, "analyze_question")
builder.add_conditional_edges(
    "analyze_question", 
    check_info_sufficient, 
    ["plan_tools", "finalize_answer"]
)
builder.add_edge("plan_tools", "approval")
builder.add_edge("approval", "execute_tools")
builder.add_edge("execute_tools", "reflection")
builder.add_conditional_edges(
    "reflection", 
    evaluate_diagnosis_progress, 
    ["plan_tools", "finalize_answer"]
)
builder.add_edge("finalize_answer", END)

# 编译图
graph = builder.compile(name="diagnostic-agent")

# 保存图像
try:
    graph_image = graph.get_graph().draw_mermaid_png()
    with open("diagnostic_agent_graph.png", "wb") as f: 
        f.write(graph_image)
    print("图已保存到: diagnostic_agent_graph.png")
except Exception as e:
    logger.error(f"保存图像失败: {e}")
