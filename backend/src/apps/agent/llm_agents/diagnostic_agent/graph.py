"""智能运维助手图定义"""

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .utils import compile_graph_with_checkpointer
from .prompts import get_system_prompt
from .tools import get_diagnostic_tools
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

def create_main_graph(enable_tool_approval: bool = False):
    """创建主图"""
    
    def get_llm_from_config(config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(model_name=configurable.query_generator_model, temperature=configurable.model_temperature)
    
    async def create_agent(state: DiagnosticState, config: RunnableConfig):
        configurable = config.get("configurable", {}) if config else {}
        # 获取agent_id，必须存在，不使用默认值
        agent_id = configurable.get("agent_id")
        if not agent_id: raise RuntimeError("配置中缺少必需的agent_id参数")
        logger.info(f"完整智能体配置: {dict(config) if config else 'None'}")
        llm = get_llm_from_config(config)
        tools = await get_diagnostic_tools(agent_id)
        
        # 获取智能体名称并获取对应的系统提示词（必须从数据库获取）
        try:
            system_prompt = get_system_prompt(agent_id)
            logger.info(f"成功获取智能体 '{agent_id}' 的系统提示词")
        except ValueError as e:
            logger.error(f"获取智能体系统提示词失败: {e}")
            # 抛出异常，让上层处理，不允许使用空提示词运行
            raise RuntimeError(f"智能体 '{agent_id}' 配置错误: {e}")
        
        agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
        return await agent.ainvoke(state, config)
    
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    builder.add_node("agent", create_agent)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder

def compile_main_graph(enable_tool_approval: bool = False):
    """编译主图"""
    builder = create_main_graph(enable_tool_approval)
    return compile_graph_with_checkpointer(builder)

# 默认导出
graph = compile_main_graph()
builder = create_main_graph()