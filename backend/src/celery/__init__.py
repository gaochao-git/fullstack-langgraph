from src.celery.celery import app as celery_app
from src.celery.logger import get_logger

# 初始化模块级别的日志
logger = get_logger('celery_app')
logger.info('Celery App 初始化')

# 导入任务模块以注册任务
import src.apps.agent.tasks  # Agent模块的任务
import src.celery.tasks  # Celery系统任务

__all__ = ['celery_app', 'get_logger'] 