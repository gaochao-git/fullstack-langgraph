from celery import Celery

# 创建 Celery 实例
app = Celery('celery_app')

# 加载配置
app.config_from_object('celery_app.config')

# 自动发现任务
app.autodiscover_tasks(['celery_app'])

if __name__ == '__main__':
    app.start() 