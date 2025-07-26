import json
from datetime import datetime, timedelta
from celery.beat import Scheduler, ScheduleEntry
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
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            session = get_session()
            try:
                db_tasks = session.query(PeriodicTask).filter_by(task_enabled=True).all()
                
                self._schedule = {}
                
                print(f"数据库调度器: 加载了 {len(db_tasks)} 个启用的任务")
                
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
                    
                    # 官方方案：让Celery自己处理时区转换
                    last_run_at = task.task_last_run_time
                    
                    # 创建ScheduleEntry对象
                    entry = ScheduleEntry(
                        name=task.task_name,
                        task=task.task_path,
                        schedule=schedule_obj,
                        args=args,
                        kwargs=kwargs,
                        options={'expires': 60.0},
                        last_run_at=last_run_at,
                        total_run_count=task.task_run_count
                    )
                    
                    print(f"📋 加载任务: {task.task_name}")
                    print(f"   上次运行: {task.task_last_run_time}")
                    print(f"   运行次数: {task.task_run_count}")
                    print(f"   间隔: {task.task_interval}秒")
                    print(f"   当前时间(UTC): {datetime.now()}")
                    
                    # 添加到调度中
                    self._schedule[task.task_name] = entry
                
                self._last_timestamp = datetime.now()
                break  # 成功则退出重试循环
                
            except Exception as e:
                retry_count += 1
                print(f"更新定时任务时出错 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    print(f"更新定时任务最终失败，使用空调度: {e}")
                    self._schedule = {}
                    self._last_timestamp = datetime.now()
            finally:
                session.close()
    
    @property
    def schedule(self):
        """返回当前的调度配置"""
        return self._schedule
    
    def tick(self, *args, **kwargs):
        # 每30秒检查一次数据库更新
        if datetime.now() - self._last_timestamp > timedelta(seconds=30):
            print("🔄 更新数据库任务配置...")
            self.update_from_database()
        
        # 调试：显示tick调用频率
        if not hasattr(self, '_last_tick_time'):
            self._last_tick_time = datetime.now()
        else:
            tick_interval = datetime.now() - self._last_tick_time
            print(f"🔄 Beat tick间隔: {tick_interval.total_seconds():.1f}s")
            self._last_tick_time = datetime.now()
        
        # 显示当前任务状态  
        current_utc = datetime.now()
        print(f"⏰ Beat tick - 当前时间(UTC): {current_utc}")
        for task_name, entry in self._schedule.items():
            is_due, next_delay = entry.is_due()
            print(f"   📝 {task_name}: due={is_due}, next_in={next_delay:.1f}s")
            # 调试：显示任务的详细时间信息
            if hasattr(entry, 'last_run_at') and entry.last_run_at:
                print(f"       last_run_at: {entry.last_run_at}")
            else:
                print(f"       last_run_at: None (首次运行)")
            
        return super(DatabaseScheduler, self).tick(*args, **kwargs) 