"""
故障诊断代理 - 使用LangGraph架构，基于SOP知识库和智能工具选择
重构版本：参考调研agent的结构，优化状态管理和节点职责
"""

import os
import json
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from .configuration import Configuration
from .state import (DiagnosticState,QuestionAnalysis,DiagnosisProgress,SOPDetail,SOPStep)
from .prompts import (get_current_datetime,get_question_analysis_prompt,get_missing_info_prompt,tool_planning_instructions,diagnosis_report_instructions)
from .schemas import QuestionInfoExtraction
from .tools import all_tools
from .utils import (merge_field, check_approval_needed, is_already_approved,process_sop_loading, update_diagnosis_step, check_diagnosis_completion,check_info_sufficient, check_tool_calls)
logger = logging.getLogger(__name__)


# 节点函数 - 参考调研agent的清晰结构
def analyze_question_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """问题分析节点 - 支持多轮补充四要素"""
    configurable = Configuration.from_runnable_config(config)
    llm = configurable.create_llm(model_name=configurable.query_generator_model,temperature=configurable.question_analysis_temperature)
    messages = state.get("messages", [])
    user_question = messages[-1].content if messages else ""
    # 获取当前已有的四要素信息
    current_analysis = state.get("question_analysis", QuestionAnalysis())
    # 使用提示词模板函数生成提示词
    prompt = get_question_analysis_prompt(user_question, current_analysis)
    
    # 使用结构化输出
    # 注意：配合 schemas.py 中的 pydantic_v1 使用
    # 这样 LangChain 会自动降级使用提示词方式而不是 response_format
    # 避免 DeepSeek API 的兼容性问题
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
        "user_question": user_question,
        "question_analysis": merged_analysis
    }


def plan_diagnosis_tools_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """工具规划节点 - 严格按照SOP执行"""
    configurable = Configuration.from_runnable_config(config)
    llm = configurable.create_llm(model_name=configurable.query_generator_model,temperature=configurable.tool_planning_temperature)
    # 绑定工具到LLM
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
    if not has_tool_calls: logger.warning("LLM没有生成任何工具调用，这可能导致诊断提前结束")
    # 返回新的消息，LangGraph会将其添加到状态中
    return {"messages": [response]}


def approval_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    SOP执行确认节点 - 简化版本
    1. 检查是否需要审批
    2. 检查是否已审批过  
    3. 执行审批流程
    """
    # 1. 检查是否需要审批
    approval_info = check_approval_needed(state)
    if not approval_info: return {}  # 无需审批，直接继续
    
    # 2. 检查是否已审批过
    if is_already_approved(state, approval_info):
        logger.info(f"步骤已审批过，跳过: {approval_info['step_id']}")
        return {}  # 已审批，直接继续
    
    # 3. 执行审批流程
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
        # 审批通过，添加到已审批列表
        approved_steps = state.get("approved_steps", []) + [step_id]
        logger.info(f"步骤审批通过，添加到已审批列表: {step_id}")
        return {"approved_steps": approved_steps}
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
    """诊断反思节点 - 简化版本"""
    # 获取当前状态
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    sop_detail = state.get("sop_detail", SOPDetail())
    messages = state.get("messages", [])
    
    # 1. 处理SOP加载结果
    updated_sop_detail, sop_loaded = process_sop_loading(messages, sop_detail)
    if not sop_loaded:
        sop_loaded = state.get("sop_loaded", False)
    
    # 2. 更新诊断步骤
    current_step, has_new_execution, tool_name = update_diagnosis_step(
        messages, diagnosis_progress.current_step
    )
    
    # 3. 更新诊断结果
    diagnosis_results = list(state.get("diagnosis_results", []))
    if has_new_execution and messages:
        last_message = messages[-1]
        diagnosis_results.append(f"Tool: {last_message.name}, Result: {last_message.content}")
    
    # 4. 检查诊断完成状态
    is_complete, termination_reason = check_diagnosis_completion(
        current_step, diagnosis_progress.max_steps, updated_sop_detail
    )
    
    # 5. 构建更新后的进度
    updated_progress = DiagnosisProgress(
        current_step=current_step,
        max_steps=diagnosis_progress.max_steps,
        is_complete=is_complete,
        termination_reason=termination_reason
    )
    
    return {
        "diagnosis_progress": updated_progress,
        "diagnosis_results": diagnosis_results,
        "sop_detail": updated_sop_detail,
        "sop_loaded": sop_loaded
    }


def handle_insufficient_info_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """处理信息不足的情况，提示用户补充缺失信息"""
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    
    # 使用提示词模板函数生成缺失信息提示
    missing_info_prompt = get_missing_info_prompt(question_analysis)
    
    return {
        "messages": [AIMessage(content=missing_info_prompt)]
    }


def finalize_diagnosis_report_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """智能最终回答节点 - 支持SOP诊断、运维问答、普通聊天"""
    configurable = Configuration.from_runnable_config(config)
    
    # 获取状态信息
    messages = state.get("messages", [])
    user_question = state.get("user_question", "")
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    sop_detail = state.get("sop_detail", SOPDetail())
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    diagnosis_results = state.get("diagnosis_results", [])
    sop_loaded = state.get("sop_loaded", False)
    report_generated = state.get("report_generated", False)
    
    # 判断对话类型和回答策略
    response_type = determine_response_type(
        user_question, messages, question_analysis, 
        diagnosis_progress, sop_loaded, diagnosis_results, report_generated
    )
    
    logger.info(f"响应类型判断: {response_type}")
    
    # 初始化推理模型
    llm = configurable.create_llm(
        model_name=configurable.answer_model,
        temperature=configurable.final_report_temperature
    )
    
    if response_type == "diagnosis_report":
        # 生成完整的SOP诊断报告
        formatted_prompt = diagnosis_report_instructions.format(
            current_date=get_current_datetime(),
            fault_ip=question_analysis.fault_ip or '未提供',
            fault_time=question_analysis.fault_time or '未提供',
            fault_info=question_analysis.fault_info or '未提供',
            sop_id=question_analysis.sop_id or '未指定',
            current_step=diagnosis_progress.current_step,
            total_steps=sop_detail.total_steps,
            completion_status='已完成' if diagnosis_progress.is_complete else '进行中',
            diagnosis_results='\n'.join(diagnosis_results) if diagnosis_results else '未进行诊断'
        )
        
        response = llm.invoke(formatted_prompt)
        
        final_message = f"""
{response.content}

📊 诊断执行摘要：
- 使用SOP：{question_analysis.sop_id}
- 执行步骤：{diagnosis_progress.current_step}/{sop_detail.total_steps}
- 完成状态：{'✅ 已完成' if diagnosis_progress.is_complete else '🔄 进行中'}

⚠️ 重要提醒：
以上诊断结果基于SOP执行。在执行任何操作前，请确认系统状态并评估风险。
"""
        
        return {
            "messages": [AIMessage(content=final_message)],
            "final_diagnosis": response.content,
            "report_generated": True
        }
    
    else:
        # 运维问答或普通聊天
        conversation_context = build_conversation_context(messages, diagnosis_results)
        
        prompt = f"""您是专业的运维技术助手，支持故障诊断、运维问答和日常交流。

用户问题：{user_question}

对话历史上下文：
{conversation_context}

请根据用户问题类型回答：
- 如果是运维技术问题，提供专业的技术指导
- 如果是普通聊天，自然友好地回应
- 如果涉及之前的诊断内容，可以引用相关信息
- 保持简洁明了，不需要生成报告格式

请直接回答用户的问题。"""
        
        response = llm.invoke(prompt)
        
        return {
            "messages": [AIMessage(content=response.content)]
        }


def determine_response_type(user_question, messages, question_analysis, diagnosis_progress, sop_loaded, diagnosis_results, report_generated=False):
    """判断回答类型：是否需要生成诊断报告"""
    
    # 1. 用户明确要求生成报告
    report_keywords = ["生成报告", "诊断报告", "故障报告", "输出报告", "总结报告"]
    if any(keyword in user_question for keyword in report_keywords):
        return "diagnosis_report"
    
    # 2. 完成了完整的SOP诊断流程且未生成过报告
    if (diagnosis_progress and diagnosis_progress.is_complete and 
        sop_loaded and len(diagnosis_results) >= 2 and not report_generated):
        return "diagnosis_report"
    
    # 3. 其他情况都是普通回答
    return "general_answer"


def build_conversation_context(messages, diagnosis_results):
    """构建对话上下文"""
    context_parts = []
    
    # 添加诊断历史（如果有）
    if diagnosis_results:
        context_parts.append("诊断历史：")
        context_parts.extend(diagnosis_results[-3:])  # 最近3个诊断结果
    
    # 添加最近对话
    if messages and len(messages) > 1:
        context_parts.append("\n最近对话：")
        recent_messages = messages[-4:] if len(messages) > 4 else messages[:-1]
        for i, msg in enumerate(recent_messages):
            role = "用户" if i % 2 == 0 else "助手"
            content = getattr(msg, 'content', str(msg))[:100]
            context_parts.append(f"{role}: {content}")
    
    return "\n".join(context_parts) if context_parts else "无历史对话"


# 路由函数 - 简化版本
def evaluate_diagnosis_progress(state: DiagnosticState, config: RunnableConfig) -> str:
    """评估诊断进度，根据执行情况决定下一步"""
    diagnosis_progress = state.get("diagnosis_progress", DiagnosisProgress())
    
    # 如果诊断已标记为完成，直接结束
    if diagnosis_progress.is_complete:
        logger.info(f"诊断完成: {diagnosis_progress.termination_reason}")
        return "finalize_answer"
    
    # 安全检查：防止无限循环
    if diagnosis_progress.current_step >= diagnosis_progress.max_steps:
        logger.warning(f"达到最大步骤限制，强制结束: {diagnosis_progress.current_step}/{diagnosis_progress.max_steps}")
        return "finalize_answer"
    
    # 继续执行下一步
    logger.info(f"继续执行，当前步骤: {diagnosis_progress.current_step}")
    return "plan_tools"


# 创建工具执行节点
tool_node = ToolNode(all_tools)
# 创建诊断Agent图 - 简化版本
builder = StateGraph(DiagnosticState, config_schema=Configuration)
# 添加节点
builder.add_node("analyze_question", analyze_question_node)
builder.add_node("handle_insufficient_info", handle_insufficient_info_node)
builder.add_node("plan_tools", plan_diagnosis_tools_node)
builder.add_node("approval", approval_node)
builder.add_node("execute_tools", tool_node)
builder.add_node("reflection", reflect_diagnosis_progress_node)
builder.add_node("finalize_answer", finalize_diagnosis_report_node)
builder.add_edge(START, "analyze_question")
builder.add_conditional_edges("analyze_question", check_info_sufficient, ["plan_tools", "handle_insufficient_info"])
# 修改：信息不足时等待用户补充，用户补充后重新回到analyze_question分析
builder.add_edge("handle_insufficient_info", END)
builder.add_conditional_edges("plan_tools",check_tool_calls,{"approval": "approval","reflection": "reflection"})
builder.add_edge("approval", "execute_tools")
builder.add_edge("execute_tools", "reflection")
builder.add_conditional_edges("reflection", evaluate_diagnosis_progress, ["plan_tools", "finalize_answer"])
builder.add_edge("finalize_answer", END)


# 编译图 - 根据环境变量决定是否使用checkpointer
checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")

if checkpointer_type == "postgres":
    # PostgreSQL模式：不在这里编译，在API请求时用async with编译
    graph = None
    print("📝 PostgreSQL模式：图将在API请求时用async with编译")
else:
    # 内存模式：直接使用MemorySaver
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer, name="diagnostic-agent")
    graph_image = graph.get_graph().draw_mermaid_png()
    # 获取当前文件所在目录并保存图片
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graph_image_path = os.path.join(current_dir, "graph.png")
    with open(graph_image_path, "wb") as f: f.write(graph_image)
    print(f"📝 内存模式：图已编译完成，已保存到 {graph_image_path}")