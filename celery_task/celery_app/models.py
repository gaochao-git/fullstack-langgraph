from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone
import pymysql
from celery_app.config import DATABASE_CONFIG

# 注册 PyMySQL 作为 MySQLdb
pymysql.install_as_MySQLdb()

# 创建数据库连接，配置连接池和重连机制
DB_URL = f"mysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
engine = create_engine(
    DB_URL, 
    echo=False,
    # 连接池配置
    pool_size=10,                    # 连接池大小
    max_overflow=20,                 # 超出连接池大小的最大连接数
    pool_pre_ping=True,             # 连接前ping测试，自动重连
    pool_recycle=3600,              # 连接回收时间(1小时)
    # 连接超时配置
    connect_args={
        "connect_timeout": 10,       # 连接超时10秒
        "read_timeout": 30,          # 读取超时30秒
        "write_timeout": 30,         # 写入超时30秒
        "charset": "utf8mb4"
    }
)
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
    task_extra_config = Column(Text, nullable=True)  # 任务额外配置JSON字符串（包含task_type、agent_id、task_timeout等）
    
    def __repr__(self):
        return f"<PeriodicTask {self.task_name}>"

# 创建数据库表
def init_db():
    Base.metadata.create_all(engine)

# 获取数据库会话（带重连机制）
def get_session():
    """获取数据库会话,自动处理连接断开"""
    from sqlalchemy import text
    
    session = Session()
    
    # 测试连接是否有效
    try:
        # 执行简单查询测试连接
        session.execute(text("SELECT 1"))
        return session
    except Exception as e:
        # 连接失败时关闭session并重新创建
        session.close()
        # 创建新的session
        return Session() 