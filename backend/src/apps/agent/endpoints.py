"""Agent API routes - 使用全局统一响应格式"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.shared.db.config import get_async_db
from src.apps.agent.schema import (
    AgentCreate, AgentUpdate, AgentQueryParams, MCPConfigUpdate,
    AgentStatusUpdate, AgentStatisticsUpdate, AgentResponse, AgentStatistics,
    AgentOwnerTransfer, FileUploadResponse, DocumentContent, FileProcessStatus
)
from src.apps.agent.service.agent_service import agent_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.apps.auth.dependencies import get_current_user_optional

# 导入LLM路由功能
from .service.streaming import stream_run_standard, RunCreate
from .service.threads import create_thread, get_thread_history_post, ThreadCreate, ThreadResponse
from .service.document_service import document_service

logger = get_logger(__name__)
router = APIRouter(tags=["Agent Management"])


@router.post("/v1/agents", response_model=UnifiedResponse)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """创建智能体"""
    agent_dict = agent_data.model_dump(exclude_none=True)
    # 设置创建者和所有者
    if current_user:
        agent_dict['create_by'] = current_user.get('username', 'system')
        agent_dict['agent_owner'] = current_user.get('username', 'system')
    else:
        agent_dict['create_by'] = 'system'
        agent_dict['agent_owner'] = 'system'
    agent = await agent_service.create_agent(db, agent_dict)
    return success_response(data=agent,msg="智能体创建成功",code=ResponseCode.CREATED)


@router.get("/v1/agents", response_model=UnifiedResponse)
async def list_agents(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态过滤"),
    enabled_only: bool = Query(False, description="仅显示启用的智能体"),
    create_by: Optional[str] = Query(None, description="创建者过滤"),
    owner_filter: Optional[str] = Query(None, description="归属过滤：mine/team/department"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """查询智能体列表"""
    # 获取当前用户名
    current_username = current_user.get('username') if current_user else None
    
    agents, total = await agent_service.list_agents(
        db, page, size, search, status, enabled_only, create_by,
        current_user=current_username, owner_filter=owner_filter
    )
    return paginated_response(items=agents,total=total,page=page,size=size,msg="查询智能体列表成功")


@router.get("/v1/agents/{agent_id}", response_model=UnifiedResponse)
async def get_agent(
    agent_id: str, 
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取指定智能体"""
    current_username = current_user.get('username') if current_user else None
    agent = await agent_service.get_agent_by_id(db, agent_id, current_username)
    if not agent: raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    return success_response(data=agent,msg="获取智能体信息成功")


@router.put("/v1/agents/{agent_id}", response_model=UnifiedResponse)
async def update_agent(
    agent_id: str,
    agent_data: AgentUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """更新智能体"""
    # 先获取智能体信息，检查权限
    existing_agent = await agent_service.get_agent_by_id(db, agent_id)
    if not existing_agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    # 检查是否为内置智能体
    if existing_agent.get('is_builtin') == 'yes':
        raise BusinessException("不能修改内置智能体", ResponseCode.FORBIDDEN)
    
    # 检查权限：只有所有者可以修改
    if current_user:
        current_username = current_user.get('username')
        if existing_agent.get('agent_owner') != current_username and existing_agent.get('create_by') != current_username:
            raise BusinessException("只有智能体所有者可以修改", ResponseCode.FORBIDDEN)
    
    update_dict = agent_data.model_dump(exclude_none=True)
    if not update_dict: 
        raise BusinessException("更新数据不能为空", ResponseCode.INVALID_PARAMETER)
    
    # 设置更新者
    if current_user:
        update_dict['update_by'] = current_user.get('username', 'system')
    
    updated_agent = await agent_service.update_agent(db, agent_id, update_dict)
    if not updated_agent: 
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    return success_response(data=updated_agent,msg="智能体更新成功")


@router.delete("/v1/agents/{agent_id}", response_model=UnifiedResponse)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """删除智能体"""
    # 先获取智能体信息，检查权限
    existing_agent = await agent_service.get_agent_by_id(db, agent_id)
    if not existing_agent:
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    
    # 检查是否为内置智能体（在service层也会检查，但这里提前检查更友好）
    if existing_agent.get('is_builtin') == 'yes':
        raise BusinessException("不能删除内置智能体", ResponseCode.FORBIDDEN)
    
    # 检查权限：只有所有者可以删除
    if current_user:
        current_username = current_user.get('username')
        if existing_agent.get('agent_owner') != current_username and existing_agent.get('create_by') != current_username:
            raise BusinessException("只有智能体所有者可以删除", ResponseCode.FORBIDDEN)
    
    success = await agent_service.delete_agent(db, agent_id)
    if not success: 
        raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    return success_response(data={"deleted_id": agent_id},msg="智能体删除成功")


@router.put("/v1/agents/{agent_id}/mcp-config", response_model=UnifiedResponse)
async def update_mcp_config(agent_id: str,mcp_config: MCPConfigUpdate,db: AsyncSession = Depends(get_async_db)):
    """更新智能体MCP配置"""
    updated_agent = await agent_service.update_mcp_config(
        db, agent_id, mcp_config.enabled_servers, mcp_config.selected_tools
    )
    if not updated_agent: raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    return success_response(data=updated_agent,msg="MCP配置更新成功")


@router.put("/v1/agents/{agent_id}/status", response_model=UnifiedResponse)
async def update_agent_status(agent_id: str,status_update: AgentStatusUpdate,db: AsyncSession = Depends(get_async_db)):
    """更新智能体状态"""
    updated_agent = await agent_service.update_agent_status(db, agent_id, status_update.status)
    if not updated_agent: raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    return success_response(data=updated_agent,msg="智能体状态更新成功")


@router.put("/v1/agents/{agent_id}/statistics", response_model=UnifiedResponse)
async def update_agent_statistics(agent_id: str,stats_update: AgentStatisticsUpdate,db: AsyncSession = Depends(get_async_db)):
    """更新智能体统计信息"""
    updated_agent = await agent_service.update_statistics(
        db, agent_id, stats_update.total_runs, 
        stats_update.success_rate, stats_update.avg_response_time
    )
    if not updated_agent:raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
    return success_response(data=updated_agent,msg="智能体统计信息更新成功")


@router.get("/v1/agents/meta/statistics", response_model=UnifiedResponse)
async def get_agent_statistics(db: AsyncSession = Depends(get_async_db)):
    """获取智能体统计信息"""
    statistics = await agent_service.get_statistics(db)
    return success_response(data=statistics,msg="获取智能体统计信息成功")


@router.get("/v1/agents/search", response_model=UnifiedResponse)
async def search_agents(
    keyword: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """搜索智能体"""
    agents, total = await agent_service.search_agents(db, keyword, page, size)
    return paginated_response(items=agents,total=total,page=page,size=size,msg="搜索智能体成功")


@router.post("/v1/agents/{agent_id}/transfer-ownership", response_model=UnifiedResponse)
async def transfer_agent_ownership(
    agent_id: str,
    transfer_data: AgentOwnerTransfer,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """转移智能体所有权"""
    if not current_user:
        raise BusinessException("需要登录才能转移所有权", ResponseCode.UNAUTHORIZED)
    
    current_username = current_user.get('username')
    if not current_username:
        raise BusinessException("无法获取当前用户信息", ResponseCode.UNAUTHORIZED)
    
    updated_agent = await agent_service.transfer_ownership(
        db, agent_id, transfer_data.new_owner, current_username, transfer_data.reason
    )
    return success_response(data=updated_agent, msg="智能体所有权转移成功")


@router.post("/v1/agents/{agent_id}/favorite", response_model=UnifiedResponse)
async def toggle_agent_favorite(
    agent_id: str,
    is_favorite: bool = True,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """切换智能体收藏状态"""
    if not current_user:
        raise BusinessException("需要登录才能收藏智能体", ResponseCode.UNAUTHORIZED)
    
    username = current_user.get('username')
    if not username:
        raise BusinessException("无法获取当前用户信息", ResponseCode.UNAUTHORIZED)
    
    result = await agent_service.toggle_favorite(db, agent_id, username, is_favorite)
    msg = "智能体收藏成功" if result else "取消收藏成功"
    return success_response(data={"is_favorite": result}, msg=msg)


@router.get("/v1/agents/favorites", response_model=UnifiedResponse)
async def get_user_favorite_agents(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取用户收藏的智能体列表"""
    if not current_user:
        raise BusinessException("需要登录才能查看收藏", ResponseCode.UNAUTHORIZED)
    
    username = current_user.get('username')
    if not username:
        raise BusinessException("无法获取当前用户信息", ResponseCode.UNAUTHORIZED)
    
    agents, total = await agent_service.get_user_favorites(db, username, page, size)
    return paginated_response(items=agents, total=total, page=page, size=size, msg="获取收藏列表成功")


# ==================== LLM智能体流式处理路由 ====================

@router.post("/chat/threads", response_model=ThreadResponse)
async def create_thread_endpoint(thread_create: ThreadCreate):
    """创建新的对话线程"""
    return await create_thread(thread_create)


@router.post("/chat/threads/{thread_id}/history")
async def get_thread_history_post_endpoint(thread_id: str, request_body: Optional[Dict[str, Any]] = None):
    """获取线程历史记录"""
    return await get_thread_history_post(thread_id, request_body)


@router.post("/chat/threads/{thread_id}/runs/stream")
async def stream_run_standard_endpoint(thread_id: str, request_body: RunCreate):
    """智能体流式对话处理"""
    return await stream_run_standard(thread_id, request_body)


@router.get("/chat/users/{user_name}/threads")
async def get_user_threads_endpoint(user_name: str, limit: int = 10, offset: int = 0):
    """获取用户的所有线程"""
    from .service.user_threads_db import get_user_threads
    threads = await get_user_threads(user_name, limit, offset)
    return {"user_name": user_name, "threads": threads, "total": len(threads)}


# ==================== 文档上传和处理路由 ====================

@router.post("/v1/agents/files/upload", response_model=UnifiedResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """上传文档文件"""
    # 验证文件名是否为空
    if not file.filename:
        raise BusinessException("文件名不能为空", ResponseCode.BAD_REQUEST)
    
    # 检查文件大小（如果有size属性）
    if hasattr(file, 'size') and file.size:
        from src.shared.core.config import settings
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file.size > max_size:
            raise BusinessException(
                f"文件大小超过限制（最大{settings.MAX_UPLOAD_SIZE_MB}MB）",
                ResponseCode.BAD_REQUEST
            )
    
    # 读取文件内容
    file_content = await file.read()
    
    # 获取用户ID
    user_id = current_user.get('username') if current_user else 'anonymous'
    
    # 上传文件
    file_info = await document_service.upload_file(
        db=db,
        file_content=file_content,
        filename=file.filename,
        user_id=user_id
    )
    
    return success_response(
        data=FileUploadResponse(**file_info).model_dump(),
        msg="文件上传成功"
    )


@router.get("/v1/agents/files/{file_id}/content", response_model=UnifiedResponse)
async def get_document_content(
    file_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取文档内容"""
    # 获取当前用户ID用于权限检查
    user_id = current_user.get('username') if current_user else None
    
    content = await document_service.get_document_content(db, file_id, user_id)
    if not content:
        raise BusinessException("文档不存在、正在处理中或无权访问", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=DocumentContent(**content).model_dump(),
        msg="获取文档内容成功"
    )


@router.get("/v1/agents/files/{file_id}/status", response_model=UnifiedResponse)
async def get_file_status(
    file_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取文件处理状态"""
    status = await document_service.get_file_status(db, file_id)
    if not status:
        raise BusinessException("文件不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=FileProcessStatus(**status).model_dump(),
        msg="获取文件状态成功"
    )