"""
Agent注册表的同步辅助函数
用于在同步上下文（如模块导入时）中操作数据库
"""
from typing import Dict, Any
from src.shared.db.config import get_sync_db, SessionLocal
from src.shared.core.logging import get_logger
from src.apps.agent.models import AgentConfig
from src.shared.db.models import now_shanghai
import json

logger = get_logger(__name__)


def sync_agents_to_database(agents: Dict[str, Dict[str, Any]]) -> bool:
    """
    同步Agent信息到数据库（同步版本）
    
    Args:
        agents: Agent字典
        
    Returns:
        是否成功
    """
    try:
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            for agent_id, agent_info in agents.items():
                try:
                    # 检查是否已存在
                    existing = db.query(AgentConfig).filter(
                        AgentConfig.agent_id == agent_id
                    ).first()
                    
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
                        existing.update_time = now_shanghai()
                        existing.update_by = 'system'
                        logger.debug(f"Agent {agent_id} 已存在，更新基本信息")
                        
                except Exception as e:
                    logger.error(f"同步Agent {agent_id} 失败: {str(e)}")
                    continue
                    
            db.commit()
            logger.info(f"成功同步 {len(agents)} 个Agent到数据库")
            return True
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"同步Agent到数据库失败: {str(e)}")
        return False


def init_agent_registry_sync() -> bool:
    """
    在同步上下文中初始化Agent注册表
    用于Celery worker等场景
    
    Returns:
        是否成功
    """
    try:
        # 这里可以添加其他初始化逻辑
        logger.info("Agent注册表同步初始化完成")
        return True
    except Exception as e:
        logger.error(f"Agent注册表同步初始化失败: {str(e)}")
        return False