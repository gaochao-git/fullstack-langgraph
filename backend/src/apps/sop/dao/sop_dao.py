"""SOP数据访问对象"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from src.shared.db.dao.base_dao import BaseDAO
from src.shared.db.models import SOPTemplate


class SOPDAO(BaseDAO[SOPTemplate]):
    """SOP模板数据访问对象 - 纯异步实现"""
    
    def __init__(self):
        super().__init__(SOPTemplate)
    
    async def get_by_sop_id(self, session: AsyncSession, sop_id: str) -> Optional[SOPTemplate]:
        """根据SOP ID查询模板"""
        return await self.get_by_field(session, 'sop_id', sop_id)
    
    async def search_by_title(
        self, 
        session: AsyncSession, 
        title_keyword: str,
        team_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """根据标题关键词搜索SOP模板"""
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
    
    async def get_all_categories(self, session: AsyncSession) -> List[str]:
        """获取所有分类"""
        result = await session.execute(
            select(distinct(self.model.sop_category))
            .where(self.model.sop_category.isnot(None))
            .order_by(self.model.sop_category)
        )
        return [category for category in result.scalars().all() if category]
    
    async def get_all_teams(self, session: AsyncSession) -> List[str]:
        """获取所有团队"""
        result = await session.execute(
            select(distinct(self.model.team_name))
            .where(self.model.team_name.isnot(None))
            .order_by(self.model.team_name)
        )
        return [team for team in result.scalars().all() if team]
    
    async def get_category_statistics(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取分类统计"""
        result = await session.execute(
            select(
                self.model.sop_category,
                func.count(self.model.id).label('count')
            )
            .where(self.model.sop_category.isnot(None))
            .group_by(self.model.sop_category)
            .order_by(func.count(self.model.id).desc())
        )
        
        return [
            {'category': row.sop_category, 'count': row.count}
            for row in result.fetchall()
        ]