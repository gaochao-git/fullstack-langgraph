"""
故障诊断代理 - 使用LangGraph子图架构
按照官方文档的方法实现：主图负责路由，子图处理具体逻辑
"""

import os
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState, QuestionAnalysis, DiagnosisProgress, SOPDetail
from .schemas import IntentAnalysisOutput, QuestionInfoExtraction, DiagnosisReflectionOutput
from .prompts import (
    get_current_datetime, get_question_analysis_prompt, get_missing_info_prompt,
    tool_planning_instructions, diagnosis_report_instructions, reflection_instructions
)
from .tools import all_tools
from .utils import (
    merge_field, check_approval_needed, is_already_approved, process_sop_loading,
    update_diagnosis_step, check_info_sufficient, check_tool_calls, save_graph_image,
    compile_graph_with_checkpointer, extract_diagnosis_results_from_messages,
    format_diagnosis_results_for_prompt, is_sop_loaded
)

logger = logging.getLogger(__name__)


# ================================
# 主图节点：意图分析和路由
# ================================

def analyze_intent_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    意图分析节点 - 判断用户是否需要SOP诊断还是普通问答
    """
    print(f"✅ 执行节点: analyze_intent_node")
    
    configurable = Configuration.from_runnable_config(config)
    messages = state.get("messages", [])
    
    if not messages:
        return {"intent": "general_qa", "intent_reason": "无用户输入"}
    
    user_question = messages[-1].content if messages else ""
    
    # 使用LLM分析用户意图
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=0.1  # 低温度确保分类准确
    )
    
    intent_analysis_prompt = f"""
你是一个专业的运维助手意图分析器。请分析用户的问题，判断用户是否需要故障诊断SOP还是普通问答。

判断标准：

1. 故障诊断SOP (sop_diagnosis)：
   - 用户明确提到故障、报错、异常、问题等需要排查的情况
   - 用户提到需要排查、诊断、解决具体问题
   - 用户描述了具体的故障现象和影响
   - 用户提到了IP、时间、错误信息等故障要素
   - 用户明确要求执行故障诊断流程或SOP
   - 关键词：故障、报错、异常、排查、诊断、SOP、问题解决、修复、恢复

2. 普通问答 (general_qa)：
   - 用户询问技术知识、操作方法、概念解释
   - 用户进行日常聊天、问候、闲聊
   - 用户询问系统信息、配置说明、状态查询
   - 用户询问历史记录、统计信息
   - 用户咨询如何使用某个功能或工具
   - 不涉及具体故障排查的技术问题
   - 关键词：如何、什么是、怎么、配置、安装、使用、查询、状态

注意：
- 如果用户只是询问故障相关概念或方法，不涉及具体故障排查，应归类为general_qa
- 如果用户描述了具体的故障现象并需要排查，应归类为sop_diagnosis
- 优先考虑用户的具体意图，而不是简单的关键词匹配

用户问题：{user_question}

请分析用户意图，返回分类结果和简要理由。
"""
    
    structured_llm = llm.with_structured_output(IntentAnalysisOutput)
    result = structured_llm.invoke(intent_analysis_prompt)
    
    logger.info(f"意图分析结果: {result.intent} - {result.reason}")
    
    return {
        "intent": result.intent,
        "intent_reason": result.reason
    }


def route_to_subgraph(state: DiagnosticState, config: RunnableConfig) -> Literal["sop_diagnosis", "general_qa"]:
    """
    路由函数 - 根据意图分析结果决定进入哪个子图
    """
    print(f"✅ 执行路由函数: route_to_subgraph")
    
    intent = state.get("intent", "general_qa")
    
    # 确保intent值有效
    if intent not in ["sop_diagnosis", "general_qa"]:
        logger.warning(f"无效的意图值: {intent}，默认使用general_qa")
        intent = "general_qa"
    
    logger.info(f"路由决策: {intent}")
    print(f"✅ 路由结果: {intent}")
    
    return intent


# ================================
# SOP诊断子图节点
# ================================

def analyze_question_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """问题分析节点 - 支持多轮补充四要素"""
    print(f"✅ 执行SOP子图节点: analyze_question_node")
    configurable = Configuration.from_runnable_config(config)
    
    messages = state.get("messages", [])
    user_question = messages[-1].content if messages else ""
    
    # 四要素分析流程
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=configurable.question_analysis_temperature
    )
    
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


def handle_insufficient_info_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """处理信息不足的情况，提示用户补充缺失信息"""
    print(f"✅ 执行SOP子图节点: handle_insufficient_info_node")
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    
    # 使用提示词模板函数生成缺失信息提示
    missing_info_prompt = get_missing_info_prompt(question_analysis)
    
    return {
        "messages": [AIMessage(content=missing_info_prompt)]
    }


def plan_diagnosis_tools_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """工具规划节点 - 严格按照SOP执行"""
    print(f"✅ 执行SOP子图节点: plan_diagnosis_tools_node")
    configurable = Configuration.from_runnable_config(config)
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=configurable.tool_planning_temperature
    )
    
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
    """SOP执行确认节点"""
    print(f"✅ 执行SOP子图节点: approval_node")
    
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
    print(f"✅ 执行SOP子图节点: reflect_diagnosis_progress_node")
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


def evaluate_diagnosis_progress(state: DiagnosticState, config: RunnableConfig) -> str:
    """评估诊断进度，根据执行情况决定下一步"""
    print(f"✅ 执行SOP子图路由: evaluate_diagnosis_progress")
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


# ================================
# 普通问答子图节点
# ================================

def analyze_question_context_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """分析问题上下文节点 - 理解用户问题并准备回答"""
    print(f"✅ 执行问答子图节点: analyze_question_context_node")
    
    messages = state.get("messages", [])
    if not messages:
        return {"qa_context": "无历史对话"}
    
    # 获取用户问题
    user_question = messages[-1].content if messages else ""
    
    # 构建对话上下文
    context_parts = []
    
    # 添加诊断历史（如果有）
    diagnosis_results = extract_diagnosis_results_from_messages(messages, max_results=3)
    if diagnosis_results:
        context_parts.append("相关诊断历史：")
        context_parts.extend(diagnosis_results[:3])  # 最近3个诊断结果
    
    # 添加最近对话
    if len(messages) > 1:
        context_parts.append("\n最近对话：")
        recent_messages = messages[-6:] if len(messages) > 6 else messages[:-1]
        for i, msg in enumerate(recent_messages):
            role = "用户" if i % 2 == 0 else "助手"
            content = getattr(msg, 'content', str(msg))[:150]  # 限制长度
            context_parts.append(f"{role}: {content}")
    
    qa_context = "\n".join(context_parts) if context_parts else "无历史对话"
    
    logger.info(f"问答上下文分析完成，历史诊断: {len(diagnosis_results)}, 对话轮次: {len(messages)}")
    
    return {
        "qa_context": qa_context,
        "user_question": user_question
    }


def generate_answer_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """生成回答节点 - 基于用户问题和上下文生成专业回答"""
    print(f"✅ 执行问答子图节点: generate_answer_node")
    
    configurable = Configuration.from_runnable_config(config)
    
    # 获取状态信息
    user_question = state.get("user_question", "")
    qa_context = state.get("qa_context", "")
    messages = state.get("messages", [])
    
    # 如果没有用户问题，从消息中获取
    if not user_question and messages:
        user_question = messages[-1].content if messages else ""
    
    # 创建LLM实例
    llm = configurable.create_llm(
        model_name=configurable.answer_model,
        temperature=configurable.final_report_temperature
    )
    
    # 生成回答提示词
    prompt = f"""您是专业的运维技术助手，支持故障诊断、运维问答和日常交流。

用户问题：{user_question}

对话历史上下文：
{qa_context}

请根据用户问题类型回答：
- 如果是运维技术问题，提供专业的技术指导
- 如果是普通聊天，自然友好地回应
- 如果涉及之前的诊断内容，可以引用相关信息
- 保持简洁明了，不需要生成报告格式

请直接回答用户的问题。"""
    
    # 生成回答
    response = llm.invoke(prompt)
    
    logger.info(f"问答回答生成完成")
    
    return {
        "messages": [AIMessage(content=response.content)]
    }


# ================================
# 子图创建函数
# ================================

def create_sop_diagnosis_subgraph():
    """创建SOP诊断子图"""
    
    # 创建工具执行节点
    tool_node = ToolNode(all_tools)
    
    # 包装工具节点以添加打印
    def execute_tools_node(state, config):
        print(f"✅ 执行SOP子图节点: execute_tools_node")
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


# 旧版本的create_general_qa_subgraph已移动到general_qa_subgraph.py文件中
# 这里保留导入以保持兼容性
from .general_qa_subgraph import create_general_qa_subgraph


# ================================
# 主图创建和编译
# ================================

def create_main_graph():
    """创建主图 - 包含路由逻辑和两个子图"""
    
    # 创建主图
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    
    # 添加意图分析节点
    builder.add_node("analyze_intent", analyze_intent_node)
    
    # 创建并添加子图 - 按照官方文档的方式
    sop_diagnosis_subgraph = create_sop_diagnosis_subgraph()
    general_qa_subgraph = create_general_qa_subgraph()
    
    # 将子图作为节点添加到主图
    builder.add_node("sop_diagnosis", sop_diagnosis_subgraph)
    builder.add_node("general_qa", general_qa_subgraph)
    
    # 设置路由
    builder.add_edge(START, "analyze_intent")
    builder.add_conditional_edges(
        "analyze_intent",
        route_to_subgraph,
        {
            "sop_diagnosis": "sop_diagnosis",
            "general_qa": "general_qa"
        }
    )
    
    # 两个子图执行完成后都结束
    builder.add_edge("sop_diagnosis", END)
    builder.add_edge("general_qa", END)
    
    return builder


def compile_main_graph():
    """编译主图"""
    builder = create_main_graph()
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    compiled_graph_tuple = compile_graph_with_checkpointer(builder, checkpointer_type)
    
    # compile_graph_with_checkpointer 返回 (graph, mode_name) 元组
    compiled_graph = compiled_graph_tuple[0] if isinstance(compiled_graph_tuple, tuple) else compiled_graph_tuple
    
    # 保存图片的逻辑已经在 compile_graph_with_checkpointer 中处理了
    
    return compiled_graph_tuple


# 创建builder并导出（用于PostgreSQL模式）
builder = create_main_graph()

# 导出编译后的图
graph = compile_main_graph()

# 保持兼容性，提供原有的接口
def get_diagnostic_agent():
    """获取诊断代理图实例 - 保持向后兼容性"""
    return graph


# 导出主要组件
__all__ = ["graph", "builder", "get_diagnostic_agent", "create_main_graph", "compile_main_graph"]