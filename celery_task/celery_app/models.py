from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pymysql
from celery_app.config import DATABASE_CONFIG

# 注册 PyMySQL 作为 MySQLdb
pymysql.install_as_MySQLdb()

# 创建数据库连接
DB_URL = f"mysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Task(Base):
    """任务模型"""
    __tablename__ = 'celery_task_records'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    task_name = Column(String(255), nullable=False)
    task_status = Column(String(50), default='PENDING')
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    create_by = Column(String(100), nullable=True)
    update_by = Column(String(100), nullable=True)
    task_start_time = Column(DateTime, nullable=True)
    task_complete_time = Column(DateTime, nullable=True)
    task_result = Column(Text, nullable=True)
    task_traceback = Column(Text, nullable=True)
    task_retry_count = Column(Integer, default=0)
    task_args = Column(Text, nullable=True)
    task_kwargs = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Task {self.task_id} ({self.task_status})>"

class PeriodicTaskRun(Base):
    """定时任务执行记录"""
    __tablename__ = 'celery_periodic_task_execution_logs'
    
    id = Column(Integer, primary_key=True)
    task_name = Column(String(255), nullable=False)
    task_schedule_time = Column(DateTime, nullable=False)
    task_execute_time = Column(DateTime, default=datetime.now)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    create_by = Column(String(100), nullable=True)
    update_by = Column(String(100), nullable=True)
    task_status = Column(String(50), default='SUCCESS')
    task_result = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PeriodicTaskRun {self.task_name} at {self.task_execute_time}>"

class PeriodicTask(Base):
    """定时任务配置模型"""
    __tablename__ = 'celery_periodic_task_configs'
    
    id = Column(Integer, primary_key=True)
    task_name = Column(String(255), unique=True, nullable=False)
    task_path = Column(String(255), nullable=False)  # 任务路径
    task_interval = Column(Integer, nullable=True)  # 间隔秒数
    task_crontab_minute = Column(String(64), nullable=True)
    task_crontab_hour = Column(String(64), nullable=True)
    task_crontab_day_of_week = Column(String(64), nullable=True)
    task_crontab_day_of_month = Column(String(64), nullable=True)
    task_crontab_month_of_year = Column(String(64), nullable=True)
    task_args = Column(Text, nullable=True)  # JSON 格式的参数
    task_kwargs = Column(Text, nullable=True)  # JSON 格式的关键字参数
    task_enabled = Column(Boolean, default=True)
    task_last_run_time = Column(DateTime, nullable=True)
    task_run_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    create_by = Column(String(100), nullable=True)
    update_by = Column(String(100), nullable=True)
    task_description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<PeriodicTask {self.task_name}>"

# 创建数据库表
def init_db():
    Base.metadata.create_all(engine)

# 获取数据库会话
def get_session():
    return Session() 