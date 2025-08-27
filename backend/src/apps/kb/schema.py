"""
知识库模块 Pydantic Schema
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==================== 请求模型 ====================

class KBCreateRequest(BaseModel):
    """知识库创建请求"""
    kb_name: str = Field(..., description="知识库名称")
    kb_description: Optional[str] = Field(None, description="知识库描述")
    kb_type: str = Field(default='general', description="知识库类型")
    visibility: str = Field(default='private', description="可见性")
    department: Optional[str] = Field(None, description="部门")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")


class KBUpdateRequest(BaseModel):
    """知识库更新请求"""
    kb_name: Optional[str] = Field(None, description="知识库名称")
    kb_description: Optional[str] = Field(None, description="知识库描述")
    kb_type: Optional[str] = Field(None, description="知识库类型")
    visibility: Optional[str] = Field(None, description="可见性")
    department: Optional[str] = Field(None, description="部门")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class FolderCreateRequest(BaseModel):
    """目录创建请求"""
    folder_name: str = Field(..., description="目录名称")
    parent_folder_id: Optional[str] = Field(None, description="父目录ID")
    folder_description: Optional[str] = Field(None, description="目录描述")


class FolderUpdateRequest(BaseModel):
    """目录更新请求"""
    folder_name: Optional[str] = Field(None, description="目录名称")
    folder_description: Optional[str] = Field(None, description="目录描述")
    sort_order: Optional[int] = Field(None, description="排序权重")


class DocumentMoveRequest(BaseModel):
    """文档移动请求"""
    target_folder_id: Optional[str] = Field(None, description="目标目录ID，NULL表示根目录")


class DocumentAddRequest(BaseModel):
    """添加文档到知识库请求"""
    file_id: str = Field(..., description="文件ID")
    doc_title: Optional[str] = Field(None, description="文档标题")
    doc_category: Optional[str] = Field(None, description="文档分类")
    folder_id: Optional[str] = Field(None, description="目录ID")


class PermissionGrantRequest(BaseModel):
    """权限授予请求"""
    user_id: str = Field(..., description="用户ID")
    permission_type: str = Field(..., description="权限类型: read, write, admin")
    expire_time: Optional[str] = Field(None, description="过期时间")


class KBSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., description="搜索查询")
    kb_ids: Optional[List[str]] = Field(None, description="指定知识库ID列表")
    limit: int = Field(default=10, description="返回结果数量")
    score_threshold: float = Field(default=0.7, description="相似度阈值")


# ==================== 响应模型 ====================

class KBResponse(BaseModel):
    """知识库响应"""
    kb_id: str
    kb_name: str
    kb_description: Optional[str]
    kb_type: str
    kb_status: int
    visibility: str
    owner_id: str
    department: Optional[str]
    tags: List[str]
    doc_count: int
    total_chunks: int
    create_by: str
    create_time: str
    update_time: str
    
    # 权限信息（动态添加）
    user_permission: Optional[str] = None


class FolderResponse(BaseModel):
    """目录响应"""
    folder_id: str
    kb_id: str
    parent_folder_id: Optional[str]
    folder_name: str
    folder_description: Optional[str]
    folder_type: str
    sort_order: int
    create_by: str
    create_time: str
    
    # 子目录
    children: Optional[List['FolderResponse']] = None


class DocumentResponse(BaseModel):
    """文档响应"""
    file_id: str
    file_name: str
    doc_title: Optional[str]
    doc_category: Optional[str]
    doc_status: int
    file_size: int
    file_type: str
    process_status: int
    vector_status: int
    display_name: Optional[str]
    is_pinned: bool
    sort_order: int
    create_time: str


class SearchResultResponse(BaseModel):
    """搜索结果响应"""
    file_id: str
    file_name: str
    kb_id: str
    kb_name: str
    chunk_text: str
    similarity: float
    chunk_metadata: Optional[Dict[str, Any]]


class FolderTreeResponse(BaseModel):
    """目录树响应"""
    tree: List[FolderResponse]


class KBStatsResponse(BaseModel):
    """知识库统计响应"""
    total_kbs: int
    total_docs: int
    total_chunks: int
    kb_types: Dict[str, int]


# 更新前向引用
FolderResponse.model_rebuild()