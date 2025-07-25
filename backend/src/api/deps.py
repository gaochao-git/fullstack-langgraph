"""
API层依赖注入模块
提供API路由专用的依赖项
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials

from core.dependencies import (
    get_settings, 
    get_database, 
    get_current_user,
    get_pagination_params
)
from core.security import security, SecurityService


def get_api_settings():
    """获取API配置"""
    return get_settings()


def get_api_database():
    """获取API数据库连接"""
    return get_database()


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取已认证用户"""
    try:
        return SecurityService.get_current_user_from_token(credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """获取可选用户（允许匿名访问）"""
    if not credentials:
        return None
    
    try:
        return SecurityService.get_current_user_from_token(credentials)
    except Exception:
        return None


def get_admin_user(current_user=Depends(get_authenticated_user)):
    """获取管理员用户"""
    # TODO: 实现管理员权限检查
    # if not current_user.get("is_admin", False):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin privileges required"
    #     )
    return current_user


def get_query_params(
    q: Optional[str] = Query(None, description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向")
):
    """获取通用查询参数"""
    return {
        "q": q,
        "category": category,
        "status": status,
        "sort_by": sort_by,
        "sort_order": sort_order
    }


def get_agent_params(
    agent_id: str,
    current_user=Depends(get_optional_user)
):
    """获取智能体相关参数"""
    # TODO: 验证用户是否有权限访问该智能体
    return {
        "agent_id": agent_id,
        "user": current_user
    }


def validate_request_size(
    content_length: Optional[int] = None
):
    """验证请求大小"""
    max_size = 10 * 1024 * 1024  # 10MB
    if content_length and content_length > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request too large"
        )
    return True


class CommonQueryParams:
    """通用查询参数类"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页数量"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        sort: str = Query("id", description="排序字段"),
        order: str = Query("asc", regex="^(asc|desc)$", description="排序方向")
    ):
        self.page = page
        self.size = size
        self.search = search
        self.sort = sort
        self.order = order
        self.offset = (page - 1) * size
        self.limit = size


def get_common_params(params: CommonQueryParams = Depends()):
    """获取通用查询参数"""
    return params