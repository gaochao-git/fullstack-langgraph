"""AI Model数据访问对象 - 纯异步实现"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from src.shared.db.dao.base_dao import BaseDAO
from src.apps.ai_model.models import AIModelConfig


class AIModelDAO(BaseDAO[AIModelConfig]):
    """AI模型数据访问对象 - 纯异步实现"""
    
    def __init__(self):
        super().__init__(AIModelConfig)
    
    async def get_by_model_id(self, session: AsyncSession, model_id: str) -> Optional[AIModelConfig]:
        """根据Model ID查询模型"""
        return await self.get_by_field(session, 'model_id', model_id)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        name_keyword: str,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AIModelConfig]:
        """根据名称关键词搜索AI模型"""
        query = select(self.model).where(
            self.model.model_name.contains(name_keyword)
        )
        
        if provider:
            query = query.where(self.model.model_provider == provider)
        
        if status:
            query = query.where(self.model.model_status == status)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_all_providers(self, session: AsyncSession) -> List[str]:
        """获取所有模型提供商"""
        result = await session.execute(
            select(distinct(self.model.model_provider))
            .where(self.model.model_provider.isnot(None))
            .order_by(self.model.model_provider)
        )
        return [provider for provider in result.scalars().all() if provider]
    
    async def get_all_types(self, session: AsyncSession) -> List[str]:
        """获取所有模型类型"""
        result = await session.execute(
            select(distinct(self.model.model_type))
            .where(self.model.model_type.isnot(None))
            .order_by(self.model.model_type)
        )
        return [model_type for model_type in result.scalars().all() if model_type]
    
    async def get_status_statistics(self, session: AsyncSession):
        """获取状态统计 - 返回原始查询结果"""
        result = await session.execute(
            select(
                self.model.model_status.label('status'),
                func.count(self.model.id).label('count')
            )
            .group_by(self.model.model_status)
            .order_by(func.count(self.model.id).desc())
        )
        return result
    
    async def get_provider_statistics(self, session: AsyncSession):
        """获取提供商统计 - 返回原始查询结果"""
        result = await session.execute(
            select(
                self.model.model_provider.label('provider'),
                func.count(self.model.id).label('count')
            )
            .group_by(self.model.model_provider)
            .order_by(func.count(self.model.id).desc())
        )
        return result
    
    async def get_active_models(self, session: AsyncSession) -> List[AIModelConfig]:
        """获取激活的模型"""
        filters = {'model_status': 'active'}
        return await self.get_list(session, filters=filters, order_by='create_time')
    
    async def get_models_by_provider(
        self, 
        session: AsyncSession, 
        provider: str
    ) -> List[AIModelConfig]:
        """根据提供商获取模型"""
        filters = {'model_provider': provider}
        return await self.get_list(session, filters=filters, order_by='create_time')
    
    async def update_model_status(
        self, 
        session: AsyncSession, 
        model_id: str, 
        status: str
    ) -> Optional[AIModelConfig]:
        """更新模型状态"""
        update_data = {'model_status': status}
        return await self.update_by_field(session, 'model_id', model_id, update_data)