from src.shared.core.config import settings
from celery.schedules import crontab
from kombu import Queue
# Broker 设置 - 使用 Redis 作为消息代理
broker_url = settings.CELERY_BROKER_URL

# Backend 设置 - 使用 MySQL 存储任务结果
# 使用 pymysql 替代 mysqldb
import pymysql
pymysql.install_as_MySQLdb()

result_backend = settings.CELERY_RESULT_BACKEND

# 序列化设置
accept_content = ['json']
task_serializer = 'json'
result_serializer = 'json'
timezone = 'UTC'  # 改为UTC避免时区问题
# 使用新的配置名称 enable_utc 替代 ENABLE_UTC  
enable_utc = True

# 添加新的配置项，解决启动时连接重试的警告
broker_connection_retry_on_startup = True

# 使用自定义数据库调度器（官方推荐模式）
beat_scheduler = 'src.celery.scheduler.DatabaseScheduler'

# 设置 Beat 最大循环间隔为30秒，提高新任务检测速度
beat_max_loop_interval = 30

# 数据库配置已移至项目统一管理，使用 src.shared.db.config

# ========== 队列配置 ==========
# 三个队列，优先级从高到低：system > priority_high > priority_low
# Worker处理顺序: -Q system,priority_high,priority_low,celery

# 显式定义队列，确保exchange一致性
task_queues = (
    Queue('system', routing_key='system'),
    Queue('priority_high', routing_key='priority_high'), 
    Queue('priority_low', routing_key='priority_low'),
    Queue('celery', routing_key='celery'),  # 默认队列
)

# 固定路由规则：只有系统任务使用固定路由
task_routes = {
    # 系统维护任务 → system队列
    'src.celery.tasks.*': {'queue': 'system'},
    # Agent健康检查任务 → system队列
    'src.apps.agent.tasks.periodic_agent_health_check': {'queue': 'system'},
}

# 默认队列：智能体任务的兜底队列
task_default_queue = 'priority_low'

# ========== 定时任务配置 ==========
beat_schedule = {
    # 健康检查任务 - 每30分钟执行一次
    'health-check': {
        'task': 'src.apps.agent.tasks.periodic_agent_health_check',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'system'},
    },
}

# ========== 重试配置 ==========
# 数据库操作重试次数
DB_RETRY_MAX = 3

# ========== 配置说明 ==========
# 1. 使用DatabaseScheduler从数据库动态加载定时任务
# 2. 支持动态添加/修改/删除任务，立即生效
# 3. 任务配置存储在celery_periodic_task_configs表中