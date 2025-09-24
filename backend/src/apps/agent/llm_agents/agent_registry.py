"""
Agent 注册中心
提供基于装饰器的自动发现机制
"""

import importlib
from typing import Dict, Any, Optional
from pathlib import Path
from src.shared.core.logging import get_logger
from .generic_agent.graph import create_generic_agent
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.agent.models import AgentConfig
from sqlalchemy import select
logger = get_logger(__name__)


class AgentRegistry:
    """Agent 注册中心"""
    
    # Agent 映射表
    _agents: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    async def initialize(cls, db: AsyncSession):
        """初始化注册表 - 自动发现所有使用装饰器的 Agent"""
        cls.auto_discover_agents()
        
        # 同步到数据库（使用异步版本）
        try:
            await cls._sync_to_database(db)
            logger.info("Agent信息同步到数据库成功")
        except Exception as e:
            logger.error(f"同步Agent到数据库时发生错误: {e}")
            logger.warning("Agent信息同步到数据库失败，但不影响内存中的注册表")
        
        logger.info(f"Agent 注册表初始化完成，共 {len(cls._agents)} 个 Agent")
    
    @classmethod
    def auto_discover_agents(cls):
        """自动发现所有使用装饰器注册的 Agent"""
        agents_dir = Path(__file__).parent
        
        # 遍历所有子目录
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name.startswith("_"):
                continue
                
            # 检查是否有 graph.py 文件
            graph_file = agent_dir / "graph.py"
            if graph_file.exists():
                try:
                    # 动态导入模块，这会触发装饰器执行
                    module_name = f"src.apps.agent.llm_agents.{agent_dir.name}.graph"
                    importlib.import_module(module_name)
                except Exception as e:
                    logger.debug(f"导入 {agent_dir.name} 失败（可能不是 Agent）: {e}")
        
        # 从装饰器注册表中获取所有 Agent
        try:
            from .decorators import get_registered_agents
            decorated_agents = get_registered_agents()
            
            for agent_id, agent_info in decorated_agents.items():
                cls._agents[agent_id] = agent_info
                logger.info(f"发现 Agent: {agent_id} - {agent_info.get('description', '')}")
        except ImportError:
            logger.error("装饰器模块不存在")
    
    @classmethod
    async def create_agent(cls, agent_id: str, config: Any):
        """动态创建 Agent 实例
        
        Args:
            agent_id: Agent 标识
            config: 运行配置
            
        Returns:
            Agent 图实例
        """
        # 获取 Agent 信息
        agent_info = cls._agents.get(agent_id)
        logger.info(f"[Agent创建] 从注册表获取Agent信息: {agent_info}")
        if not agent_info:
            logger.warning(f"未注册的 Agent: {agent_id}，使用 generic_agent 模板")
            return await create_generic_agent(config)
        try:
            # 直接使用保存的函数引用
            creator_func = agent_info['func']
            logger.info(f"创建 Agent: {agent_id}")
            
            # 创建 Agent
            return await creator_func(config)
            
        except Exception as e:
            logger.error(f"创建 Agent {agent_id} 失败: {e}", exc_info=True)
            raise Exception(f"无法创建 Agent {agent_id}: {str(e)}")
    
    @classmethod
    def get_agent_info(cls, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取 Agent 信息"""
        return cls._agents.get(agent_id)
    
    @classmethod
    def list_agents(cls) -> Dict[str, Dict[str, Any]]:
        """列出所有已注册的 Agent"""
        return cls._agents.copy()
    
    @classmethod
    def is_builtin(cls, agent_id: str) -> bool:
        """判断是否为内置 Agent"""
        agent_info = cls._agents.get(agent_id, {})
        return agent_info.get('builtin', False)
    
    @classmethod
    async def _sync_to_database(cls, db: AsyncSession) -> bool:
        """
        同步Agent信息到数据库（异步版本）
        
        Args:
            db: 数据库会话
            
        Returns:
            是否成功
        """
        try:
            async with db.begin():
                for agent_id, agent_info in cls._agents.items():
                    try:
                        # 检查是否已存在
                        result = await db.execute(
                            select(AgentConfig).where(AgentConfig.agent_id == agent_id)
                        )
                        existing = result.scalar_one_or_none()
                        
                        if not existing:
                            # 创建新记录
                            agent_config = AgentConfig(
                                agent_id=agent_id,
                                agent_name=agent_info.get('description', agent_id),
                                agent_type=agent_info.get('agent_type', '自定义'),
                                agent_description=agent_info.get('description', ''),
                                agent_capabilities=agent_info.get('capabilities', []),
                                agent_version=agent_info.get('version', '1.0.0'),
                                agent_status='active',
                                agent_enabled='yes',
                                agent_icon=agent_info.get('icon', 'Bot'),
                                is_builtin='yes' if agent_info.get('builtin', False) else 'no',
                                tools_info={},
                                llm_info={},
                                prompt_info={},
                                agent_owner=agent_info.get('owner', 'system'),
                                visibility_type='public',
                                create_by=agent_info.get('owner', 'system')
                            )
                            db.add(agent_config)
                            logger.info(f"注册新Agent到数据库: {agent_id}")
                        else:
                            # 更新现有记录的基本信息（保留用户自定义的配置）
                            existing.agent_name = agent_info.get('description', existing.agent_name)
                            existing.is_builtin = 'yes' if agent_info.get('builtin', False) else 'no'
                            existing.update_by = 'system'
                            logger.debug(f"Agent {agent_id} 已存在，更新基本信息")
                            
                    except Exception as e:
                        logger.error(f"同步Agent {agent_id} 失败: {str(e)}")
                        continue
                        
                await db.flush()
                logger.info(f"成功同步 {len(cls._agents)} 个Agent到数据库")
                return True
                
        except Exception as e:
            logger.error(f"同步Agent到数据库失败: {str(e)}")
            return False


# 注意：初始化将在 FastAPI 的 lifespan 中进行，而不是在模块导入时
# 这样可以确保数据库已经初始化，并且使用异步操作