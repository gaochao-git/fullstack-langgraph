"""Agent API routes - 使用全局统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Request, Body, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from src.shared.db.models import now_shanghai
import uuid
import json
import os

from src.shared.db.config import get_async_db
from src.apps.agent.schema import (
    AgentCreate, AgentUpdate, MCPConfigUpdate,AgentStatusUpdate, AgentStatisticsUpdate,
    AgentOwnerTransfer, FileUploadResponse, DocumentContent, FileProcessStatus,
    MessageFeedbackCreate, MessageFeedbackResponse
)
from src.apps.agent.service.agent_service import agent_service
from src.apps.agent.service.agent_permission_service import agent_permission_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (UnifiedResponse, success_response, paginated_response, ResponseCode)
from src.shared.core.exceptions import BusinessException
from src.apps.auth.dependencies import get_current_user_optional

# 导入LLM路由功能
from .service.run_handler import stream_run_standard, invoke_run_standard, RunCreate, get_thread_file_ids
from .service.document_service import document_service
from .service.document_export_service import document_export_service

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


@router.get("/v1/agents/system-tools", response_model=UnifiedResponse)
async def get_available_system_tools():
    """获取所有可用的系统工具列表"""
    tools = agent_service.get_available_system_tools()
    return success_response(data=tools, msg="获取系统工具列表成功")


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
    update_dict = agent_data.model_dump(exclude_none=True)
    if not update_dict: 
        raise BusinessException("更新数据不能为空", ResponseCode.BAD_REQUEST)
    
    # 设置更新者信息
    current_username = None
    if current_user:
        current_username = current_user.get('username')
        update_dict['update_by'] = current_username or 'system'
    
    # 所有数据库操作都在 service 层处理
    updated_agent = await agent_service.update_agent(
        db, 
        agent_id, 
        update_dict,
        current_username=current_username
    )
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
    # 获取当前用户名
    current_username = current_user.get('username') if current_user else None
    
    # 直接调用service层的delete_agent方法
    # service层会在事务中完成所有检查和删除操作
    success = await agent_service.delete_agent_with_permission_check(db, agent_id, current_username)
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



# ==================== 智能体权限管理路由 ====================

class CreatePermissionRequest(BaseModel):
    user_name: str
    mark_comment: Optional[str] = ''

@router.post("/v1/agents/{agent_id}/permissions", response_model=UnifiedResponse)
async def create_agent_permission(
    agent_id: str,
    request: CreatePermissionRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """为智能体创建访问权限"""
    if not current_user:
        raise BusinessException("需要登录才能创建权限", ResponseCode.UNAUTHORIZED)
    
    create_by = current_user.get('username', 'system')
    
    permission = await agent_permission_service.create_permission(
        db, agent_id, request.user_name, request.mark_comment, create_by
    )
    
    return success_response(
        data={
            "id": permission.id,
            "agent_id": permission.agent_id,
            "user_name": permission.user_name,
            "agent_key": permission.agent_key,
            "mark_comment": permission.mark_comment,
            "is_active": permission.is_active,
            "create_time": permission.create_time.isoformat()
        },
        msg="权限创建成功"
    )


@router.get("/v1/agents/{agent_id}/permissions", response_model=UnifiedResponse)
async def list_agent_permissions(
    agent_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取智能体的权限列表"""
    permissions, total = await agent_permission_service.list_permissions(
        db, agent_id=agent_id, page=page, size=size
    )
    
    items = [
        {
            "id": p.id,
            "agent_id": p.agent_id,
            "user_name": p.user_name,
            "agent_key": p.agent_key,  # 返回完整密钥，前端负责显示处理
            "mark_comment": p.mark_comment,
            "is_active": p.is_active,
            "create_by": p.create_by,
            "create_time": p.create_time.strftime("%Y-%m-%d %H:%M:%S")  # 后端格式化时间
        }
        for p in permissions
    ]
    
    return paginated_response(
        items=items,
        total=total,
        page=page,
        size=size,
        msg="获取权限列表成功"
    )


@router.delete("/v1/agents/permissions/{permission_id}", response_model=UnifiedResponse)
async def revoke_agent_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """撤销智能体权限"""
    if not current_user:
        raise BusinessException("需要登录才能撤销权限", ResponseCode.UNAUTHORIZED)
    
    update_by = current_user.get('username', 'system')
    
    success = await agent_permission_service.revoke_permission(
        db, permission_id, update_by
    )
    
    return success_response(
        data={"success": success},
        msg="权限撤销成功"
    )


@router.post("/v1/agents/permissions/{permission_id}/regenerate-key", response_model=UnifiedResponse)
async def regenerate_permission_key(
    permission_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """重新生成权限密钥"""
    if not current_user:
        raise BusinessException("需要登录才能重新生成密钥", ResponseCode.UNAUTHORIZED)
    
    update_by = current_user.get('username', 'system')
    
    new_key = await agent_permission_service.regenerate_key(
        db, permission_id, update_by
    )
    
    return success_response(
        data={"agent_key": new_key},
        msg="密钥重新生成成功"
    )


@router.put("/v1/agents/permissions/{permission_id}/status", response_model=UnifiedResponse)
async def toggle_permission_status(
    permission_id: int,
    is_active: bool = Query(..., description="是否启用"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """切换权限状态（启用/禁用）"""
    if not current_user:
        raise BusinessException("需要登录才能更改权限状态", ResponseCode.UNAUTHORIZED)
    
    update_by = current_user.get('username', 'system')
    
    permission = await agent_permission_service.toggle_permission_status(
        db, permission_id, is_active, update_by
    )
    
    return success_response(
        data={
            "id": permission.id,
            "is_active": permission.is_active,
            "update_time": permission.update_time.strftime("%Y-%m-%d %H:%M:%S")
        },
        msg=f"权限已{'启用' if is_active else '禁用'}"
    )


# ==================== LLM智能体流式处理路由 ====================

class ThreadRequest(BaseModel):
    agent_id: str

@router.post("/v1/chat/threads", response_model=UnifiedResponse)
async def create_thread_endpoint(
    request: ThreadRequest
):
    """创建新的对话线程"""
    # 直接生成线程ID和时间戳
    thread_id = str(uuid.uuid4())
    created_at = now_shanghai().isoformat()
    
    # 返回统一响应格式
    return success_response(
        data={
            "thread_id": thread_id,
            "created_at": created_at,
            "agent_id": request.agent_id
        },
        msg="线程创建成功"
    )


@router.get("/v1/chat/threads/{thread_id}", response_model=UnifiedResponse)
async def get_thread_detail(
    thread_id: str,
    limit: int = Query(50, ge=1, le=100, description="返回的消息数量"),
    agent_id: Optional[str] = Query(None, description="智能体ID（agent_key认证时必须）"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取线程详情（历史记录）"""
    from .service.threads import get_thread_history_post
    
    # 调用原有的服务方法
    history = await get_thread_history_post(thread_id, None)
    
    # 返回标准格式
    return success_response(
        data=history[:limit] if history else [],
        msg="获取线程详情成功"
    )


@router.get("/v1/chat/threads/{thread_id}/messages", response_model=UnifiedResponse)
async def get_thread_messages(
    thread_id: str,
    agent_id: Optional[str] = Query(None, description="智能体ID"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取线程中的所有消息（从checkpoint）
    
    返回checkpoint中存储的实际消息历史，这是会发送给大模型的真实内容。
    自动计算每条消息的token数。
    """
    try:
        # 导入必要的模块
        import tiktoken
        from .checkpoint_factory import get_checkpointer
        
        # 初始化 tiktoken 编码器
        encoder = tiktoken.get_encoding("cl100k_base")
        
        checkpointer = await get_checkpointer()
        
        # 获取最新的checkpoint
        config = {"configurable": {"thread_id": thread_id}}
        
        # 使用 alist 获取checkpoint历史
        history = [c async for c in checkpointer.alist(config, limit=1)]
        
        if not history:
            return success_response(data={"messages": [], "total_tokens": 0}, msg="线程中没有消息")
        
        checkpoint_tuple = history[0]
        
        # 提取消息
        if hasattr(checkpoint_tuple, 'checkpoint') and checkpoint_tuple.checkpoint:
            messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])
        else:
            # 如果是字典格式，尝试直接获取
            messages = checkpoint_tuple.get("channel_values", {}).get("messages", []) if isinstance(checkpoint_tuple, dict) else []
        
        # 转换消息格式
        formatted_messages = []
        total_tokens = 0
        
        for msg in messages:
            formatted_msg = {
                "id": getattr(msg, "id", None),
                "type": msg.__class__.__name__.lower().replace("message", ""),
                "content": msg.content,
                "additional_kwargs": getattr(msg, "additional_kwargs", {}),
            }
            
            # 添加工具相关信息
            if hasattr(msg, "tool_calls"):
                formatted_msg["tool_calls"] = msg.tool_calls
            if hasattr(msg, "name"):
                formatted_msg["name"] = msg.name
            if hasattr(msg, "tool_call_id"):
                formatted_msg["tool_call_id"] = msg.tool_call_id
                
            # 始终计算token数
            # 注意：msg.content 可能为空字符串，特别是对于某些工具消息
            token_count = len(encoder.encode(msg.content if msg.content else ""))
            formatted_msg["token_count"] = token_count
            total_tokens += token_count
                
            formatted_messages.append(formatted_msg)
        
        return success_response(
            data={
                "messages": formatted_messages,
                "total_tokens": total_tokens,
                "message_count": len(formatted_messages),
                "thread_id": thread_id
            },
            msg="获取消息成功"
        )
        
    except Exception as e:
        logger.error(f"获取线程消息失败: {str(e)}", exc_info=True)
        raise BusinessException(f"获取消息失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.post("/v1/chat/threads/{thread_id}/completion")
async def completion_endpoint(
    thread_id: str,
    request_body: RunCreate,
    request: Request = None
):
    """统一的补全接口 - 支持流式和非流式"""
    from .service.run_handler import completion_handler
    return await completion_handler(thread_id, request_body, request)


@router.post("/v1/chat/threads/{thread_id}/runs/stream")
async def stream_run_standard_endpoint(
    thread_id: str, 
    request_body: RunCreate = None, 
    request: Request = None
):
    """智能体流式对话处理"""
    return await stream_run_standard(thread_id, request_body, request)


@router.post("/v1/chat/threads/{thread_id}/runs/invoke")
async def invoke_run_standard_endpoint(
    thread_id: str, 
    request_body: RunCreate = None, 
    request: Request = None
):
    """智能体非流式对话处理"""
    return await invoke_run_standard(thread_id, request_body, request)


@router.get("/v1/chat/threads")
async def get_threads(
    agent_id: Optional[str] = Query(None, description="智能体ID"),
    user_name: Optional[str] = Query(None, description="用户名"), 
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    request: Request = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取会话线程列表"""
    from .service.user_threads_db import get_user_threads
    
    # 如果没有提供user_name，尝试从当前用户获取
    if not user_name and current_user:
        user_name = current_user.get('username')
    
    # 如果是agent_key认证且没有传agent_id，从认证信息中获取
    if not agent_id and current_user and current_user.get('auth_type') == 'agent_key':
        agent_id = current_user.get('agent_id')
    
    if not user_name:
        raise BusinessException("必须提供用户名", ResponseCode.BAD_REQUEST)
    
    threads = await get_user_threads(user_name, limit, offset, agent_id=agent_id)
    
    return success_response(
        data={
            "user_name": user_name,
            "agent_id": agent_id,
            "threads": threads,
            "total": len(threads),
            "limit": limit,
            "offset": offset
        },
        msg="获取会话列表成功"
    )




# ==================== 文档上传和处理路由 ====================

@router.post("/v1/chat/files", response_model=UnifiedResponse)
async def create_file(
    file: UploadFile = File(...),
    agent_id: Optional[str] = Form(None, description="智能体ID（agent_key认证时必须）"),
    user_name: Optional[str] = Form(None, description="上传文件的用户名（agent_key认证时必须）"),
    db: AsyncSession = Depends(get_async_db),
    request: Request = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """上传文档文件"""
    # 如果是 agent_key 认证，agent_id 和 user_name 应该已经在中间件验证过了
    # 如果是 JWT 认证，从 current_user 获取用户名
    if not user_name and current_user:
        user_name = current_user.get('username')
    
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
    
    # 上传文件
    file_info = await document_service.upload_file(
        db=db,
        file_content=file_content,
        filename=file.filename,
        user_name=user_name  # 使用传入的用户名
    )
    
    return success_response(
        data=FileUploadResponse(**file_info).model_dump(),
        msg="文件上传成功"
    )




@router.get("/v1/chat/files/{file_id}/content", response_model=UnifiedResponse)
async def get_document_content(
    file_id: str,
    agent_id: Optional[str] = Query(None, description="智能体ID（agent_key认证时必须）"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取文档内容"""
    # 获取当前用户名用于权限检查
    user_name = current_user.get('username') if current_user else None
    
    content = await document_service.get_document_content(db, file_id, user_name)
    if not content:
        raise BusinessException("文档不存在、正在处理中或无权访问", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=DocumentContent(**content).model_dump(),
        msg="获取文档内容成功"
    )


@router.get("/v1/chat/files/{file_id}/metadata", response_model=UnifiedResponse)
async def get_file_metadata(
    file_id: str,
    agent_id: Optional[str] = Query(None, description="智能体ID（agent_key认证时必须）"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取文件元数据（文件名、大小、类型等）"""
    # 获取当前用户名用于权限检查
    user_name = current_user.get('username') if current_user else None
    
    # 使用已有的 get_file_info 方法获取文件信息
    file_info = await document_service.get_file_info(db, file_id, user_name)
    if not file_info:
        raise BusinessException("文件不存在或无权访问", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=file_info,
        msg="获取文件元数据成功"
    )


@router.post("/v1/chat/files/batch/metadata", response_model=UnifiedResponse)
async def get_batch_file_metadata(
    file_ids: List[str],
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """批量获取文件元数据"""
    # 获取当前用户名用于权限检查
    user_name = current_user.get('username') if current_user else None
    
    # 限制最多500个文件，防止请求过大
    if len(file_ids) > 500:
        file_ids = file_ids[:500]
    
    # 使用批量查询方法
    file_map = await document_service.get_batch_file_info(db, file_ids, user_name)
    
    return success_response(
        data={
            'files': file_map,
            'total': len(file_map)
        },
        msg="批量获取文件元数据成功"
    )


@router.get("/v1/chat/files/{file_id}/status", response_model=UnifiedResponse)
async def get_file_status(
    file_id: str,
    agent_id: Optional[str] = Query(None, description="智能体ID（agent_key认证时必须）"),
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


@router.get("/v1/chat/files/{file_id}")
async def get_file(
    file_id: str,
    agent_id: Optional[str] = Query(None, description="智能体ID（agent_key认证时必须）"),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """下载上传的文件"""
    from fastapi.responses import FileResponse
    from urllib.parse import quote
    import os
    
    try:
        # 获取当前用户名用于权限检查
        user_name = current_user.get('username') if current_user else None
        
        # 获取文件信息
        file_info = await document_service.get_file_info(db, file_id, user_name)
        if not file_info:
            raise BusinessException("文件不存在或无权访问", ResponseCode.NOT_FOUND)
        
        # 构建文件路径
        file_path = file_info['file_path']
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            raise BusinessException("文件不存在", ResponseCode.NOT_FOUND)
        
        # 对文件名进行URL编码，处理中文字符
        filename = file_info['file_name']
        encoded_filename = quote(filename.encode('utf-8'))
        
        # 根据文件扩展名设置 MIME 类型
        content_type = "application/octet-stream"
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        mime_types = {
            'txt': 'text/plain',
            'md': 'text/markdown',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'doc': 'application/msword',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'ppt': 'application/vnd.ms-powerpoint',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel'
        }
        content_type = mime_types.get(ext, content_type)
        
        logger.info(f"下载文件: {filename}, 路径: {file_path}")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}", exc_info=True)
        raise BusinessException(f"文件下载失败: {str(e)}", ResponseCode.INTERNAL_ERROR)




@router.get("/v1/agents/threads/{thread_id}/files", response_model=UnifiedResponse)
async def get_thread_files(
    thread_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取会话关联的文件ID列表"""
    file_ids = await get_thread_file_ids(thread_id)
    return success_response(data={"file_ids": file_ids}, msg="获取会话文件成功")


# ==================== 文档导出相关模型 ====================

class MermaidImage(BaseModel):
    """Mermaid图片数据"""
    index: int
    image_data: str  # base64编码的图片数据

class ExportDocumentRequest(BaseModel):
    """文档导出请求"""
    content: str
    title: Optional[str] = None
    format: str = 'markdown'
    mermaid_images: Optional[List[MermaidImage]] = None


@router.post("/v1/agents/export/word", response_model=UnifiedResponse)
async def export_to_word(
    request: ExportDocumentRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    导出内容为Word文档
    
    支持将Markdown内容导出为Word文档，包括：
    - Markdown文本转换
    - Mermaid图表转换为图片
    - 使用模板样式（如果配置）
    """
    try:
        # 导出为Word，支持前端提供的Mermaid图片
        file_path = await document_export_service.export_to_word(
            content=request.content,
            title=request.title,
            format=request.format,
            mermaid_images=request.mermaid_images
        )
        
        # 创建文件响应
        from fastapi.responses import FileResponse
        import os
        from urllib.parse import quote
        
        filename = f"{request.title or 'document'}.docx"
        # 对文件名进行URL编码，处理中文字符
        encoded_filename = quote(filename.encode('utf-8'))
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"导出Word文档失败: {e}")
        raise BusinessException(f"导出失败: {str(e)}", ResponseCode.INTERNAL_ERROR)


@router.post("/v1/multimodal/extract-image", response_model=UnifiedResponse)
async def extract_image_content(
    file: UploadFile = File(...),
    prompt: Optional[str] = Query(default=None, description="AI视觉模式的提示词"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    提取图片内容
    
    使用 AI 视觉模型理解图片内容
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith("image/"):
            raise BusinessException("只支持图片文件", ResponseCode.PARAM_ERROR)
        
        # 读取图片数据
        image_data = await file.read()
        
        # 检查图片大小
        from src.shared.core.config import settings
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # 使用配置的大小限制
        if len(image_data) > max_size:
            raise BusinessException(f"图片大小不能超过{settings.MAX_UPLOAD_SIZE_MB}MB", ResponseCode.PARAM_ERROR)
        
        # 构建选项
        options = {}
        if prompt:
            options["prompt"] = prompt
        else:
            options["prompt"] = "请详细描述这张图片的内容，如果是图表请提取其中的数据和信息。"
        
        # 调用多模态服务
        from .service.multimodal_service import multimodal_service
        result = await multimodal_service.extract_image_content(
            image_data=image_data,
            options=options
        )
        
        if result["success"]:
            return success_response(
                data={
                    "content": result["content"],
                    "model": result.get("model")
                },
                msg="图片内容提取成功"
            )
        else:
            raise BusinessException(
                result.get("error", "图片处理失败"),
                ResponseCode.INTERNAL_ERROR
            )
            
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"提取图片内容失败: {e}")
        raise BusinessException("提取图片内容失败", ResponseCode.INTERNAL_ERROR)


# ==================== 报告访问路由 ====================

@router.get("/v1/extract/task/{task_id}")
async def get_task_extract_results(
    task_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    根据任务ID获取所有文件的扫描结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务中所有文件的扫描结果
    """
    import os
    import glob
    
    # 检查认证
    if not current_user:
        raise BusinessException("需要登录才能查看提取结果", ResponseCode.UNAUTHORIZED)
    
    # 扫描目录下所有 task_id 开头的文件
    scan_dir = "/tmp/scan_visualizations"
    pattern = f"{scan_dir}/{task_id}_*.jsonl"
    jsonl_files = glob.glob(pattern)
    
    if not jsonl_files:
        raise BusinessException(f"任务 {task_id} 的扫描结果不存在", ResponseCode.NOT_FOUND)
    
    # 收集所有文件的扫描结果
    all_items = []
    all_statistics = {}
    all_files_with_sensitive = set()
    
    # 从文件名中提取file_id
    file_results = []
    
    for jsonl_path in jsonl_files:
        # 从文件名提取 file_id
        filename = os.path.basename(jsonl_path)
        # 去掉 .jsonl 后缀
        name_without_ext = filename[:-6]
        # 去掉 task_id_ 前缀
        file_id = name_without_ext[len(task_id)+1:]
        
        # 读取 JSONL 文件
        documents = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    documents.append(json.loads(line))
        
        # 获取文件信息
        file_info = {}
        if file_id:
            file_info_list = await document_service.get_documents_info_async(db, [file_id])
            if file_info_list:
                file_info = file_info_list[0]
        
        file_name = file_info.get("file_name", f"文档_{file_id[:8]}")
        file_size = file_info.get("file_size", 0)
        
        # 统计该文件的敏感信息
        file_items = []
        file_statistics = {}
        
        for doc in documents:
            doc_file_id = doc.get("document_id", "")
            text = doc.get("text", "")
            char_count = len(text)
            
            has_sensitive = False
            for extraction in doc.get("extractions", []):
                extraction_class = extraction.get("extraction_class", "")
                
                has_sensitive = True
                
                # 统计每种类型的数量
                if extraction_class not in file_statistics:
                    file_statistics[extraction_class] = 0
                file_statistics[extraction_class] += 1
                
                # 总体统计
                if extraction_class not in all_statistics:
                    all_statistics[extraction_class] = 0
                all_statistics[extraction_class] += 1
                
                # 创建单条记录
                item = {
                    "type": extraction_class,
                    "context": extraction.get("extraction_text", ""),
                    "file_id": file_id,
                    "file_name": file_name,
                    "file_size": file_size,
                    "char_count": char_count,
                    "position": extraction.get("char_interval"),
                    "image_count": 0
                }
                file_items.append(item)
                all_items.append(item)
            
            if has_sensitive:
                all_files_with_sensitive.add(file_id)
        
        # 计算文档字符数（从第一个文档获取，所有文档应该有相同的文本）
        char_count = 0
        if documents and documents[0].get("text"):
            char_count = len(documents[0].get("text", ""))
        
        # 添加文件结果摘要
        file_results.append({
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "char_count": char_count,
            "sensitive_count": len(file_items),
            "sensitive_types": file_statistics,
            "items": file_items
        })
    
    # 返回结果
    return success_response({
        "task_id": task_id,
        "files": file_results,
        "total_files": len(jsonl_files),
        "items": all_items,  # 所有敏感信息项
        "statistics": all_statistics,  # 总体统计
        "total_sensitive": len(all_items),
        "files_with_sensitive": len(all_files_with_sensitive)
    })


@router.get("/v1/extract/{scan_id}/html")
async def get_extract_html(
    scan_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    获取扫描结果的HTML可视化页面
    
    Args:
        scan_id: 扫描ID（可以是 task_id_file_id 格式）
    
    Returns:
        HTML文件响应
    """
    from fastapi.responses import FileResponse
    import os
    
    # HTML查看不需要强制认证，允许公开访问
    # if not current_user:
    #     raise BusinessException("需要登录才能查看提取结果", ResponseCode.UNAUTHORIZED)
    
    # 构建 HTML 文件路径
    html_path = f"/tmp/scan_visualizations/{scan_id}.html"
    
    # 检查文件是否存在
    if not os.path.exists(html_path):
        raise BusinessException(f"扫描结果不存在: {scan_id}", ResponseCode.NOT_FOUND)
    
    # 返回HTML文件
    return FileResponse(
        path=html_path,
        media_type="text/html",
        headers={
            "Content-Type": "text/html; charset=utf-8"
        }
    )


@router.get("/v1/extract/{scan_id}")
async def get_extract_result(
    scan_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取数据提取结果
    
    Args:
        scan_id: 扫描ID
    
    Returns:
        提取结果内容（JSONL转换为JSON数组）
    """
    import os
    
    # 检查认证（支持JWT和Cookie认证）
    if not current_user:
        raise BusinessException("需要登录才能查看提取结果", ResponseCode.UNAUTHORIZED)
    
    # 构建 JSONL 文件路径
    jsonl_path = f"/tmp/scan_visualizations/{scan_id}.jsonl"
    
    # 检查文件是否存在
    if not os.path.exists(jsonl_path):
        raise BusinessException(f"扫描结果不存在: {scan_id}", ResponseCode.NOT_FOUND)
    
    # 读取 JSONL 文件，转换为 JSON 数组
    documents = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                documents.append(json.loads(line))
    
    # 收集所有文件ID
    file_ids = [doc.get("document_id", "") for doc in documents if doc.get("document_id")]
    
    # 批量从数据库获取文件信息
    file_info_map = {}
    if file_ids:
        file_info_list = await document_service.get_documents_info_async(db, file_ids)
        # 转换为字典，以file_id为key
        for info in file_info_list:
            file_info_map[info["file_id"]] = info
        logger.info(f"从数据库获取到 {len(file_info_map)} 个文件的元信息")
    
    # 处理数据，将每个extraction转换为单独的记录
    items = []
    statistics = {}
    files_with_sensitive = set()
    
    for doc in documents:
        file_id = doc.get("document_id", "")
        text = doc.get("text", "")
        
        # 从数据库获取文件信息，如果没有则使用默认值
        file_info = file_info_map.get(file_id, {})
        file_name = file_info.get("file_name", f"文档_{file_id[:8]}")
        file_size = file_info.get("file_size", len(text.encode('utf-8')))
        
        # 计算文档基本信息
        char_count = len(text)
        
        # 统计敏感信息
        has_sensitive = False
        for extraction in doc.get("extractions", []):
            extraction_class = extraction.get("extraction_class", "")
                
            has_sensitive = True
            
            # 统计每种类型的数量
            if extraction_class not in statistics:
                statistics[extraction_class] = 0
            statistics[extraction_class] += 1
            
            # 创建单条记录
            item = {
                "type": extraction_class,
                "context": extraction.get("extraction_text", ""),
                "file_id": file_id,
                "file_name": file_name,  # 使用数据库中的真实文件名
                "file_size": file_size,  # 使用数据库中的真实文件大小
                "char_count": char_count,
                "position": extraction.get("char_interval"),
                "image_count": 0  # 从文本无法判断图片数量
            }
            items.append(item)
        
        if has_sensitive:
            files_with_sensitive.add(file_id)
    
    # 返回前端期望的格式
    return success_response({
        "items": items,
        "statistics": statistics,
        "total_sensitive": len(items),
        "files_with_sensitive": len(files_with_sensitive)
    })


# ========== 消息压缩相关API ==========

@router.post("/v1/chat/compress-message", response_model=UnifiedResponse, summary="压缩单条消息")
async def compress_single_message(
    request: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    使用AI模型压缩单条消息，保留关键信息
    
    请求体格式:
    {
        "message": {
            "id": "msg_id",
            "type": "ai",
            "content": "长文本内容...",
            "additional_kwargs": {}
        },
        "options": {
            "compression_level": "medium",  // light/medium/heavy
            "preserve_context": true,
            "target_token_ratio": 0.5
        }
    }
    """
    try:
        from src.apps.ai_model.service.ai_model_service import ai_model_service
        
        message = request.get("message", {})
        options = request.get("options", {})
        
        # 获取默认的压缩模型
        llm = await ai_model_service.get_default_llm(db)
        
        # 构建压缩提示词
        compression_prompt = _build_compression_prompt(
            message.get("content", ""),
            options.get("compression_level", "medium"),
            options.get("preserve_context", True),
            options.get("target_token_ratio", 0.5)
        )
        
        # 调用模型进行压缩
        compressed_content = await llm.ainvoke(compression_prompt)
        
        # 构建压缩后的消息
        compressed_message = {
            "id": message.get("id"),
            "type": message.get("type"),
            "content": compressed_content.content,
            "additional_kwargs": {
                **message.get("additional_kwargs", {}),
                "compressed": True,
                "original_length": len(message.get("content", "")),
                "compressed_length": len(compressed_content.content),
                "compression_ratio": len(compressed_content.content) / len(message.get("content", "")) if message.get("content") else 0
            }
        }
        
        logger.info(
            f"消息压缩成功: 原长度={len(message.get('content', ''))}, "
            f"压缩后={len(compressed_content.content)}"
        )
        
        return success_response(data={"compressed_message": compressed_message})
        
    except Exception as e:
        logger.error(f"压缩消息失败: {str(e)}", exc_info=True)
        raise BusinessException(ResponseCode.INTERNAL_ERROR, f"压缩失败: {str(e)}")


@router.post("/v1/chat/compress-messages", response_model=UnifiedResponse, summary="批量压缩消息")
async def compress_messages(
    request: dict = Body(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """批量压缩多条消息"""
    try:
        from src.apps.ai_model.service.ai_model_service import ai_model_service
        
        messages = request.get("messages", [])
        options = request.get("options", {})
        
        # 获取默认的压缩模型
        llm = await ai_model_service.get_default_llm(db)
        
        compressed_messages = []
        
        for message in messages:
            # 只压缩AI消息和较长的消息
            if message.get("type") != "ai" or len(message.get("content", "")) < 100:
                compressed_messages.append(message)
                continue
                
            # 构建压缩提示词
            compression_prompt = _build_compression_prompt(
                message.get("content", ""),
                options.get("compression_level", "medium"),
                options.get("preserve_context", True),
                options.get("target_token_ratio", 0.5)
            )
            
            # 调用模型进行压缩
            compressed_content = await llm.ainvoke(compression_prompt)
            
            # 构建压缩后的消息
            compressed_message = {
                "id": message.get("id"),
                "type": message.get("type"),
                "content": compressed_content.content,
                "additional_kwargs": {
                    **message.get("additional_kwargs", {}),
                    "compressed": True,
                    "original_length": len(message.get("content", "")),
                    "compressed_length": len(compressed_content.content),
                    "compression_ratio": len(compressed_content.content) / len(message.get("content", "")) if message.get("content") else 0
                }
            }
            compressed_messages.append(compressed_message)
        
        logger.info(f"批量压缩完成: 处理了 {len(compressed_messages)} 条消息")
        
        return success_response(data={"compressed_messages": compressed_messages})
        
    except Exception as e:
        logger.error(f"批量压缩消息失败: {str(e)}", exc_info=True)
        raise BusinessException(ResponseCode.INTERNAL_ERROR, f"批量压缩失败: {str(e)}")


def _build_compression_prompt(
    content: str,
    compression_level: str,
    preserve_context: bool,
    target_token_ratio: float
) -> str:
    """构建压缩提示词"""
    
    level_instructions = {
        "light": "轻度压缩：去除冗余信息，保留大部分细节",
        "medium": "中度压缩：保留关键信息和主要细节，去除次要内容",
        "heavy": "重度压缩：只保留核心要点，大幅精简内容"
    }
    
    context_instruction = "保持上下文的连贯性" if preserve_context else "独立压缩，不考虑上下文"
    
    prompt = f"""请对以下内容进行{level_instructions.get(compression_level, level_instructions['medium'])}。
要求：
1. {context_instruction}
2. 目标压缩到原文的{int(target_token_ratio * 100)}%左右
3. 保留关键信息、数据和结论
4. 使用简洁清晰的语言
5. 不要添加"总结："等前缀，直接输出压缩后的内容

原文内容：
{content}

压缩后的内容："""
    
    return prompt


# ==================== 消息反馈API ====================

@router.post("/v1/chat/threads/{thread_id}/messages/{message_id}/feedback", response_model=UnifiedResponse)
async def submit_message_feedback(
    thread_id: str,
    message_id: str,
    feedback: MessageFeedbackCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    提交消息反馈（点赞/点踩）
    
    - 每个用户对每条消息只能有一个反馈
    - 如果已有反馈，会更新反馈类型
    - 反馈会汇总到智能体维度的统计数据
    """
    if not current_user:
        raise BusinessException("需要登录才能提交反馈", ResponseCode.UNAUTHORIZED)
    
    try:
        from .service.feedback_service import feedback_service
        
        # 获取用户名
        user_name = current_user.get("username")
        if not user_name:
            raise BusinessException("无法获取用户名", ResponseCode.BAD_REQUEST)
        
        # 提交反馈
        result = await feedback_service.submit_feedback(
            db=db,
            thread_id=thread_id,
            message_id=message_id,
            user_name=user_name,
            feedback_type=feedback.feedback_type,
            feedback_content=feedback.feedback_content
        )
        
        return success_response(
            data=result,
            msg="反馈提交成功"
        )
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"提交消息反馈失败: {str(e)}", exc_info=True)
        raise BusinessException("提交反馈失败", ResponseCode.INTERNAL_ERROR)


# ==================== 运行日志API ====================

@router.get("/v1/agents/{agent_id}/run-logs", response_model=UnifiedResponse)
async def get_agent_run_logs(
    agent_id: str,
    limit: int = 20,
    offset: int = 0,
    user_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    获取智能体运行日志
    
    - 支持分页查询
    - 支持按用户筛选
    - 支持按时间范围筛选
    - 返回运行统计信息
    """
    try:
        from .service.run_log_service import run_log_service
        from datetime import datetime
        
        # 解析日期参数
        start_datetime = datetime.fromisoformat(start_date) if start_date else None
        end_datetime = datetime.fromisoformat(end_date) if end_date else None
        
        # 获取运行日志和统计
        result = await run_log_service.get_agent_run_logs(
            db=db,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
            user_name=user_name,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return success_response(
            data=result,
            msg="获取运行日志成功"
        )
        
    except Exception as e:
        logger.error(f"获取运行日志失败: {str(e)}", exc_info=True)
        raise BusinessException("获取运行日志失败", ResponseCode.INTERNAL_ERROR)


@router.get("/v1/agents/{agent_id}/run-summary", response_model=UnifiedResponse)
async def get_agent_run_summary(
    agent_id: str,
    days: int = 7,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    获取智能体运行统计摘要
    
    - 返回最近N天的用户运行统计
    - 包含每个用户的运行次数、成功率等
    """
    try:
        from .service.run_log_service import run_log_service
        
        # 获取用户运行统计
        summary = await run_log_service.get_user_run_summary(
            db=db,
            agent_id=agent_id,
            days=days
        )
        
        return success_response(
            data={
                "agent_id": agent_id,
                "days": days,
                "user_stats": summary
            },
            msg="获取运行统计成功"
        )
        
    except Exception as e:
        logger.error(f"获取运行统计失败: {str(e)}", exc_info=True)
        raise BusinessException("获取运行统计失败", ResponseCode.INTERNAL_ERROR)