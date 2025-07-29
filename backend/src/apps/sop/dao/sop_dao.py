"""SOP数据访问对象"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func, distinct

from src.shared.db.dao.base_dao import BaseDAO
from src.apps.sop.models import SOPTemplate


class SOPDAO(BaseDAO[SOPTemplate]):
    """SOP模板数据访问对象 - 纯异步实现"""
    
    def __init__(self):
        super().__init__(SOPTemplate)
    
    async def get_by_sop_id(self, db: AsyncSession, sop_id: str) -> Optional[SOPTemplate]:
        """根据SOP ID查询模板"""
        return await self.get_by_field(db, 'sop_id', sop_id)
    
    def sync_get_by_sop_id(self, db: Session, sop_id: str) -> Optional[SOPTemplate]:
        """同步根据SOP ID查询模板 - 兼容LangGraph工具"""
        return db.query(self.model).filter(self.model.sop_id == sop_id).first()
    
    async def search_by_title(
        self, 
        db: AsyncSession, 
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
        
        result = await db.execute(query)
        return result.scalars().all()
    
    def sync_search_by_title(
        self, 
        db: Session, 
        title_keyword: str,
        team_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[SOPTemplate]:
        """同步根据标题关键词搜索SOP模板 - 兼容LangGraph工具"""
        query = db.query(self.model).filter(
            self.model.sop_title.contains(title_keyword)
        )
        
        if team_name:
            query = query.filter(self.model.team_name == team_name)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    # ========== 选项和统计方法 - 返回原始查询结果让Router层处理 ==========
    async def get_category_options(self, db: AsyncSession):
        """获取分类选项 - 返回原始查询结果"""
        result = await db.execute(
            select(
                self.model.sop_category.label('value'),
                func.count().label('count')
            )
            .where(self.model.sop_category.isnot(None))
            .group_by(self.model.sop_category)
            .order_by(self.model.sop_category)
        )
        return result
    
    async def get_team_options(self, db: AsyncSession):
        """获取团队选项 - 返回原始查询结果"""
        result = await db.execute(
            select(
                self.model.team_name.label('value'),
                func.count().label('count')
            )
            .where(self.model.team_name.isnot(None))
            .group_by(self.model.team_name)
            .order_by(self.model.team_name)
        )
        return result
    
    async def get_severity_options(self, db: AsyncSession):
        """获取严重程度选项 - 返回原始查询结果"""
        result = await db.execute(
            select(
                self.model.sop_severity.label('value'),
                func.count().label('count')
            )
            .where(self.model.sop_severity.isnot(None))
            .group_by(self.model.sop_severity)
            .order_by(func.count().desc())  # 按使用频率排序
        )
        return result