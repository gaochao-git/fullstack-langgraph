"""
普通问答子图 - 处理运维技术问答和日常对话
"""

import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .tools import sop_tools, general_tools
from .utils import extract_diagnosis_results_from_messages

logger = logging.getLogger(__name__)


def analyze_question_context_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    分析问题上下文节点 - 理解用户问题并准备回答
    """
    print(f"✅ 执行节点: analyze_question_context_node")
    
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


def plan_qa_tools_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    问答工具规划节点 - 为系统查询类问题规划工具调用
    """
    print(f"✅ 执行节点: plan_qa_tools_node")
    
    configurable = Configuration.from_runnable_config(config)
    user_question = state.get("user_question", "")
    qa_context = state.get("qa_context", "")
    messages = state.get("messages", [])
    
    # 如果没有用户问题，从消息中获取
    if not user_question and messages:
        user_question = messages[-1].content if messages else ""
    
    # 判断问题类型
    response_type = determine_qa_type(user_question, qa_context)
    
    # 只有系统查询类问题才需要工具
    if response_type == "system_query":
        # 创建可用工具列表（只包含安全的查询工具）
        available_tools = sop_tools + general_tools
        
        # 创建带工具的LLM
        llm = configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=0.3
        )
        llm_with_tools = llm.bind_tools(available_tools)
        
        # 构建工具规划提示
        tool_planning_prompt = f"""
你是一个专业的运维助手。用户询问了系统查询相关的问题，请分析是否需要使用工具来获取信息。

用户问题：{user_question}

对话上下文：
{qa_context}

可用工具：
- SOP相关工具：查询SOP文档、搜索SOP等
- 通用工具：获取当前时间等

请分析用户问题，如果需要查询具体信息（如SOP文档、系统时间等），请调用相应工具。
如果是概念性问题或不需要实时数据，请直接回答，不要调用工具。

注意：只调用安全的查询工具，不要执行任何可能影响系统的操作。
"""
        
        # 构建消息
        system_message = SystemMessage(content=tool_planning_prompt)
        messages_with_system = [system_message] + messages
        
        # 调用LLM生成工具调用
        response = llm_with_tools.invoke(messages_with_system)
        
        # 检查是否生成了工具调用
        has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
        logger.info(f"工具规划结果: 生成了 {len(response.tool_calls) if has_tool_calls else 0} 个工具调用")
        
        return {
            "messages": [response],
            "qa_type": response_type
        }
    else:
        # 非系统查询类问题直接跳过工具调用
        return {
            "qa_type": response_type
        }


def generate_answer_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成回答节点 - 基于用户问题和上下文生成专业回答
    """
    print(f"✅ 执行节点: generate_answer_node")
    
    configurable = Configuration.from_runnable_config(config)
    
    # 获取状态信息
    user_question = state.get("user_question", "")
    qa_context = state.get("qa_context", "")
    qa_type = state.get("qa_type", "technical_qa")
    messages = state.get("messages", [])
    
    # 如果没有用户问题，从消息中获取
    if not user_question and messages:
        user_question = messages[-1].content if messages else ""
    
    logger.info(f"问答类型: {qa_type}")
    
    # 创建LLM实例
    llm = configurable.create_llm(
        model_name=configurable.answer_model,
        temperature=configurable.final_report_temperature
    )
    
    # 生成回答提示词
    if qa_type == "technical_qa":
        prompt = generate_technical_qa_prompt(user_question, qa_context)
    elif qa_type == "system_query":
        prompt = generate_system_query_prompt(user_question, qa_context)
    elif qa_type == "follow_up":
        prompt = generate_follow_up_prompt(user_question, qa_context)
    else:  # casual_chat
        prompt = generate_casual_chat_prompt(user_question, qa_context)
    
    # 生成回答
    response = llm.invoke(prompt)
    
    logger.info(f"问答回答生成完成，类型: {qa_type}")
    
    return {
        "messages": [AIMessage(content=response.content)]
    }


def determine_qa_type(user_question: str, qa_context: str) -> str:
    """
    判断问答类型
    """
    user_question_lower = user_question.lower()
    
    # 技术问答
    tech_keywords = [
        "如何", "怎么", "什么是", "配置", "安装", "部署", "监控", "日志",
        "性能", "优化", "故障", "错误", "命令", "脚本", "数据库", "网络",
        "服务器", "系统", "应用", "架构", "设计", "实现"
    ]
    
    # 系统查询
    query_keywords = [
        "状态", "信息", "查看", "显示", "列出", "统计", "报告", "历史",
        "记录", "日志", "配置信息", "版本", "详情"
    ]
    
    # 后续问题
    follow_up_keywords = [
        "详细", "更多", "具体", "解释", "说明", "为什么", "怎么办",
        "接下来", "然后", "还有", "另外", "补充"
    ]
    
    # 判断逻辑
    if any(keyword in user_question_lower for keyword in tech_keywords):
        return "technical_qa"
    elif any(keyword in user_question_lower for keyword in query_keywords):
        return "system_query"
    elif any(keyword in user_question_lower for keyword in follow_up_keywords) and qa_context != "无历史对话":
        return "follow_up"
    else:
        return "casual_chat"


def check_qa_tool_calls(state: DiagnosticState, config: RunnableConfig) -> Literal["execute_tools", "generate_answer"]:
    """检查是否有工具调用需要执行"""
    print(f"✅ 执行路由函数: check_qa_tool_calls")
    
    messages = state.get("messages", [])
    if not messages:
        return "generate_answer"
    
    last_message = messages[-1]
    has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
    
    if has_tool_calls:
        logger.info(f"检测到工具调用，数量: {len(last_message.tool_calls)}")
        return "execute_tools"
    else:
        logger.info("无工具调用，直接生成回答")
        return "generate_answer"


def generate_technical_qa_prompt(user_question: str, qa_context: str) -> str:
    """生成技术问答提示词"""
    return f"""您是专业的运维技术专家，请回答用户的技术问题。

用户问题：{user_question}

对话上下文：
{qa_context}

请提供：
1. 直接回答用户问题
2. 如果涉及操作，提供具体步骤
3. 如果有风险，提醒注意事项
4. 如果需要更多信息，主动询问

回答要求：
- 专业准确，简洁明了
- 提供实用的解决方案
- 包含具体的命令或配置示例（如适用）
- 避免过于复杂的术语解释
"""


def generate_system_query_prompt(user_question: str, qa_context: str) -> str:
    """生成系统查询提示词"""
    return f"""您是运维系统助手，用户想要查询系统信息。

用户问题：{user_question}

对话上下文：
{qa_context}

请根据用户需求：
1. 如果有相关历史信息，提供摘要
2. 如果需要实时查询，说明查询方法
3. 如果信息不足，询问更多细节

回答要求：
- 直接回答用户查询
- 提供具体的查询命令或方法
- 如果涉及历史诊断，引用相关结果
"""


def generate_follow_up_prompt(user_question: str, qa_context: str) -> str:
    """生成后续问题提示词"""
    return f"""用户对之前的对话有后续问题，请基于上下文提供详细回答。

用户问题：{user_question}

对话上下文：
{qa_context}

请：
1. 结合之前的对话内容回答
2. 提供更详细的解释或补充信息
3. 如果用户问题不够清楚，主动澄清

回答要求：
- 连贯性强，与之前对话呼应
- 提供具体的补充信息
- 保持专业和友好的语调
"""


def generate_casual_chat_prompt(user_question: str, qa_context: str) -> str:
    """生成日常聊天提示词"""
    return f"""您是友好的运维助手，用户在进行日常对话。

用户问题：{user_question}

对话上下文：
{qa_context}

请：
1. 自然友好地回应用户
2. 如果涉及运维相关内容，提供简单说明
3. 保持专业但轻松的语调

回答要求：
- 简洁自然
- 友好亲切
- 如果合适，可以询问是否需要技术帮助
"""


def create_general_qa_subgraph():
    """创建普通问答子图"""
    
    # 创建工具执行节点
    qa_safe_tools = sop_tools + general_tools  # 只包含安全的查询工具
    tool_node = ToolNode(qa_safe_tools)
    
    # 包装工具节点以添加打印
    def execute_qa_tools_node(state, config):
        print(f"✅ 执行节点: execute_qa_tools_node")
        return tool_node.invoke(state, config)
    
    # 创建子图
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    
    # 添加节点
    builder.add_node("analyze_context", analyze_question_context_node)
    builder.add_node("plan_tools", plan_qa_tools_node)
    builder.add_node("execute_tools", execute_qa_tools_node)
    builder.add_node("generate_answer", generate_answer_node)
    
    # 设置流程
    builder.add_edge(START, "analyze_context")
    builder.add_edge("analyze_context", "plan_tools")
    builder.add_conditional_edges(
        "plan_tools",
        check_qa_tool_calls,
        {
            "execute_tools": "execute_tools",
            "generate_answer": "generate_answer"
        }
    )
    builder.add_edge("execute_tools", "generate_answer")
    builder.add_edge("generate_answer", END)
    
    return builder.compile()