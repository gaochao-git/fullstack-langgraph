"""
SOP业务服务层
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..db.dao import SOPDAO
from ..db.models import SOPTemplate
from ..db.transaction import transactional, sync_transactional
from ..core.logging import get_logger

logger = get_logger(__name__)


class SOPService:
    """SOP模板业务服务"""
    
    def __init__(self):
        self.dao = SOPDAO()
    
    # ==================== 异步业务方法 ====================
    
    @transactional()
    async def create_sop_template(
        self, 
        session: AsyncSession,
        sop_data: Dict[str, Any]
    ) -> SOPTemplate:
        """创建SOP模板"""
        # 业务验证
        if not sop_data.get('sop_id'):
            raise ValueError("SOP ID is required")
        
        # 检查是否已存在
        existing = await self.dao.get_by_sop_id(session, sop_data['sop_id'])
        if existing:
            raise ValueError(f"SOP template with ID {sop_data['sop_id']} already exists")
        
        # 设置默认值
        sop_data.setdefault('sop_severity', 'medium')
        sop_data.setdefault('team_name', 'default')
        
        logger.info(f"Creating SOP template: {sop_data['sop_id']}")
        return await self.dao.create(session, sop_data)
    
    async def get_sop_by_id(
        self, 
        session: AsyncSession, 
        sop_id: str
    ) -> Optional[SOPTemplate]:
        """根据ID获取SOP模板"""
        return await self.dao.get_by_sop_id(session, sop_id)
    
    async def get_sop_list(
        self, 
        session: AsyncSession,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        team_name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取SOP模板列表"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {}
        if category:
            filters['sop_category'] = category
        if severity:
            filters['sop_severity'] = severity
        if team_name:
            filters['team_name'] = team_name
        
        # 获取数据和总数
        templates = await self.dao.get_list(
            session, 
            filters=filters if filters else None,
            limit=size, 
            offset=offset
        )
        
        total = await self.dao.count(session, filters=filters if filters else None)
        
        return {
            'items': [template.to_dict() for template in templates],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    async def search_sops(
        self, 
        session: AsyncSession,
        keyword: str,
        team_name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """搜索SOP模板"""
        offset = (page - 1) * size
        
        templates = await self.dao.search_by_title(
            session, 
            keyword,
            team_name=team_name,
            limit=size, 
            offset=offset
        )
        
        # 获取搜索结果总数（简化实现）
        all_results = await self.dao.search_by_title(session, keyword, team_name=team_name)
        total = len(all_results)
        
        return {
            'items': [template.to_dict() for template in templates],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size,
            'keyword': keyword
        }
    
    @transactional()
    async def update_sop_template(
        self, 
        session: AsyncSession,
        sop_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[SOPTemplate]:
        """更新SOP模板"""
        # 检查是否存在
        existing = await self.dao.get_by_sop_id(session, sop_id)
        if not existing:
            raise ValueError(f"SOP template with ID {sop_id} not found")
        
        # 移除不可更新的字段
        update_data.pop('sop_id', None)
        update_data.pop('create_time', None)
        update_data.pop('create_by', None)
        
        logger.info(f"Updating SOP template: {sop_id}")
        return await self.dao.update_by_field(session, 'sop_id', sop_id, update_data)
    
    @transactional()
    async def delete_sop_template(
        self, 
        session: AsyncSession,
        sop_id: str
    ) -> bool:
        """删除SOP模板"""
        # 检查是否存在
        existing = await self.dao.get_by_sop_id(session, sop_id)
        if not existing:
            raise ValueError(f"SOP template with ID {sop_id} not found")
        
        logger.info(f"Deleting SOP template: {sop_id}")
        return await self.dao.delete_by_field(session, 'sop_id', sop_id) > 0
    
    async def get_category_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取分类统计"""
        # 简化实现，实际可能需要执行聚合查询
        categories = ['security', 'performance', 'maintenance', 'incident']
        stats = []
        
        for category in categories:
            count = await self.dao.count_by_category(session, category)
            if count > 0:
                stats.append({
                    'category': category,
                    'count': count
                })
        
        return stats
    
    # ==================== 同步业务方法（兼容） ====================
    
    @sync_transactional()
    def sync_create_sop_template(
        self, 
        session: Session,
        sop_data: Dict[str, Any]
    ) -> SOPTemplate:
        """同步创建SOP模板"""
        # 业务验证
        if not sop_data.get('sop_id'):
            raise ValueError("SOP ID is required")
        
        # 检查是否已存在
        existing = self.dao.sync_get_by_sop_id(session, sop_data['sop_id'])
        if existing:
            raise ValueError(f"SOP template with ID {sop_data['sop_id']} already exists")
        
        # 设置默认值
        sop_data.setdefault('sop_severity', 'medium')
        sop_data.setdefault('team_name', 'default')
        
        logger.info(f"Creating SOP template (sync): {sop_data['sop_id']}")
        return self.dao.sync_create(session, sop_data)
    
    def sync_get_sop_by_id(
        self, 
        session: Session, 
        sop_id: str
    ) -> Optional[SOPTemplate]:
        """同步根据ID获取SOP模板"""
        return self.dao.sync_get_by_sop_id(session, sop_id)