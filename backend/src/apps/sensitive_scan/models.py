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


class NotifyStatus(str, enum.Enum):
    """通知状态枚举"""
    PENDING = "pending"      # 待通知
    SENT = "sent"           # 已发送
    FAILED = "failed"       # 发送失败


class ScanTask(Base):
    """扫描任务表"""
    __tablename__ = "scan_tasks"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    task_id = Column(String(64), nullable=False, unique=True, comment="任务ID")
    
    # 任务基本信息 - 匹配实际表结构
    task_status = Column(String(64), default='pending', nullable=False, comment="任务状态,pending,processing,completed,failed")
    task_errors = Column(Text, comment="错误信息")

    # 通知状态
    notify_status = Column(String(20), default='pending', nullable=False, comment="通知状态：pending-待通知，sent-已发送，failed-发送失败")

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
        Index('uk_task_id', 'task_id', unique=True),
        Index('idx_status', 'task_status'),
        Index('idx_notify_status', 'notify_status'),
        Index('idx_create_time', 'create_time'),
        Index('idx_create_by', 'create_by'),
    )


class ScanFile(Base):
    """扫描文件表"""
    __tablename__ = "scan_files"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    task_id = Column(String(64), nullable=False, comment="任务ID")
    file_id = Column(String(64), nullable=False, comment="文件ID")
    
    # 文件状态 - 匹配实际表结构
    file_status = Column(String(64), default='pending', nullable=False, comment="任务状态,pending,processing,completed,failed")
    
    # 扫描结果路径
    jsonl_path = Column(String(500), comment="JSONL结果文件路径")
    html_path = Column(String(500), comment="HTML可视化文件路径")
    
    # 错误信息
    file_error = Column(Text, comment="错误信息")
    
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
        Index('idx_task_id', 'task_id'),
        Index('idx_file_id', 'file_id'),
    )


class ScanConfig(Base):
    """扫描配置表"""
    __tablename__ = "scan_configs"

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    config_id = Column(String(64), nullable=False, unique=True, comment="配置ID")

    # 配置基本信息
    config_name = Column(String(200), nullable=False, comment="配置名称")
    config_description = Column(Text, comment="配置描述")

    # 扫描提示词配置
    prompt_description = Column(Text, nullable=False, comment="扫描提示词，用于指导LLM识别敏感信息")

    # Few-shot示例配置（JSON格式）
    examples_config = Column(Text, comment="Few-shot示例配置，JSON格式存储")

    # 是否为默认配置
    is_default = Column(Integer, default=0, comment="是否为默认配置，1-是，0-否")

    # 状态
    status = Column(String(20), default='active', comment="配置状态：active-启用，inactive-禁用")

    # 审计字段
    create_by = Column(String(100), nullable=False, comment="创建人用户名")
    update_by = Column(String(100), comment="最后更新人用户名")
    create_time = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 创建索引
    __table_args__ = (
        Index('uk_config_id', 'config_id', unique=True),
        Index('idx_config_name', 'config_name'),
        Index('idx_create_by', 'create_by'),
        Index('idx_status', 'status'),
    )