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