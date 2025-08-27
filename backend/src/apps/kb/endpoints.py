"""
知识库模块API端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.auth.dependencies import get_current_user
from src.shared.db.config import get_async_db
from src.shared.schemas.response import success_response, paginated_response
from .service import kb_service, kb_folder_service
from .schema import (
    KBCreateRequest, KBUpdateRequest, KBResponse,
    FolderCreateRequest, FolderUpdateRequest, FolderResponse,
    DocumentAddRequest, DocumentMoveRequest, PermissionGrantRequest
)

router = APIRouter(prefix="/v1/kb", tags=["知识库管理"])


# ==================== 知识库管理 ====================

@router.post("/knowledge-bases")
async def create_knowledge_base(
    kb_data: KBCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """创建知识库"""
    kb = await kb_service.create_kb(db, kb_data.dict(), current_user['username'])
    return success_response(kb)


@router.get("/knowledge-bases")
async def get_knowledge_bases(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户可访问的知识库列表"""
    result = await kb_service.get_user_kbs(
        db, current_user['username'], page, page_size
    )
    return paginated_response(**result)


@router.get("/knowledge-bases/{kb_id}")
async def get_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取知识库详情"""
    kb = await kb_service.get_kb_by_id(db, kb_id, current_user['username'])
    return success_response(kb)


@router.put("/knowledge-bases/{kb_id}")
async def update_knowledge_base(
    kb_id: str,
    update_data: KBUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新知识库"""
    kb = await kb_service.update_kb(
        db, kb_id, update_data.dict(exclude_unset=True), current_user['username']
    )
    return success_response(kb)


@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(
    kb_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除知识库"""
    await kb_service.delete_kb(db, kb_id, current_user['username'])
    return success_response({"message": "知识库删除成功"})


# ==================== 知识库文档管理 ====================

@router.post("/knowledge-bases/{kb_id}/documents")
async def add_document_to_kb(
    kb_id: str,
    doc_data: DocumentAddRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """添加文档到知识库"""
    await kb_service.add_document_to_kb(
        db, kb_id, doc_data.file_id, doc_data.dict(), current_user['username']
    )
    
    # 如果指定了目录，同时添加到目录
    if doc_data.folder_id:
        await kb_folder_service.add_document_to_folder(
            db, kb_id, doc_data.file_id, doc_data.folder_id,
            doc_data.dict(), current_user['username']
        )
    
    return success_response({"message": "文档添加成功"})


@router.delete("/knowledge-bases/{kb_id}/documents/{file_id}")
async def remove_document_from_kb(
    kb_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """从知识库移除文档"""
    await kb_service.remove_document_from_kb(db, kb_id, file_id, current_user['username'])
    return success_response({"message": "文档移除成功"})


@router.get("/knowledge-bases/{kb_id}/documents")
async def get_kb_documents(
    kb_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取知识库文档列表"""
    result = await kb_service.get_kb_documents(
        db, kb_id, current_user['username'], page, page_size
    )
    return paginated_response(**result)


# ==================== 知识库目录管理 ====================

@router.post("/knowledge-bases/{kb_id}/folders")
async def create_folder(
    kb_id: str,
    folder_data: FolderCreateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """创建目录"""
    folder = await kb_folder_service.create_folder(
        db, kb_id, folder_data.dict(), current_user['username']
    )
    return success_response(folder)


@router.get("/knowledge-bases/{kb_id}/folders/tree")
async def get_folder_tree(
    kb_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取知识库目录树"""
    tree = await kb_folder_service.get_folder_tree(
        db, kb_id, current_user['username']
    )
    return success_response({"tree": tree})


@router.put("/folders/{folder_id}")
async def update_folder(
    folder_id: str,
    update_data: FolderUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """更新目录"""
    folder = await kb_folder_service.update_folder(
        db, folder_id, update_data.dict(exclude_unset=True), current_user['username']
    )
    return success_response(folder)


@router.post("/folders/{folder_id}/move")
async def move_folder(
    folder_id: str,
    target_parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """移动目录"""
    await kb_folder_service.move_folder(
        db, folder_id, target_parent_id, current_user['username']
    )
    return success_response({"message": "目录移动成功"})


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """删除目录"""
    await kb_folder_service.delete_folder(db, folder_id, current_user['username'])
    return success_response({"message": "目录删除成功"})


# ==================== 目录文档管理 ====================

@router.get("/knowledge-bases/{kb_id}/folders/{folder_id}/documents")
async def get_folder_documents(
    kb_id: str,
    folder_id: Optional[str] = None,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """获取目录下的文档列表
    
    folder_id为None时获取根目录文档
    """
    result = await kb_folder_service.get_folder_documents(
        db, kb_id, folder_id, current_user['username'], page, page_size
    )
    return paginated_response(**result)


@router.post("/knowledge-bases/{kb_id}/folders/{folder_id}/documents")
async def add_document_to_folder(
    kb_id: str,
    folder_id: Optional[str],
    move_data: DocumentMoveRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """添加文档到目录（拖拽功能）"""
    await kb_folder_service.add_document_to_folder(
        db, kb_id, move_data.dict().get('file_id'), folder_id,
        move_data.dict(), current_user['username']
    )
    return success_response({"message": "文档移动成功"})


# ==================== 权限管理 ====================

@router.post("/knowledge-bases/{kb_id}/permissions")
async def grant_permission(
    kb_id: str,
    permission_data: PermissionGrantRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    """授予知识库权限"""
    await kb_service.grant_permission(
        db, kb_id, permission_data.user_id,
        permission_data.permission_type, current_user['username']
    )
    return success_response({"message": "权限授予成功"})