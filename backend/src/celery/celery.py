from celery import Celery
from celery.signals import worker_ready
from .logger import get_logger

# 创建 Celery 实例
app = Celery('omind_celery')

# 加载配置
app.config_from_object('src.celery.config')

# 获取日志器
logger = get_logger(__name__)

# 自动发现任务
app.autodiscover_tasks(['src.celery', 'src.apps'])

# Worker启动时初始化数据库
@worker_ready.connect
def init_worker(**kwargs):
    """Worker准备就绪时初始化数据库连接"""
    from .db_utils import init_celery_db
    success = init_celery_db()
    if not success:
        logger.warning("数据库初始化失败，但Worker将继续运行。某些功能可能受限。")

# 确保导入任务模块以注册信号处理器
from . import tasks

# 动态调度功能由 scheduler.py 中的 DatabaseScheduler 提供

if __name__ == '__main__':
    app.start() 