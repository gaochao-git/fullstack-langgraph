import json
from datetime import datetime, timedelta
from celery.beat import Scheduler
from celery import current_app
from celery.schedules import crontab, schedule
from celery_app.models import get_session, PeriodicTask

class DatabaseScheduler(Scheduler):
    """从数据库加载定时任务的调度器"""
    
    def __init__(self, *args, **kwargs):
        self._schedule = {}
        self._last_timestamp = datetime.now()
        super(DatabaseScheduler, self).__init__(*args, **kwargs)
    
    def setup_schedule(self):
        self.update_from_database()
    
    def update_from_database(self):
        """从数据库更新定时任务"""
        session = get_session()
        try:
            db_tasks = session.query(PeriodicTask).filter_by(task_enabled=True).all()
            
            self._schedule = {}
            
            for task in db_tasks:
                # 解析参数
                args = json.loads(task.task_args) if task.task_args else []
                kwargs = json.loads(task.task_kwargs) if task.task_kwargs else {}
                
                # 创建调度
                if task.task_interval is not None:
                    # 间隔调度
                    schedule_obj = schedule(timedelta(seconds=task.task_interval))
                else:
                    # Crontab 调度
                    schedule_obj = crontab(
                        minute=task.task_crontab_minute or '*',
                        hour=task.task_crontab_hour or '*',
                        day_of_week=task.task_crontab_day_of_week or '*',
                        day_of_month=task.task_crontab_day_of_month or '*',
                        month_of_year=task.task_crontab_month_of_year or '*'
                    )
                
                # 添加到调度中
                self._schedule[task.task_name] = {
                    'task': task.task_path,
                    'schedule': schedule_obj,
                    'args': args,
                    'kwargs': kwargs,
                    'options': {'expires': 60.0}
                }
            
            self._last_timestamp = datetime.now()
            
        except Exception as e:
            print(f"更新定时任务时出错: {e}")
        finally:
            session.close()
    
    def tick(self, *args, **kwargs):
        # 每分钟检查一次数据库更新
        if datetime.now() - self._last_timestamp > timedelta(minutes=1):
            self.update_from_database()
        return super(DatabaseScheduler, self).tick(*args, **kwargs) 