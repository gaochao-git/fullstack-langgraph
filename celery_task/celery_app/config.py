# Broker 设置 - 使用 Redis 作为消息代理
# 使用新的配置名称 broker_url 替代 BROKER_URL
# 格式: redis://:password@host:port/db
broker_url = 'redis://:fffjjj@82.156.146.51:6379/0'

# Backend 设置 - 使用 MySQL 存储任务结果
# 格式: mysql://用户名:密码@主机:端口/数据库名
result_backend = 'db+mysql://gaochao:fffjjj@82.156.146.51:3306/celery_tasks'

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
beat_scheduler = 'celery_app.scheduler.DatabaseScheduler'

# 设置 Beat 最大循环间隔为30秒，提高新任务检测速度
beat_max_loop_interval = 30

# MySQL 配置
DATABASE_CONFIG = {
    'host': '82.156.146.51',
    'port': 3306,
    'user': 'gaochao',
    'password': 'fffjjj',
    'database': 'celery_tasks',
    'charset': 'utf8mb4'
}

# ========== 队列配置 ==========
# 三个队列，优先级从高到低：system > priority_high > priority_low
# Worker处理顺序: -Q system,priority_high,priority_low,celery

from kombu import Queue

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
    'celery_app.tasks.*': {'queue': 'system'},
    'celery_app.agent_tasks.periodic_agent_health_check': {'queue': 'system'},
}

# 默认队列：智能体任务的兜底队列
task_default_queue = 'priority_low'

# ========== 定时任务配置 ==========
from celery.schedules import crontab

beat_schedule = {
    # 健康检查任务 - 每30分钟执行一次
    'health-check': {
        'task': 'celery_app.agent_tasks.periodic_agent_health_check',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'system'},
    },
}

# ========== 智能体API配置 ==========
# 智能体API地址
AGENT_API_BASE_URL = 'http://172.20.10.2:8000'

# ========== 重试配置 ==========
# 数据库操作重试次数
DB_RETRY_MAX = 3

# ========== 配置说明 ==========
# 1. 使用DatabaseScheduler从数据库动态加载定时任务
# 2. 支持动态添加/修改/删除任务，立即生效
# 3. 任务配置存储在celery_periodic_task_configs表中