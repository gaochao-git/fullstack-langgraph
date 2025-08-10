"""
基础数据库服务类
提供通用的CRUD操作
"""

from typing import Type, Optional, List, Dict, Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.shared.db.config import get_async_db, get_sync_db
from src.shared.db.models import now_shanghai

# 泛型类型变量
ModelType = TypeVar('ModelType')


class BaseService(Generic[ModelType]):
    """基础服务类，提供通用CRUD操作"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    # ==================== 查询操作（推荐使用） ====================
    
    async def get_by_id(self, session: AsyncSession, id_value: Any) -> Optional[ModelType]:
        """根据ID获取记录"""
        result = await session.execute(
            select(self.model).where(self.model.id == id_value)
        )
        return result.scalar_one_or_none()
    
    async def get_by_field(self, session: AsyncSession, field_name: str, field_value: Any) -> Optional[ModelType]:
        """根据字段获取记录"""
        field = getattr(self.model, field_name)
        result = await session.execute(
            select(self.model).where(field == field_value)
        )
        return result.scalar_one_or_none()
    
    async def get_list(
        self, 
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """获取记录列表"""
        query = select(self.model)
        
        # 添加过滤条件
        if filters:
            conditions = []
            for field_name, field_value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    if isinstance(field_value, (list, tuple)):
                        conditions.append(field.in_(field_value))
                    else:
                        conditions.append(field == field_value)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # 添加排序
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            query = query.order_by(order_field.desc())
        
        # 添加分页
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    
    async def count(
        self, 
        session: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计记录数量"""
        query = select(func.count(self.model.id))
        
        # 添加过滤条件
        if filters:
            conditions = []
            for field_name, field_value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    conditions.append(field == field_value)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await session.execute(query)
        return result.scalar()
    
    async def exists(
        self, 
        session: AsyncSession, 
        field_name: str, 
        field_value: Any
    ) -> bool:
        """检查记录是否存在"""
        field = getattr(self.model, field_name)
        result = await session.execute(
            select(self.model.id).where(field == field_value)
        )
        return result.first() is not None
    
    # ==================== 简单写操作（不自动提交） ====================
    
    async def delete_by_id(self, session: AsyncSession, id_value: Any) -> int:
        """根据ID删除记录（不自动提交，需要在 async with session.begin() 中使用）
        
        返回删除的记录数
        """
        result = await session.execute(
            delete(self.model).where(self.model.id == id_value)
        )
        return result.rowcount
    
    
    # ==================== 工具方法 ====================
    
    def to_dict(self, instance: ModelType) -> Dict[str, Any]:
        """将模型实例转换为字典"""
        if hasattr(instance, 'to_dict'):
            return instance.to_dict()
        
        # 默认转换逻辑
        result = {}
        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                result[column.name] = value
        return result