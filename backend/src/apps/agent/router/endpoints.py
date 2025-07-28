"""Agent API routes - 使用全局统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.apps.agent.schema.agent import (
    AgentCreate, AgentUpdate, AgentQueryParams, MCPConfigUpdate,
    AgentStatusUpdate, AgentStatisticsUpdate, AgentResponse, AgentStatistics
)
from src.apps.agent.service.agent_service import agent_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException

logger = get_logger(__name__)
router = APIRouter(tags=["Agent Management"])


@router.post("/v1/agents", response_model=UnifiedResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建智能体"""
    agent_dict = agent_data.model_dump(exclude_none=True)
    agent = await agent_service.create_agent(db, agent_dict)
    
    return success_response(
        data=agent.to_dict(),
        msg="智能体创建成功",
        code=ResponseCode.CREATED
    )


@router.get("/v1/agents/{agent_id}", response_model=UnifiedResponse)
async def get_agent(
    agent_id: str,
    include_builtin: bool = Query(True, description="是否包含内置智能体"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定智能体"""
    agent = await agent_service.get_agent_by_id(db, agent_id, include_builtin)
    if not agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=agent,
        msg="获取智能体信息成功"
    )


@router.get("/v1/agents", response_model=UnifiedResponse)
async def list_agents(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态过滤"),
    enabled_only: bool = Query(False, description="仅显示启用的智能体"),
    include_builtin: bool = Query(True, description="包含内置智能体"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询智能体列表"""
    agents, total = await agent_service.list_agents(
        db, page, size, search, status, enabled_only, include_builtin
    )
    
    return paginated_response(
        items=agents,
        total=total,
        page=page,
        size=size,
        msg="查询智能体列表成功"
    )


@router.put("/v1/agents/{agent_id}", response_model=UnifiedResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新智能体"""
    update_dict = agent_data.model_dump(exclude_none=True)
    if not update_dict:
        raise BusinessException("更新数据不能为空", ResponseCode.INVALID_PARAMETER)
    
    updated_agent = await agent_service.update_agent(db, agent_id, update_dict)
    if not updated_agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_agent.to_dict(),
        msg="智能体更新成功"
    )


@router.delete("/v1/agents/{agent_id}", response_model=UnifiedResponse)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """删除智能体"""
    success = await agent_service.delete_agent(db, agent_id)
    if not success:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_id": agent_id},
        msg="智能体删除成功"
    )


@router.put("/v1/agents/{agent_id}/mcp-config", response_model=UnifiedResponse)
async def update_mcp_config(
    agent_id: str,
    mcp_config: MCPConfigUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新智能体MCP配置"""
    updated_agent = await agent_service.update_mcp_config(
        db, agent_id, mcp_config.enabled_servers, mcp_config.selected_tools
    )
    if not updated_agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_agent.to_dict(),
        msg="MCP配置更新成功"
    )


@router.put("/v1/agents/{agent_id}/status", response_model=UnifiedResponse)
async def update_agent_status(
    agent_id: str,
    status_update: AgentStatusUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新智能体状态"""
    updated_agent = await agent_service.update_agent_status(
        db, agent_id, status_update.status
    )
    if not updated_agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_agent.to_dict(),
        msg="智能体状态更新成功"
    )


@router.put("/v1/agents/{agent_id}/statistics", response_model=UnifiedResponse)
async def update_agent_statistics(
    agent_id: str,
    stats_update: AgentStatisticsUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新智能体统计信息"""
    updated_agent = await agent_service.update_statistics(
        db, agent_id, stats_update.total_runs, 
        stats_update.success_rate, stats_update.avg_response_time
    )
    if not updated_agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_agent.to_dict(),
        msg="智能体统计信息更新成功"
    )


@router.get("/v1/agents/meta/statistics", response_model=UnifiedResponse)
async def get_agent_statistics(
    db: AsyncSession = Depends(get_async_db)
):
    """获取智能体统计信息"""
    statistics = await agent_service.get_statistics(db)
    return success_response(
        data=statistics,
        msg="获取智能体统计信息成功"
    )


@router.get("/v1/agents/search", response_model=UnifiedResponse)
async def search_agents(
    keyword: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """搜索智能体"""
    agents, total = await agent_service.search_agents(db, keyword, page, size)
    
    return paginated_response(
        items=agents,
        total=total,
        page=page,
        size=size,
        msg="搜索智能体成功"
    )