"""
Celery相关的数据库模型
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from src.shared.db.models import BaseModel, now_shanghai


class CeleryTaskRecord(BaseModel):
    """Celery任务执行记录"""
    __tablename__ = 'celery_task_records'
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    task_status = Column(String(50), default='PENDING')
    task_start_time = Column(DateTime, nullable=True)
    task_complete_time = Column(DateTime, nullable=True)
    task_result = Column(Text, nullable=True)
    task_traceback = Column(Text, nullable=True)
    task_retry_count = Column(Integer, default=0)
    task_args = Column(Text, nullable=True)
    task_kwargs = Column(Text, nullable=True)
    task_queue = Column(String(100), nullable=True)
    task_extra_info = Column(Text, nullable=True)


class CeleryPeriodicTaskConfig(BaseModel):
    """Celery定时任务配置"""
    __tablename__ = 'celery_periodic_task_configs'
    __table_args__ = {'extend_existing': True}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    task_name = Column(String(255), nullable=False, unique=True, index=True)
    task_path = Column(String(255), nullable=False)
    task_enabled = Column(Boolean, default=True)
    task_description = Column(Text, nullable=True)
    
    # 定时配置：支持interval和crontab两种方式
    task_interval = Column(Integer, nullable=True)  # 间隔秒数
    task_crontab_minute = Column(String(10), nullable=True, default='*')
    task_crontab_hour = Column(String(10), nullable=True, default='*')
    task_crontab_day_of_week = Column(String(10), nullable=True, default='*')
    task_crontab_day_of_month = Column(String(10), nullable=True, default='*')
    task_crontab_month_of_year = Column(String(10), nullable=True, default='*')
    
    # 任务参数
    task_args = Column(Text, nullable=True)  # JSON格式的参数列表
    task_kwargs = Column(Text, nullable=True)  # JSON格式的关键字参数
    
    # 执行信息
    task_last_run_time = Column(DateTime, nullable=True)
    task_run_count = Column(Integer, default=0)
    
    # 额外配置（JSON格式）
    task_extra_config = Column(Text, nullable=True)
    
    # 关联运行记录（已禁用）
    # runs = relationship("CeleryPeriodicTaskRun", back_populates="task", cascade="all, delete-orphan")


# class CeleryPeriodicTaskRun(BaseModel):
#     """定时任务执行记录（已禁用，改为通过日志记录）"""
#     __tablename__ = 'celery_periodic_task_runs'
#     __table_args__ = {'extend_existing': True}
#     
#     id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
#     task_config_id = Column(Integer, ForeignKey('celery_periodic_task_configs.id'), nullable=False)
#     run_time = Column(DateTime, nullable=False, default=now_shanghai)
#     status = Column(String(50), nullable=False)  # SUCCESS, FAILURE, RETRY
#     result = Column(Text, nullable=True)
#     error = Column(Text, nullable=True)
#     traceback = Column(Text, nullable=True)
#     execution_time = Column(Integer, nullable=True)  # 执行时长（秒）
#     
#     # 关联任务配置
#     # task = relationship("CeleryPeriodicTaskConfig", back_populates="runs")