"""
知识库目录管理服务
基于邻接列表模型（adjacency list）实现树形结构
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
from ..models import KBFolder, KBDocument, KBDocumentFolder, KnowledgeBase
from .kb_service import KnowledgeBaseService

logger = get_logger(__name__)


class KBFolderService:
    """知识库目录管理服务
    
    使用邻接列表模型（adjacency list）存储树形结构：
    - 每个节点存储指向父节点的引用（parent_folder_id）
    - 树的构建通过遍历所有节点并根据父子关系组装
    - 这是业界标准的关系型数据库树存储方案
    """
    
    # 目录最大层级深度（不包括知识库根层级）
    MAX_FOLDER_DEPTH = 4
    
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
    
    async def _get_folder_depth(self, db: AsyncSession, folder_id: str) -> int:
        """获取目录的层级深度"""
        depth = 0
        current_folder_id = folder_id
        
        while current_folder_id:
            result = await db.execute(
                select(KBFolder.parent_folder_id)
                .where(KBFolder.folder_id == current_folder_id)
            )
            parent_id = result.scalar_one_or_none()
            if parent_id:
                depth += 1
                current_folder_id = parent_id
            else:
                break
                
        return depth

    async def create_folder(
        self,
        db: AsyncSession,
        kb_id: str,
        folder_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """创建目录"""
        async with db.begin():
            # 检查知识库权限
            if not await self.kb_service._check_permission(db, kb_id, user_id, 'write'):
                raise BusinessException("无权限在此知识库创建目录", ResponseCode.FORBIDDEN)
            folder_id = str(uuid.uuid4())
            parent_folder_id = folder_data.get('parent_folder_id')
            
            # 验证父目录是否存在且属于同一知识库
            if parent_folder_id:
                parent_result = await db.execute(
                    select(KBFolder).where(
                        and_(
                            KBFolder.folder_id == parent_folder_id,
                            KBFolder.kb_id == kb_id
                        )
                    )
                )
                parent_folder = parent_result.scalar_one_or_none()
                if not parent_folder:
                    raise BusinessException("父目录不存在", ResponseCode.NOT_FOUND)
                
                # 检查层级深度限制
                parent_depth = await self._get_folder_depth(db, parent_folder_id)
                if parent_depth >= self.MAX_FOLDER_DEPTH:
                    raise BusinessException(f"目录层级深度不能超过{self.MAX_FOLDER_DEPTH}层", ResponseCode.BAD_REQUEST)
            
            folder = KBFolder(
                folder_id=folder_id,
                kb_id=kb_id,
                parent_folder_id=parent_folder_id,
                folder_name=folder_data['folder_name'],
                folder_description=folder_data.get('folder_description'),
                folder_type=folder_data.get('folder_type', 'folder'),
                sort_order=folder_data.get('sort_order', 0),
                create_by=user_id,
                update_by=user_id
            )
            
            db.add(folder)
            await db.flush()
            await db.refresh(folder)
        
        logger.info(f"目录创建成功: {folder_data['folder_name']} in {kb_id} by {user_id}")
        return self._folder_to_dict(folder)
    
    async def get_folder_tree_optimized(
        self,
        db: AsyncSession,
        kb_id: str,
        user_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """获取知识库目录树（简化版本，移除JSON缓存复杂性）"""
        # 检查权限
        if not await self.kb_service._check_permission(db, kb_id, user_id, 'read'):
            raise BusinessException("无权限访问此知识库", ResponseCode.FORBIDDEN)
        
        # 直接构建树结构（基于父子ID关系的邻接列表模型）
        tree = await self._build_tree_structure(db, kb_id)
        
        return {
            "tree": tree,
            "from_cache": False,
            "has_children": len(tree) > 0
        }

    async def get_folder_tree(
        self,
        db: AsyncSession,
        kb_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """获取知识库目录树（保持向后兼容）"""
        result = await self.get_folder_tree_optimized(db, kb_id, user_id)
        return result["tree"]
    
    async def _build_tree_structure(
        self,
        db: AsyncSession,
        kb_id: str
    ) -> List[Dict[str, Any]]:
        """构建目录树结构（邻接列表模型实现）
        
        算法步骤：
        1. 获取知识库下的所有目录节点
        2. 创建节点映射表（folder_id -> node_dict）
        3. 遍历所有节点，根据 parent_folder_id 建立父子关系
        4. 返回所有根节点（parent_folder_id 为空的节点）
        """
        # 获取所有目录
        result = await db.execute(
            select(KBFolder).where(KBFolder.kb_id == kb_id)
            .order_by(KBFolder.sort_order, KBFolder.folder_name)
        )
        folders = result.scalars().all()
        
        # 获取每个文件夹的文件数量
        folder_file_counts = {}
        if folders:
            folder_ids = [f.folder_id for f in folders]
            # 统计每个文件夹下的文件数量
            file_count_result = await db.execute(
                select(
                    KBDocumentFolder.folder_id,
                    func.count(KBDocumentFolder.file_id).label('file_count')
                )
                .where(KBDocumentFolder.folder_id.in_(folder_ids))
                .group_by(KBDocumentFolder.folder_id)
            )
            for folder_id, count in file_count_result:
                folder_file_counts[folder_id] = count
        
        # 构建树形结构
        folder_map = {}
        root_folders = []
        
        # 步骤1: 先创建所有节点的映射
        for folder in folders:
            folder_dict = self._folder_to_dict(folder)
            folder_dict['children'] = []
            folder_dict['file_count'] = folder_file_counts.get(folder.folder_id, 0)
            folder_map[folder.folder_id] = folder_dict
        
        # 步骤2: 构建父子关系（邻接列表转换为树）
        for folder in folders:
            folder_dict = folder_map[folder.folder_id]
            if folder.parent_folder_id and folder.parent_folder_id in folder_map:
                # 添加到父目录的children中
                folder_map[folder.parent_folder_id]['children'].append(folder_dict)
            else:
                # 根目录（parent_folder_id为空）
                root_folders.append(folder_dict)
        
        return root_folders
    
    # 移除JSON缓存方法 - 邻接列表模型已经足够高效
    
    async def update_folder(
        self,
        db: AsyncSession,
        folder_id: str,
        update_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """更新目录"""
        async with db.begin():
            # 获取目录信息
            result = await db.execute(
                select(KBFolder).where(KBFolder.folder_id == folder_id)
            )
            folder = result.scalar_one_or_none()
            
            if not folder:
                raise BusinessException("目录不存在", ResponseCode.NOT_FOUND)
            
            # 检查权限
            if not await self.kb_service._check_permission(db, folder.kb_id, user_id, 'write'):
                raise BusinessException("无权限修改此目录", ResponseCode.FORBIDDEN)
            
            # 更新字段
            if 'folder_name' in update_data:
                folder.folder_name = update_data['folder_name']
            if 'folder_description' in update_data:
                folder.folder_description = update_data['folder_description']
            if 'sort_order' in update_data:
                folder.sort_order = update_data['sort_order']
            
            folder.update_by = user_id
            
            await db.flush()
            await db.refresh(folder)
            
            logger.info(f"目录更新成功: {folder_id} by {user_id}")
            return self._folder_to_dict(folder)
    
    async def move_folder(
        self,
        db: AsyncSession,
        folder_id: str,
        target_parent_id: Optional[str],
        user_id: str
    ) -> bool:
        """移动目录"""
        async with db.begin():
            # 获取目录信息
            result = await db.execute(
                select(KBFolder).where(KBFolder.folder_id == folder_id)
            )
            folder = result.scalar_one_or_none()
            
            if not folder:
                raise BusinessException("目录不存在", ResponseCode.NOT_FOUND)
            
            # 检查权限
            if not await self.kb_service._check_permission(db, folder.kb_id, user_id, 'write'):
                raise BusinessException("无权限移动此目录", ResponseCode.FORBIDDEN)
            
            # 防止循环引用
            if target_parent_id and await self._would_create_cycle(db, folder_id, target_parent_id):
                raise BusinessException("不能移动到自己的子目录", ResponseCode.BAD_REQUEST)
            
            # 验证目标父目录
            if target_parent_id:
                parent_result = await db.execute(
                    select(KBFolder).where(
                        and_(
                            KBFolder.folder_id == target_parent_id,
                            KBFolder.kb_id == folder.kb_id
                        )
                    )
                )
                if not parent_result.scalar_one_or_none():
                    raise BusinessException("目标父目录不存在", ResponseCode.NOT_FOUND)
            
            # 执行移动
            folder.parent_folder_id = target_parent_id
            folder.update_by = user_id
            
            await db.flush()
            
            logger.info(f"目录移动成功: {folder_id} -> {target_parent_id} by {user_id}")
            return True
    
    async def delete_folder(
        self,
        db: AsyncSession,
        folder_id: str,
        user_id: str
    ) -> bool:
        """删除目录（级联删除子目录）"""
        async with db.begin():
            # 获取目录信息
            result = await db.execute(
                select(KBFolder).where(KBFolder.folder_id == folder_id)
            )
            folder = result.scalar_one_or_none()
            
            if not folder:
                raise BusinessException("目录不存在", ResponseCode.NOT_FOUND)
            
            # 检查权限
            if not await self.kb_service._check_permission(db, folder.kb_id, user_id, 'write'):
                raise BusinessException("无权限删除此目录", ResponseCode.FORBIDDEN)
            
            # 获取所有子目录（递归）
            all_folder_ids = await self._get_all_child_folders(db, folder_id)
            all_folder_ids.add(folder_id)
            
            # 检查是否有文档
            doc_result = await db.execute(
                select(func.count()).select_from(KBDocumentFolder)
                .where(KBDocumentFolder.folder_id.in_(all_folder_ids))
            )
            doc_count = doc_result.scalar()
            
            if doc_count > 0:
                raise BusinessException("目录中包含文档，无法删除", ResponseCode.BAD_REQUEST)
            
            # 删除所有相关目录
            await db.execute(
                delete(KBFolder).where(KBFolder.folder_id.in_(all_folder_ids))
            )
            
            logger.info(f"目录删除成功: {folder_id} (包含{len(all_folder_ids)}个目录) by {user_id}")
            return True
    
    async def add_document_to_folder(
        self,
        db: AsyncSession,
        kb_id: str,
        file_id: str,
        folder_id: Optional[str],
        doc_data: Dict[str, Any],
        user_id: str
    ) -> bool:
        """添加文档到目录"""
        async with db.begin():
            # 检查权限
            if not await self.kb_service._check_permission(db, kb_id, user_id, 'write'):
                raise BusinessException("无权限操作此知识库", ResponseCode.FORBIDDEN)
            # 验证目录是否存在且属于同一知识库
            if folder_id:
                folder_result = await db.execute(
                    select(KBFolder).where(
                        and_(
                            KBFolder.folder_id == folder_id,
                            KBFolder.kb_id == kb_id
                        )
                    )
                )
                if not folder_result.scalar_one_or_none():
                    raise BusinessException("目录不存在", ResponseCode.NOT_FOUND)
            
            # 检查文档是否已在知识库中
            kb_doc_result = await db.execute(
                select(KBDocument).where(
                    and_(
                        KBDocument.kb_id == kb_id,
                        KBDocument.file_id == file_id
                    )
                )
            )
            if not kb_doc_result.scalar_one_or_none():
                raise BusinessException("文档未添加到知识库", ResponseCode.NOT_FOUND)
            
            # 检查是否已在目录中
            existing_result = await db.execute(
                select(KBDocumentFolder).where(
                    and_(
                        KBDocumentFolder.kb_id == kb_id,
                        KBDocumentFolder.file_id == file_id
                    )
                )
            )
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                # 更新目录位置
                existing.folder_id = folder_id
                existing.display_name = doc_data.get('display_name')
                existing.sort_order = doc_data.get('sort_order', 0)
                existing.is_pinned = doc_data.get('is_pinned', False)
                existing.update_by = user_id
            else:
                # 创建新的目录关联
                doc_folder = KBDocumentFolder(
                    kb_id=kb_id,
                    file_id=file_id,
                    folder_id=folder_id,
                    display_name=doc_data.get('display_name'),
                    sort_order=doc_data.get('sort_order', 0),
                    is_pinned=doc_data.get('is_pinned', False),
                    create_by=user_id,
                    update_by=user_id
                )
                db.add(doc_folder)
            
            await db.flush()
            
            logger.info(f"文档添加到目录成功: {file_id} -> {folder_id or 'root'} by {user_id}")
            return True
    
    async def get_folder_documents(
        self,
        db: AsyncSession,
        kb_id: str,
        folder_id: Optional[str],
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取目录下的文档"""
        # 检查权限
        if not await self.kb_service._check_permission(db, kb_id, user_id, 'read'):
            raise BusinessException("无权限访问此知识库", ResponseCode.FORBIDDEN)
        
        offset = (page - 1) * page_size
        
        # 构建查询条件
        folder_condition = KBDocumentFolder.folder_id == folder_id
        if folder_id is None:
            folder_condition = KBDocumentFolder.folder_id.is_(None)
        
        # 查询文档
        from ...agent.models import AgentDocumentUpload
        
        query = select(
            KBDocumentFolder,
            AgentDocumentUpload.file_name,
            AgentDocumentUpload.file_size,
            AgentDocumentUpload.file_type,
            AgentDocumentUpload.process_status,
            KBDocument.doc_status
        ).join(
            AgentDocumentUpload,
            KBDocumentFolder.file_id == AgentDocumentUpload.file_id
        ).join(
            KBDocument,
            and_(
                KBDocument.kb_id == KBDocumentFolder.kb_id,
                KBDocument.file_id == KBDocumentFolder.file_id
            )
        ).where(
            and_(
                KBDocumentFolder.kb_id == kb_id,
                folder_condition,
                KBDocument.doc_status == 1
            )
        ).order_by(
            KBDocumentFolder.is_pinned.desc(),
            KBDocumentFolder.sort_order,
            KBDocumentFolder.create_time.desc()
        )
        
        # 分页
        result = await db.execute(query.offset(offset).limit(page_size))
        rows = result.all()
        
        # 统计总数
        count_query = select(func.count()).select_from(
            select(KBDocumentFolder.id).join(
                KBDocument,
                and_(
                    KBDocument.kb_id == KBDocumentFolder.kb_id,
                    KBDocument.file_id == KBDocumentFolder.file_id
                )
            ).where(
                and_(
                    KBDocumentFolder.kb_id == kb_id,
                    folder_condition,
                    KBDocument.doc_status == 1
                )
            ).subquery()
        )
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 格式化结果
        documents = []
        for row in rows:
            doc_folder, file_name, file_size, file_type, process_status, doc_status = row
            documents.append({
                'file_id': doc_folder.file_id,
                'file_name': file_name,
                'display_name': doc_folder.display_name or file_name,
                'file_size': file_size,
                'file_type': file_type,
                'process_status': process_status,
                'doc_status': doc_status,
                'is_pinned': doc_folder.is_pinned,
                'sort_order': doc_folder.sort_order,
                'create_time': doc_folder.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return {
            'items': documents,
            'total': total,
            'page': page,
            'size': page_size
        }
    
    async def _would_create_cycle(
        self,
        db: AsyncSession,
        folder_id: str,
        target_parent_id: str
    ) -> bool:
        """检查是否会创建循环引用"""
        current_parent = target_parent_id
        
        while current_parent:
            if current_parent == folder_id:
                return True
            
            result = await db.execute(
                select(KBFolder.parent_folder_id)
                .where(KBFolder.folder_id == current_parent)
            )
            current_parent = result.scalar_one_or_none()
        
        return False
    
    async def _get_all_child_folders(
        self,
        db: AsyncSession,
        folder_id: str
    ) -> set:
        """递归获取所有子目录ID"""
        child_ids = set()
        
        result = await db.execute(
            select(KBFolder.folder_id)
            .where(KBFolder.parent_folder_id == folder_id)
        )
        direct_children = result.scalars().all()
        
        for child_id in direct_children:
            child_ids.add(child_id)
            # 递归获取子目录的子目录
            grandchildren = await self._get_all_child_folders(db, child_id)
            child_ids.update(grandchildren)
        
        return child_ids
    
    async def get_kb_tree_with_stats(
        self,
        db: AsyncSession,
        kb_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """获取知识库完整树结构和统计信息（一次性查询）"""
        # 检查权限
        if not await self.kb_service._check_permission(db, kb_id, user_id, 'read'):
            raise BusinessException("无权限访问此知识库", ResponseCode.FORBIDDEN)
        
        # 获取完整目录树
        tree = await self.get_folder_tree(db, kb_id, user_id)
        
        # 获取根目录文档数量
        root_doc_result = await db.execute(
            select(func.count()).select_from(KBDocumentFolder)
            .join(
                KBDocument,
                and_(
                    KBDocument.kb_id == KBDocumentFolder.kb_id,
                    KBDocument.file_id == KBDocumentFolder.file_id
                )
            )
            .where(
                and_(
                    KBDocumentFolder.kb_id == kb_id,
                    KBDocumentFolder.folder_id.is_(None),
                    KBDocument.doc_status == 1
                )
            )
        )
        root_doc_count = root_doc_result.scalar()
        
        # 计算是否有子元素
        has_children = len(tree) > 0 or root_doc_count > 0
        
        return {
            "tree": tree,
            "has_children": has_children,
            "has_folders": len(tree) > 0,
            "has_documents": root_doc_count > 0,
            "folder_count": len(tree),
            "document_count": root_doc_count
        }
    
    async def check_has_children(
        self,
        db: AsyncSession,
        kb_id: str,
        folder_id: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """检查知识库或目录是否有子元素（简化版本）"""
        if folder_id is None:
            # 对于知识库根节点，使用更全面的检查
            return await self.get_kb_tree_with_stats(db, kb_id, user_id)
        
        # 检查权限
        if not await self.kb_service._check_permission(db, kb_id, user_id, 'read'):
            raise BusinessException("无权限访问此知识库", ResponseCode.FORBIDDEN)
        
        # 对于具体目录，只检查直接子元素
        folder_count_result = await db.execute(
            select(func.count()).select_from(KBFolder)
            .where(
                and_(
                    KBFolder.kb_id == kb_id,
                    KBFolder.parent_folder_id == folder_id
                )
            )
        )
        folder_count = folder_count_result.scalar()
        
        doc_count_result = await db.execute(
            select(func.count()).select_from(KBDocumentFolder)
            .join(
                KBDocument,
                and_(
                    KBDocument.kb_id == KBDocumentFolder.kb_id,
                    KBDocument.file_id == KBDocumentFolder.file_id
                )
            )
            .where(
                and_(
                    KBDocumentFolder.kb_id == kb_id,
                    KBDocumentFolder.folder_id == folder_id,
                    KBDocument.doc_status == 1
                )
            )
        )
        doc_count = doc_count_result.scalar()
        
        has_children = folder_count > 0 or doc_count > 0
        
        return {
            "has_children": has_children,
            "has_folders": folder_count > 0,
            "has_documents": doc_count > 0,
            "folder_count": folder_count,
            "document_count": doc_count
        }
    
    def _folder_to_dict(self, folder: KBFolder) -> Dict[str, Any]:
        """目录模型转字典"""
        folder_dict = folder.to_dict()
        
        # 处理JSON字段
        try:
            folder_dict['custom_permissions'] = json.loads(folder.custom_permissions) if folder.custom_permissions else {}
        except (json.JSONDecodeError, TypeError):
            folder_dict['custom_permissions'] = {}
        
        return folder_dict


# 全局服务实例
kb_folder_service = KBFolderService()