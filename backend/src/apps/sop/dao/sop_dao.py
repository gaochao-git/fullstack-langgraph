"""
SOP数据访问对象
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.shared.db.dao.base_dao import BaseDAO
from src.shared.db.models import SOPTemplate


class SOPDAO(BaseDAO[SOPTemplate]):
    """SOP模板数据访问对象"""
    
    def __init__(self):
        super().__init__(SOPTemplate)
    
    # ==================== 专用查询方法 ====================
    
    async def get_by_sop_id(self, session: AsyncSession, sop_id: str) -> Optional[SOPTemplate]:
        """根据SOP ID查询模板"""
        return await self.get_by_field(session, 'sop_id', sop_id)
    
    async def get_by_category(
        self, 
        session: AsyncSession, 
        category: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """根据分类查询SOP模板"""
        filters = {'sop_category': category}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_by_severity(
        self, 
        session: AsyncSession, 
        severity: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """根据严重程度查询SOP模板"""
        filters = {'sop_severity': severity}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def get_by_team(
        self, 
        session: AsyncSession, 
        team_name: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """根据团队查询SOP模板"""
        filters = {'team_name': team_name}
        return await self.get_list(session, filters=filters, limit=limit, offset=offset)
    
    async def search_by_title(
        self, 
        session: AsyncSession, 
        title_keyword: str,
        team_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """根据标题关键词搜索SOP模板"""
        from sqlalchemy import select, and_
        
        query = select(self.model).where(
            self.model.sop_title.contains(title_keyword)
        )
        
        if team_name:
            query = query.where(self.model.team_name == team_name)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def count_by_category(self, session: AsyncSession, category: str) -> int:
        """统计指定分类的SOP数量"""
        filters = {'sop_category': category}
        return await self.count(session, filters=filters)
    
    async def count_by_team(self, session: AsyncSession, team_name: str) -> int:
        """统计指定团队的SOP数量"""
        filters = {'team_name': team_name}
        return await self.count(session, filters=filters)
    
    # ==================== 同步方法（兼容） ====================
    
    def sync_get_by_sop_id(self, session: Session, sop_id: str) -> Optional[SOPTemplate]:
        """同步根据SOP ID查询模板"""
        return session.query(self.model).filter(self.model.sop_id == sop_id).first()
    
    def sync_get_by_category(
        self, 
        session: Session, 
        category: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """同步根据分类查询SOP模板"""
        query = session.query(self.model).filter(self.model.sop_category == category)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()