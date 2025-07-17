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
from .tools import all_tools
from .utils import extract_diagnosis_results_from_messages

logger = logging.getLogger(__name__)


def analyze_question_context_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    分析问题上下文节点 - 理解用户问题并准备回答
    """
    print(f"✅ 执行节点: analyze_question_context_node")
    print(f"🔍 analyze_question_context_node - 输入状态: {list(state.keys())}")
    
    messages = state.get("messages", [])
    print(f"🔍 analyze_question_context_node - 消息数量: {len(messages)}")
    
    if not messages:
        print(f"🔍 analyze_question_context_node - 无消息，返回默认上下文")
        return {"qa_context": "无历史对话"}
    
    # 获取用户问题
    user_question = messages[-1].content if messages else ""
    print(f"🔍 analyze_question_context_node - 用户问题: {user_question}")
    
    # 构建对话上下文
    context_parts = []
    
    # 添加诊断历史（如果有）
    diagnosis_results = extract_diagnosis_results_from_messages(messages, max_results=3)
    print(f"🔍 analyze_question_context_node - 诊断历史数量: {len(diagnosis_results)}")
    if diagnosis_results:
        context_parts.append("相关诊断历史：")
        context_parts.extend(diagnosis_results[:3])  # 最近3个诊断结果
    
    # 添加最近对话
    if len(messages) > 1:
        context_parts.append("\n最近对话：")
        recent_messages = messages[-6:] if len(messages) > 6 else messages[:-1]
        print(f"🔍 analyze_question_context_node - 最近对话数量: {len(recent_messages)}")
        for i, msg in enumerate(recent_messages):
            role = "用户" if i % 2 == 0 else "助手"
            content = getattr(msg, 'content', str(msg))[:150]  # 限制长度
            context_parts.append(f"{role}: {content}")
    
    qa_context = "\n".join(context_parts) if context_parts else "无历史对话"
    print(f"🔍 analyze_question_context_node - 构建的上下文长度: {len(qa_context)}")
    
    logger.info(f"问答上下文分析完成，历史诊断: {len(diagnosis_results)}, 对话轮次: {len(messages)}")
    
    result = {
        "qa_context": qa_context,
        "user_question": user_question
    }
    print(f"🔍 analyze_question_context_node - 返回结果: {list(result.keys())}")
    print(f"🔍 analyze_question_context_node - qa_context: {result['qa_context'][:100]}...")
    print(f"🔍 analyze_question_context_node - user_question: {result['user_question']}")
    
    return result


def plan_qa_tools_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    问答工具规划节点 - 让LLM自己决定是否需要工具调用
    """
    print(f"✅ 执行节点: plan_qa_tools_node")
    
    configurable = Configuration.from_runnable_config(config)
    user_question = state.get("user_question", "")
    qa_context = state.get("qa_context", "")
    messages = state.get("messages", [])
    

    
    # 如果没有用户问题，从消息中获取
    if not user_question and messages:
        user_question = messages[-1].content if messages else ""
        print(f"🔍 plan_qa_tools_node - 从消息中获取用户问题: {user_question}")
    
    # 创建可用工具列表（只包含安全的查询工具）
    # 普通问答助手只需要：通用工具（如时间查询）
    # 不包含SSH、MySQL、Elasticsearch、Zabbix等系统诊断工具
    # 也不包含SOP工具，因为SOP是诊断专用的
    available_tools = all_tools
    
    # 创建带工具的LLM
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=0.3
    )
    llm_with_tools = llm.bind_tools(available_tools)
    print(f"🔍 plan_qa_tools_node - LLM模型: {configurable.query_generator_model}")
    
    # 构建工具规划提示 - 让LLM自己决定是否需要工具
    tool_planning_prompt = f"""
你是一个专业的运维助手。请分析用户问题，自主决定是否需要使用工具来获取信息。

用户问题：{user_question}

对话上下文：
{qa_context}

请分析用户问题：
1. 如果需要获取实时信息（如当前时间、SOP文档内容等），请调用相应工具
2. 如果是概念性问题、技术解释或不需要实时数据，请直接回答，不要调用工具
3. 如果不确定，优先尝试调用工具获取准确信息

注意：只调用安全的查询工具，不要执行任何可能影响系统的操作。
"""
    
    # 构建消息
    system_message = SystemMessage(content=tool_planning_prompt)
    messages_with_system = [system_message] + messages
    
    # 调用LLM生成工具调用
    response = llm_with_tools.invoke(messages_with_system)
    
    # 检查是否生成了工具调用
    has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
    if hasattr(response, 'tool_calls'):
        print(f"🔍 plan_qa_tools_node - tool_calls值: {response.tool_calls}")
    
    if has_tool_calls:
        for i, tool_call in enumerate(response.tool_calls):
            print(f"  工具调用 {i+1}: {tool_call.get('name', 'unknown')} - {tool_call.get('args', {})}")
    else:
        print(f"  LLM回答: {response.content[:200]}...")
        
    result = {
        "messages": [response]
    }
    
    return result


def generate_answer_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    生成回答节点 - 基于用户问题和上下文生成专业回答
    """
    print(f"✅ 执行节点: generate_answer_node")
    print(f"🔍 generate_answer_node - 输入状态: {list(state.keys())}")
    
    configurable = Configuration.from_runnable_config(config)
    
    # 获取状态信息
    user_question = state.get("user_question", "")
    qa_context = state.get("qa_context", "")
    messages = state.get("messages", [])
    
    print(f"🔍 generate_answer_node - user_question: {user_question}")
    print(f"🔍 generate_answer_node - qa_context: {qa_context[:100]}...")
    print(f"🔍 generate_answer_node - messages数量: {len(messages)}")
    
    # 如果没有用户问题，从消息中获取
    if not user_question and messages:
        user_question = messages[-1].content if messages else ""
        print(f"🔍 generate_answer_node - 从消息中获取用户问题: {user_question}")
    
    # 创建LLM实例
    llm = configurable.create_llm(
        model_name=configurable.answer_model,
        temperature=configurable.final_report_temperature
    )
    print(f"🔍 generate_answer_node - LLM模型: {configurable.answer_model}")
    
    # 检查是否有工具结果
    tool_results = []
    print(f"🔍 检查消息中的工具结果，总消息数: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"  消息 {i}: type={type(msg)}, name={getattr(msg, 'name', None)}, content={getattr(msg, 'content', '')[:100]}...")
        if hasattr(msg, 'name') and msg.name and hasattr(msg, 'content'):
            tool_results.append(f"工具 {msg.name} 返回: {msg.content}")
            print(f"    ✅ 找到工具结果: {msg.name}")
    
    print(f"🔍 找到的工具结果数量: {len(tool_results)}")
    
    # 生成通用的回答提示词
    if tool_results:
        tool_info = "\n".join(tool_results)
        print(f"🛠️ 使用工具结果生成回答:")
        print(f"  工具信息: {tool_info}")
        
        prompt = f"""你是一个专业的运维技术助手，擅长回答各种运维相关问题。

用户问题：{user_question}

对话历史上下文：
{qa_context}

工具执行结果：
{tool_info}

请根据用户问题、上下文信息和工具执行结果，提供专业、准确的回答。

重要：
1. 必须使用工具返回的实际结果来回答用户问题
2. 不要说"无法获取"或"建议通过其他方式"，直接使用工具结果
3. 保持专业和友好的语调
4. 如果工具返回的是JSON格式，请解析并使用其中的有效信息

请直接回答用户的问题。"""
    else:
        print(f"❌ 没有找到工具结果，使用默认回答模式")
        prompt = f"""你是一个专业的运维技术助手，擅长回答各种运维相关问题。

用户问题：{user_question}

对话历史上下文：
{qa_context}

请根据用户问题和上下文信息，提供专业、准确的回答。

回答要求：
1. 保持专业和友好的语调
2. 提供具体、实用的建议
3. 如果涉及操作步骤，请详细说明
4. 如果需要注意事项，请提醒用户

请直接回答用户的问题。"""
    
    print(f"🔍 generate_answer_node - 开始调用LLM生成回答...")
    print(f"🔍 generate_answer_node - 提示词长度: {len(prompt)}")
    
    # 生成回答
    response = llm.invoke(prompt)
    print(f"🔍 generate_answer_node - LLM响应完成")
    print(f"🔍 generate_answer_node - 响应内容: {response.content[:200]}...")
    
    logger.info(f"问答回答生成完成")
    
    result = {
        "messages": [AIMessage(content=response.content)]
    }
    print(f"🔍 generate_answer_node - 返回结果: {list(result.keys())}")
    print(f"🔍 generate_answer_node - 返回消息数量: {len(result['messages'])}")
    
    return result


def determine_qa_type(user_question: str, qa_context: str, config: RunnableConfig) -> str:
    """
    使用LLM智能判断问答类型
    """
    configurable = Configuration.from_runnable_config(config)
    
    # 创建LLM
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=0.1
    )
    
    # 构建判断提示词
    classification_prompt = f"""
你是一个专业的问答类型分类器。请分析用户问题，判断属于以下哪种类型：

1. **technical_qa** - 技术问答：
   - 询问技术知识、操作方法、概念解释
   - 询问如何配置、安装、部署、监控等
   - 询问命令用法、脚本编写、架构设计等
   - 例如："如何配置nginx"、"什么是docker"、"怎么优化数据库性能"

2. **system_query** - 系统查询：
   - 需要查询实时信息、系统状态、配置信息
   - 需要搜索文档、SOP、历史记录
   - 需要获取当前时间、版本信息、统计数据
   - 例如："现在几点了"、"查询SOP文档"、"显示系统状态"、"搜索相关文档"

3. **follow_up** - 后续问题：
   - 对之前回答的追问和补充
   - 要求更详细解释或相关延伸
   - 基于历史对话的继续讨论
   - 例如："详细说明一下"、"还有其他方法吗"、"为什么会这样"

4. **casual_chat** - 日常聊天：
   - 问候、感谢、闲聊
   - 不涉及技术内容的对话
   - 例如："你好"、"谢谢"、"再见"

用户问题：{user_question}

对话历史：{qa_context}

请分析用户问题，只返回类型名称：technical_qa、system_query、follow_up、casual_chat
"""
    
    # 调用LLM分类
    try:
        result = llm.invoke(classification_prompt)
        qa_type = result.content.strip().lower()
        
        # 确保返回有效类型
        valid_types = ["technical_qa", "system_query", "follow_up", "casual_chat"]
        if qa_type in valid_types:
            return qa_type
        else:
            # 如果LLM返回的不是有效类型，使用简单的fallback逻辑
            logger.warning(f"LLM返回无效类型: {qa_type}，使用fallback逻辑")
            return "technical_qa"  # 默认为技术问答
            
    except Exception as e:
        logger.error(f"LLM分类失败: {e}，使用fallback逻辑")
        return "technical_qa"  # 默认为技术问答


def check_qa_tool_calls(state: DiagnosticState, config: RunnableConfig) -> Literal["execute_tools", "END"]:
    """检查是否有工具调用需要执行，如果没有工具调用且已有回复则直接结束"""
    print(f"✅ 执行路由函数: check_qa_tool_calls")
    
    messages = state.get("messages", [])
    print(f"🔍 路由检查 - 消息总数: {len(messages)}")
    
    if not messages:
        print(f"❌ 没有消息，直接结束")
        return "END"
    
    last_message = messages[-1]
    print(f"🔍 最后一条消息类型: {type(last_message)}")
    print(f"🔍 消息内容: {getattr(last_message, 'content', 'N/A')[:100]}...")
    
    has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
    has_content = hasattr(last_message, 'content') and last_message.content.strip()
    
    print(f"🔍 hasattr(tool_calls): {hasattr(last_message, 'tool_calls')}")
    print(f"🔍 has_content: {has_content}")
    if hasattr(last_message, 'tool_calls'):
        print(f"🔍 tool_calls值: {last_message.tool_calls}")
    
    if has_tool_calls:
        print(f"✅ 检测到工具调用，数量: {len(last_message.tool_calls)}")
        logger.info(f"检测到工具调用，数量: {len(last_message.tool_calls)}")
        return "execute_tools"
    elif has_content:
        print(f"✅ 无工具调用但有回复内容，直接结束")
        logger.info("无工具调用但有回复内容，直接结束")
        return "END"
    else:
        print(f"❌ 无工具调用也无回复内容，直接结束")
        logger.info("无工具调用也无回复内容，直接结束")
        return "END"


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
    # 普通问答助手只使用通用工具（如时间查询）
    # 不包含SSH、MySQL、Elasticsearch、Zabbix等系统诊断工具
    # 也不包含SOP工具，因为SOP是诊断专用的
    qa_safe_tools = all_tools
    tool_node = ToolNode(qa_safe_tools)
    
    # 包装工具节点以添加打印
    def execute_qa_tools_node(state, config):
        print(f"✅ 执行节点: execute_qa_tools_node")
        print(f"🔍 execute_qa_tools_node - 输入状态: {list(state.keys())}")
        
        messages = state.get("messages", [])
        print(f"🔍 execute_qa_tools_node - messages数量: {len(messages)}")
        
        # 检查最后一条消息是否有工具调用
        if messages:
            last_message = messages[-1]
            print(f"🔍 execute_qa_tools_node - 最后一条消息类型: {type(last_message)}")
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                print(f"🔍 execute_qa_tools_node - 检测到工具调用数量: {len(last_message.tool_calls)}")
                for i, tool_call in enumerate(last_message.tool_calls):
                    print(f"  工具调用 {i+1}: {tool_call.get('name', 'unknown')} - {tool_call.get('args', {})}")
            else:
                print(f"🔍 execute_qa_tools_node - 未检测到工具调用")
        
        print(f"🔍 execute_qa_tools_node - 开始执行工具...")
        result = tool_node.invoke(state, config)
        print(f"🔍 execute_qa_tools_node - 工具执行完成")
        print(f"🔍 execute_qa_tools_node - 返回结果: {list(result.keys())}")
        
        if "messages" in result:
            print(f"🔍 execute_qa_tools_node - 返回消息数量: {len(result['messages'])}")
            for i, msg in enumerate(result["messages"]):
                print(f"  返回消息 {i}: type={type(msg)}, name={getattr(msg, 'name', None)}, content={getattr(msg, 'content', '')[:100]}...")
        
        return result
    
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
    builder.add_conditional_edges("plan_tools", check_qa_tool_calls, {"execute_tools": "execute_tools", "END": END})
    builder.add_edge("execute_tools", "generate_answer")
    builder.add_edge("generate_answer", END)
    return builder.compile()