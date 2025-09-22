"""
IDC运维报告业务逻辑服务
"""

import os
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.db.models import now_shanghai

from ..models import IDCReport, IDCLocation, ReportStatus, ReportType
from ..schema import (
    IDCReportCreate,
    IDCReportUpdate,
    IDCReportListParams,
    IDCReportStats,
    IDCLocationResponse
)

logger = get_logger(__name__)


class IDCReportService:
    """IDC报告服务类"""

    @staticmethod
    async def create_report(db: AsyncSession, data: IDCReportCreate, created_by: str) -> IDCReport:
        """创建IDC报告生成任务"""
        try:
            async with db.begin():
                # 检查IDC位置是否有效
                location_exists = await IDCReportService._check_location_exists(db, data.idc_location)
                if not location_exists:
                    raise BusinessException(ResponseCode.BUSINESS_ERROR, f"IDC位置 '{data.idc_location}' 不存在")

                # 创建报告记录
                report = IDCReport(
                    report_name=data.report_name,
                    idc_location=data.idc_location,
                    report_type=data.report_type,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    status=ReportStatus.PENDING,
                    created_by=created_by,
                    created_at=now_shanghai()
                )

                db.add(report)
                await db.flush()
                await db.refresh(report)

                logger.info(f"Created IDC report: {report.report_id} by {created_by}")
                return report

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Failed to create IDC report: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "创建报告失败")

    @staticmethod
    async def get_report_list(db: AsyncSession, params: IDCReportListParams) -> Tuple[List[IDCReport], int]:
        """获取报告列表"""
        try:
            # 构建查询条件
            conditions = []

            if params.keyword:
                conditions.append(
                    or_(
                        IDCReport.report_name.contains(params.keyword),
                        IDCReport.idc_location.contains(params.keyword)
                    )
                )

            if params.idc_location:
                conditions.append(IDCReport.idc_location == params.idc_location)

            if params.report_type:
                conditions.append(IDCReport.report_type == params.report_type)

            if params.status:
                conditions.append(IDCReport.status == params.status)

            if params.start_date:
                conditions.append(IDCReport.start_date >= params.start_date)

            if params.end_date:
                conditions.append(IDCReport.end_date <= params.end_date)

            # 构建基础查询
            query = select(IDCReport)
            if conditions:
                query = query.where(and_(*conditions))

            # 获取总数
            count_query = select(func.count(IDCReport.report_id))
            if conditions:
                count_query = count_query.where(and_(*conditions))

            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # 分页查询
            query = query.order_by(IDCReport.created_at.desc())
            query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)

            result = await db.execute(query)
            reports = result.scalars().all()

            return list(reports), total

        except Exception as e:
            logger.error(f"Failed to get report list: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "获取报告列表失败")

    @staticmethod
    async def get_report_by_id(db: AsyncSession, report_id: UUID) -> Optional[IDCReport]:
        """根据ID获取报告详情"""
        try:
            result = await db.execute(
                select(IDCReport).where(IDCReport.report_id == report_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "获取报告详情失败")

    @staticmethod
    async def update_report(db: AsyncSession, report_id: UUID, data: IDCReportUpdate, updated_by: str) -> IDCReport:
        """更新报告信息"""
        try:
            async with db.begin():
                report = await IDCReportService.get_report_by_id(db, report_id)
                if not report:
                    raise BusinessException(ResponseCode.NOT_FOUND, "报告不存在")

                # 更新字段
                update_data = data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(report, field):
                        setattr(report, field, value)

                report.updated_by = updated_by
                report.updated_at = now_shanghai()

                if data.status == ReportStatus.COMPLETED:
                    report.generation_time = now_shanghai()

                await db.flush()
                await db.refresh(report)

                logger.info(f"Updated IDC report: {report_id} by {updated_by}")
                return report

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "更新报告失败")

    @staticmethod
    async def delete_report(db: AsyncSession, report_id: UUID, deleted_by: str) -> bool:
        """删除报告"""
        try:
            async with db.begin():
                report = await IDCReportService.get_report_by_id(db, report_id)
                if not report:
                    raise BusinessException(ResponseCode.NOT_FOUND, "报告不存在")

                # 删除关联文件
                if report.file_path and os.path.exists(report.file_path):
                    try:
                        os.remove(report.file_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete report file {report.file_path}: {str(e)}")

                await db.delete(report)
                await db.flush()

                logger.info(f"Deleted IDC report: {report_id} by {deleted_by}")
                return True

        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete report {report_id}: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "删除报告失败")

    @staticmethod
    async def get_idc_locations(db: AsyncSession) -> List[IDCLocation]:
        """获取IDC位置列表"""
        try:
            result = await db.execute(
                select(IDCLocation)
                .where(IDCLocation.is_active == 1)
                .order_by(IDCLocation.location_name)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get IDC locations: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "获取IDC位置列表失败")

    @staticmethod
    async def get_report_stats(db: AsyncSession) -> IDCReportStats:
        """获取报告统计信息"""
        try:
            # 获取各状态报告数量
            status_counts = {}
            for status in ReportStatus:
                result = await db.execute(
                    select(func.count(IDCReport.report_id))
                    .where(IDCReport.status == status)
                )
                status_counts[status.value] = result.scalar()

            # 获取总报告数
            total_result = await db.execute(select(func.count(IDCReport.report_id)))
            total_reports = total_result.scalar()

            # 获取本月报告数
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            this_month_result = await db.execute(
                select(func.count(IDCReport.report_id))
                .where(IDCReport.created_at >= current_month_start)
            )
            this_month_reports = this_month_result.scalar()

            # 获取IDC位置总数
            locations_result = await db.execute(
                select(func.count(IDCLocation.location_id))
                .where(IDCLocation.is_active == 1)
            )
            total_locations = locations_result.scalar()

            # 获取最近5个报告
            recent_result = await db.execute(
                select(IDCReport)
                .order_by(IDCReport.created_at.desc())
                .limit(5)
            )
            recent_reports = recent_result.scalars().all()

            return IDCReportStats(
                total_reports=total_reports,
                pending_reports=status_counts.get('pending', 0),
                generating_reports=status_counts.get('generating', 0),
                completed_reports=status_counts.get('completed', 0),
                failed_reports=status_counts.get('failed', 0),
                this_month_reports=this_month_reports,
                total_locations=total_locations,
                recent_reports=recent_reports
            )

        except Exception as e:
            logger.error(f"Failed to get report stats: {str(e)}")
            raise BusinessException(ResponseCode.INTERNAL_ERROR, "获取统计信息失败")

    @staticmethod
    async def _check_location_exists(db: AsyncSession, location_name: str) -> bool:
        """检查IDC位置是否存在"""
        result = await db.execute(
            select(IDCLocation.location_id)
            .where(and_(
                IDCLocation.location_name == location_name,
                IDCLocation.is_active == 1
            ))
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def generate_mock_report_data(report: IDCReport) -> Dict[str, Any]:
        """生成模拟报告数据 (实际项目中应该连接真实的监控数据源)"""
        return {
            "summary": {
                "report_period": f"{report.start_date.strftime('%Y-%m-%d')} 至 {report.end_date.strftime('%Y-%m-%d')}",
                "idc_location": report.idc_location,
                "total_servers": 150,
                "avg_cpu_usage": 65.2,
                "avg_memory_usage": 72.8,
                "total_power_consumption": 12500.5,
                "pue_value": 1.42,
                "availability_rate": 99.95,
                "incident_count": 2
            },
            "details": {
                "server_stats": {
                    "web_servers": 60,
                    "database_servers": 40,
                    "cache_servers": 30,
                    "other_servers": 20
                },
                "incidents": [
                    {
                        "date": "2024-01-15",
                        "type": "网络故障",
                        "duration": "30分钟",
                        "impact": "轻微"
                    }
                ]
            }
        }