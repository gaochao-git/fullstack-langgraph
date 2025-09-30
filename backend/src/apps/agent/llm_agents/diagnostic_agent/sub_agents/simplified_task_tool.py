"""
简化的诊断子智能体任务工具
基于 DeepAgent 的设计理念
"""

from typing import List, Dict, Any, Annotated, Optional, Union
from langchain_core.tools import tool, InjectedToolCallId, BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.language_models import LanguageModelLike
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.types import Command
try:
    from langchain.chat_models import init_chat_model
except ImportError:
    # 兼容旧版本
    from langchain_community.chat_models import init_chat_model

from src.shared.core.logging import get_logger
from src.apps.agent.llm_agents.state_schemas import DiagnosticAgentState
from . import SubAgent
from .log_analyzer import LOG_ANALYZER_CONFIG
from .alert_correlator import ALERT_CORRELATOR_CONFIG
from .monitor_analyzer import MONITOR_ANALYZER_CONFIG
from .change_analyzer import CHANGE_ANALYZER_CONFIG

logger = get_logger(__name__)

# 更新子智能体配置，使用工具名称列表
SIMPLIFIED_SUBAGENTS = [
    {
        **LOG_ANALYZER_CONFIG,
        "tools": [
            # 系统工具
            "get_current_time",
            # ES 工具
            "get_es_data", "get_es_trends_data", "get_es_indices",
            # SSH 工具
            "execute_command", "execute_parameterized_command",
            "analyze_system_logs", "list_available_commands"
        ]
    },
    {
        **ALERT_CORRELATOR_CONFIG,
        "tools": [
            # 系统工具
            "get_current_time",
            # Zabbix 工具
            "get_zabbix_metric_data", "get_zabbix_metrics",
            # SSH 工具
            "check_service_status", "execute_command"
        ]
    },
    {
        **MONITOR_ANALYZER_CONFIG,
        "tools": [
            # 系统工具
            "get_current_time",
            # SSH 工具
            "execute_command", "execute_parameterized_command",
            "get_system_info", "analyze_processes",
            "check_service_status", "list_available_commands",
            # Zabbix 工具
            "get_zabbix_metric_data", "get_zabbix_metrics",
            # 数据库工具
            "execute_diagnostic_query", "list_diagnostic_queries",
            "check_database_health", "execute_readonly_sql",
            # 图表工具
            "create_line_chart", "create_bar_chart"
        ]
    },
    {
        **CHANGE_ANALYZER_CONFIG,
        "tools": [
            # 系统工具
            "get_current_time", "get_documents_content",
            # SSH 工具
            "execute_command", "get_system_info"
        ]
    }
]


def _get_agents(
    tools: List[Any], 
    main_prompt: str, 
    subagents: List[Dict], 
    model: LanguageModelLike,
    state_schema: type = DiagnosticAgentState
) -> Dict[str, Any]:
    """创建所有智能体（主智能体 + 子智能体）
    
    基于 DeepAgent 的设计：
    - 工具通过名称引用
    - 子智能体可以选择工具子集
    - 模型可以独立配置
    """
    # 创建工具名称到工具实例的映射
    tools_by_name = {}
    for tool in tools:
        if hasattr(tool, 'name'):
            tools_by_name[tool.name] = tool
    
    logger.info(f"🔧 可用工具总数: {len(tools_by_name)}")
    logger.debug(f"   工具列表: {list(tools_by_name.keys())}")
    
    # 创建智能体字典
    agents = {
        "general-purpose": create_react_agent(
            model, 
            prompt=main_prompt, 
            tools=tools,
            state_schema=state_schema,
            checkpointer=False
        )
    }
    
    # 创建各个子智能体
    for agent_config in subagents:
        agent_name = agent_config["name"]
        
        # 获取子智能体需要的工具
        if "tools" in agent_config:
            # 根据名称筛选工具
            agent_tools = []
            missing_tools = []
            
            for tool_name in agent_config["tools"]:
                if tool_name in tools_by_name:
                    agent_tools.append(tools_by_name[tool_name])
                else:
                    missing_tools.append(tool_name)
            
            if missing_tools:
                logger.warning(f"子智能体 {agent_name} 缺少工具: {missing_tools}")
            
            logger.info(f"子智能体 {agent_name} 获得 {len(agent_tools)}/{len(agent_config['tools'])} 个请求的工具")
        else:
            # 默认使用所有工具
            agent_tools = tools
            logger.info(f"子智能体 {agent_name} 使用所有 {len(tools)} 个工具")
        
        # 处理模型配置
        if "model" in agent_config:
            agent_model = agent_config["model"]
            if isinstance(agent_model, dict):
                # 字典配置 - 创建新模型
                sub_model = init_chat_model(**agent_model)
                logger.info(f"子智能体 {agent_name} 使用自定义模型配置")
            else:
                # 模型实例 - 直接使用
                sub_model = agent_model
                logger.info(f"子智能体 {agent_name} 使用提供的模型实例")
        else:
            # 使用主模型
            sub_model = model
            logger.debug(f"子智能体 {agent_name} 使用主模型")
        
        # 创建子智能体
        agents[agent_name] = create_react_agent(
            sub_model,
            prompt=agent_config["prompt"],
            tools=agent_tools,
            state_schema=state_schema,
            checkpointer=False
        )
        
        logger.info(f"✓ 创建子智能体 {agent_name} 完成")
    
    return agents


def _get_subagent_description(subagents: List[Dict]) -> List[str]:
    """获取子智能体描述列表"""
    return [f"- {agent['name']}: {agent['description']}" for agent in subagents]


def create_simplified_sub_agent_task_tool(
    tools: List[Any],
    main_prompt: str,
    model: LanguageModelLike,
    subagents: List[Dict] = None
):
    """创建简化的子智能体任务工具（基于 DeepAgent 设计）"""
    
    if subagents is None:
        subagents = SIMPLIFIED_SUBAGENTS
    
    # 在创建时就初始化所有智能体
    agents = _get_agents(tools, main_prompt, subagents, model)
    
    # 获取子智能体描述
    subagent_descriptions = _get_subagent_description(subagents)
    
    # 任务工具描述
    task_description = f"""启动专业子智能体来处理特定领域的诊断任务。

可用的子智能体类型：
- general-purpose: 通用诊断智能体，处理综合性问题和协调其他智能体
{chr(10).join(subagent_descriptions)}

使用场景示例：
1. 需要深入分析日志时，使用 log-analyzer
2. 多个报警需要关联分析时，使用 alert-correlator  
3. 需要分析性能指标时，使用 monitor-analyzer
4. 怀疑是变更导致的问题时，使用 change-analyzer

使用建议：
- 可以同时启动多个子智能体并行分析
- 每个子智能体都是独立的，会返回专业的分析报告
- 根据返回的报告综合判断故障原因"""
    
    @tool(description=task_description)
    async def sub_agent_task(
        description: str,
        subagent_type: str,
        state: Annotated[Dict[str, Any], InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId]
    ):
        """执行诊断子任务"""
        logger.info("="*60)
        logger.info(f"🤖 子智能体调用开始（简化版）")
        logger.info(f"📋 任务类型: {subagent_type}")
        logger.info(f"📝 任务描述: {description}")
        logger.info("="*60)
        
        # 检查子智能体类型是否有效
        if subagent_type not in agents:
            logger.error(f"❌ 未知的子智能体类型: {subagent_type}")
            return f"错误：未知的子智能体类型 '{subagent_type}'。可用类型：{list(agents.keys())}"
        
        try:
            # 获取选定的子智能体
            sub_agent = agents[subagent_type]
            
            # 创建子智能体的状态（基于 DeepAgent 的简化方式）
            state_dict = state if isinstance(state, dict) else {}
            
            # 子智能体使用新的消息历史
            sub_state = {
                "messages": [{"role": "user", "content": description}],
                "remaining_steps": state_dict.get("remaining_steps", 10),
                "todos": [],  # 子智能体有自己的 TODO 列表
                "files": state_dict.get("files", {}),  # 共享文件系统
                "current_dir": state_dict.get("current_dir", "/"),
                "context": state_dict.get("context", {}),
                "diagnosis_results": [],
                "system_metrics": {},
                "root_causes": []
            }
            
            logger.info(f"🚀 正在启动子智能体: {subagent_type}")
            
            # 执行子智能体
            result = await sub_agent.ainvoke(sub_state)
            
            # 提取最后的回复
            final_message = result["messages"][-1].content if result.get("messages") else "子智能体未返回结果"
            
            logger.info(f"✅ 子智能体 {subagent_type} 执行完成")
            logger.info("="*60)
            
            # 返回结果（基于 DeepAgent 的 Command 模式）
            update_dict = {
                "messages": [
                    ToolMessage(
                        content=f"[{subagent_type}] 分析结果:\n\n{final_message}",
                        tool_call_id=tool_call_id
                    )
                ],
                # 共享文件系统状态
                "files": result.get("files", state_dict.get("files", {}))
            }
            
            # 传递子智能体的诊断结果
            if result.get("diagnosis_results"):
                update_dict["diagnosis_results"] = state_dict.get("diagnosis_results", []) + result["diagnosis_results"]
                
            if result.get("system_metrics"):
                current_metrics = state_dict.get("system_metrics", {})
                current_metrics.update(result["system_metrics"])
                update_dict["system_metrics"] = current_metrics
                
            if result.get("root_causes"):
                update_dict["root_causes"] = state_dict.get("root_causes", []) + result["root_causes"]
            
            return Command(update=update_dict)
            
        except Exception as e:
            logger.error(f"❌ 子智能体 {subagent_type} 执行失败: {e}", exc_info=True)
            return f"子智能体执行失败: {str(e)}"
    
    return sub_agent_task