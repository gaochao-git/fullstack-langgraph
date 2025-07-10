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
    """工具规划节点 - 严格按照SOP执行"""
    configurable = Configuration.from_runnable_config(config)
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=0.1,  # 降低温度，确保严格执行
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
    sop_state = state.get("sop_state", "none")
    
    formatted_prompt = tool_planning_instructions.format(
        fault_ip=state.get("fault_ip", ""),
        fault_time=state.get("fault_time", ""),
        fault_info=state.get("fault_info", ""),
        sop_id=state.get("sop_id", ""),
        sop_state=sop_state,
        sop_content=sop_content
    )

    # 构建消息
    messages = state.get("messages", [])
    system_message = SystemMessage(content=formatted_prompt)
    messages_with_system = [system_message] + messages
    
    # 调用LLM生成工具调用
    response = llm_with_tools.invoke(messages_with_system)
    
    # 返回新的消息，LangGraph会将其添加到状态中
    return {"messages": [response]}


def approval_node(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """SOP执行确认节点 - 确认每个SOP步骤的执行"""
    # 获取最新的工具调用消息
    messages = state.get("messages", [])
    if not messages:
        return {}
    
    last_message = messages[-1]
    
    # 如果有工具调用，检查是否符合SOP要求
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        sop_id = state.get("sop_id", "")
        sop_detail = state.get("sop_detail", {})
        diagnosis_step_count = state.get("diagnosis_step_count", 0)
        
        # 从SOP详情中获取当前步骤
        current_step_info = None
        if sop_detail and isinstance(sop_detail, dict):
            steps = sop_detail.get("steps", [])
            if 0 <= diagnosis_step_count < len(steps):
                current_step_info = steps[diagnosis_step_count]

        # 检查当前步骤是否需要审批
        if current_step_info and current_step_info.get("requires_approval", False):
            tool_descriptions = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_descriptions.append(f"工具: {tool_name}, 参数: {tool_args}")
            
            # 中断并请求用户确认
            interrupt_info = {
                "message": f"按照SOP '{sop_id}' 要求，即将执行需要审批的步骤:\n\n"
                           f"**步骤详情:** {current_step_info.get('action', 'N/A')}\n"
                           f"**计划操作:**\n" + "\n".join(tool_descriptions) +
                           f"\n\n确认执行？",
                "tool_calls": tool_calls,
                "sop_id": sop_id,
                "current_sop_step": current_step_info.get('action', ''),
                "suggestion_type": "sop_execution"
            }
            return interrupt(interrupt_info)
        
        # 如果不需要审批，则不返回任何内容，直接继续
    return {}


def execute_diagnosis_tools(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """工具执行节点 - 使用ToolNode执行工具"""
    # 这个节点会被ToolNode替代，但我们需要在这里处理工具执行后的状态更新
    # 增加一个空返回，因为所有节点都需要返回一个字典
    return {}


def reflect_diagnosis_progress(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosisReflectionState:
    """诊断反思节点 - 按SOP顺序执行，找到根因可提前结束"""
    # 1. 同步SOP状态并更新步骤计数器
    updated_state = sync_sop_state_from_messages(state)
    diagnosis_step_count = updated_state.get("diagnosis_step_count", 0)
    
    # 为下一步执行增加步骤计数
    updated_state["diagnosis_step_count"] = diagnosis_step_count + 1

    # 2. 准备反思
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.reflection_model,
        temperature=0.1,  # 降低温度，确保严格检查
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 从最新的ToolMessage中提取诊断结果
    diagnosis_results = updated_state.get("diagnosis_results", [])
    last_message = updated_state.get("messages", [])[-1]
    if isinstance(last_message, ToolMessage):
        diagnosis_results.append(f"Tool: {last_message.name}, Result: {last_message.content}")

    # 格式化反思提示
    formatted_prompt = reflection_instructions.format(
        diagnosis_step_count=diagnosis_step_count, # 使用当前步骤数进行反思
        max_diagnosis_steps=updated_state.get("max_diagnosis_steps", 10),
        fault_info=updated_state.get("fault_info", ""),
        sop_state=updated_state.get("sop_state", "none"),
        diagnosis_results="\n".join(diagnosis_results)
    )
    
    # 调用LLM进行SOP执行检查和根因分析
    try:
        from agents.diagnostic_agent.tools_and_schemas import DiagnosisReflectionOutput
        result = llm.with_structured_output(DiagnosisReflectionOutput).invoke(formatted_prompt)
    
    return {
            "is_complete": result.is_complete,
            "confidence_score": result.confidence_score,
            "sop_steps_completed": result.sop_steps_completed,
            "sop_steps_remaining": result.sop_steps_remaining,
            "root_cause_found": result.root_cause_found,
            "root_cause_analysis": result.root_cause_analysis,
            "next_steps": result.next_steps,
            "user_recommendations": result.user_recommendations,
            "termination_reason": result.termination_reason,
            "diagnosis_step_count": updated_state["diagnosis_step_count"], # 返回更新后的步骤数
            "diagnosis_results": diagnosis_results
        }
    except Exception as e:
        logger.error(f"诊断反思失败: {e}")
        # 降级处理 - 如果分析失败，要求重新按照SOP执行
        return {
            "is_complete": False,
            "confidence_score": 0.0,
            "sop_steps_completed": [],
            "sop_steps_remaining": ["重新按照SOP执行"],
            "root_cause_found": False,
            "root_cause_analysis": "反思分析异常",
            "next_steps": ["重新获取SOP内容并严格执行"],
            "user_recommendations": ["请重新提交诊断请求"],
            "termination_reason": "continue",
            "diagnosis_step_count": updated_state["diagnosis_step_count"] # 返回更新后的步骤数
        }


def finalize_diagnosis_report(state: DiagnosticOverallState, config: RunnableConfig) -> DiagnosticOverallState:
    """完成诊断报告节点 - 基于严格的SOP执行结果"""
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.answer_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 获取SOP执行状态
    sop_id = state.get("sop_id", "")
    sop_steps_completed = state.get("sop_steps_completed", [])
    sop_steps_remaining = state.get("sop_steps_remaining", [])
    
    # 构建SOP执行报告
    current_date = get_current_date()
    
    sop_execution_report = f"""
【故障诊断报告】
诊断日期：{current_date}

基本信息：
- 故障IP：{state.get('fault_ip', '未提供')}
- 故障时间：{state.get('fault_time', '未提供')}
- 故障现象：{state.get('fault_info', '未提供')}
- 使用SOP：{sop_id}

SOP执行情况：
已完成步骤：{chr(10).join(sop_steps_completed) if sop_steps_completed else '无'}
剩余步骤：{chr(10).join(sop_steps_remaining) if sop_steps_remaining else '无'}

诊断过程：
{chr(10).join(state.get('diagnosis_results', ['未进行诊断']))}

请基于以上SOP执行结果，生成最终的诊断报告，包括：
1. SOP执行完整性评估
2. 故障根因分析（如已确定）
3. 解决方案建议
4. 预防措施建议
5. 后续监控建议

注意：所有建议必须基于SOP执行结果，不得偏离SOP要求。
"""
    
    # 调用LLM生成最终诊断报告
    response = llm.invoke(sop_execution_report)
    
    # 根据SOP执行完整性生成不同的报告
    if len(sop_steps_remaining) == 0:
        # SOP完全执行完毕
        final_message = f"""
{response.content}

✅ SOP执行状态：已完成
- 使用SOP：{sop_id}
- 已完成步骤：{len(sop_steps_completed)}个
- 剩余步骤：0个

⚠️ 重要提醒：
以上诊断结果基于严格的SOP {sop_id} 执行。在执行任何操作前，请：
1. 确认当前系统状态
2. 评估操作风险
3. 备份重要数据
4. 在非生产环境测试

如需执行建议的解决方案，请严格按照SOP要求操作。
"""
    else:
        # SOP未完全执行
        final_message = f"""
{response.content}

⚠️ SOP执行状态：未完成
- 使用SOP：{sop_id}
- 已完成步骤：{len(sop_steps_completed)}个
- 剩余步骤：{len(sop_steps_remaining)}个

📋 未完成的SOP步骤：
{chr(10).join(sop_steps_remaining)}

重要说明：
由于SOP未完全执行，当前诊断结果可能不完整。建议：
1. 继续执行剩余的SOP步骤
2. 或联系技术专家进行进一步诊断
3. 避免在SOP未完成时执行修复操作

请确保严格按照SOP要求完成所有步骤后再进行故障修复。
"""
    
    return {
        "messages": [AIMessage(content=final_message)],
        "diagnosis_step_count": state.get("diagnosis_step_count", 0),
        "sop_steps_completed": sop_steps_completed,
        "sop_steps_remaining": sop_steps_remaining
    }


# 辅助函数
def sync_sop_state_from_messages(state: DiagnosticOverallState) -> DiagnosticOverallState:
    """同步SOP状态 - 从ToolMessage中提取SOP内容"""
    messages = state.get("messages", [])
    # 创建一个可变副本以进行修改
    mutable_state = dict(state)

    for msg in reversed(messages):
        # 检查是否为ToolMessage以及工具名称是否正确
        if isinstance(msg, ToolMessage) and msg.name == "get_sop_content":
            try:
                result = json.loads(msg.content)
                mutable_state["sop_state"] = result.get("sop_state", "none")
                mutable_state["sop_detail"] = result.get("sop_content")
                # 找到后即可退出循环
                break
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"解析SOP内容失败: {e}, 内容: {msg.content}")
                mutable_state["sop_state"] = "error"
                mutable_state["sop_detail"] = {"error": "Failed to parse SOP content"}
                break
    return mutable_state


# 路由函数 - 参考调研agent的条件路由
def check_info_sufficient(state: QuestionAnalysisState, config: RunnableConfig) -> str:
    """检查信息是否充足"""
    return "plan_tools" if state.get("info_sufficient") else "finalize_answer"


def evaluate_diagnosis_progress(state: DiagnosisReflectionState, config: RunnableConfig) -> str:
    """评估诊断进度，根据SOP执行情况和根因发现情况决定下一步"""
    configurable = Configuration.from_runnable_config(config)
    max_steps = configurable.max_diagnosis_steps
    
    current_steps = state.get("diagnosis_step_count", 0)
    termination_reason = state.get("termination_reason", "continue")
    root_cause_found = state.get("root_cause_found", False)
    
    # 检查是否达到最大步骤数
    if current_steps >= max_steps:
        logger.warning(f"已达到最大步骤数 {max_steps}，强制结束诊断")
        return "finalize_answer"
    
    # 根据终止原因决定下一步
    if termination_reason == "root_cause_found" and root_cause_found:
        logger.info("已找到根因，可以提前结束诊断")
        return "finalize_answer"
    elif termination_reason == "sop_completed":
        logger.info("已完成所有SOP步骤，结束诊断")
        return "finalize_answer"
    elif state.get("is_complete", False):
        # 兼容处理：如果is_complete为True，也可以结束
        logger.info("诊断完成，结束诊断")
        return "finalize_answer"
    else:
        # 继续执行下一个SOP步骤
        sop_steps_remaining = state.get("sop_steps_remaining", [])
        logger.info(f"继续执行SOP步骤，剩余步骤: {sop_steps_remaining}")
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

# 新的流程: plan -> approval -> execute -> reflect
builder.add_edge("plan_tools", "approval")
builder.add_edge("approval", "execute_tools")

# ToolNode会自动将ToolMessage附加到状态中
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
