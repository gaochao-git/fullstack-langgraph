"""
Celery健康检查模块
提供Celery worker和beat的健康状态检查
"""
from typing import Dict, Any, List
from celery import current_app
from src.celery.db_utils import get_db_session
from src.celery.sync_db_helpers import test_database_connection_sync
from src.celery.logger import get_logger

logger = get_logger(__name__)


def get_celery_worker_status() -> Dict[str, Any]:
    """
    获取Celery Worker的状态信息
    
    Returns:
        包含worker状态的字典
    """
    try:
        # 获取活跃的worker
        inspect = current_app.control.inspect()
        active_nodes = inspect.active()
        
        if not active_nodes:
            return {
                "status": "error",
                "message": "No active workers found",
                "workers": []
            }
        
        workers = []
        for node_name, tasks in active_nodes.items():
            workers.append({
                "name": node_name,
                "active_tasks": len(tasks),
                "status": "active"
            })
        
        return {
            "status": "healthy",
            "workers": workers,
            "total_workers": len(workers)
        }
        
    except Exception as e:
        logger.error(f"获取Worker状态失败: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "workers": []
        }


def get_celery_beat_status() -> Dict[str, Any]:
    """
    获取Celery Beat的状态信息
    
    Returns:
        包含beat状态的字典
    """
    try:
        # 检查数据库中的定时任务
        from src.apps.scheduled_task.celery_models import CeleryPeriodicTaskConfig
        
        with get_db_session() as db:
            total_tasks = db.query(CeleryPeriodicTaskConfig).count()
            enabled_tasks = db.query(CeleryPeriodicTaskConfig).filter(
                CeleryPeriodicTaskConfig.task_enabled == True
            ).count()
        
        return {
            "status": "healthy",
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks
        }
        
    except Exception as e:
        logger.error(f"获取Beat状态失败: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def get_registered_tasks() -> List[str]:
    """
    获取已注册的任务列表
    
    Returns:
        任务名称列表
    """
    try:
        return sorted(list(current_app.tasks.keys()))
    except Exception as e:
        logger.error(f"获取注册任务失败: {str(e)}")
        return []


def get_celery_health_status() -> Dict[str, Any]:
    """
    获取Celery整体健康状态
    
    Returns:
        包含完整健康状态的字典
    """
    # 检查数据库连接
    db_healthy = test_database_connection_sync()
    
    # 获取各组件状态
    worker_status = get_celery_worker_status()
    beat_status = get_celery_beat_status()
    registered_tasks = get_registered_tasks()
    
    # 判断整体健康状态
    overall_healthy = (
        db_healthy and 
        worker_status.get("status") == "healthy" and
        len(registered_tasks) > 0
    )
    
    return {
        "healthy": overall_healthy,
        "database": {
            "connected": db_healthy
        },
        "worker": worker_status,
        "beat": beat_status,
        "registered_tasks": {
            "count": len(registered_tasks),
            "tasks": registered_tasks
        }
    }