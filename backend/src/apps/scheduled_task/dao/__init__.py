"""
Scheduled Task DAO
"""

# TODO: 定时任务使用的是 celery_app 自己的数据库模型
# 暂不需要单独的DAO，直接使用 celery_app.models

__all__ = []