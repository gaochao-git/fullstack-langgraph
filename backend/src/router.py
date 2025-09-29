"""
API路由聚合模块
统一管理所有API路由
"""

from fastapi import APIRouter

# 导入所有业务模块路由
from .apps.sop import router as sop_router
from .apps.agent import router as agents_router
from .apps.mcp import router as mcp_router
from .apps.ai_model import router as ai_models_router
from .apps.scheduled_task import router as scheduled_tasks_router
from .apps.user import router as rbac_router
from .apps.auth import router as auth_router
from .apps.kb import router as kb_router
from .shared.core.endpoints import router as common_router
from .apps.speech import router as speech_router
from .apps.sensitive_scan import router as scan_router
from .apps.idc_research import reports_router as idc_reports_router
from .apps.idc_research import analysis_router as idc_analysis_router
from .apps.idc_research import docs_router as idc_docs_router

# 创建主API路由器
api_router = APIRouter()

# 注册各个子路由
api_router.include_router(common_router, tags=["common"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(sop_router, tags=["sop"])
api_router.include_router(mcp_router, tags=["mcp"])
api_router.include_router(ai_models_router, tags=["ai-models"])
api_router.include_router(scheduled_tasks_router, tags=["scheduled-tasks"])
api_router.include_router(rbac_router, tags=["rbac"])
api_router.include_router(kb_router, tags=["knowledge-base"])
api_router.include_router(speech_router, tags=["speech"])
api_router.include_router(scan_router, tags=["scan"])
# 注意：全局在 main.py 中已挂载前缀 "/api"，
# 这里仅加版本前缀，避免出现 "/api/api/..." 的重复。
api_router.include_router(idc_reports_router, prefix="/v1/idc-reports", tags=["idc-reports"])
api_router.include_router(idc_analysis_router, prefix="/v1/idc-research", tags=["idc-research"])
api_router.include_router(idc_docs_router, prefix="/v1/idc-research", tags=["idc-research-docs"])

@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "Omind API is running"}


@api_router.get("/version")
async def get_version():
    """获取API版本信息"""
    return {"version": "1.0.0","api_version": "v1","description": "OMIND API"}
