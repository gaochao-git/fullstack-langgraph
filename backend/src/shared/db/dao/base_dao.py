"""
基础DAO类
提供纯数据访问操作，不包含业务逻辑
"""

from typing import Type, Optional, List, Dict, Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from ..models import now_shanghai

# 泛型类型变量
ModelType = TypeVar('ModelType')


class BaseDAO(Generic[ModelType]):
    """基础数据访问对象，提供纯CRUD操作"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    # ==================== 异步CRUD操作 ====================
    
    async def create(self, session: AsyncSession, entity_data: Dict[str, Any]) -> ModelType:
        """创建实体"""
        # 自动设置时间戳
        if hasattr(self.model, 'create_time') and 'create_time' not in entity_data:
            entity_data['create_time'] = now_shanghai()
        if hasattr(self.model, 'update_time') and 'update_time' not in entity_data:
            entity_data['update_time'] = now_shanghai()
        
        instance = self.model(**entity_data)
        session.add(instance)
        await session.flush()  # 获取ID但不提交事务
        await session.refresh(instance)
        return instance
    
    async def get_by_id(self, session: AsyncSession, id_value: Any) -> Optional[ModelType]:
        """根据ID查询实体"""
        result = await session.execute(
            select(self.model).where(self.model.id == id_value)
        )
        return result.scalar_one_or_none()
    
    async def get_by_field(
        self, 
        session: AsyncSession, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """根据字段查询实体"""
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
        """查询实体列表"""
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
    
    async def update_by_id(
        self,
        session: AsyncSession,
        id_value: Any,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """根据ID更新实体"""
        # 自动设置更新时间
        if hasattr(self.model, 'update_time'):
            update_data['update_time'] = now_shanghai()
        
        result = await session.execute(
            update(self.model)
            .where(self.model.id == id_value)
            .values(**update_data)
            .returning(self.model)
        )
        
        updated_instance = result.scalar_one_or_none()
        if updated_instance:
            await session.refresh(updated_instance)
        
        return updated_instance
    
    async def update_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """根据字段更新实体"""
        # 自动设置更新时间
        if hasattr(self.model, 'update_time'):
            update_data['update_time'] = now_shanghai()
        
        field = getattr(self.model, field_name)
        result = await session.execute(
            update(self.model)
            .where(field == field_value)
            .values(**update_data)
            .returning(self.model)
        )
        
        updated_instance = result.scalar_one_or_none()
        if updated_instance:
            await session.refresh(updated_instance)
        
        return updated_instance
    
    async def delete_by_id(self, session: AsyncSession, id_value: Any) -> bool:
        """根据ID删除实体"""
        result = await session.execute(
            delete(self.model).where(self.model.id == id_value)
        )
        return result.rowcount > 0
    
    async def delete_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any
    ) -> int:
        """根据字段删除实体，返回删除数量"""
        field = getattr(self.model, field_name)
        result = await session.execute(
            delete(self.model).where(field == field_value)
        )
        return result.rowcount
    
    async def count(
        self,
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计实体数量"""
        query = select(func.count(self.model.id))
        
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
        """检查实体是否存在"""
        field = getattr(self.model, field_name)
        result = await session.execute(
            select(self.model.id).where(field == field_value)
        )
        return result.first() is not None
    
    # ==================== 同步CRUD操作（兼容） ====================
    
    def sync_create(self, session: Session, entity_data: Dict[str, Any]) -> ModelType:
        """同步创建实体"""
        # 自动设置时间戳
        if hasattr(self.model, 'create_time') and 'create_time' not in entity_data:
            entity_data['create_time'] = now_shanghai()
        if hasattr(self.model, 'update_time') and 'update_time' not in entity_data:
            entity_data['update_time'] = now_shanghai()
        
        instance = self.model(**entity_data)
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance
    
    def sync_get_by_id(self, session: Session, id_value: Any) -> Optional[ModelType]:
        """同步根据ID查询实体"""
        return session.query(self.model).filter(self.model.id == id_value).first()
    
    def sync_get_list(
        self,
        session: Session,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """同步查询实体列表"""
        query = session.query(self.model)
        
        if filters:
            for field_name, field_value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    query = query.filter(field == field_value)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    # ==================== 工具方法 ====================
    
    def to_dict(self, instance: ModelType) -> Dict[str, Any]:
        """将实体转换为字典"""
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