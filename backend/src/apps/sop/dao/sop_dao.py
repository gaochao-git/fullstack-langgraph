"""SOP数据访问对象"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from src.shared.db.dao.base_dao import BaseDAO
from src.apps.sop.models import SOPTemplate


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
    
    # ========== 旧格式方法 - 向后兼容 ==========
    async def get_all_categories(self, session: AsyncSession) -> List[str]:
        """获取所有分类 - 字符串数组格式（向后兼容）"""
        result = await session.execute(
            select(distinct(self.model.sop_category))
            .where(self.model.sop_category.isnot(None))
            .order_by(self.model.sop_category)
        )
        return [category for category in result.scalars().all() if category]
    
    async def get_all_teams(self, session: AsyncSession) -> List[str]:
        """获取所有团队 - 字符串数组格式（向后兼容）"""
        result = await session.execute(
            select(distinct(self.model.team_name))
            .where(self.model.team_name.isnot(None))
            .order_by(self.model.team_name)
        )
        return [team for team in result.scalars().all() if team]
    
    # ========== 简单方法 - 直接转为[{}]格式 ==========
    async def get_category_options(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取分类选项 - 简单直接"""
        result = await session.execute(
            select(
                self.model.sop_category.label('value'),
                func.count().label('count')
            )
            .where(self.model.sop_category.isnot(None))
            .group_by(self.model.sop_category)
            .order_by(self.model.sop_category)
        )
        return self.to_dict_list(result)
    
    async def get_team_options(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取团队选项 - 简单直接"""
        result = await session.execute(
            select(
                self.model.team_name.label('value'),
                func.count().label('count')
            )
            .where(self.model.team_name.isnot(None))
            .group_by(self.model.team_name)
            .order_by(self.model.team_name)
        )
        return self.to_dict_list(result)
    
    async def get_severity_options(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取严重程度选项 - 简单直接"""
        result = await session.execute(
            select(
                self.model.sop_severity.label('value'),
                func.count().label('count')
            )
            .where(self.model.sop_severity.isnot(None))
            .group_by(self.model.sop_severity)
            .order_by(func.count().desc())  # 按使用频率排序
        )
        return self.to_dict_list(result)
    
    async def get_category_statistics(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取分类统计 - 简单直接"""
        return await self.get_category_options(session)