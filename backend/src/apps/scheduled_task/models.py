"""Periodic Task model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai


class PeriodicTask(Base):
    """定时任务模型 - 统一数据库架构"""
    __tablename__ = "celery_periodic_task_configs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(255), unique=True, nullable=False, index=True)
    task_path = Column(String(255), nullable=False)
    task_interval = Column(Integer, nullable=True)
    task_crontab_minute = Column(String(64), nullable=True)
    task_crontab_hour = Column(String(64), nullable=True)
    task_crontab_day_of_week = Column(String(64), nullable=True)
    task_crontab_day_of_month = Column(String(64), nullable=True)
    task_crontab_month_of_year = Column(String(64), nullable=True)
    task_args = Column(Text, nullable=True)
    task_kwargs = Column(Text, nullable=True)
    task_enabled = Column(Boolean, default=True, nullable=False)
    task_last_run_time = Column(DateTime, nullable=True)
    task_run_count = Column(Integer, default=0, nullable=False)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(100), nullable=True)
    update_by = Column(String(100), nullable=True)
    task_description = Column(Text, nullable=True)
    task_extra_config = Column(Text, nullable=True)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_path': self.task_path,
            'task_description': self.task_description,
            'task_args': self.task_args or '[]',
            'task_kwargs': self.task_kwargs or '{}',
            'task_enabled': self.task_enabled,
            'task_interval': self.task_interval,
            'task_crontab_minute': self.task_crontab_minute,
            'task_crontab_hour': self.task_crontab_hour,
            'task_crontab_day_of_week': self.task_crontab_day_of_week,
            'task_crontab_day_of_month': self.task_crontab_day_of_month,
            'task_crontab_month_of_year': self.task_crontab_month_of_year,
            'task_last_run_time': self.task_last_run_time.strftime('%Y-%m-%d %H:%M:%S') if self.task_last_run_time else None,
            'task_run_count': self.task_run_count,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'task_extra_config': self.task_extra_config,
            'task_status': 'active' if self.task_enabled else 'inactive'
        }


"""Task Result model."""
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai


class TaskResult(Base):
    """任务执行结果模型 - 统一数据库架构"""
    __tablename__ = "celery_periodic_task_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_name = Column(String(255), nullable=False, index=True)
    task_schedule_time = Column(DateTime, nullable=False)
    task_execute_time = Column(DateTime, default=now_shanghai)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(100), nullable=True)
    update_by = Column(String(100), nullable=True)
    task_status = Column(String(50), default='SUCCESS', nullable=False, index=True)
    task_result = Column(Text, nullable=True)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_name': self.task_name,
            'task_status': self.task_status,
            'task_result': self.task_result,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'task_schedule_time': self.task_schedule_time.strftime('%Y-%m-%d %H:%M:%S') if self.task_schedule_time else None,
            'task_execute_time': self.task_execute_time.strftime('%Y-%m-%d %H:%M:%S') if self.task_execute_time else None,
            'create_by': self.create_by,
            'update_by': self.update_by
        }


"""Celery Task Record model."""
from sqlalchemy import Column, Integer, String, Text, DateTime
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai


class CeleryTaskRecord(Base):
    """Celery任务执行记录模型"""
    __tablename__ = "celery_task_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_name = Column(String(255), nullable=False, index=True)
    task_status = Column(String(50), default='PENDING', nullable=False, index=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)
    create_by = Column(String(100), nullable=True)
    update_by = Column(String(100), nullable=True)
    task_start_time = Column(DateTime, nullable=True)
    task_complete_time = Column(DateTime, nullable=True)
    task_result = Column(Text, nullable=True)
    task_traceback = Column(Text, nullable=True)
    task_retry_count = Column(Integer, default=0, nullable=False)
    task_args = Column(Text, nullable=True)
    task_kwargs = Column(Text, nullable=True)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_name': self.task_name,
            'task_status': self.task_status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'task_start_time': self.task_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.task_start_time else None,
            'task_complete_time': self.task_complete_time.strftime('%Y-%m-%d %H:%M:%S') if self.task_complete_time else None,
            'task_result': self.task_result,
            'task_traceback': self.task_traceback,
            'task_retry_count': self.task_retry_count,
            'task_args': self.task_args,
            'task_kwargs': self.task_kwargs,
            'create_by': self.create_by,
            'update_by': self.update_by
        }