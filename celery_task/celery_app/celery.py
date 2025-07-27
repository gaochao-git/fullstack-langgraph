from celery import Celery

# 创建 Celery 实例
app = Celery('celery_app')

# 加载配置
app.config_from_object('celery_app.config')

# 自动发现任务
app.autodiscover_tasks(['celery_app'])

# 确保导入任务模块以注册信号处理器
from celery_app import tasks, agent_tasks

# 动态调度功能由 scheduler.py 中的 DatabaseScheduler 提供

if __name__ == '__main__':
    app.start() 