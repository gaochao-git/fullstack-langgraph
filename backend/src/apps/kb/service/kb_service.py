"""
知识库管理服务
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func

from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.db.models import now_shanghai
from ..models import KnowledgeBase, KBDocument, KBPermission, KBFolder
from ...agent.models import AgentDocumentUpload

logger = get_logger(__name__)


class KnowledgeBaseService:
    """知识库管理服务"""
    
    async def create_kb(
        self, 
        db: AsyncSession, 
        kb_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """创建知识库"""
        async with db.begin():
            kb_id = str(uuid.uuid4())
            
            # 处理标签
            tags_json = json.dumps(kb_data.get('tags', []), ensure_ascii=False)
            settings_json = json.dumps({
                'search_config': {},
                'permission_config': {}
            }, ensure_ascii=False)
            
            kb = KnowledgeBase(
                kb_id=kb_id,
                kb_name=kb_data['kb_name'],
                kb_description=kb_data.get('kb_description'),
                kb_type=kb_data.get('kb_type', 'general'),
                visibility=kb_data.get('visibility', 'private'),
                owner_id=user_id,
                department=kb_data.get('department'),
                tags=tags_json,
                settings=settings_json,
                create_by=user_id,
                update_by=user_id
            )
            
            db.add(kb)
            await db.flush()
            await db.refresh(kb)
            
            # 自动给创建者管理员权限
            await self._grant_permission_internal(
                db, kb_id, user_id, 'admin', user_id
            )
            
            logger.info(f"知识库创建成功: {kb_data['kb_name']} by {user_id}")
            return self._kb_to_dict(kb)
    
    async def get_user_kbs(
        self, 
        db: AsyncSession, 
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户可访问的知识库"""
        offset = (page - 1) * page_size
        
        # 查询用户可访问的知识库（所有者 + 有权限的 + 公开的）
        query = select(
            KnowledgeBase,
            KBPermission.permission_type
        ).outerjoin(
            KBPermission,
            and_(
                KnowledgeBase.kb_id == KBPermission.kb_id,
                KBPermission.user_id == user_id
            )
        ).where(
            and_(
                KnowledgeBase.kb_status == 1,  # 启用状态
                or_(
                    KnowledgeBase.owner_id == user_id,  # 所有者
                    KBPermission.permission_type.isnot(None),  # 有权限
                    KnowledgeBase.visibility == 'public'  # 公开
                )
            )
        ).order_by(KnowledgeBase.update_time.desc())
        
        # 分页查询
        result = await db.execute(query.offset(offset).limit(page_size))
        rows = result.all()
        
        # 统计总数
        count_query = select(func.count()).select_from(
            select(KnowledgeBase.id).outerjoin(
                KBPermission,
                and_(
                    KnowledgeBase.kb_id == KBPermission.kb_id,
                    KBPermission.user_id == user_id
                )
            ).where(
                and_(
                    KnowledgeBase.kb_status == 1,
                    or_(
                        KnowledgeBase.owner_id == user_id,
                        KBPermission.permission_type.isnot(None),
                        KnowledgeBase.visibility == 'public'
                    )
                )
            ).subquery()
        )
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 格式化结果
        kbs = []
        for kb, permission in rows:
            kb_dict = self._kb_to_dict(kb)
            kb_dict['user_permission'] = permission or 'owner' if kb.owner_id == user_id else 'read'
            
            # 检查知识库是否有子目录
            folder_count_result = await db.execute(
                select(func.count()).select_from(KBFolder)
                .where(
                    and_(
                        KBFolder.kb_id == kb.kb_id,
                        KBFolder.parent_folder_id.is_(None)  # 只检查根目录
                    )
                )
            )
            folder_count = folder_count_result.scalar()
            kb_dict['has_folders'] = folder_count > 0
            
            kbs.append(kb_dict)
        
        return {
            'items': kbs,
            'total': total,
            'page': page,
            'size': page_size
        }
    
    async def get_kb_by_id(
        self, 
        db: AsyncSession, 
        kb_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """根据ID获取知识库"""
        # 检查权限
        if not await self._check_permission(db, kb_id, user_id, 'read'):
            raise BusinessException("无权限访问此知识库", ResponseCode.FORBIDDEN)
        
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.kb_id == kb_id)
        )
        kb = result.scalar_one_or_none()
        
        if not kb:
            return None
        
        return self._kb_to_dict(kb)
    
    async def update_kb(
        self, 
        db: AsyncSession, 
        kb_id: str, 
        update_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """更新知识库"""
        async with db.begin():
            # 检查权限
            if not await self._check_permission(db, kb_id, user_id, 'admin'):
                raise BusinessException("无权限修改此知识库", ResponseCode.FORBIDDEN)
            
            result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.kb_id == kb_id)
            )
            kb = result.scalar_one_or_none()
            
            if not kb:
                raise BusinessException("知识库不存在", ResponseCode.NOT_FOUND)
            
            # 更新字段
            if 'kb_name' in update_data:
                kb.kb_name = update_data['kb_name']
            if 'kb_description' in update_data:
                kb.kb_description = update_data['kb_description']
            if 'kb_type' in update_data:
                kb.kb_type = update_data['kb_type']
            if 'visibility' in update_data:
                kb.visibility = update_data['visibility']
            if 'department' in update_data:
                kb.department = update_data['department']
            if 'tags' in update_data:
                kb.tags = json.dumps(update_data['tags'], ensure_ascii=False)
            
            kb.update_by = user_id
            
            await db.flush()
            await db.refresh(kb)
            
            logger.info(f"知识库更新成功: {kb_id} by {user_id}")
            return self._kb_to_dict(kb)
    
    async def delete_kb(
        self, 
        db: AsyncSession, 
        kb_id: str, 
        user_id: str
    ) -> bool:
        """删除知识库"""
        async with db.begin():
            # 检查权限
            if not await self._check_permission(db, kb_id, user_id, 'admin'):
                raise BusinessException("无权限删除此知识库", ResponseCode.FORBIDDEN)
            
            # 检查是否存在
            result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.kb_id == kb_id)
            )
            kb = result.scalar_one_or_none()
            
            if not kb:
                raise BusinessException("知识库不存在", ResponseCode.NOT_FOUND)
            
            # 软删除：更新状态
            kb.kb_status = 0
            kb.update_by = user_id
            
            await db.flush()
            
            logger.info(f"知识库删除成功: {kb_id} by {user_id}")
            return True
    
    async def add_document_to_kb(
        self,
        db: AsyncSession,
        kb_id: str,
        file_id: str,
        doc_data: Dict[str, Any],
        user_id: str
    ) -> bool:
        """将文档添加到知识库"""
        async with db.begin():
            # 检查权限
            if not await self._check_permission(db, kb_id, user_id, 'write'):
                raise BusinessException("无权限添加文档", ResponseCode.FORBIDDEN)
            # 检查文档是否存在且向量已生成
            doc_result = await db.execute(
                select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
            )
            doc = doc_result.scalar_one_or_none()
            
            if not doc:
                raise BusinessException("文档不存在", ResponseCode.NOT_FOUND)
            
            # 检查是否已添加到此知识库
            existing_result = await db.execute(
                select(KBDocument).where(
                    and_(
                        KBDocument.kb_id == kb_id,
                        KBDocument.file_id == file_id
                    )
                )
            )
            if existing_result.scalar_one_or_none():
                raise BusinessException("文档已在此知识库中", ResponseCode.BAD_REQUEST)
            
            # 添加到知识库
            kb_doc = KBDocument(
                kb_id=kb_id,
                file_id=file_id,
                doc_title=doc_data.get('doc_title') or doc.file_name,
                doc_category=doc_data.get('doc_category'),
                create_by=user_id,
                update_by=user_id
            )
            
            db.add(kb_doc)
            
            # 更新知识库文档计数
            await self._update_kb_stats(db, kb_id)
            
            await db.flush()
            
            logger.info(f"文档添加到知识库成功: {file_id} -> {kb_id} by {user_id}")
            return True
    
    async def remove_document_from_kb(
        self,
        db: AsyncSession,
        kb_id: str,
        file_id: str,
        user_id: str
    ) -> bool:
        """从知识库移除文档"""
        async with db.begin():
            # 检查权限
            if not await self._check_permission(db, kb_id, user_id, 'write'):
                raise BusinessException("无权限移除文档", ResponseCode.FORBIDDEN)
            result = await db.execute(
                delete(KBDocument).where(
                    and_(
                        KBDocument.kb_id == kb_id,
                        KBDocument.file_id == file_id
                    )
                )
            )
            
            if result.rowcount == 0:
                raise BusinessException("文档不在此知识库中", ResponseCode.NOT_FOUND)
            
            # 更新知识库统计
            await self._update_kb_stats(db, kb_id)
            
            logger.info(f"文档从知识库移除成功: {file_id} <- {kb_id} by {user_id}")
            return True
    
    async def get_kb_documents(
        self,
        db: AsyncSession,
        kb_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取知识库文档列表"""
        # 检查权限
        if not await self._check_permission(db, kb_id, user_id, 'read'):
            raise BusinessException("无权限访问此知识库", ResponseCode.FORBIDDEN)
        
        offset = (page - 1) * page_size
        
        # 查询知识库文档
        query = select(
            KBDocument,
            AgentDocumentUpload.file_name,
            AgentDocumentUpload.file_size,
            AgentDocumentUpload.file_type,
            AgentDocumentUpload.process_status,
            AgentDocumentUpload.create_time
        ).join(
            AgentDocumentUpload,
            KBDocument.file_id == AgentDocumentUpload.file_id
        ).where(
            and_(
                KBDocument.kb_id == kb_id,
                KBDocument.doc_status == 1
            )
        ).order_by(KBDocument.create_time.desc())
        
        # 分页
        result = await db.execute(query.offset(offset).limit(page_size))
        rows = result.all()
        
        # 总数
        count_result = await db.execute(
            select(func.count()).select_from(KBDocument).where(
                and_(
                    KBDocument.kb_id == kb_id,
                    KBDocument.doc_status == 1
                )
            )
        )
        total = count_result.scalar()
        
        # 格式化结果
        documents = []
        for row in rows:
            kb_doc, file_name, file_size, file_type, process_status, doc_create_time = row
            documents.append({
                'file_id': kb_doc.file_id,
                'file_name': file_name,
                'doc_title': kb_doc.doc_title,
                'doc_category': kb_doc.doc_category,
                'file_size': file_size,
                'file_type': file_type,
                'process_status': process_status,
                'doc_status': kb_doc.doc_status,
                'create_time': kb_doc.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'add_by': kb_doc.create_by
            })
        
        return {
            'items': documents,
            'total': total,
            'page': page,
            'size': page_size
        }
    
    async def grant_permission(
        self,
        db: AsyncSession,
        kb_id: str,
        target_user_id: str,
        permission_type: str,
        user_id: str
    ) -> bool:
        """授予权限"""
        async with db.begin():
            # 检查权限
            if not await self._check_permission(db, kb_id, user_id, 'admin'):
                raise BusinessException("无权限管理此知识库权限", ResponseCode.FORBIDDEN)
            await self._grant_permission_internal(
                db, kb_id, target_user_id, permission_type, user_id
            )
            
            logger.info(f"权限授予成功: {target_user_id} -> {permission_type} on {kb_id} by {user_id}")
            return True
    
    async def _grant_permission_internal(
        self,
        db: AsyncSession,
        kb_id: str,
        target_user_id: str,
        permission_type: str,
        granted_by: str
    ):
        """内部权限授予方法"""
        # 检查是否已有权限
        existing_result = await db.execute(
            select(KBPermission).where(
                and_(
                    KBPermission.kb_id == kb_id,
                    KBPermission.user_id == target_user_id
                )
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # 更新权限
            existing.permission_type = permission_type
            existing.granted_by = granted_by
            existing.granted_time = now_shanghai()
            existing.update_by = granted_by
        else:
            # 创建新权限
            permission = KBPermission(
                kb_id=kb_id,
                user_id=target_user_id,
                permission_type=permission_type,
                granted_by=granted_by,
                create_by=granted_by,
                update_by=granted_by
            )
            db.add(permission)
        
        await db.flush()
    
    async def _check_permission(
        self,
        db: AsyncSession,
        kb_id: str,
        user_id: str,
        required_permission: str
    ) -> bool:
        """检查用户权限"""
        # 权限等级
        permission_levels = {'read': 1, 'write': 2, 'admin': 3}
        required_level = permission_levels.get(required_permission, 0)
        
        # 查询知识库和权限
        result = await db.execute(
            select(
                KnowledgeBase,
                KBPermission.permission_type
            ).outerjoin(
                KBPermission,
                and_(
                    KnowledgeBase.kb_id == KBPermission.kb_id,
                    KBPermission.user_id == user_id
                )
            ).where(KnowledgeBase.kb_id == kb_id)
        )
        
        row = result.first()
        if not row:
            return False
        
        kb, user_permission = row
        
        # 所有者拥有所有权限
        if kb.owner_id == user_id:
            return True
        
        # 公开知识库的读权限
        if kb.visibility == 'public' and required_permission == 'read':
            return True
        
        # 检查用户权限
        if user_permission:
            user_level = permission_levels.get(user_permission, 0)
            return user_level >= required_level
        
        return False
    
    async def _update_kb_stats(self, db: AsyncSession, kb_id: str):
        """更新知识库统计信息"""
        # 统计文档数
        doc_count_result = await db.execute(
            select(func.count()).select_from(KBDocument).where(
                and_(
                    KBDocument.kb_id == kb_id,
                    KBDocument.doc_status == 1
                )
            )
        )
        doc_count = doc_count_result.scalar()
        
        # 更新知识库统计
        await db.execute(
            update(KnowledgeBase)
            .where(KnowledgeBase.kb_id == kb_id)
            .values(doc_count=doc_count)
        )
    
    def _kb_to_dict(self, kb: KnowledgeBase) -> Dict[str, Any]:
        """知识库模型转字典"""
        kb_dict = kb.to_dict()
        
        # 处理JSON字段
        try:
            kb_dict['tags'] = json.loads(kb.tags) if kb.tags else []
        except (json.JSONDecodeError, TypeError):
            kb_dict['tags'] = []
        
        try:
            kb_dict['settings'] = json.loads(kb.settings) if kb.settings else {}
        except (json.JSONDecodeError, TypeError):
            kb_dict['settings'] = {}
        
        return kb_dict


# 全局服务实例
kb_service = KnowledgeBaseService()