"""
智能体相关的依赖注入
"""
from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.db.config import get_async_db
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.logging import get_logger
from typing import Dict, Any, Optional

logger = get_logger(__name__)


async def verify_agent_key(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
) -> str:
    """
    验证 agent_key
    返回 agent_id
    """
    # 获取 Authorization header
    auth_header = request.headers.get('authorization', '')
    
    if not auth_header.startswith('Bearer '):
        raise BusinessException("缺少认证信息", ResponseCode.UNAUTHORIZED)
    
    token = auth_header.replace('Bearer ', '').strip()
    
    # 检查是否是 agent_key（以 agent_ 开头）
    if not token.startswith('agent_'):
        raise BusinessException("无效的认证令牌", ResponseCode.UNAUTHORIZED)
    
    # 查询数据库验证 agent_key
    from .models import AgentConfig
    from sqlalchemy import select
    
    result = await db.execute(
        select(AgentConfig).where(AgentConfig.agent_key == token)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        logger.warning(f"无效的 agent_key: {token[:20]}...")
        raise BusinessException("智能体调用密钥错误", ResponseCode.INVALID_API_KEY)
    
    logger.info(f"智能体 {agent.agent_id} 密钥验证成功")
    return agent.agent_id