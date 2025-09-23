"""
敏感数据扫描的 Celery 任务
"""
from typing import List
from src.celery.celery import app
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@app.task(bind=True, time_limit=3600, soft_time_limit=3300, queue='priority_low')
def scan_files_task(self, task_id: str, file_ids: List[str]):
    """
    扫描文件任务（Celery版本）
    
    Args:
        task_id: 扫描任务ID
        file_ids: 文件ID列表
    """
    from .service import scan_task_service
    import asyncio
    
    logger.info(f"开始执行扫描任务: {task_id}, 文件数: {len(file_ids)}")
    
    try:
        # 使用 asyncio.run() 运行异步代码
        # 这是在同步环境中运行异步代码的推荐方式
        asyncio.run(
            scan_task_service._process_scan_task(task_id, file_ids)
        )
        
        logger.info(f"扫描任务完成: {task_id}")
        return {
            "status": "success", 
            "task_id": task_id,
            "total_files": len(file_ids)
        }
        
    except Exception as e:
        logger.error(f"扫描任务失败 {task_id}: {str(e)}")
        # 支持重试，每次重试间隔5分钟，最多重试3次
        raise self.retry(exc=e, countdown=300, max_retries=3)