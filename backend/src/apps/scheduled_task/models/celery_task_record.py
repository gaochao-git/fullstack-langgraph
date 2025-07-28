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