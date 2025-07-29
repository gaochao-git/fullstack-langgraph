"""智能运维助手图定义"""

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState
from .utils import compile_graph_with_checkpointer
from .prompts import get_system_prompt
from .tools_mcp import get_diagnostic_tools

def create_main_graph(enable_tool_approval: bool = False):
    """创建主图"""
    
    def get_llm_from_config(config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=configurable.model_temperature
        )
    
    async def create_agent(state: DiagnosticState, config: RunnableConfig):
        configurable = config.get("configurable", {}) if config else {}
        
        # 优先从configurable获取，fallback到assistant_id
        agent_name = configurable.get("agent_name")
        if not agent_name:
            agent_name = config.get("assistant_id", "diagnostic_agent") if config else "diagnostic_agent"
            
        selected_model = configurable.get("selected_model")
        
        print(f"🚀 处理消息:")
        print(f"   智能体: {agent_name}")
        print(f"   选择模型: {selected_model or '使用默认配置'}")
        print(f"   完整config: {dict(config) if config else 'None'}")
        if state.get("messages"):
            last_message = state["messages"][-1]
            print(f"   用户消息: {last_message.content[:50]}..." if len(last_message.content) > 50 else f"   用户消息: {last_message.content}")
        
        llm = get_llm_from_config(config)
        tools = await get_diagnostic_tools(enable_tool_approval)
        
        # 获取智能体名称并获取对应的系统提示词
        system_prompt = get_system_prompt(agent_name)
        print(9999999,system_prompt)
        
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