# Broker 设置 - 使用 Redis 作为消息代理
# 使用新的配置名称 broker_url 替代 BROKER_URL
broker_url = 'redis://82.156.146.51:6379/0'

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

# 添加自定义调度器配置
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
}

# ========== 队列配置 ==========
# 三个队列，优先级从高到低：system > priority_high > priority_low
# Worker处理顺序: -Q system,priority_high,priority_low,celery

# 固定路由规则：只有系统任务使用固定路由
task_routes = {
    # 系统维护任务 → system队列
    'celery_app.tasks.*': {'queue': 'system'},
    'celery_app.dynamic_scheduler.*': {'queue': 'system'},
    'celery_app.agent_tasks.periodic_agent_health_check': {'queue': 'system'},
}

# 默认队列：智能体任务的兜底队列
task_default_queue = 'priority_low'
task_default_exchange = 'default'
task_default_exchange_type = 'direct'
task_default_routing_key = 'default'

# ========== 智能体任务路由逻辑 ==========
# 1. 调度器读取 task_extra_config 中的 "queue" 字段
# 2. 有效值: "priority_high", "priority_low"  
# 3. 无效值或未配置: 使用默认 "priority_low"
# 4. 示例配置:
#    {"task_type":"agent", "queue":"priority_high", ...}  → priority_high队列
#    {"task_type":"agent", ...}                          → priority_low队列 