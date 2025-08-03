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
from .apps.user.rbac_endpoints import rbac_router

# 创建主API路由器
api_router = APIRouter()

# 注册各个子路由
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(sop_router, tags=["sop"])
api_router.include_router(mcp_router, tags=["mcp"])
api_router.include_router(ai_models_router, tags=["ai-models"])
api_router.include_router(scheduled_tasks_router, tags=["scheduled-tasks"])
api_router.include_router(rbac_router, tags=["rbac"])

@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "Omind API is running"}


@api_router.get("/version")
async def get_version():
    """获取API版本信息"""
    return {"version": "1.0.0","api_version": "v1","description": "OMIND API"}