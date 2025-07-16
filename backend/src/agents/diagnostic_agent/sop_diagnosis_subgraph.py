"""
SOP诊断子图 - 专门处理故障诊断SOP流程
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState, QuestionAnalysis, DiagnosisProgress, SOPDetail
from .prompts import (
    get_current_datetime, get_question_analysis_prompt, get_missing_info_prompt,
    tool_planning_instructions, diagnosis_report_instructions, reflection_instructions
)
from .schemas import QuestionInfoExtraction, DiagnosisReflectionOutput
from .tools import all_tools
from .utils import (
    merge_field, check_approval_needed, is_already_approved, process_sop_loading,
    update_diagnosis_step, check_diagnosis_completion, check_info_sufficient,
    check_tool_calls, extract_diagnosis_results_from_messages,
    format_diagnosis_results_for_prompt, is_sop_loaded
)

logger = logging.getLogger(__name__)


def analyze_question_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """问题分析节点 - 支持多轮补充四要素"""
    print(f"✅ 执行节点: analyze_question_node")
    configurable = Configuration.from_runnable_config(config)
    
    messages = state.get("messages", [])
    user_question = messages[-1].content if messages else ""
    
    # 四要素分析流程
    llm = configurable.create_llm(model_name=configurable.query_generator_model,temperature=configurable.question_analysis_temperature)
    
    # 获取当前已有的四要素信息
    current_analysis = state.get("question_analysis", QuestionAnalysis())
    
    # 使用提示词模板函数生成提示词
    prompt = get_question_analysis_prompt(user_question, current_analysis)
    
    # 使用结构化输出
    structured_llm = llm.with_structured_output(QuestionInfoExtraction)
    result = structured_llm.invoke(prompt)
    
    merged_analysis = QuestionAnalysis(
        fault_ip=merge_field(result.fault_ip, current_analysis.fault_ip),
        fault_time=merge_field(result.fault_time, current_analysis.fault_time, "fault_time"),
        fault_info=merge_field(result.fault_info, current_analysis.fault_info),
        sop_id=merge_field(result.sop_id, current_analysis.sop_id)
    )
    
    # 检查四要素是否都完整
    info_sufficient = (
        merged_analysis.fault_ip and merged_analysis.fault_ip != "待提取" and
        merged_analysis.fault_time and merged_analysis.fault_time != "待提取" and
        merged_analysis.fault_info and merged_analysis.fault_info != "待提取" and
        merged_analysis.sop_id and merged_analysis.sop_id != "待提取"
    )
    
    # 生成缺失字段列表
    missing_fields = []
    if not merged_analysis.fault_ip or merged_analysis.fault_ip == "待提取": missing_fields.append("故障IP")
    if not merged_analysis.fault_time or merged_analysis.fault_time == "待提取": missing_fields.append("故障时间")
    if not merged_analysis.fault_info or merged_analysis.fault_info == "待提取": missing_fields.append("故障现象")
    if not merged_analysis.sop_id or merged_analysis.sop_id == "待提取": missing_fields.append("排查SOP编号")
    
    merged_analysis.missing_fields = missing_fields
    merged_analysis.info_sufficient = info_sufficient
    
    logger.info(f"四要素分析: 充足={info_sufficient}, 缺失={missing_fields}")
    
    return {
        "question_analysis": merged_analysis
    }


def plan_diagnosis_tools_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """工具规划节点 - 严格按照SOP执行"""
    print(f"✅ 执行节点: plan_diagnosis_tools_node")
    configurable = Configuration.from_runnable_config(config)
    llm = configurable.create_llm(model_name=configurable.query_generator_model,temperature=configurable.tool_planning_temperature)
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(all_tools)
    
    # 构建工具规划提示
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    sop_detail = state.get("sop_detail", SOPDetail())
    sop_state = "loaded" if is_sop_loaded(sop_detail) else "none"
    
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
    
    if not has_tool_calls: 
        logger.warning("LLM没有生成任何工具调用，这可能导致诊断提前结束")
    
    return {"messages": [response]}


def approval_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """SOP执行确认节点 - 简化版本"""
    print(f"✅ 执行节点: approval_node")
    
    # 检查是否需要审批
    approval_info = check_approval_needed(state)
    if not approval_info: 
        return {}  # 无需审批，直接继续
    
    # 检查是否已审批过
    if is_already_approved(state, approval_info):
        logger.info(f"步骤已审批过，跳过: {approval_info['step_id']}")
        return {}  # 已审批，直接继续
    
    # 执行审批流程
    step_info = approval_info["step_info"]
    step_id = approval_info["step_id"]
    tool_calls = approval_info["tool_calls"]
    sop_id = approval_info["sop_id"]
    
    logger.info(f"触发审批流程: SOP {sop_id}, 步骤: {step_info.action}")
    
    # 构建工具描述
    tool_descriptions = [
        f"工具: {tc.get('name', '')}, 参数: {tc.get('args', {})}"
        for tc in tool_calls
    ]
    
    # 中断并请求用户确认
    from langgraph.types import interrupt
    interrupt_info = {
        "message": f"按照SOP '{sop_id}' 要求，即将执行需要审批的步骤:\n\n"
                   f"**步骤详情:** {step_info.action}\n"
                   f"**计划操作:**\n" + "\n".join(tool_descriptions) +
                   f"\n\n确认执行？",
        "tool_calls": tool_calls,
        "sop_id": sop_id,
        "current_sop_step": step_info.action,
        "suggestion_type": "sop_execution"
    }
    
    # 调用interrupt并处理用户确认结果
    user_approved = interrupt(interrupt_info)
    logger.info(f"用户审批结果: {user_approved}")
    
    if user_approved:
        # 审批通过，更新SOP步骤的审批状态
        sop_detail = state.get("sop_detail", SOPDetail())
        updated_steps = []
        
        for step in sop_detail.steps:
            if step.action == step_info.action:
                # 更新匹配步骤的审批状态
                step.approved = True
                step.approved_at = get_current_datetime()
                step.approval_id = step_id
                logger.info(f"步骤审批通过，更新审批状态: {step_id}")
            updated_steps.append(step)
        
        updated_sop_detail = SOPDetail(
            sop_id=sop_detail.sop_id,
            title=sop_detail.title,
            description=sop_detail.description,
            steps=updated_steps,
            total_steps=sop_detail.total_steps
        )
        
        return {"sop_detail": updated_sop_detail}
    else:
        # 用户取消，中止执行
        diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
        return {
            "messages": [AIMessage(content="用户取消了SOP步骤执行，诊断流程已中止。")],
            "diagnosis_progress": DiagnosisProgress(
                current_step=diagnosis_progress.current_step,
                max_steps=diagnosis_progress.max_steps,
                is_complete=True,
                termination_reason="user_cancelled"
            )
        }


def reflect_diagnosis_progress_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """诊断反思节点 - 使用LLM智能决策下一步行动"""
    print(f"✅ 执行节点: reflect_diagnosis_progress_node")
    configurable = Configuration.from_runnable_config(config)
    
    # 获取当前状态
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    sop_detail = state.get("sop_detail", SOPDetail())
    messages = state.get("messages", [])
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    report_generated = state.get("report_generated", False)
    
    # 1. 处理SOP加载结果
    updated_sop_detail = process_sop_loading(messages, sop_detail)
    
    # 2. 更新诊断步骤
    current_step, has_new_execution, tool_name = update_diagnosis_step(
        messages, diagnosis_progress.current_step
    )
    
    # 3. 更新诊断结果
    diagnosis_results = extract_diagnosis_results_from_messages(messages)
    
    # 4. 获取用户最新输入
    user_input = ""
    if messages:
        user_input = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    
    # 5. 使用LLM进行智能决策
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=0.3
    )
    
    structured_llm = llm.with_structured_output(DiagnosisReflectionOutput)
    
    formatted_prompt = reflection_instructions.format(
        fault_info=question_analysis.fault_info or '未提供',
        current_step=current_step,
        total_steps=updated_sop_detail.total_steps,
        sop_state="loaded" if is_sop_loaded(updated_sop_detail) else "none",
        report_generated=report_generated,
        diagnosis_results=format_diagnosis_results_for_prompt(diagnosis_results),
        user_input=user_input
    )
    
    reflection_result = structured_llm.invoke(formatted_prompt)
    logger.info(f"反思决策结果: {reflection_result.action}, 完成状态: {reflection_result.is_complete}")
    
    # 6. 根据LLM决策执行相应行动
    if reflection_result.action == "answer_question":
        # 基于历史信息回答用户追问
        completed_progress = DiagnosisProgress(
            current_step=diagnosis_progress.current_step,
            max_steps=diagnosis_progress.max_steps,
            is_complete=True,
            termination_reason="answer_completed"
        )
        return {
            "messages": [AIMessage(content=reflection_result.response_content)],
            "diagnosis_progress": completed_progress,
            "sop_detail": updated_sop_detail
        }
    
    elif reflection_result.action == "generate_report":
        # 生成诊断报告
        logger.info("LLM决策：生成诊断报告")
        
        report_llm = configurable.create_llm(
            model_name=configurable.answer_model,
            temperature=configurable.final_report_temperature
        )
        
        formatted_prompt = diagnosis_report_instructions.format(
            current_date=get_current_datetime(),
            fault_ip=question_analysis.fault_ip or '未提供',
            fault_time=question_analysis.fault_time or '未提供',
            fault_info=question_analysis.fault_info or '未提供',
            sop_id=question_analysis.sop_id or '未指定',
            current_step=current_step,
            total_steps=updated_sop_detail.total_steps,
            completion_status='已完成',
            diagnosis_results='\n'.join(diagnosis_results) if diagnosis_results else '未进行诊断'
        )
        
        response = report_llm.invoke(formatted_prompt)
        
        final_message = f"""
{response.content}

📊 诊断执行摘要：
- 使用SOP：{question_analysis.sop_id}
- 执行步骤：{current_step}/{updated_sop_detail.total_steps}
- 完成状态：✅ 已完成

⚠️ 重要提醒：
以上诊断结果基于SOP执行。在执行任何操作前，请确认系统状态并评估风险。
"""
        
        updated_progress = DiagnosisProgress(
            current_step=current_step,
            max_steps=diagnosis_progress.max_steps,
            is_complete=True,
            termination_reason=reflection_result.termination_reason
        )
        
        return {
            "messages": [AIMessage(content=final_message)],
            "diagnosis_progress": updated_progress,
            "sop_detail": updated_sop_detail,
            "final_diagnosis": response.content,
            "report_generated": True
        }
    
    else:  # continue
        # 继续诊断
        logger.info("LLM决策：继续诊断")
        
        updated_progress = DiagnosisProgress(
            current_step=current_step,
            max_steps=diagnosis_progress.max_steps,
            is_complete=False,
            termination_reason="continue"
        )
        
        return {
            "diagnosis_progress": updated_progress,
            "sop_detail": updated_sop_detail
        }


def handle_insufficient_info_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """处理信息不足的情况，提示用户补充缺失信息"""
    print(f"✅ 执行节点: handle_insufficient_info_node")
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    
    # 使用提示词模板函数生成缺失信息提示
    missing_info_prompt = get_missing_info_prompt(question_analysis)
    
    return {
        "messages": [AIMessage(content=missing_info_prompt)]
    }


def evaluate_diagnosis_progress(state: DiagnosticState, config: RunnableConfig) -> str:
    """评估诊断进度，根据执行情况决定下一步"""
    print(f"✅ 执行路由函数: evaluate_diagnosis_progress")
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    
    # 如果诊断已标记为完成，直接结束
    if diagnosis_progress.is_complete:
        logger.info(f"诊断完成，流程结束: {diagnosis_progress.termination_reason}")
        print(f"✅ 路由结果: END (诊断完成)")
        return END
    
    # 安全检查：防止无限循环
    if diagnosis_progress.current_step >= diagnosis_progress.max_steps:
        logger.warning(f"达到最大步骤限制，强制结束: {diagnosis_progress.current_step}/{diagnosis_progress.max_steps}")
        print(f"✅ 路由结果: END (达到最大步骤)")
        return END
    
    # 继续执行下一步
    logger.info(f"继续执行，当前步骤: {diagnosis_progress.current_step}")
    print(f"✅ 路由结果: plan_tools (继续诊断)")
    return "plan_tools"


def create_sop_diagnosis_subgraph():
    """创建SOP诊断子图"""
    
    # 创建工具执行节点
    tool_node = ToolNode(all_tools)
    
    # 包装工具节点以添加打印
    def execute_tools_node(state, config):
        print(f"✅ 执行节点: execute_tools_node")
        return tool_node.invoke(state, config)
    
    # 创建子图
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    
    # 添加节点
    builder.add_node("analyze_question", analyze_question_node)
    builder.add_node("handle_insufficient_info", handle_insufficient_info_node)
    builder.add_node("plan_tools", plan_diagnosis_tools_node)
    builder.add_node("approval", approval_node)
    builder.add_node("execute_tools", execute_tools_node)
    builder.add_node("reflection", reflect_diagnosis_progress_node)
    
    # 设置流程
    builder.add_edge(START, "analyze_question")
    builder.add_conditional_edges(
        "analyze_question", 
        check_info_sufficient, 
        ["plan_tools", "handle_insufficient_info"]
    )
    builder.add_edge("handle_insufficient_info", END)
    builder.add_conditional_edges(
        "plan_tools",
        check_tool_calls,
        {"approval": "approval", "reflection": "reflection"}
    )
    builder.add_edge("approval", "execute_tools")
    builder.add_edge("execute_tools", "reflection")
    builder.add_conditional_edges(
        "reflection", 
        evaluate_diagnosis_progress, 
        ["plan_tools", END]
    )
    
    return builder.compile()