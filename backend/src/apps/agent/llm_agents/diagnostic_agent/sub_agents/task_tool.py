"""诊断子智能体任务工具"""

from typing import List, Dict, Any, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langchain_core.language_models import LanguageModelLike
try:
    from langchain.chat_models import init_chat_model
except ImportError:
    # 兼容旧版本
    from langchain_community.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.types import Command

from src.shared.core.logging import get_logger
from src.apps.agent.llm_agents.state_schemas import DiagnosticAgentState
from . import SubAgent
from .log_analyzer import LOG_ANALYZER_CONFIG
from .alert_correlator import ALERT_CORRELATOR_CONFIG
from .monitor_analyzer import MONITOR_ANALYZER_CONFIG
from .change_analyzer import CHANGE_ANALYZER_CONFIG

logger = get_logger(__name__)

# 所有子智能体配置
DIAGNOSTIC_SUBAGENTS = [
    LOG_ANALYZER_CONFIG,
    ALERT_CORRELATOR_CONFIG,
    MONITOR_ANALYZER_CONFIG,
    CHANGE_ANALYZER_CONFIG
]


def _get_subagent_description(subagents: List[SubAgent]) -> List[str]:
    """获取子智能体描述列表"""
    return [f"- {agent['name']}: {agent['description']}" for agent in subagents]


def _get_tools_for_subagent(agent_name: str, tools_by_name: Dict[str, Any]) -> List[Any]:
    """根据子智能体类型精确指定工具列表
    
    Args:
        agent_name: 子智能体名称
        tools_by_name: 工具名称到工具实例的映射
        
    Returns:
        该子智能体应该拥有的工具列表
    """
    # 定义每个子智能体的精确工具列表
    tool_assignments = {
        "log-analyzer": [
            # Elasticsearch工具
            "get_es_data",
            "get_es_trends_data", 
            "get_es_indices",
            # SSH工具
            "execute_command",
            "execute_parameterized_command",
            "analyze_system_logs",
            "list_available_commands",
            # 系统工具
            "get_current_time"
        ],
        "monitor-analyzer": [
            # SSH工具
            "execute_command",
            "execute_parameterized_command",
            "get_system_info",
            "analyze_processes",
            "check_service_status",
            "list_available_commands",
            # Zabbix工具
            "get_zabbix_metric_data",
            "get_zabbix_metrics",
            # 数据库诊断工具
            "execute_diagnostic_query",
            "list_diagnostic_queries", 
            "check_database_health",
            "execute_readonly_sql",
            # 系统工具
            "get_current_time",
            # 图表工具
            "create_line_chart",
            "create_bar_chart"
        ],
        "alert-correlator": [
            # Zabbix工具
            "get_zabbix_metric_data",
            "get_zabbix_metrics",
            # SSH基础工具
            "check_service_status",
            "execute_command",
            # 系统工具
            "get_current_time"
        ],
        "change-analyzer": [
            # SSH基础工具
            "execute_command",
            "get_system_info",
            # 系统工具
            "get_current_time",
            "get_documents_content"
        ]
    }
    
    # 获取该子智能体的工具名称列表
    assigned_tool_names = tool_assignments.get(agent_name, [])
    
    # 根据名称获取实际的工具对象
    assigned_tools = []
    for tool_name in assigned_tool_names:
        if tool_name in tools_by_name:
            assigned_tools.append(tools_by_name[tool_name])
        else:
            logger.warning(f"工具 '{tool_name}' 未找到，跳过分配给 {agent_name}")
    
    logger.info(f"为 {agent_name} 分配了 {len(assigned_tools)} 个工具: {assigned_tool_names}")
    
    return assigned_tools


async def _create_subagent_registry(
    tools: List[Any],
    main_prompt: str,
    subagents: List[SubAgent],
    default_model: LanguageModelLike,
    state_schema: type = None
) -> Dict[str, Any]:
    """创建子智能体注册表"""
    logger.info("🔧 开始创建子智能体注册表...")
    # 如果没有指定 state_schema，使用 DiagnosticAgentState
    if state_schema is None:
        state_schema = DiagnosticAgentState
    
    agents = {
        "general-purpose": create_react_agent(
            default_model,
            prompt=main_prompt,
            tools=tools,
            state_schema=state_schema,
            checkpointer=False
        )
    }
    logger.info("  ✓ 创建 general-purpose 智能体")
    
    # 将工具列表转换为字典，方便查找
    tools_by_name = {}
    for tool in tools:
        if hasattr(tool, 'name'):
            tools_by_name[tool.name] = tool
    
    # 创建各个子智能体
    for agent_config in subagents:
        # 根据子智能体类型精确分配工具
        agent_tools = _get_tools_for_subagent(agent_config["name"], tools_by_name)
        
        # 简化处理：始终使用默认模型
        # 未来可以支持自定义模型配置
        sub_model = default_model
        
        # 创建子智能体
        agents[agent_config["name"]] = create_react_agent(
            sub_model,
            prompt=agent_config["prompt"],
            tools=agent_tools,
            state_schema=state_schema,
            checkpointer=False
        )
        
        logger.info(f"  ✓ 创建子智能体: {agent_config['name']}")
        logger.info(f"    - 描述: {agent_config['description'][:50]}...")
        logger.info(f"    - 工具数: {len(agent_tools)}")
        
        # 显示分配的工具类别统计
        tool_categories = {}
        for tool in agent_tools:
            tool_name = getattr(tool, 'name', str(tool))
            if '_' in tool_name:
                category = tool_name.split('_')[0]
            else:
                category = 'system'
            tool_categories[category] = tool_categories.get(category, 0) + 1
        logger.info(f"    - 工具类别: {tool_categories}")
    
    return agents


def create_diagnostic_task_tool(
    tools: List[Any],
    main_prompt: str,
    model: LanguageModelLike,
    subagents: List[SubAgent] = None
):
    """创建诊断任务工具（用于调度子智能体）"""
    
    if subagents is None:
        subagents = DIAGNOSTIC_SUBAGENTS
    
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
    async def diagnostic_task(
        description: str,
        subagent_type: str,
        state: Annotated[Dict[str, Any], InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId]
    ):
        """执行诊断子任务"""
        logger.info("="*60)
        logger.info(f"🤖 子智能体调用开始")
        logger.info(f"📋 任务类型: {subagent_type}")
        logger.info(f"📝 任务描述: {description}")
        
        # 调试：打印传入的 state 结构
        logger.debug(f"📊 传入的 state 键: {list(state.keys()) if isinstance(state, dict) else 'Not a dict'}")
        if isinstance(state, dict):
            if 'todos' in state and state['todos']:
                logger.debug(f"   - todos 示例: {state['todos'][0] if state['todos'] else 'empty'}")
            logger.debug(f"   - remaining_steps: {state.get('remaining_steps', 'Missing')}")
        
        logger.info("="*60)
        # 延迟创建智能体注册表，避免循环依赖
        if not hasattr(diagnostic_task, '_agents'):
            diagnostic_task._agents = await _create_subagent_registry(
                tools, main_prompt, subagents, model
            )
        
        agents = diagnostic_task._agents
        
        # 检查子智能体类型是否有效
        if subagent_type not in agents:
            logger.error(f"❌ 未知的子智能体类型: {subagent_type}")
            logger.error(f"   可用类型: {list(agents.keys())}")
            return f"错误：未知的子智能体类型 '{subagent_type}'。可用类型：{list(agents.keys())}"
        
        try:
            # 获取选定的子智能体
            sub_agent = agents[subagent_type]
            
            # 创建子智能体的状态（需要满足 DiagnosticAgentState 的所有必需字段）
            # 从主智能体状态中继承一些信息，但要确保 state 是字典类型
            state_dict = state if isinstance(state, dict) else {}
            
            sub_state = {
                "messages": [{"role": "user", "content": description}],
                "remaining_steps": 10,  # 给子智能体足够的步骤数
                "todos": [],  # 子智能体开始时没有todos
                "files": state_dict.get("files", {}),  # 继承文件系统状态
                "current_dir": state_dict.get("current_dir", "/"),
                "context": state_dict.get("context", {}),  # 继承上下文
                "diagnosis_results": [],  # 子智能体的诊断结果
                "system_metrics": {},  # 子智能体的系统指标
                "root_causes": []  # 子智能体的根因分析
            }
            
            logger.info(f"🚀 正在启动子智能体: {subagent_type}")
            logger.info(f"📊 子智能体配置:")
            # 找到对应的子智能体配置并打印描述
            for sub in subagents:
                if sub['name'] == subagent_type:
                    logger.info(f"   - 描述: {sub['description']}")
                    break
            
            # 执行子智能体
            logger.info(f"⏳ 子智能体执行中...")
            result = await sub_agent.ainvoke(sub_state)
            
            # 提取最后的回复
            final_message = result["messages"][-1].content if result.get("messages") else "子智能体未返回结果"
            
            logger.info(f"✅ 子智能体 {subagent_type} 执行完成")
            logger.info(f"📄 返回结果长度: {len(final_message)} 字符")
            logger.info("="*60)
            
            # 返回结果给主智能体
            # 提取子智能体可能产生的状态更新
            update_dict = {
                "messages": [
                    ToolMessage(
                        content=f"[{subagent_type}] 分析结果:\\n\\n{final_message}",
                        tool_call_id=tool_call_id
                    )
                ]
            }
            
            # 如果子智能体产生了诊断结果，传递回主智能体
            if result.get("diagnosis_results"):
                update_dict["diagnosis_results"] = state_dict.get("diagnosis_results", []) + result["diagnosis_results"]
                
            # 如果子智能体更新了系统指标
            if result.get("system_metrics"):
                current_metrics = state_dict.get("system_metrics", {})
                current_metrics.update(result["system_metrics"])
                update_dict["system_metrics"] = current_metrics
                
            # 如果子智能体识别了根因
            if result.get("root_causes"):
                update_dict["root_causes"] = state_dict.get("root_causes", []) + result["root_causes"]
            
            return Command(update=update_dict)
            
        except Exception as e:
            logger.error(f"❌ 子智能体 {subagent_type} 执行失败: {e}", exc_info=True)
            logger.error("="*60)
            return f"子智能体执行失败: {str(e)}"
    
    return diagnostic_task