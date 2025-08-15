from celery_app.celery import app as celery_app
from celery_app.logger import get_logger

# 初始化模块级别的日志
logger = get_logger('celery_app')
logger.info('Celery App 初始化')

# 导入任务模块以注册任务
import celery_app.agent_tasks
import celery_app.tasks

__all__ = ['celery_app', 'get_logger'] 