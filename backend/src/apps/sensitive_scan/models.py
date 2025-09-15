"""敏感数据扫描任务数据库模型"""

from sqlalchemy import Column, String, Text, Integer, DateTime, BigInteger, Index, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import enum

from src.shared.db.config import Base


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileStatus(str, enum.Enum):
    """文件扫描状态枚举"""
    PENDING = "pending"
    READING = "reading"
    READ_COMPLETE = "read_complete"
    SCANNING = "scanning"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanTask(Base):
    """扫描任务表"""
    __tablename__ = "scan_tasks"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    task_id = Column(String(64), nullable=False, unique=True, comment="任务ID")
    
    # 任务基本信息
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, comment="任务状态")
    total_files = Column(Integer, default=0, nullable=False, comment="总文件数")
    processed_files = Column(Integer, default=0, nullable=False, comment="已处理文件数")
    failed_files = Column(Integer, default=0, nullable=False, comment="失败文件数")
    
    # 进度信息（JSON格式存储在TEXT中）
    progress = Column(Text, comment="进度信息（JSON格式）")
    
    # 统计信息（JSON格式存储在TEXT中）
    statistics = Column(Text, comment="统计信息（JSON格式）")
    
    # 摘要信息（JSON格式存储在TEXT中）
    summary = Column(Text, comment="任务摘要（JSON格式）")
    
    # 错误信息（JSON数组格式存储在TEXT中）
    errors = Column(Text, comment="错误信息列表（JSON格式）")
    
    # 时间戳
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    
    # 审计字段
    create_by = Column(String(100), nullable=False, default="system", comment="创建人用户名")
    update_by = Column(String(100), comment="最后更新人用户名")
    create_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 创建索引
    __table_args__ = (
        Index('idx_scan_task_status', 'status'),
        Index('idx_scan_task_create_time', 'create_time'),
        Index('idx_scan_task_create_by', 'create_by'),
    )


class ScanFile(Base):
    """扫描文件表"""
    __tablename__ = "scan_files"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    task_id = Column(String(64), nullable=False, comment="任务ID")
    file_id = Column(String(64), nullable=False, comment="文件ID")
    
    # 文件状态
    status = Column(SQLEnum(FileStatus), default=FileStatus.PENDING, nullable=False, comment="文件状态")
    
    # 扫描结果路径
    jsonl_path = Column(String(500), comment="JSONL结果文件路径")
    html_path = Column(String(500), comment="HTML报告文件路径")
    
    # 错误信息
    error = Column(Text, comment="错误信息")
    
    # 时间戳
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    
    # 审计字段
    create_by = Column(String(100), nullable=False, default="system", comment="创建人用户名")
    update_by = Column(String(100), comment="最后更新人用户名")
    create_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")
    
    # 创建索引
    __table_args__ = (
        Index('uk_task_file', 'task_id', 'file_id', unique=True),
        Index('idx_scan_file_task_id', 'task_id'),
        Index('idx_scan_file_status', 'status'),
        Index('idx_scan_file_create_by', 'create_by'),
    )