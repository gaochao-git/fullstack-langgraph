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
timezone = 'Asia/Shanghai'
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