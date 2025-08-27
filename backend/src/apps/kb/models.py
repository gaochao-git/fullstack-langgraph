"""
知识库模块数据模型
"""
import json
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, BigInteger
from sqlalchemy.sql import func
from src.shared.db.models import BaseModel, now_shanghai


class KnowledgeBase(BaseModel):
    """知识库模型"""
    __tablename__ = "knowledge_bases"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    kb_id = Column(String(36), unique=True, nullable=False, comment="知识库唯一标识")
    kb_name = Column(String(255), nullable=False, comment="知识库名称")
    kb_description = Column(Text, comment="知识库描述")
    kb_type = Column(String(50), default='general', comment="知识库类型")
    kb_status = Column(Integer, default=1, comment="状态: 1-启用, 0-禁用")
    visibility = Column(String(20), default='private', comment="可见性")
    
    # 业务字段
    owner_id = Column(String(100), nullable=False, comment="所有者用户名")
    department = Column(String(100), comment="部门")
    tags = Column(Text, comment="标签(JSON格式)")
    settings = Column(Text, comment="设置(JSON格式)")
    
    # 统计字段
    doc_count = Column(Integer, default=0, comment="文档数量")
    total_chunks = Column(Integer, default=0, comment="总分块数")
    
    # 标准字段
    create_by = Column(String(100), nullable=False, comment="创建人")
    update_by = Column(String(100), comment="更新人")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)
    
    def _process_tags(self, value):
        """处理标签字段"""
        return self._parse_json_field(value, default=[])
    
    def _process_settings(self, value):
        """处理设置字段"""
        return self._parse_json_field(value, default={})


class KBFolder(BaseModel):
    """知识库目录模型"""
    __tablename__ = "kb_folders"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    folder_id = Column(String(36), unique=True, nullable=False, comment="目录唯一标识")
    kb_id = Column(String(36), nullable=False, comment="所属知识库ID")
    parent_folder_id = Column(String(36), comment="父目录ID")
    
    folder_name = Column(String(255), nullable=False, comment="目录名称")
    folder_description = Column(Text, comment="目录描述")
    folder_type = Column(String(50), default='folder', comment="目录类型")
    sort_order = Column(Integer, default=0, comment="排序权重")
    
    # 权限继承
    inherit_permissions = Column(Boolean, default=True, comment="是否继承权限")
    custom_permissions = Column(Text, comment="自定义权限(JSON格式)")
    
    # 标准字段
    create_by = Column(String(100), nullable=False, comment="创建人")
    update_by = Column(String(100), comment="更新人")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)
    
    def _process_custom_permissions(self, value):
        """处理自定义权限字段"""
        return self._parse_json_field(value, default={})


class KBDocument(BaseModel):
    """知识库文档关联模型"""
    __tablename__ = "kb_documents"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    kb_id = Column(String(36), nullable=False, comment="知识库ID")
    file_id = Column(String(36), nullable=False, comment="文件ID")
    
    # 文档在知识库中的属性
    doc_title = Column(String(500), comment="文档标题")
    doc_category = Column(String(100), comment="文档分类")
    doc_priority = Column(Integer, default=0, comment="权重")
    doc_status = Column(Integer, default=1, comment="状态")
    
    # 移除版本管理字段
    
    # 标准字段
    create_by = Column(String(100), nullable=False, comment="添加人")
    update_by = Column(String(100), comment="更新人")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)


class KBDocumentFolder(BaseModel):
    """文档目录关联模型"""
    __tablename__ = "kb_document_folders"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    kb_id = Column(String(36), nullable=False, comment="知识库ID")
    file_id = Column(String(36), nullable=False, comment="文件ID")
    folder_id = Column(String(36), comment="目录ID")
    
    # 在目录中的属性
    display_name = Column(String(255), comment="显示名")
    sort_order = Column(Integer, default=0, comment="排序权重")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    
    # 标准字段
    create_by = Column(String(100), nullable=False, comment="操作人")
    update_by = Column(String(100), comment="更新人")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)


class KBPermission(BaseModel):
    """知识库权限模型"""
    __tablename__ = "kb_permissions"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    kb_id = Column(String(36), nullable=False, comment="知识库ID")
    user_id = Column(String(100), nullable=False, comment="用户ID")
    permission_type = Column(String(20), nullable=False, comment="权限类型")
    
    # 权限来源
    granted_by = Column(String(100), comment="授权人")
    granted_time = Column(DateTime, default=now_shanghai, comment="授权时间")
    expire_time = Column(DateTime, comment="过期时间")
    
    # 标准字段
    create_by = Column(String(100), nullable=False, comment="创建人")
    update_by = Column(String(100), comment="更新人")
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai)