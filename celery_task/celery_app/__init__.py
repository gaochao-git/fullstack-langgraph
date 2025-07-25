from celery_app.celery import app as celery_app

# 导入任务模块以注册任务
import celery_app.agent_tasks
import celery_app.tasks

__all__ = ['celery_app'] 