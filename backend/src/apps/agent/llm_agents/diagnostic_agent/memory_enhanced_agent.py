"""
集成长期记忆的增强诊断Agent
"""
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
import json

from src.apps.agent.memory_factory import get_enterprise_memory
from src.shared.core.logging import get_logger
from src.shared.db.config import get_sync_db
from .state import DiagnosticState

logger = get_logger(__name__)


class MemoryEnhancedDiagnosticAgent:
    """集成长期记忆的诊断Agent"""
    
    def __init__(self, llm, tools, checkpointer, memory_config=None):
        self.llm = llm
        self.tools = tools
        self.checkpointer = checkpointer
        self.memory = None
        self.memory_config = memory_config or {}
        
    async def initialize(self):
        """初始化记忆系统"""
        self.memory = await get_enterprise_memory()
        
    async def retrieve_context(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """从长期记忆中检索相关上下文"""
        try:
            # 获取最新的用户消息
            user_message = state["messages"][-1].content if state["messages"] else ""
            
            # 从配置中获取用户ID和系统ID
            configurable = config.get("configurable", {})
            
            # 优先从 configurable 中获取，这是 LangGraph 的标准方式
            user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
            agent_id = configurable.get("agent_id")
            if not agent_id:
                from src.shared.core.exceptions import BusinessException, ResponseCode
                raise BusinessException("agent_id is required in configurable", ResponseCode.PARAM_ERROR)
            system_id = configurable.get("system_id") or "default_system"
            
            logger.info(f"从配置中获取到的用户信息: user_id={user_id}, agent_id={agent_id}, configurable={configurable}")
            
            # 从配置中获取记忆搜索参数
            search_limit = self.memory_config.get('memory_search_limit', 10)
            distance_threshold = self.memory_config.get('memory_distance_threshold', None)
            
            # 使用标准的 Mem0 API 参数
            search_params = {
                "namespace": "diagnostic_context",  # 保留用于 search_memories 方法
                "query": user_message,
                "limit": search_limit,
                "user_id": user_id,
                "agent_id": agent_id,  # 添加 agent_id
                # 将 system_id 移到 metadata 中
                "metadata": {
                    "system_id": system_id,
                    "context_type": "diagnostic"
                }
            }
            
            # 如果配置了距离阈值，添加到搜索参数
            if distance_threshold is not None:
                search_params["distance_threshold"] = distance_threshold
            
            # 暂时分离出 metadata，因为 search_memories 可能还不支持
            metadata = search_params.pop("metadata", {})
            memories = await self.memory.search_memories(**search_params)
            
            # 将搜索结果组织成结构化的上下文
            context = {
                "system_context": [],
                "similar_incidents": [],
                "solution_patterns": [],
                "user_preferences": []
            }
            
            # 根据记忆内容分类（简化处理）
            for memory in memories:
                if memory and isinstance(memory, dict):
                    # 暂时将所有记忆都作为历史经验
                    context["similar_incidents"].append(memory)
            
            # 如果有相关记忆，构建增强的系统提示
            if any(context.values()):
                enhanced_prompt = self._build_enhanced_prompt(context)
                # 添加系统消息到状态
                state["messages"].insert(0, SystemMessage(content=enhanced_prompt))
            
            # 保存上下文到状态供后续使用
            state["memory_context"] = context
            
            logger.info(f"搜索记忆: user_id={user_id}, agent_id={agent_id}, 找到 {len(memories)} 条相关记忆")
            
        except Exception as e:
            logger.error(f"检索记忆上下文失败: {e}")
            
        return state
    
    def _build_enhanced_prompt(self, context: Dict[str, Any]) -> str:
        """构建增强的系统提示"""
        prompt_parts = ["基于历史知识和企业信息进行诊断：\n"]
        
        # 添加系统架构信息
        if context.get("system_context"):
            prompt_parts.append("\n## 相关系统架构信息：")
            for mem in context["system_context"][:3]:  # 只取最相关的3条
                prompt_parts.append(f"- {mem['content']}")
        
        # 添加历史故障案例
        if context.get("similar_incidents"):
            prompt_parts.append("\n## 相似历史故障案例：")
            for mem in context["similar_incidents"][:3]:
                prompt_parts.append(f"- {mem['content']}")
        
        # 添加解决方案模式
        if context.get("solution_patterns"):
            prompt_parts.append("\n## 推荐的解决方案模式：")
            for mem in context["solution_patterns"][:2]:
                prompt_parts.append(f"- {mem['content']}")
        
        # 添加用户偏好
        if context.get("user_preferences"):
            prompt_parts.append("\n## 用户偏好设置：")
            for pref in context["user_preferences"]:
                prompt_parts.append(f"- {pref['content']}")
        
        prompt_parts.append("\n请基于以上历史信息和当前问题进行诊断。")
        
        return "\n".join(prompt_parts)
    
    async def save_diagnosis_result(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """保存诊断结果到长期记忆"""
        try:
            # 获取配置信息
            configurable = config.get("configurable", {})
            
            # 优先从 configurable 中获取
            user_id = configurable.get("user_name") or configurable.get("user_id") or "default_user"
            agent_id = configurable.get("agent_id")
            if not agent_id:
                from src.shared.core.exceptions import BusinessException, ResponseCode
                raise BusinessException("agent_id is required in configurable", ResponseCode.PARAM_ERROR)
            
            logger.info(f"保存记忆时的用户信息: user_id={user_id}, agent_id={agent_id}")
            
            # 构建对话消息用于Mem0学习
            conversation_messages = []
            for msg in state["messages"]:
                if hasattr(msg, 'type'):
                    if msg.type == "human":
                        conversation_messages.append({"role": "user", "content": msg.content})
                    elif msg.type == "ai":
                        conversation_messages.append({"role": "assistant", "content": msg.content})
            
            # 使用后台任务异步保存记忆，避免阻塞对话结束
            if conversation_messages:
                import asyncio
                # 创建后台任务，不等待完成
                task = asyncio.create_task(self._save_memory_background(
                    conversation_messages, 
                    user_id, 
                    agent_id,
                    {
                        "session_type": "diagnostic",
                        "system_id": configurable.get("system_id", ""),
                        "resolved": state.get("resolved", False)
                    }
                ))
                logger.info(f"已启动后台记忆保存任务 (user_id={user_id})")
            
        except Exception as e:
            logger.error(f"保存诊断结果失败: {e}")
            
        return state
    
    async def _save_memory_background(self, conversation_messages, user_id, agent_id, metadata):
        """后台异步保存记忆，不阻塞主流程"""
        try:
            memory_id = await self.memory.add_conversation_memory(
                messages=conversation_messages,
                user_id=user_id,
                agent_id=agent_id,
                metadata=metadata
            )
            logger.info(f"后台记忆保存完成: {memory_id} (user_id={user_id})")
        except Exception as e:
            logger.error(f"后台记忆保存失败: {e} (user_id={user_id})")
    
    async def analyze_and_learn(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """分析诊断过程并学习新模式"""
        try:
            # 获取工具调用历史
            tool_calls = state.get("tool_calls", [])
            
            # 分析成功的工具调用模式
            if tool_calls and state.get("resolved"):
                # 提取问题类型
                problem_type = self._extract_problem_type(state)
                
                # 构建解决方案模式
                solution_pattern = {
                    "problem_type": problem_type,
                    "successful_tools": [tool["name"] for tool in tool_calls if tool.get("success")],
                    "diagnosis_steps": self._extract_diagnosis_steps(state),
                    "resolution_time": state.get("resolution_time", "")
                }
                
                # 存储解决方案模式
                content = f"""
问题类型: {problem_type}
成功使用的工具: {', '.join(solution_pattern['successful_tools'])}
诊断步骤: {json.dumps(solution_pattern['diagnosis_steps'], ensure_ascii=False)}
"""
                
                await self.memory.add_memory(
                    namespace=self.memory.NAMESPACES["solution_patterns"],
                    content=content,
                    metadata=solution_pattern,
                    problem_type=problem_type
                )
                
                logger.info(f"已学习新的解决方案模式: {problem_type}")
                
        except Exception as e:
            logger.error(f"分析学习失败: {e}")
            
        return state
    
    def _extract_problem_type(self, state: DiagnosticState) -> str:
        """提取问题类型"""
        # 这里可以使用NLP或规则提取问题类型
        # 简化示例：基于关键词
        user_message = ""
        for msg in state["messages"]:
            if hasattr(msg, 'type') and msg.type == "human":
                user_message = msg.content.lower()
                break
        
        if "cpu" in user_message:
            return "cpu_performance"
        elif "内存" in user_message or "memory" in user_message:
            return "memory_issue"
        elif "网络" in user_message or "network" in user_message:
            return "network_issue"
        elif "数据库" in user_message or "database" in user_message:
            return "database_issue"
        else:
            return "general"
    
    def _extract_diagnosis_steps(self, state: DiagnosticState) -> List[str]:
        """提取诊断步骤"""
        steps = []
        
        # 从消息历史中提取诊断步骤
        for msg in state["messages"]:
            if hasattr(msg, 'content') and "执行" in msg.content:
                # 简化提取：查找包含命令的行
                lines = msg.content.split('\n')
                for line in lines:
                    if any(cmd in line for cmd in ["执行:", "查看:", "分析:"]):
                        steps.append(line.strip())
        
        return steps[:10]  # 最多返回10个步骤
    
    def create_graph(self):
        """创建集成记忆的诊断图"""
        # 创建工具节点
        tool_node = ToolNode(self.tools)
        
        # 创建状态图
        workflow = StateGraph(DiagnosticState)
        
        # 添加节点
        workflow.add_node("retrieve_context", self.retrieve_context)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", tool_node)
        workflow.add_node("save_result", self.save_diagnosis_result)
        workflow.add_node("analyze_learn", self.analyze_and_learn)
        
        # 设置入口点
        workflow.add_edge(START, "retrieve_context")
        workflow.add_edge("retrieve_context", "agent")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "agent",
            self._should_use_tools,
            {
                "tools": "tools",
                "save": "save_result"
            }
        )
        
        workflow.add_edge("tools", "agent")
        workflow.add_edge("save_result", "analyze_learn")
        workflow.add_edge("analyze_learn", END)
        
        # 编译图
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _agent_node(self, state: DiagnosticState, config: RunnableConfig) -> DiagnosticState:
        """Agent节点处理逻辑"""
        # 调用LLM
        response = await self.llm.ainvoke(state["messages"])
        state["messages"].append(response)
        
        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            state["tool_calls"] = response.tool_calls
        
        return state
    
    def _should_use_tools(self, state: DiagnosticState) -> str:
        """判断是否需要使用工具"""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        return "save"


async def create_memory_enhanced_diagnostic_agent(llm, tools, checkpointer, agent_id="diagnostic_agent"):
    """创建集成长期记忆的诊断Agent"""
    # 获取智能体的memory_info配置
    memory_config = {}
    try:
        from src.apps.agent.service.agent_config_service import AgentConfigService
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            # 直接查询数据库获取 agent 配置
            from sqlalchemy import select
            from src.apps.agent.models import AgentConfig
            
            stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            result = db.execute(stmt)
            agent_config = result.scalar_one_or_none()
            
            if agent_config and agent_config.memory_info:
                memory_config = agent_config.memory_info
                logger.info(f"获取到智能体记忆配置: {memory_config}")
            else:
                logger.info(f"智能体 {agent_id} 没有配置记忆信息")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"无法获取智能体记忆配置: {e}")
    
    agent = MemoryEnhancedDiagnosticAgent(llm, tools, checkpointer, memory_config)
    await agent.initialize()
    return agent.create_graph()


# 示例：在诊断完成后存储系统架构信息
async def store_system_info_example():
    """存储系统架构信息示例"""
    memory = await get_enterprise_memory()
    
    # 存储系统架构
    await memory.store_system_architecture(
        system_id="order_system",
        architecture_info={
            "service_name": "订单管理系统",
            "technology_stack": ["Java", "Spring Boot", "MySQL", "Redis"],
            "deployment": {
                "environment": "生产环境",
                "servers": ["192.168.1.10", "192.168.1.11"],
                "load_balancer": "nginx",
                "database": {
                    "type": "MySQL",
                    "version": "8.0",
                    "cluster": "master-slave"
                }
            },
            "dependencies": ["用户服务", "库存服务", "支付服务"],
            "monitoring": {
                "metrics": "Prometheus",
                "logs": "ELK Stack",
                "tracing": "Jaeger"
            },
            "contacts": {
                "owner": "张三",
                "team": "订单组",
                "oncall": "李四"
            }
        }
    )
    
    # 存储故障案例
    await memory.store_incident(
        system_id="order_system",
        incident={
            "timestamp": "2024-01-15 10:30:00",
            "symptoms": "订单创建接口响应时间超过5秒，大量超时",
            "root_cause": "数据库连接池耗尽，连接数达到上限",
            "solution": "1. 临时增加连接池大小到200\n2. 优化慢查询\n3. 增加数据库读副本",
            "impact": "影响约1000个订单创建，持续时间30分钟",
            "prevention": "设置连接池监控告警，当使用率超过80%时预警"
        }
    )
    
    logger.info("系统信息存储完成")