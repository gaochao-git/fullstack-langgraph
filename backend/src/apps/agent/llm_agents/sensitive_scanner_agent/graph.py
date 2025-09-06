"""敏感数据扫描智能体图定义 - 使用MapReduce模式"""

from typing import Literal, Dict, Any
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from .state import ScannerState
from .nodes import (
    initialize_scan,
    create_chunks, 
    parallel_scan,
    aggregate_results,
    generate_report,
    tool_node
)
from .configuration import INIT_AGENT_CONFIG
from .prompts import get_system_prompt_async
from .llm import get_llm_config
from .tools import get_scanner_tools
from src.apps.agent.llm_agents.hooks import create_monitor_hook
from src.apps.agent.llm_agents.decorators import agent
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def should_use_tools(state: ScannerState) -> Literal["tools", "scan"]:
    """判断是否需要使用工具还是直接扫描"""
    messages = state.get("messages", [])
    if not messages:
        return "scan"
    
    last_message = messages[-1]
    
    # 如果最后一条消息包含工具调用，则使用工具
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info(f"检测到工具调用: {[tc.get('name') for tc in last_message.tool_calls]}")
        return "tools"
    
    # 检查是否已经获取了文件内容
    file_contents = state.get("file_contents", {})
    if file_contents:
        # 如果已经有文件内容，进行扫描流程
        logger.info("检测到文件内容，转入扫描流程")
        return "scan"
    
    # 如果有file_ids但还没有文件内容，返回agent让LLM决定是否调用工具
    # 不应该直接进入scan，应该让LLM有机会调用工具
    file_ids = state.get("file_ids", [])
    if file_ids and not file_contents:
        logger.info("检测到file_ids但没有文件内容，继续等待LLM调用工具")
        # 这里应该返回什么？如果LLM没有调用工具，我们需要重新考虑
        # 临时返回scan，但需要在initialize_scan中处理
        return "scan"
    
    # 默认进入扫描流程
    return "scan"


def has_files_to_scan(state: ScannerState) -> Literal["continue", "no_files"]:
    """检查是否有文件需要扫描"""
    file_contents = state.get("file_contents", {})
    if file_contents:
        return "continue"
    else:
        return "no_files"


async def handle_no_files(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """处理没有文件的情况"""
    from langchain_core.messages import AIMessage
    
    response = AIMessage(
        content="未找到需要扫描的文件。请确保：\n"
        "1. 提供正确的文件ID（格式如：file_xxxxx）\n"
        "2. 文件已经上传并处理完成\n"
        "3. 您有访问该文件的权限\n\n"
        "您可以通过上传文件或提供文件ID来开始敏感数据扫描。"
    )
    
    return {
        **state,
        "messages": state.get("messages", []) + [response]
    }


async def agent_node(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """智能体节点 - 处理用户交互"""
    import re
    import json
    from langchain_core.messages import HumanMessage
    
    # 检查是否需要从用户消息中提取file_ids
    messages = state.get("messages", [])
    file_ids = state.get("file_ids", [])
    
    logger.info(f"[agent_node] 初始状态 - file_ids: {file_ids}, messages数量: {len(messages)}")
    if messages:
        logger.info(f"[agent_node] 最后一条消息内容: {messages[-1]}")
    
    # 如果还没有file_ids，尝试从最新的用户消息中提取
    if not file_ids and messages:
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                # 首先检查消息对象是否有 file_ids 属性
                if hasattr(msg, 'file_ids') and msg.file_ids:
                    file_ids = msg.file_ids
                    logger.info(f"从消息属性中获取到file_ids: {file_ids}")
                # 如果消息是字典形式，检查是否有 file_ids 键
                elif isinstance(msg, dict) and 'file_ids' in msg:
                    file_ids = msg['file_ids']
                    logger.info(f"从消息字典中获取到file_ids: {file_ids}")
                else:
                    # 尝试从消息内容中解析
                    content = str(msg.content)
                    # 尝试匹配 file_ids:["xxx", "yyy"] 格式
                    file_ids_match = re.search(r'file_ids\s*:\s*\[(.*?)\]', content, re.DOTALL)
                    if file_ids_match:
                        try:
                            # 提取并解析file_ids
                            ids_str = '[' + file_ids_match.group(1) + ']'
                            file_ids = json.loads(ids_str)
                            logger.info(f"从用户消息内容中提取到file_ids: {file_ids}")
                        except:
                            logger.warning("解析file_ids失败")
                    
                    # 也尝试匹配单个file_id
                    single_id_match = re.findall(r'file_[a-zA-Z0-9\-]+', content)
                    if single_id_match and not file_ids:
                        file_ids = list(set(single_id_match))  # 去重
                        logger.info(f"从用户消息中提取到单个file_ids: {file_ids}")
                break
    
    # 获取配置
    agent_id = INIT_AGENT_CONFIG["agent_id"]
    selected_model = config.get("configurable", {}).get("selected_model") if config else None
    llm_config = get_llm_config(agent_id, selected_model)
    
    # 创建LLM
    llm = ChatOpenAI(**llm_config)
    
    # 获取系统提示词
    system_prompt = await get_system_prompt_async(agent_id)
    
    # 获取工具
    tools = await get_scanner_tools(agent_id)
    logger.info(f"[{agent_id}] 获取到工具: {[tool.name for tool in tools]}")
    
    # 绑定工具到LLM
    llm_with_tools = llm.bind_tools(tools)
    logger.info(f"[{agent_id}] 工具已绑定到LLM")
    
    # 创建监控hook
    monitor_hook = create_monitor_hook(llm_config)
    
    # 添加系统消息（如果还没有）
    if not any(isinstance(msg, SystemMessage) for msg in messages):
        # 如果已经提取到 file_ids，在系统提示词中添加说明
        if file_ids:
            enhanced_prompt = system_prompt + f"\n\n当前已识别到需要扫描的文件ID列表：{file_ids}\n请使用 get_file_content 工具获取这些文件的内容。"
            messages = [SystemMessage(content=enhanced_prompt)] + messages
        else:
            messages = [SystemMessage(content=system_prompt)] + messages
    
    # 调用LLM前记录工具的详细信息
    logger.info(f"[{agent_id}] 准备调用LLM，工具数量: {len(tools)}")
    logger.info(f"[{agent_id}] LLM类型: {type(llm_with_tools)}")
    logger.info(f"[{agent_id}] 消息内容: {[msg.content if hasattr(msg, 'content') else str(msg) for msg in messages]}")
    
    # 调用LLM
    if monitor_hook:
        # monitor_hook需要一个包含messages的state字典
        hook_result = monitor_hook({"messages": messages})
        # 如果hook返回了llm_input_messages，使用它；否则使用原始messages
        messages_to_use = hook_result.get("llm_input_messages", messages)
        response = await llm_with_tools.ainvoke(messages_to_use)
    else:
        response = await llm_with_tools.ainvoke(messages)
    
    # 记录LLM的响应
    logger.info(f"[{agent_id}] LLM响应类型: {type(response)}")
    logger.info(f"[{agent_id}] LLM响应内容: {response.content if hasattr(response, 'content') else str(response)}")
    if hasattr(response, 'tool_calls'):
        logger.info(f"[{agent_id}] 工具调用: {response.tool_calls}")
    
    # 如果LLM没有调用工具，但我们有file_ids，强制创建工具调用
    if file_ids and not (hasattr(response, 'tool_calls') and response.tool_calls):
        logger.warning(f"[{agent_id}] LLM未调用工具但有file_ids，强制创建工具调用")
        from langchain_core.messages import AIMessage
        
        # 创建工具调用
        tool_calls = []
        for file_id in file_ids:
            tool_calls.append({
                "id": f"call_{file_id}",
                "name": "get_file_content",
                "args": {"file_id": file_id}
            })
        
        # 创建包含工具调用的AI消息
        response = AIMessage(
            content="正在获取文件内容...",
            tool_calls=tool_calls
        )
        logger.info(f"[{agent_id}] 强制创建了 {len(tool_calls)} 个工具调用")
    
    return {
        **state,
        "messages": state.get("messages", []) + [response],
        "file_ids": file_ids  # 更新file_ids到状态
    }


@agent(**INIT_AGENT_CONFIG)
async def create_sensitive_scanner_agent(config: RunnableConfig, checkpointer=None):
    """创建敏感数据扫描智能体 - 使用MapReduce模式"""
    
    # 创建状态图
    workflow = StateGraph(ScannerState)
    
    # 添加节点
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("initialize", initialize_scan)
    workflow.add_node("create_chunks", create_chunks)
    workflow.add_node("parallel_scan", parallel_scan)
    workflow.add_node("aggregate", aggregate_results)
    workflow.add_node("generate_report", generate_report)
    workflow.add_node("no_files", handle_no_files)
    
    # 设置入口点
    workflow.add_edge(START, "agent")
    
    # 从agent节点的条件边
    workflow.add_conditional_edges(
        "agent",
        should_use_tools,
        {
            "tools": "tools",
            "scan": "initialize"
        }
    )
    
    # 工具执行后进入初始化扫描
    workflow.add_edge("tools", "initialize")
    
    # 初始化后的条件边
    workflow.add_conditional_edges(
        "initialize",
        has_files_to_scan,
        {
            "continue": "create_chunks",
            "no_files": "no_files"
        }
    )
    
    # MapReduce流程
    workflow.add_edge("create_chunks", "parallel_scan")
    workflow.add_edge("parallel_scan", "aggregate")
    workflow.add_edge("aggregate", "generate_report")
    
    # 完成边
    workflow.add_edge("generate_report", END)
    workflow.add_edge("no_files", END)
    
    # 编译图
    graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=[],
        interrupt_after=[]
    )
    
    # 设置图的名称
    graph.name = f"{INIT_AGENT_CONFIG['agent_id']}-mapreduce-graph"
    
    logger.info(f"[{INIT_AGENT_CONFIG['agent_id']}] 创建了MapReduce模式的敏感数据扫描图")
    
    return graph