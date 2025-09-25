"""
IDC运行报告管理API（供前端 IDCReportManagement 使用）
当前为Mock实现：内存列表 + 简单过滤/分页
"""

from typing import List, Dict, Any
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.shared.schemas.response import success_response, paginated_response, UnifiedResponse, ResponseCode
from src.shared.core.exceptions import BusinessException
from src.apps.auth.dependencies import get_current_user

router = APIRouter()


# ---------------------------
# 内存 Mock 数据
# ---------------------------
NOW = datetime.now()

def _mock_report_item(
    name: str,
    location: str,
    rtype: str,
    status: str,
    start: datetime,
    end: datetime,
    with_file: bool = True,
) -> Dict[str, Any]:
    rid = str(uuid4())
    return {
        "report_id": rid,
        "report_name": name,
        "idc_location": location,
        "report_type": rtype,  # monthly/quarterly/yearly/custom
        "status": status,       # pending/generating/completed/failed
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_servers": 120,
        "avg_cpu_usage": 62.5,
        "avg_memory_usage": 70.3,
        "total_power_consumption": 9800.4,
        "pue_value": 1.42,
        "availability_rate": 99.95,
        "incident_count": 3,
        "generated_by": "system",
        "generation_time": (end + timedelta(hours=1)).isoformat() if status == "completed" else None,
        "file_name": f"{name}.pdf" if with_file and status == "completed" else None,
        "file_size": 2560000 if with_file and status == "completed" else None,
        "created_at": start.isoformat(),
        "updated_at": end.isoformat(),
        "created_by": "system",
        "updated_by": "system",
    }


MOCK_REPORTS: List[Dict[str, Any]] = [
    _mock_report_item(
        name="2024年12月机房A运行报告",
        location="北京机房A",
        rtype="monthly",
        status="completed",
        start=NOW.replace(month=12, day=1, hour=0, minute=0, second=0, microsecond=0),
        end=NOW.replace(month=12, day=1, hour=8, minute=0, second=0, microsecond=0),
    ),
    _mock_report_item(
        name="2024年12月机房B运行报告",
        location="上海机房B",
        rtype="monthly",
        status="generating",
        start=NOW.replace(month=12, day=1, hour=0, minute=0, second=0, microsecond=0),
        end=NOW.replace(month=12, day=1, hour=8, minute=30, second=0, microsecond=0),
        with_file=False,
    ),
    _mock_report_item(
        name="2024年第4季度综合报告",
        location="全部机房",
        rtype="quarterly",
        status="completed",
        start=NOW.replace(month=10, day=1, hour=0, minute=0, second=0, microsecond=0),
        end=NOW.replace(month=12, day=15, hour=10, minute=0, second=0, microsecond=0),
    ),
]


def _apply_filters(items: List[Dict[str, Any]], keyword: str, idc_location: str, report_type: str, status: str) -> List[Dict[str, Any]]:
    results = items
    if keyword:
        results = [i for i in results if keyword in i["report_name"] or keyword in (i["idc_location"] or "")]
    if idc_location:
        results = [i for i in results if i["idc_location"] == idc_location]
    if report_type:
        results = [i for i in results if i["report_type"] == report_type]
    if status:
        results = [i for i in results if i["status"] == status]
    return results


@router.get("/", response_model=UnifiedResponse)
async def get_reports(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    keyword: str = Query(None, description="关键词搜索"),
    idc_location: str = Query(None, description="IDC位置筛选"),
    report_type: str = Query(None, description="报告类型筛选"),
    status: str = Query(None, description="状态筛选"),
    start_date: str = Query(None, description="开始时间筛选"),
    end_date: str = Query(None, description="结束时间筛选"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取IDC报告列表（Mock）"""
    filtered = _apply_filters(MOCK_REPORTS, keyword, idc_location, report_type, status)

    # 时间范围过滤（若传入）
    def _parse_iso(dt: str) -> datetime:
        return datetime.fromisoformat(dt.replace('Z', '+00:00'))

    if start_date:
        sd = _parse_iso(start_date)
        filtered = [i for i in filtered if datetime.fromisoformat(i["start_date"]) >= sd]
    if end_date:
        ed = _parse_iso(end_date)
        filtered = [i for i in filtered if datetime.fromisoformat(i["end_date"]) <= ed]

    total = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = filtered[start_idx:end_idx]

    return paginated_response(
        items=page_items,
        total=total,
        page=page,
        size=page_size,
        msg="查询IDC报告列表成功"
    )


@router.get("/{report_id}", response_model=UnifiedResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    report = next((r for r in MOCK_REPORTS if str(r["report_id"]) == str(report_id)), None)
    if not report:
        raise BusinessException("报告不存在", ResponseCode.NOT_FOUND)
    return success_response(report, msg="获取报告详情成功")


@router.post("/", response_model=UnifiedResponse)
async def create_report(
    data: Dict[str, Any],  # 兼容前端字段：reportName/idcLocation/reportType/dateRange
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    # 映射前端字段
    try:
        name = data.get("reportName") or data.get("report_name") or "未命名报告"
        location = data.get("idcLocation") or data.get("idc_location") or "全部机房"
        rtype = data.get("reportType") or data.get("report_type") or "custom"
        dr = data.get("dateRange")
        if dr and isinstance(dr, list) and len(dr) == 2:
            start = datetime.fromisoformat(str(dr[0]).replace('Z', '+00:00'))
            end = datetime.fromisoformat(str(dr[1]).replace('Z', '+00:00'))
        else:
            start = NOW - timedelta(days=30)
            end = NOW
    except Exception:
        start = NOW - timedelta(days=30)
        end = NOW

    new_item = _mock_report_item(
        name=name,
        location=location,
        rtype=rtype,
        status="pending",
        start=start,
        end=end,
        with_file=False,
    )
    MOCK_REPORTS.insert(0, new_item)

    resp = {
        "report_id": new_item["report_id"],
        "message": "报告生成任务已创建，正在后台生成中",
        "status": "pending",
        "estimated_time": 30,
    }
    return success_response(resp, msg="创建报告任务成功", code=ResponseCode.CREATED)


@router.delete("/{report_id}", response_model=UnifiedResponse)
async def delete_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    idx = next((i for i, r in enumerate(MOCK_REPORTS) if str(r["report_id"]) == str(report_id)), -1)
    if idx >= 0:
        MOCK_REPORTS.pop(idx)
        return success_response({"message": "报告删除成功"})
    raise BusinessException("报告不存在", ResponseCode.NOT_FOUND)


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    report = next((r for r in MOCK_REPORTS if str(r["report_id"]) == str(report_id)), None)
    if not report:
        raise BusinessException("报告不存在", ResponseCode.NOT_FOUND)

    # 生成一个临时文本文件模拟下载
    import os, tempfile
    tmp_dir = tempfile.gettempdir()
    filename = report.get("file_name") or f"report_{report_id}.txt"
    path = os.path.join(tmp_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Mock 报告文件: {report.get('report_name')}\n")
        f.write("该文件仅用于前端联调测试。\n")
    from fastapi.responses import FileResponse
    return FileResponse(path=path, filename=filename, media_type='application/octet-stream')


@router.get("/locations", response_model=UnifiedResponse)
async def get_idc_locations(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    locations = [
        {"location_id": str(uuid4()), "location_name": "北京机房A", "location_code": "BJ-A"},
        {"location_id": str(uuid4()), "location_name": "上海机房B", "location_code": "SH-B"},
        {"location_id": str(uuid4()), "location_name": "广州机房C", "location_code": "GZ-C"},
        {"location_id": str(uuid4()), "location_name": "全部机房", "location_code": "ALL"},
    ]
    return success_response(locations, msg="获取IDC位置列表成功")


@router.get("/stats", response_model=UnifiedResponse)
async def report_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    total = len(MOCK_REPORTS)
    pending = len([r for r in MOCK_REPORTS if r["status"] == "pending"])
    generating = len([r for r in MOCK_REPORTS if r["status"] == "generating"])
    completed = len([r for r in MOCK_REPORTS if r["status"] == "completed"])
    failed = len([r for r in MOCK_REPORTS if r["status"] == "failed"])
    month_start = NOW.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = len([r for r in MOCK_REPORTS if datetime.fromisoformat(r["created_at"]) >= month_start])
    stats = {
        "total_reports": total,
        "pending_reports": pending,
        "generating_reports": generating,
        "completed_reports": completed,
        "failed_reports": failed,
        "this_month_reports": this_month,
        "total_locations": 4,
        "recent_reports": sorted(MOCK_REPORTS, key=lambda x: x["created_at"], reverse=True)[:5],
    }
    return success_response(stats, msg="获取统计信息成功")

