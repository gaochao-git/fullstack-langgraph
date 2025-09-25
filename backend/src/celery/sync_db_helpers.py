"""
Celery同步数据库辅助函数
提供在Celery任务中使用的同步数据库操作方法
"""
from typing import Optional, Dict, Any
from sqlalchemy import text
from src.celery.db_utils import get_db_session
from src.celery.logger import get_logger

logger = get_logger(__name__)


def test_database_connection_sync() -> bool:
    """
    同步测试数据库连接
    返回: True 如果连接成功，False 如果连接失败
    """
    try:
        with get_db_session() as db:
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False


def get_agent_config_sync(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    同步获取智能体配置
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        智能体配置字典，如果不存在返回None
    """
    try:
        from src.apps.agent.models import AgentConfig
        
        with get_db_session() as db:
            agent = db.query(AgentConfig).filter(
                AgentConfig.agent_id == agent_id
            ).first()
            
            if agent:
                return {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "agent_type": agent.agent_type,
                    "agent_prompt": agent.agent_prompt,
                    "agent_config": agent.agent_config,
                    "agent_tools": agent.agent_tools
                }
            return None
            
    except Exception as e:
        logger.error(f"获取智能体配置失败: {str(e)}")
        return None


def count_registered_agents_sync() -> int:
    """
    同步统计已注册的智能体数量
    
    Returns:
        智能体数量
    """
    try:
        from src.apps.agent.models import AgentConfig
        
        with get_db_session() as db:
            count = db.query(AgentConfig).filter(
                AgentConfig.agent_enabled == 'yes'
            ).count()
            return count
            
    except Exception as e:
        logger.error(f"统计智能体数量失败: {str(e)}")
        return 0


def update_task_status_sync(task_id: str, status: str, error: Optional[str] = None) -> bool:
    """
    同步更新任务状态
    
    Args:
        task_id: 任务ID
        status: 新状态
        error: 错误信息（可选）
        
    Returns:
        更新是否成功
    """
    try:
        from src.apps.scheduled_task.celery_models import CeleryPeriodicTaskConfig
        from src.shared.db.models import now_shanghai
        
        with get_db_session() as db:
            task = db.query(CeleryPeriodicTaskConfig).filter(
                CeleryPeriodicTaskConfig.id == task_id
            ).first()
            
            if task:
                task.task_status = status
                task.update_time = now_shanghai()
                if error:
                    task.task_errors = error
                db.commit()
                return True
            return False
            
    except Exception as e:
        logger.error(f"更新任务状态失败: {str(e)}")
        return False


def get_all_agent_configs_sync() -> list:
    """
    同步获取所有活跃的智能体配置
    
    Returns:
        智能体配置列表
    """
    try:
        from src.apps.agent.models import AgentConfig
        
        with get_db_session() as db:
            agents = db.query(AgentConfig).filter(
                AgentConfig.agent_enabled == 'yes'
            ).all()
            
            return [{
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "agent_type": agent.agent_type,
                "agent_prompt": agent.agent_prompt,
                "agent_config": agent.agent_config,
                "agent_tools": agent.agent_tools
            } for agent in agents]
            
    except Exception as e:
        logger.error(f"获取所有智能体配置失败: {str(e)}")
        return []