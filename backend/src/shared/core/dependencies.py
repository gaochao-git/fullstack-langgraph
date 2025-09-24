"""
核心依赖注入模块
提供全局依赖项，如数据库连接、配置等
"""

from typing import Generator, Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session  
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from .config import settings
from src.shared.db.config import get_async_db

# 设置日志
logger = logging.getLogger(__name__)


def get_settings():
    """获取应用配置"""
    return settings


# ==================== 数据库依赖注入 ====================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话（推荐使用）"""
    try:
        async with get_async_db() as session:
            yield session
    except Exception as e:
        logger.error(f"Async database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )


# ==================== 用户认证依赖 ====================

def get_current_user():
    """
    获取当前用户
    TODO: 实现用户认证逻辑
    """
    # 这里实现JWT token验证或其他认证方式
    # 临时返回None，表示未实现认证
    return None


def get_current_user_optional():
    """获取当前用户（可选，不会抛出异常）"""
    try:
        return get_current_user()
    except:
        return None


# ==================== 服务层依赖注入 ====================

def get_sop_service():
    """获取SOP服务实例"""
    from ..services import SOPService
    return SOPService()


def get_agent_service():
    """获取智能体服务实例"""
    from ..services import AgentService
    return AgentService()


def get_mcp_service():
    """获取MCP服务实例"""
    from ..services import MCPService
    return MCPService()


def get_user_service():
    """获取用户服务实例"""
    from ..services import UserService
    return UserService()


def get_user_thread_service():
    """获取用户线程服务实例"""
    from ..services import UserThreadService
    return UserThreadService()


# ==================== 工具函数 ====================

def get_logger():
    """获取日志记录器"""
    return logger


def get_optional_database() -> Optional[Session]:
    """获取可选的数据库连接"""
    try:
        return next(get_database())
    except Exception:
        return None


def get_pagination_params(page: int = 1, size: int = 10):
    """获取分页参数"""
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 10
    
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size,
        "limit": size
    }