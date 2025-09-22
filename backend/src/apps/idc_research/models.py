"""
IDC运维报告模块数据模型
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from src.shared.db.base_model import BaseModel


class ReportStatus(str, enum.Enum):
    """报告状态枚举"""
    PENDING = "pending"      # 待生成
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 生成失败


class ReportType(str, enum.Enum):
    """报告类型枚举"""
    MONTHLY = "monthly"      # 月度报告
    QUARTERLY = "quarterly"  # 季度报告
    YEARLY = "yearly"        # 年度报告
    CUSTOM = "custom"        # 自定义时间段


class IDCReport(BaseModel):
    """IDC运维报告模型"""
    __tablename__ = "idc_reports"

    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_name = Column(String(200), nullable=False, comment="报告名称")
    idc_location = Column(String(100), nullable=False, comment="IDC位置/名称")
    report_type = Column(Enum(ReportType), nullable=False, comment="报告类型")
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, comment="报告状态")

    # 时间范围
    start_date = Column(DateTime, nullable=False, comment="报告开始时间")
    end_date = Column(DateTime, nullable=False, comment="报告结束时间")

    # 报告内容和文件
    content = Column(Text, comment="报告内容(JSON格式)")
    file_path = Column(String(500), comment="报告文件路径")
    file_name = Column(String(200), comment="报告文件名")
    file_size = Column(Integer, comment="文件大小(字节)")

    # 统计数据摘要
    total_servers = Column(Integer, comment="服务器总数")
    avg_cpu_usage = Column(Float, comment="平均CPU使用率")
    avg_memory_usage = Column(Float, comment="平均内存使用率")
    total_power_consumption = Column(Float, comment="总耗电量(kWh)")
    pue_value = Column(Float, comment="PUE值")
    availability_rate = Column(Float, comment="可用性率")
    incident_count = Column(Integer, comment="事故数量")

    # 生成信息
    generated_by = Column(String(100), comment="生成人员")
    generation_time = Column(DateTime, comment="生成完成时间")
    error_message = Column(Text, comment="错误信息(如果生成失败)")

    # 继承的字段: created_at, updated_at, created_by, updated_by

    def __repr__(self):
        return f"<IDCReport(report_id='{self.report_id}', name='{self.report_name}', location='{self.idc_location}')>"


class IDCLocation(BaseModel):
    """IDC位置信息模型"""
    __tablename__ = "idc_locations"

    location_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_name = Column(String(100), nullable=False, unique=True, comment="位置名称")
    location_code = Column(String(20), nullable=False, unique=True, comment="位置代码")
    description = Column(String(500), comment="位置描述")
    address = Column(String(500), comment="详细地址")
    is_active = Column(Integer, default=1, comment="是否活跃")

    def __repr__(self):
        return f"<IDCLocation(location_id='{self.location_id}', name='{self.location_name}')>"