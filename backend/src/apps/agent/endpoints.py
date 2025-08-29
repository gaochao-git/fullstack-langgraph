"""Agent API routes - 使用全局统一响应格式"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.shared.db.config import get_async_db
from src.apps.agent.schema import (
    AgentCreate, AgentUpdate, AgentQueryParams, MCPConfigUpdate,
    AgentStatusUpdate, AgentStatisticsUpdate, AgentResponse, AgentStatistics,
    AgentOwnerTransfer, FileUploadResponse, DocumentContent, FileProcessStatus
)
from src.apps.agent.service.agent_service import agent_service
from src.apps.agent.service.agent_permission_service import agent_permission_service
from src.shared.core.logging import get_logger
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.apps.auth.dependencies import get_current_user_optional
from .dependencies import verify_agent_key

# 导入LLM路由功能
from .service.streaming import stream_run_standard, RunCreate
from .service.threads import create_thread, get_thread_history_post, ThreadCreate, ThreadResponse
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
        raise BusinessException("更新数据不能为空", ResponseCode.INVALID_PARAMETER)
    
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
            "agent_key_preview": p.agent_key[:10] + "...",  # 提供预览版本
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

@router.post("/chat/threads", response_model=ThreadResponse)
async def create_thread_endpoint(
    thread_create: Optional[ThreadCreate] = None,
    request: Request = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """创建新的对话线程"""
    # 如果没有传递 body，创建一个空的 ThreadCreate 对象
    if thread_create is None:
        thread_create = ThreadCreate()
    
    # 如果没有提供 user_name，从认证信息中获取
    if not thread_create.user_name and current_user:
        thread_create.user_name = current_user.get('username')
    
    # 如果是 agent_key 认证且没有提供 assistant_id，从认证信息中获取
    if not thread_create.assistant_id and current_user and current_user.get('auth_type') == 'agent_key':
        thread_create.assistant_id = current_user.get('agent_id')
    
    # 验证必需参数
    if not thread_create.assistant_id:
        raise BusinessException("必须提供智能体ID", ResponseCode.INVALID_PARAMETER)
    
    if not thread_create.user_name:
        raise BusinessException("无法获取用户名", ResponseCode.INVALID_PARAMETER)
    
    return await create_thread(thread_create)


@router.get("/chat/threads/{thread_id}/history")
async def get_thread_history_endpoint(
    thread_id: str,
    limit: int = Query(50, ge=1, le=100, description="返回的消息数量"),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取线程历史记录"""
    from .service.threads import get_thread_history_post
    
    # 调用原有的服务方法
    history = await get_thread_history_post(thread_id, None)
    
    return success_response(
        data={
            "thread_id": thread_id,
            "history": history[:limit] if history else []
        },
        msg="获取对话历史成功"
    )




@router.post("/chat/threads/{thread_id}/runs/stream")
async def stream_run_standard_endpoint(
    thread_id: str, 
    request_body: Optional[RunCreate] = None, 
    request: Request = None
):
    """智能体流式对话处理"""
    # 如果没有传递 body，创建一个空的 RunCreate 对象
    if request_body is None:
        request_body = RunCreate()
    return await stream_run_standard(thread_id, request_body, request)


@router.post("/chat/threads/{thread_id}/runs/invoke")
async def invoke_run_standard_endpoint(
    thread_id: str, 
    request_body: Optional[RunCreate] = None, 
    request: Request = None
):
    """智能体非流式对话处理"""
    # 如果没有传递 body，创建一个空的 RunCreate 对象
    if request_body is None:
        request_body = RunCreate()
    from .service.streaming import invoke_run_standard
    return await invoke_run_standard(thread_id, request_body, request)


@router.get("/chat/threads")
async def get_threads(
    user_name: Optional[str] = Query(None, description="用户名"), 
    assistant_id: Optional[str] = Query(None, description="智能体ID"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    request: Request = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """获取会话线程列表"""
    from .service.user_threads_db import get_user_threads
    
    # 如果没有提供user_name，尝试从当前用户获取
    if not user_name and current_user:
        user_name = current_user.get('username')
    
    # 如果是agent_key认证且没有传assistant_id，从认证信息中获取
    if not assistant_id and current_user and current_user.get('auth_type') == 'agent_key':
        assistant_id = current_user.get('agent_id')
    
    if not user_name:
        raise BusinessException("必须提供用户名", ResponseCode.INVALID_PARAMETER)
    
    threads = await get_user_threads(user_name, limit, offset, agent_id=assistant_id)
    
    return success_response(
        data={
            "user_name": user_name,
            "agent_id": assistant_id,
            "threads": threads,
            "total": len(threads),
            "limit": limit,
            "offset": offset
        },
        msg="获取会话列表成功"
    )




# ==================== 文档上传和处理路由 ====================

@router.post("/chat/files", response_model=UnifiedResponse)
async def create_file(
    file: UploadFile = File(...),
    assistant_id: Optional[str] = Query(None, description="智能体ID（agent_key认证时必须）"),
    user_name: Optional[str] = Query(None, description="上传文件的用户名（agent_key认证时必须）"),
    db: AsyncSession = Depends(get_async_db),
    request: Request = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """上传文档文件"""
    # 如果是 agent_key 认证，assistant_id 和 user_name 应该已经在中间件验证过了
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




@router.get("/chat/files/{file_id}/content", response_model=UnifiedResponse)
async def get_document_content(
    file_id: str,
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


@router.get("/chat/files/{file_id}/status", response_model=UnifiedResponse)
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


@router.get("/chat/files/{file_id}")
async def get_file(
    file_id: str,
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
            'doc': 'application/msword'
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
    from .service.streaming import get_thread_file_ids
    
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
        raise BusinessException(f"处理失败: {str(e)}", ResponseCode.INTERNAL_ERROR)