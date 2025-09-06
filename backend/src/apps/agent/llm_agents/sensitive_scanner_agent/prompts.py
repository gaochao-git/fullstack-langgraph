"""敏感数据扫描智能体提示词管理"""

from src.shared.core.logging import get_logger
from src.apps.agent.service.agent_service import agent_service
from src.shared.db.config import get_sync_db
from src.apps.agent.models import AgentConfig
from .configuration import AGENT_DETAIL_CONFIG

logger = get_logger(__name__)


async def get_system_prompt_async(agent_id: str) -> str:
    """异步获取系统提示词"""
    try:
        # 尝试从数据库获取最新的提示词
        from src.shared.db.config import get_async_db_context
        
        async with get_async_db_context() as db:
            agent = await agent_service.get_agent_by_id(db, agent_id)
            if agent and agent.get("system_message"):
                logger.debug(f"[{agent_id}] 从数据库获取系统提示词")
                return agent["system_message"]
    except Exception as e:
        logger.warning(f"[{agent_id}] 从数据库获取提示词失败: {e}")
    
    # 使用默认提示词
    logger.debug(f"[{agent_id}] 使用默认系统提示词")
    return AGENT_DETAIL_CONFIG.get("system_message", "")


def get_system_prompt_sync(agent_id: str) -> str:
    """同步获取系统提示词（供工具使用）"""
    try:
        # 从数据库获取
        db_gen = get_sync_db()
        db = next(db_gen)
        
        agent = db.query(AgentConfig).filter(
            AgentConfig.agent_id == agent_id
        ).first()
        
        if agent and agent.system_message:
            logger.debug(f"[{agent_id}] 从数据库获取系统提示词")
            return agent.system_message
            
    except Exception as e:
        logger.warning(f"[{agent_id}] 从数据库获取提示词失败: {e}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    # 使用默认提示词
    logger.debug(f"[{agent_id}] 使用默认系统提示词")
    return AGENT_DETAIL_CONFIG.get("system_message", "")