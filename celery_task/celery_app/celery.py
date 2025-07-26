from celery import Celery

# 创建 Celery 实例
app = Celery('celery_app')

# 加载配置
app.config_from_object('celery_app.config')

# 自动发现任务
app.autodiscover_tasks(['celery_app'])

# 确保导入任务模块以注册信号处理器
from celery_app import tasks, agent_tasks

# 导入动态调度器以初始化
try:
    from celery_app import dynamic_scheduler
    print("动态任务调度器已加载")
except ImportError as e:
    print(f"警告: 无法加载动态任务调度器: {e}")

if __name__ == '__main__':
    app.start() 