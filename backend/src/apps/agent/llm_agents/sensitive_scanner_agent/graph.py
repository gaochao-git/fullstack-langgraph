"""敏感数据扫描智能体图定义"""
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from .configuration import INIT_AGENT_CONFIG
from .state import OverallState
from .nodes import (
    prepare_scan, 
    emit_scan_progress, 
    perform_scan, 
    generate_final_report, 
    check_scan_progress
)
from src.apps.agent.llm_agents.decorators import agent
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def compile_graph():
    """编译敏感数据扫描图 - 细粒度流式版本"""
    from src.apps.agent.checkpoint_factory import get_checkpointer
    
    # 创建状态图
    workflow = StateGraph(OverallState)
    
    # 添加节点
    workflow.add_node("prepare_scan", prepare_scan)            # 准备扫描队列
    workflow.add_node("emit_progress", emit_scan_progress)      # 发送进度消息
    workflow.add_node("perform_scan", perform_scan)             # 执行扫描
    workflow.add_node("generate_report", generate_final_report)  # 生成最终报告
    
    # 设置入口点
    workflow.set_entry_point("prepare_scan")
    
    # 添加条件边：从prepare_scan决定下一步
    workflow.add_conditional_edges(
        "prepare_scan",
        check_scan_progress,
        {
            "progress": "emit_progress",
            "report": "generate_report"  # 如果没有内容要扫描
        }
    )
    
    # 进度消息后执行扫描
    workflow.add_edge("emit_progress", "perform_scan")
    
    # 扫描完成后决定下一步
    workflow.add_conditional_edges(
        "perform_scan",
        check_scan_progress,
        {
            "progress": "emit_progress",  # 继续下一个：先发进度
            "report": "generate_report"   # 全部完成：生成报告
        }
    )
    
    # 生成报告后结束
    workflow.add_edge("generate_report", END)
    
    # 获取 checkpointer
    checkpointer = get_checkpointer()
    
    # 编译图
    logger.info(f"[Agent创建] 编译敏感数据扫描图（细粒度流式版本）")
    return workflow.compile(checkpointer=checkpointer)


@agent(**INIT_AGENT_CONFIG)
async def create_sensitive_scanner_agent(config: RunnableConfig):
    """创建敏感数据扫描智能体"""
    return compile_graph()