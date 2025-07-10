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
    DiagnosticState,
    QuestionAnalysis,
    DiagnosisProgress,
    SOPDetail,
    SOPStep,
)
from agents.diagnostic_agent.configuration import Configuration
from agents.diagnostic_agent.prompts import (
    get_current_date,
    question_analysis_instructions,
    tool_planning_instructions,
    reflection_instructions,
    final_diagnosis_instructions,
    diagnosis_report_instructions,
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
def analyze_question(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
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
    
    # 创建QuestionAnalysis对象
    question_analysis = QuestionAnalysis(
        fault_ip=result.fault_ip,
        fault_time=result.fault_time,
        fault_info=result.fault_info,
        sop_id=result.sop_id,
        missing_fields=missing_fields,
        info_sufficient=info_sufficient
    )
    
    return {
        "user_question": user_question,
        "question_analysis": question_analysis
    }


def plan_diagnosis_tools(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
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
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    sop_detail = state.get("sop_detail", SOPDetail())
    sop_state = "loaded" if state.get("sop_loaded", False) else "none"
    
    formatted_prompt = tool_planning_instructions.format(
        fault_ip=question_analysis.fault_ip or "",
        fault_time=question_analysis.fault_time or "",
        fault_info=question_analysis.fault_info or "",
        sop_id=question_analysis.sop_id or "",
        sop_state=sop_state,
        sop_content=sop_detail.description if sop_detail else ""
    )

    # 构建消息
    messages = state.get("messages", [])
    system_message = SystemMessage(content=formatted_prompt)
    messages_with_system = [system_message] + messages
    
    # 调用LLM生成工具调用
    response = llm_with_tools.invoke(messages_with_system)
    
    # 检查是否生成了工具调用
    has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
    logger.info(f"工具规划结果: 生成了 {len(response.tool_calls) if has_tool_calls else 0} 个工具调用")
    
    if has_tool_calls:
        for i, tool_call in enumerate(response.tool_calls):
            logger.info(f"工具调用 {i+1}: {tool_call.get('name', 'unknown')}")
    else:
        logger.warning("LLM没有生成任何工具调用，这可能导致诊断提前结束")
    
    # 返回新的消息，LangGraph会将其添加到状态中
    return {"messages": [response]}


def approval_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """SOP执行确认节点 - 确认每个SOP步骤的执行"""
    # 获取最新的工具调用消息
    messages = state.get("messages", [])
    if not messages:
        return {}
    
    last_message = messages[-1]
    
    # 如果有工具调用，检查是否符合SOP要求
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        question_analysis = state.get("question_analysis", QuestionAnalysis())
        sop_detail = state.get("sop_detail", SOPDetail())
        diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
        
        logger.info(f"审批节点检查: SOP已加载={state.get('sop_loaded', False)}, SOP步骤数={len(sop_detail.steps)}, 当前步骤={diagnosis_progress.current_step}")
        
        # 从SOP详情中获取当前步骤
        current_step_info = None
        if sop_detail.steps and 0 <= diagnosis_progress.current_step < len(sop_detail.steps):
            current_step_info = sop_detail.steps[diagnosis_progress.current_step]
            logger.info(f"当前步骤: {diagnosis_progress.current_step}, 步骤信息: {current_step_info.action}, 需要审批: {current_step_info.requires_approval}")

        # 检查当前步骤是否需要审批
        if current_step_info and current_step_info.requires_approval:
            logger.info(f"触发审批流程: SOP {question_analysis.sop_id}, 步骤: {current_step_info.action}")
            tool_descriptions = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_descriptions.append(f"工具: {tool_name}, 参数: {tool_args}")
            
            # 中断并请求用户确认
            interrupt_info = {
                "message": f"按照SOP '{question_analysis.sop_id}' 要求，即将执行需要审批的步骤:\n\n"
                           f"**步骤详情:** {current_step_info.action}\n"
                           f"**计划操作:**\n" + "\n".join(tool_descriptions) +
                           f"\n\n确认执行？",
                "tool_calls": tool_calls,
                "sop_id": question_analysis.sop_id,
                "current_sop_step": current_step_info.action,
                "suggestion_type": "sop_execution"
            }
            
            # 调用interrupt并处理用户确认结果
            user_approved = interrupt(interrupt_info)
            logger.info(f"用户审批结果: {user_approved}")
            
            # 根据用户确认结果返回相应状态
            if user_approved:
                # 用户确认，允许继续执行
                return {}
            else:
                # 用户取消，中止执行并跳转到报告
                return {
                    "messages": [AIMessage(content="用户取消了SOP步骤执行，诊断流程已中止。")],
                    "diagnosis_progress": DiagnosisProgress(
                        current_step=diagnosis_progress.current_step,
                        max_steps=diagnosis_progress.max_steps,
                        is_complete=True,
                        termination_reason="user_cancelled"
                    )
                }
        
        # 如果不需要审批，则不返回任何内容，直接继续
    return {}


def reflect_diagnosis_progress(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """诊断反思节点 - 简化版本，直接更新诊断进度"""
    configurable = Configuration.from_runnable_config(config)
    
    # 获取当前状态
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    sop_detail = state.get("sop_detail", SOPDetail())
    messages = state.get("messages", [])
    
    # 处理SOP加载结果
    updated_sop_detail = sop_detail
    sop_loaded = state.get("sop_loaded", False)
    
    if messages and isinstance(messages[-1], ToolMessage) and messages[-1].name == "get_sop_content":
        try:
            # 解析SOP内容
            result = json.loads(messages[-1].content)
            if result.get("success") and result.get("sop_content"):
                sop_content = result["sop_content"]
                
                # 解析步骤并创建SOPStep对象
                steps = []
                for step_data in sop_content.get("steps", []):
                    sop_step = SOPStep(
                        title=step_data.get("title", ""),
                        description=step_data.get("description", ""),
                        action=step_data.get("action", ""),
                        requires_approval=step_data.get("requires_approval", False),
                        status="pending"
                    )
                    steps.append(sop_step)
                
                # 创建SOPDetail对象
                updated_sop_detail = SOPDetail(
                    sop_id=sop_content.get("id", ""),
                    title=sop_content.get("title", ""),
                    description=sop_content.get("description", ""),
                    steps=steps,
                    total_steps=len(steps)
                )
                sop_loaded = True
                logger.info(f"SOP加载成功: {updated_sop_detail.sop_id}, 步骤数: {len(steps)}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析SOP内容失败: {e}")
    
    # 检查是否有新的工具执行
    has_new_tool_execution = False
    if messages and isinstance(messages[-1], ToolMessage):
        # 有新的工具执行，更新步骤计数
        current_step = diagnosis_progress.current_step + 1
        has_new_tool_execution = True
        logger.info(f"检测到工具执行，步骤数更新为: {current_step}")
    else:
        # 没有新的工具执行，保持原步骤数
        current_step = diagnosis_progress.current_step
        logger.info(f"没有检测到工具执行，步骤数保持: {current_step}")
    
    # 从最新的ToolMessage中提取诊断结果
    diagnosis_results = list(state.get("diagnosis_results", []))
    if has_new_tool_execution:
        last_message = messages[-1]
        diagnosis_results.append(f"Tool: {last_message.name}, Result: {last_message.content}")
    
    # 检查是否完成诊断 - 放宽条件，让诊断能够充分执行
    is_complete = False
    termination_reason = "continue"
    
    # 只有在达到真正的上限时才强制退出
    max_steps = max(diagnosis_progress.max_steps, 15)  # 增加到至少15步
    if current_step >= max_steps:
        is_complete = True
        termination_reason = "max_steps_reached"
        logger.warning(f"达到最大步骤限制退出: {current_step}/{max_steps}")
    # 只有当SOP步骤完全执行完毕且至少执行了5步诊断时才退出
    elif updated_sop_detail.steps and len(updated_sop_detail.steps) > 0 and current_step > len(updated_sop_detail.steps) + 3:
        # 允许在SOP步骤基础上再执行几步额外诊断
        is_complete = True
        termination_reason = "sop_completed"
        logger.info(f"SOP步骤完成退出: {current_step} > {len(updated_sop_detail.steps)} + 3")
    # 安全退出：如果没有SOP步骤且已执行了8步，才结束
    elif (not updated_sop_detail.steps or len(updated_sop_detail.steps) == 0) and current_step >= 8:
        is_complete = True
        termination_reason = "no_sop_fallback"
        logger.info(f"无SOP退出: {current_step} >= 8")
    
    # 更新诊断进度
    updated_progress = DiagnosisProgress(
        current_step=current_step,
        max_steps=diagnosis_progress.max_steps,
        is_complete=is_complete,
        confidence_score=min(current_step / max(updated_sop_detail.total_steps, 1), 1.0),
        termination_reason=termination_reason
    )
    
    return {
        "diagnosis_progress": updated_progress,
        "diagnosis_results": diagnosis_results,
        "sop_detail": updated_sop_detail,
        "sop_loaded": sop_loaded
    }


def finalize_diagnosis_report(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """完成诊断报告节点 - 基于严格的SOP执行结果"""
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=configurable.answer_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    
    # 获取状态信息
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    sop_detail = state.get("sop_detail", SOPDetail())
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    diagnosis_results = state.get("diagnosis_results", [])
    
    # 使用提示词模板生成最终诊断报告
    formatted_prompt = diagnosis_report_instructions.format(
        current_date=get_current_date(),
        fault_ip=question_analysis.fault_ip or '未提供',
        fault_time=question_analysis.fault_time or '未提供',
        fault_info=question_analysis.fault_info or '未提供',
        sop_id=question_analysis.sop_id or '未指定',
        current_step=diagnosis_progress.current_step,
        total_steps=sop_detail.total_steps,
        completion_status='已完成' if diagnosis_progress.is_complete else '进行中',
        confidence_score=f"{diagnosis_progress.confidence_score:.2f}",
        diagnosis_results='\n'.join(diagnosis_results) if diagnosis_results else '未进行诊断'
    )
    
    response = llm.invoke(formatted_prompt)
    
    final_message = f"""
{response.content}

📊 诊断执行摘要：
- 使用SOP：{question_analysis.sop_id}
- 执行步骤：{diagnosis_progress.current_step}/{sop_detail.total_steps}
- 完成状态：{'✅ 已完成' if diagnosis_progress.is_complete else '🔄 进行中'}
- 置信度：{diagnosis_progress.confidence_score:.1%}

⚠️ 重要提醒：
以上诊断结果基于SOP执行。在执行任何操作前，请确认系统状态并评估风险。
"""
    
    return {
        "messages": [AIMessage(content=final_message)],
        "final_diagnosis": response.content
    }


# 路由函数 - 简化版本
def check_info_sufficient(state: DiagnosticState, config: RunnableConfig) -> str:
    """检查信息是否充足"""
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    return "plan_tools" if question_analysis.info_sufficient else "finalize_answer"


def evaluate_diagnosis_progress(state: DiagnosticState, config: RunnableConfig) -> str:
    """评估诊断进度，根据执行情况决定下一步"""
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    
    # 安全检查：使用动态最大步骤限制
    max_steps = max(diagnosis_progress.max_steps, 20)  # 动态设置，至少20步
    if diagnosis_progress.current_step >= max_steps:
        logger.warning(f"强制终止：步骤数达到安全上限 {diagnosis_progress.current_step}/{max_steps}")
        return "finalize_answer"
    
    # 如果诊断完成，生成最终报告
    if diagnosis_progress.is_complete:
        logger.info(f"诊断完成: {diagnosis_progress.termination_reason}")
        return "finalize_answer"
    else:
        # 继续执行下一步
        logger.info(f"继续执行，当前步骤: {diagnosis_progress.current_step}")
        return "plan_tools"


# 创建诊断Agent图 - 简化版本
builder = StateGraph(DiagnosticState, config_schema=Configuration)

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

# 修复：使用tools_condition来决定是否有工具调用
builder.add_conditional_edges(
    "plan_tools",
    tools_condition,
    {
        "tools": "approval",
        "continue": "reflection"  # 如果没有工具调用，也进入反思环节
    }
)

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
graph_image = graph.get_graph().draw_mermaid_png()
with open("diagnostic_agent_graph.png", "wb") as f: 
    f.write(graph_image)
print("图已保存到: diagnostic_agent_graph.png")