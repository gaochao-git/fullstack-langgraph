"""
故障诊断代理 - 使用LangGraph架构，基于SOP知识库和智能工具选择
重构版本：参考调研agent的结构，优化状态管理和节点职责
"""

import json
import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from agents.diagnostic_agent.configuration import Configuration
from agents.diagnostic_agent.state import (DiagnosticState,QuestionAnalysis,DiagnosisProgress,SOPDetail,SOPStep)
from agents.diagnostic_agent.prompts import (get_current_date,question_analysis_instructions,tool_planning_instructions,diagnosis_report_instructions)
from agents.diagnostic_agent.tools_and_schemas import QuestionInfoExtraction

# 导入工具
from tools import ssh_tool, sop_tool
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)


# 节点函数 - 参考调研agent的清晰结构
def analyze_question(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """问题分析节点 - 支持多轮补充四要素"""
    configurable = Configuration.from_runnable_config(config)
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=configurable.question_analysis_temperature
    )
    
    messages = state.get("messages", [])
    user_question = messages[-1].content if messages else ""
    
    # 获取当前已有的四要素信息
    current_analysis = state.get("question_analysis", QuestionAnalysis())
    
    # 调试：打印当前状态
    print(f"🔍 [DEBUG] 当前状态获取:")
    print(f"  - fault_ip: {current_analysis.fault_ip}")
    print(f"  - fault_time: {current_analysis.fault_time}")
    print(f"  - fault_info: {current_analysis.fault_info}")
    print(f"  - sop_id: {current_analysis.sop_id}")
    print(f"  - 用户输入: {user_question}")
    
    # 构建包含当前信息的提示词
    current_date = get_current_date()
    enhanced_prompt = f"""当前时间：{current_date}

用户最新输入：{user_question}

当前已有信息：
- 故障IP: {current_analysis.fault_ip or '待提取'}
- 故障时间: {current_analysis.fault_time or '待提取'}
- 故障现象: {current_analysis.fault_info or '待提取'}
- SOP编号: {current_analysis.sop_id or '待提取'}

请从用户输入中提取或更新故障诊断信息。如果用户提供了新信息，请更新对应字段；如果没有提供新信息，保持原有值。

请按照以下JSON格式返回：
{{
    "fault_ip": "故障IP地址（如果无法提取或用户未提供，填写'待提取'）",
    "fault_time": "故障时间（如果无法提取或用户未提供，填写'待提取'）",
    "fault_info": "故障现象描述（如果无法提取或用户未提供，填写'待提取'）",
    "sop_id": "SOP编号（如果无法提取或用户未提供，填写'待提取'）"
}}"""
    
    # 使用JSON模式兼容DeepSeek
    response = llm.invoke(enhanced_prompt)
    
    # 解析JSON响应
    import json
    import re
    try:
        result_dict = json.loads(response.content)
        result = QuestionInfoExtraction(**result_dict)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"JSON解析失败，使用正则提取: {e}")
        # 备用：正则表达式提取
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', user_question)
        time_match = re.search(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', user_question)
        sop_match = re.search(r'sop[_-]?\d+', user_question, re.IGNORECASE)
        
        result = QuestionInfoExtraction(
            fault_ip=ip_match.group() if ip_match else (current_analysis.fault_ip or "待提取"),
            fault_time=time_match.group() if time_match else (current_analysis.fault_time or "待提取"),
            fault_info="磁盘空间满" if "磁盘" in user_question or "空间" in user_question else (current_analysis.fault_info or "待提取"),
            sop_id=sop_match.group() if sop_match else (current_analysis.sop_id or "待提取")
        )
    
    # 调试：打印提取结果
    print(f"📤 [DEBUG] LLM/正则提取结果:")
    print(f"  - fault_ip: {result.fault_ip}")
    print(f"  - fault_time: {result.fault_time}")
    print(f"  - fault_info: {result.fault_info}")
    print(f"  - sop_id: {result.sop_id}")
    
    # 合并信息：优先使用新信息，无新信息时保持原值
    merged_analysis = QuestionAnalysis(
        fault_ip=result.fault_ip if result.fault_ip != "待提取" else (current_analysis.fault_ip or "待提取"),
        fault_time=result.fault_time if result.fault_time != "待提取" else (current_analysis.fault_time or "待提取"),
        fault_info=result.fault_info if result.fault_info != "待提取" else (current_analysis.fault_info or "待提取"),
        sop_id=result.sop_id if result.sop_id != "待提取" else (current_analysis.sop_id or "待提取")
    )
    
    # 调试：打印合并结果
    print(f"🔄 [DEBUG] 合并后状态:")
    print(f"  - fault_ip: {merged_analysis.fault_ip}")
    print(f"  - fault_time: {merged_analysis.fault_time}")
    print(f"  - fault_info: {merged_analysis.fault_info}")
    print(f"  - sop_id: {merged_analysis.sop_id}")
    
    # 检查四要素是否都完整
    info_sufficient = (
        merged_analysis.fault_ip and merged_analysis.fault_ip != "待提取" and
        merged_analysis.fault_time and merged_analysis.fault_time != "待提取" and
        merged_analysis.fault_info and merged_analysis.fault_info != "待提取" and
        merged_analysis.sop_id and merged_analysis.sop_id != "待提取"
    )
    
    # 生成缺失字段列表
    missing_fields = []
    if not merged_analysis.fault_ip or merged_analysis.fault_ip == "待提取":
        missing_fields.append("故障IP")
    if not merged_analysis.fault_time or merged_analysis.fault_time == "待提取":
        missing_fields.append("故障时间")
    if not merged_analysis.fault_info or merged_analysis.fault_info == "待提取":
        missing_fields.append("故障现象")
    if not merged_analysis.sop_id or merged_analysis.sop_id == "待提取":
        missing_fields.append("排查SOP编号")
    
    merged_analysis.missing_fields = missing_fields
    merged_analysis.info_sufficient = info_sufficient
    
    logger.info(f"四要素分析: 充足={info_sufficient}, 缺失={missing_fields}")
    
    return {
        "user_question": user_question,
        "question_analysis": merged_analysis
    }


def plan_diagnosis_tools(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """工具规划节点 - 严格按照SOP执行"""
    configurable = Configuration.from_runnable_config(config)
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=configurable.tool_planning_temperature
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
    if not has_tool_calls:
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
        
        # 从工具调用中找到匹配的SOP步骤
        current_step_info = None
        
        # 获取原始SOP数据（从最近的get_sop_content工具消息中）
        raw_sop_data = None
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and msg.name == "get_sop_content":
                try:
                    result = json.loads(msg.content)
                    if result.get("success") and result.get("sop_content"):
                        raw_sop_data = result["sop_content"]
                        break
                except (json.JSONDecodeError, TypeError):
                    continue
        
        if not raw_sop_data:
            logger.warning("无法获取原始SOP数据，跳过审批检查")
            return {}
        
        # 查找匹配的SOP步骤
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            
            # 跳过SOP加载相关的工具调用
            if tool_name in ["get_sop_content", "get_sop_detail", "list_sops", "search_sops"]:
                continue
                
            # 在原始SOP步骤中查找匹配的工具和命令
            for sop_step in raw_sop_data.get("steps", []):
                step_tool = sop_step.get("tool", "")
                step_command = sop_step.get("command", "")
                
                # 检查工具名称是否匹配
                if tool_name == step_tool:
                    # 如果有命令参数，检查命令是否匹配
                    if "command" in tool_args:
                        if tool_args["command"] == step_command:
                            current_step_info = SOPStep(
                                title=sop_step.get("action", ""),
                                description=sop_step.get("description", ""),
                                action=sop_step.get("action", ""),
                                requires_approval=sop_step.get("requires_approval", False),
                                status="pending"
                            )
                            break
                    else:
                        # 没有具体命令参数，只根据工具匹配
                        current_step_info = SOPStep(
                            title=sop_step.get("action", ""),
                            description=sop_step.get("description", ""),
                            action=sop_step.get("action", ""),
                            requires_approval=sop_step.get("requires_approval", False),
                            status="pending"
                        )
                        break
            
            # 找到匹配的步骤就退出
            if current_step_info:
                break
        
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
    
    # 检查是否有新的诊断工具执行（排除SOP工具）
    has_new_diagnostic_execution = False
    if messages and isinstance(messages[-1], ToolMessage):
        last_tool_name = messages[-1].name
        # 只有非SOP工具才算诊断步骤
        if last_tool_name not in ["get_sop_content", "get_sop_detail", "list_sops", "search_sops"]:
            current_step = diagnosis_progress.current_step + 1
            has_new_diagnostic_execution = True
            logger.info(f"检测到诊断工具执行: {last_tool_name}，步骤数更新为: {current_step}")
        else:
            current_step = diagnosis_progress.current_step
    else:
        # 没有新的工具执行，保持原步骤数
        current_step = diagnosis_progress.current_step
    
    # 从最新的ToolMessage中提取诊断结果
    diagnosis_results = list(state.get("diagnosis_results", []))
    if has_new_diagnostic_execution:
        last_message = messages[-1]
        diagnosis_results.append(f"Tool: {last_message.name}, Result: {last_message.content}")
    
    # 检查是否完成诊断 - 放宽条件，让诊断能够充分执行
    is_complete = False
    termination_reason = "continue"
    
    # 使用配置的max_steps进行退出判断
    max_steps = diagnosis_progress.max_steps
    
    # 达到最大步骤限制
    if current_step >= max_steps:
        is_complete = True
        termination_reason = "max_steps_reached"
        logger.warning(f"达到最大步骤限制退出: {current_step}/{max_steps}")
    # 检查SOP是否已完全执行
    elif (updated_sop_detail.steps and len(updated_sop_detail.steps) > 0 and 
          current_step >= len(updated_sop_detail.steps) and current_step >= 3):
        is_complete = True
        termination_reason = "sop_completed"
        logger.info(f"SOP步骤完成退出: {current_step} >= {len(updated_sop_detail.steps)}")
    
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


def handle_insufficient_info(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """处理信息不足的情况，提示用户补充缺失信息"""
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    
    # 显示当前信息状态
    info_status = []
    info_status.append(f"✅ 故障IP: {question_analysis.fault_ip}" if question_analysis.fault_ip and question_analysis.fault_ip != '待提取' else "❌ 故障IP: 待提取")
    info_status.append(f"✅ 故障时间: {question_analysis.fault_time}" if question_analysis.fault_time and question_analysis.fault_time != '待提取' else "❌ 故障时间: 待提取")
    info_status.append(f"✅ 故障现象: {question_analysis.fault_info}" if question_analysis.fault_info and question_analysis.fault_info != '待提取' else "❌ 故障现象: 待提取")
    info_status.append(f"✅ SOP编号: {question_analysis.sop_id}" if question_analysis.sop_id and question_analysis.sop_id != '待提取' else "❌ SOP编号: 待提取")
    
    # 构建提示信息
    missing_info_prompt = "❗ 故障诊断信息不完整，当前状态：\n\n"
    missing_info_prompt += "\n".join(info_status) + "\n\n"
    
    if question_analysis.missing_fields:
        missing_info_prompt += "📋 还需要补充以下信息：\n\n"
        field_descriptions = {
            "故障IP": "故障服务器的IP地址（如：192.168.1.100）",
            "故障时间": "故障发生的具体时间（如：2024-01-15 14:30）",
            "故障现象": "具体的故障表现和症状描述",
            "排查SOP编号": "对应的标准作业程序编号（如：SOP-001）"
        }
        
        for i, field in enumerate(question_analysis.missing_fields, 1):
            description = field_descriptions.get(field, "")
            missing_info_prompt += f"{i}. **{field}**：{description}\n"
    
    missing_info_prompt += "\n📝 您可以通过以下方式提供信息：\n"
    missing_info_prompt += "**方式一：自然语言**\n"
    missing_info_prompt += "例如：\"故障IP是192.168.1.100，时间是今天下午2点\"\n\n"
    missing_info_prompt += "**方式二：结构化格式**\n"
    missing_info_prompt += "```\n"
    missing_info_prompt += "故障IP: [请填写]\n"
    missing_info_prompt += "故障时间: [请填写]\n"
    missing_info_prompt += "故障现象: [请填写]\n"
    missing_info_prompt += "SOP编号: [请填写]\n"
    missing_info_prompt += "```\n\n"
    missing_info_prompt += "💡 您可以分多次补充，信息完整后将自动开始诊断。"
    
    return {
        "messages": [AIMessage(content=missing_info_prompt)]
    }


def finalize_diagnosis_report(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """完成诊断报告节点 - 基于严格的SOP执行结果"""
    configurable = Configuration.from_runnable_config(config)
    
    # 初始化推理模型
    llm = configurable.create_llm(
        model_name=configurable.answer_model,
        temperature=configurable.final_report_temperature
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
    if question_analysis.info_sufficient:
        return "plan_tools"
    else:
        # 信息不足时，提示用户补充
        return "handle_insufficient_info"


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


# 修复：自定义条件函数来决定是否有工具调用
def check_tool_calls(state: DiagnosticState, config: RunnableConfig) -> str:
    """检查是否有工具调用"""
    messages = state.get("messages", [])
    if not messages:
        return "reflection"
    
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "approval"
    else:
        return "reflection"
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


# 创建诊断Agent图 - 简化版本
builder = StateGraph(DiagnosticState, config_schema=Configuration)
# 添加节点
builder.add_node("analyze_question", analyze_question)
builder.add_node("handle_insufficient_info", handle_insufficient_info)
builder.add_node("plan_tools", plan_diagnosis_tools)
builder.add_node("approval", approval_node)
builder.add_node("execute_tools", tool_node)
builder.add_node("reflection", reflect_diagnosis_progress)
builder.add_node("finalize_answer", finalize_diagnosis_report)
builder.add_edge(START, "analyze_question")
builder.add_conditional_edges("analyze_question", check_info_sufficient, ["plan_tools", "handle_insufficient_info"])
# 修改：信息不足时等待用户补充，用户补充后重新回到analyze_question分析
builder.add_edge("handle_insufficient_info", END)
builder.add_conditional_edges("plan_tools",check_tool_calls,{"approval": "approval","reflection": "reflection"})
builder.add_edge("approval", "execute_tools")
builder.add_edge("execute_tools", "reflection")
builder.add_conditional_edges("reflection", evaluate_diagnosis_progress, ["plan_tools", "finalize_answer"])
builder.add_edge("finalize_answer", END)


# 编译图
graph = builder.compile(name="diagnostic-agent")
# 保存图像
graph_image = graph.get_graph().draw_mermaid_png()
with open("diagnostic_agent_graph.png", "wb") as f: 
    f.write(graph_image)
print("图已保存到: diagnostic_agent_graph.png")