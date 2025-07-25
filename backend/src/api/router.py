"""
API路由聚合模块
统一管理所有API路由
"""

from fastapi import APIRouter

# 导入各个端点路由
from .endpoints.agents import router as agents_router
from .endpoints.sop import router as sop_router
from .endpoints.mcp import router as mcp_router
from .endpoints.ai_models import router as ai_models_router

# 创建主API路由器
api_router = APIRouter()

# 注册各个子路由
api_router.include_router(agents_router,prefix="/agents",tags=["agents"])
api_router.include_router(sop_router,prefix="/sops",tags=["sop"])
api_router.include_router(mcp_router,prefix="/mcp",tags=["mcp"])
api_router.include_router(ai_models_router,prefix="/ai-models",tags=["ai-models"])


@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "Omind API is running"}


@api_router.get("/version")
async def get_version():
    """获取API版本信息"""
    return {"version": "1.0.0","api_version": "v1","description": "OMIND API"}