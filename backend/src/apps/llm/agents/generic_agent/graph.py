"""通用Agent工作流图定义

使用create_react_agent方式，参考diagnostic_agent的简洁模式
"""

from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import AgentState
from .utils import compile_graph_with_checkpointer
from .prompts import get_system_prompt_from_config
from .tools import get_langchain_tools_by_categories


def create_main_graph():
    """创建主图 - 使用create_react_agent方式"""
    
    def get_llm_from_config(config: RunnableConfig):
        """从配置获取LLM实例"""
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.model_name,
            temperature=configurable.model_temperature
        )
    
    async def create_agent(state: AgentState, config: RunnableConfig):
        """创建并运行Agent"""
        configurable = config.get("configurable", {}) if config else {}
        
        # 获取agent_id，优先从configurable获取
        agent_id = configurable.get("agent_id", "generic_agent")
        agent_name = configurable.get("agent_name", "通用智能体")
        selected_model = configurable.get("model_name")
        
        print(f"🚀 处理消息:")
        print(f"   智能体: {agent_name} ({agent_id})")
        print(f"   选择模型: {selected_model or '使用默认配置'}")
        if state.get("messages"):
            last_message = state["messages"][-1]
            content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            print(f"   用户消息: {content[:50]}..." if len(content) > 50 else f"   用户消息: {content}")
        
        # 获取LLM实例
        llm = get_llm_from_config(config)
        
        # 获取配置实例
        agent_config = Configuration.from_runnable_config(config)
        
        # 获取工具
        tools = get_langchain_tools_by_categories(agent_config.enabled_tool_categories)
        
        # 获取系统提示词
        system_prompt = get_system_prompt_from_config(
            agent_id=agent_id,
            agent_name=agent_name,
            role_description=agent_config.role_description,
            enabled_tools=agent_config.enabled_tool_categories,
            require_approval_tools=agent_config.require_approval_tools,
            personality_traits=agent_config.personality_traits,
            custom_template=agent_config.system_prompt_template
        )
        
        print(f"🤖 系统提示词长度: {len(system_prompt)}")
        print(f"🤖 系统提示词预览: {system_prompt[:100]}...")
        
        # 创建ReAct agent - 确保prompt是string类型
        agent = create_react_agent(
            model=llm, 
            tools=tools, 
            prompt=str(system_prompt)
        )
        
        # 执行agent
        return await agent.ainvoke(state, config)
    
    # 创建状态图
    builder = StateGraph(AgentState, config_schema=Configuration)
    builder.add_node("agent", create_agent)
    builder.set_entry_point("agent")
    builder.set_finish_point("agent")
    
    return builder


def create_graph():
    """创建并编译图"""
    workflow = create_main_graph()
    return compile_graph_with_checkpointer(workflow)


# 创建默认图实例
graph = create_graph()

# 导出builder用于动态编译
builder = create_main_graph()