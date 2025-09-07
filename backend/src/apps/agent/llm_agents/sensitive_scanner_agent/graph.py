"""敏感数据扫描智能体图定义"""
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from .configuration import INIT_AGENT_CONFIG
from .state import OverallState
from .nodes import fetch_files, scan_files
from src.apps.agent.llm_agents.decorators import agent
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def compile_graph(checkpointer=None):
    """编译敏感数据扫描图"""
    # 创建状态图（使用项目中的标准方式）
    workflow = StateGraph(OverallState)
    
    # 添加节点
    workflow.add_node("fetch_files", fetch_files)  # 获取文件内容
    workflow.add_node("scan_files", scan_files)    # 扫描敏感数据
    
    # 定义边
    workflow.set_entry_point("fetch_files")
    workflow.add_edge("fetch_files", "scan_files")
    workflow.add_edge("scan_files", END)
    
    # 编译图
    logger.info(f"[Agent创建] 编译敏感数据扫描图")
    return workflow.compile(checkpointer=checkpointer)


@agent(**INIT_AGENT_CONFIG)
async def create_sensitive_scanner_agent(config: RunnableConfig, checkpointer=None):
    """创建敏感数据扫描智能体"""
    return compile_graph(checkpointer)