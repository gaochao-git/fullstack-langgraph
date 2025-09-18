from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from .configuration import INIT_AGENT_CONFIG
from .state import ExampleAgentState
from .nodes import (
    analyze_task_node,
    process_task_node,
    format_response_node,
    error_handler_node,
    llm_process_node,
    should_continue_after_task,
    should_retry_or_continue
)
from src.apps.agent.llm_agents.decorators import agent
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@agent(**INIT_AGENT_CONFIG)
async def create_example_agent(config: RunnableConfig):
    """创建示例智能体
    展示如何自己编译图，实现复杂工作流
    这是前端创建的 Agent 无法做到的高级功能
    """
    # 获取配置
    enable_debug = config.get("configurable", {}).get("enable_debug", False) if config else False
    return await create_workflow(enable_debug)


async def create_workflow(
    enable_debug: bool
):
    """创建自定义工作流
    
    展示如何：
    1. 定义自定义状态
    2. 创建多个处理节点
    3. 定义复杂的工作流逻辑
    4. 使用条件边进行动态路由
    5. 编译成可执行的图
    6. 使用静态上下文（可选）
    """
    # 创建状态图
    workflow = StateGraph(ExampleAgentState)
    
    # ========== 添加节点 ==========
    # 1. 任务分析节点（入口）
    workflow.add_node("analyze_task", analyze_task_node)
    
    # 2. 任务处理节点（主要处理逻辑）
    workflow.add_node("process_task", process_task_node)
    
    # 3. LLM 处理节点（用于复杂任务）
    workflow.add_node("llm_process", llm_process_node)
    
    # 4. 响应格式化节点
    workflow.add_node("format_response", format_response_node)
    
    # 5. 错误处理节点
    workflow.add_node("error_handler", error_handler_node)
    
    # ========== 定义工作流逻辑 ==========
    # 设置入口点
    workflow.set_entry_point("analyze_task")
    
    # 条件边1：任务分析后根据类型路由
    workflow.add_conditional_edges(
        "analyze_task",
        should_continue_after_task,
        {
            "process_task": "process_task",    # 简单任务
            "llm_process": "llm_process",      # 复杂任务需要LLM
        }
    )
    
    # 条件边2：处理节点完成后的路由
    for node in ["process_task", "llm_process"]:
        workflow.add_conditional_edges(
            node,
            should_retry_or_continue,
            {
                "retry": node,                    # 重试当前节点
                "error_handler": "error_handler", # 错误处理
                "format_response": "format_response" # 正常完成
            }
        )
    
    # 错误处理和格式化响应后结束
    workflow.add_edge("error_handler", END)
    workflow.add_edge("format_response", END)
    from src.apps.agent.checkpoint_factory import get_checkpointer
    
    # 获取 checkpointer
    checkpointer = await get_checkpointer()
    
    logger.info(f"[Agent创建] 编译自定义工作流图")
    compiled_graph = workflow.compile(
        checkpointer=checkpointer,
        debug=enable_debug,
    )
    # 设置图的名称（用于追踪和监控）
    compiled_graph.name = f"{INIT_AGENT_CONFIG['agent_id']}-workflow"
    return compiled_graph


