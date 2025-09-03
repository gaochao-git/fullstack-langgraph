"""
Example Agent 节点定义
展示如何定义自定义工作流节点
"""

from typing import Dict, Any, Literal
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_openai import ChatOpenAI
from .state import ExampleAgentState
from .tools import word_counter, text_analyzer
from .configuration import INIT_AGENT_CONFIG  # 从 configuration.py 导入
from .llm import get_llm_config
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def analyze_task_node(state: ExampleAgentState) -> Dict[str, Any]:
    """分析任务类型的节点
    
    根据用户消息判断需要执行的任务类型
    """
    messages = state.get("messages", [])
    if not messages:
        return {"task_type": "unknown", "error": "没有消息"}
    
    # 获取最后一条用户消息
    last_user_message = None
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == "human":
            last_user_message = msg.content
            break
    
    if not last_user_message:
        return {"task_type": "unknown", "error": "没有找到用户消息"}
    
    # 简单的任务分类：复杂任务需要 LLM，其他用通用处理
    content_lower = last_user_message.lower()
    if "复杂" in content_lower or "详细分析" in content_lower or len(last_user_message) > 200:
        task_type = "complex"
    else:
        task_type = "simple"
    
    logger.debug(f"识别任务类型: {task_type}")
    
    return {
        "task_type": task_type,
        "workflow_steps": [f"任务识别: {task_type}"]
    }


async def process_task_node(state: ExampleAgentState) -> Dict[str, Any]:
    """处理简单任务的节点
    
    使用内置工具处理任务
    """
    messages = state.get("messages", [])
    processing_results = state.get("processing_results", {})
    workflow_steps = state.get("workflow_steps", [])
    
    # 获取要处理的文本
    text_to_process = ""
    for msg in reversed(messages):
        if hasattr(msg, 'type') and msg.type == "human":
            text_to_process = msg.content
            break
    
    # 执行处理（这里演示使用工具）
    try:
        # 字数统计
        word_result = word_counter.invoke({"text": text_to_process})
        processing_results["word_count"] = word_result
        
        # 文本分析
        analysis_result = text_analyzer.invoke({"text": text_to_process})
        processing_results["analysis"] = analysis_result
        
        workflow_steps.append("使用工具处理任务")
        
    except Exception as e:
        # 如果处理失败，设置错误状态
        return {
            "error": str(e),
            "workflow_steps": workflow_steps + ["处理失败"]
        }
    
    return {
        "processing_results": processing_results,
        "workflow_steps": workflow_steps
    }


async def format_response_node(state: ExampleAgentState) -> Dict[str, Any]:
    """格式化响应的节点
    
    将处理结果格式化为用户友好的消息
    """
    processing_results = state.get("processing_results", {})
    workflow_steps = state.get("workflow_steps", [])
    
    # 构建响应消息
    response_parts = []
    
    # 如果有处理结果，格式化输出
    if processing_results:
        if "word_count" in processing_results:
            response_parts.append(f"📊 {processing_results['word_count']}")
        
        if "analysis" in processing_results:
            response_parts.append(f"\n🔍 {processing_results['analysis']}")
            
        if "llm_response" in processing_results:
            response_parts.append(f"\n💡 {processing_results['llm_response']}")
    else:
        response_parts.append("✅ 处理完成")
    
    # 添加工作流步骤（调试模式）
    if logger.isEnabledFor(10):  # DEBUG level
        response_parts.append(f"\n\n🔧 工作流步骤：")
        for step in workflow_steps:
            response_parts.append(f"\n  - {step}")
    
    workflow_steps.append("格式化响应")
    
    # 创建 AI 消息
    response_message = AIMessage(content="".join(response_parts))
    
    return {
        "messages": [response_message],
        "workflow_steps": workflow_steps
    }


def should_continue_after_task(state: ExampleAgentState) -> Literal["process_task", "llm_process"]:
    """任务分析后的路由决策
    
    使用 Literal 类型注解提供更好的类型安全性（LangGraph 0.6.6 推荐）
    
    Returns:
        下一个节点的名称
    """
    task_type = state.get("task_type", "unknown")
    
    # 简化的路由逻辑：复杂任务用 LLM，其他用通用处理
    if task_type == "complex":
        return "llm_process"
    else:
        return "process_task"


def should_retry_or_continue(state: ExampleAgentState) -> Literal["retry", "error_handler", "format_response"]:
    """处理后决定是否重试或继续
    
    使用 Literal 类型注解提供更好的类型安全性（LangGraph 0.6.6 推荐）
    
    Returns:
        下一个节点的名称
    """
    # 检查是否有错误
    error = state.get("error")
    if error:
        retry_count = state.get("retry_count", 0)
        if retry_count < 3:
            return "retry"
        else:
            return "error_handler"
    
    # 正常流程，格式化响应
    return "format_response"


async def error_handler_node(state: ExampleAgentState) -> Dict[str, Any]:
    """错误处理节点"""
    error = state.get("error", "未知错误")
    workflow_steps = state.get("workflow_steps", [])
    
    error_message = f"❌ 处理失败: {error}"
    workflow_steps.append(f"错误处理: {error}")
    
    return {
        "messages": [AIMessage(content=error_message)],
        "workflow_steps": workflow_steps
    }


async def llm_process_node(state: ExampleAgentState) -> Dict[str, Any]:
    """使用 LLM 处理复杂任务
    
    这个节点展示了如何在节点内部创建和使用 LLM
    """
    messages = state.get("messages", [])
    workflow_steps = state.get("workflow_steps", [])
    
    # 获取 LLM 配置（使用 agent_utils 的公共方法）
    llm_config = get_llm_config(INIT_AGENT_CONFIG["agent_id"])
    llm = ChatOpenAI(**llm_config)
    
    # 构建 LLM 提示
    prompt = "请处理以下复杂任务："
    for msg in messages:
        if hasattr(msg, 'content'):
            prompt += f"\n{msg.content}"
    
    try:
        # 调用 LLM
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        workflow_steps.append("LLM 处理复杂任务")
        
        return {
            "messages": [response],
            "processing_results": {"llm_response": response.content},
            "workflow_steps": workflow_steps
        }
    except Exception as e:
        return {
            "error": f"LLM 调用失败: {str(e)}",
            "workflow_steps": workflow_steps + ["LLM 调用失败"]
        }