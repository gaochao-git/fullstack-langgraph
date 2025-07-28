"""
基础数据库服务类
提供通用的CRUD操作
"""

from typing import Type, Optional, List, Dict, Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.shared.db.config import get_async_db, get_sync_db
from ..db.models import now_shanghai

# 泛型类型变量
ModelType = TypeVar('ModelType')


class BaseService(Generic[ModelType]):
    """基础服务类，提供通用CRUD操作"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    # ==================== 异步操作 ====================
    
    async def create(self, session: AsyncSession, **kwargs) -> ModelType:
        """创建记录"""
        try:
            # 自动设置创建时间
            if hasattr(self.model, 'create_time') and 'create_time' not in kwargs:
                kwargs['create_time'] = now_shanghai()
            if hasattr(self.model, 'update_time') and 'update_time' not in kwargs:
                kwargs['update_time'] = now_shanghai()
            
            instance = self.model(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance
        except IntegrityError as e:
            await session.rollback()
            raise ValueError(f"数据完整性错误: {str(e)}")
        except Exception as e:
            await session.rollback()
            raise e
    
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
    
    async def update(
        self, 
        session: AsyncSession, 
        id_value: Any, 
        **kwargs
    ) -> Optional[ModelType]:
        """更新记录"""
        try:
            # 自动设置更新时间
            if hasattr(self.model, 'update_time'):
                kwargs['update_time'] = now_shanghai()
            
            # 执行更新
            result = await session.execute(
                update(self.model)
                .where(self.model.id == id_value)
                .values(**kwargs)
                .returning(self.model)
            )
            
            updated_instance = result.scalar_one_or_none()
            if updated_instance:
                await session.commit()
                await session.refresh(updated_instance)
            
            return updated_instance
        except IntegrityError as e:
            await session.rollback()
            raise ValueError(f"数据完整性错误: {str(e)}")
        except Exception as e:
            await session.rollback()
            raise e
    
    async def update_by_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any,
        **kwargs
    ) -> Optional[ModelType]:
        """根据字段更新记录"""
        try:
            # 自动设置更新时间
            if hasattr(self.model, 'update_time'):
                kwargs['update_time'] = now_shanghai()
            
            field = getattr(self.model, field_name)
            result = await session.execute(
                update(self.model)
                .where(field == field_value)
                .values(**kwargs)
                .returning(self.model)
            )
            
            updated_instance = result.scalar_one_or_none()
            if updated_instance:
                await session.commit()
                await session.refresh(updated_instance)
            
            return updated_instance
        except Exception as e:
            await session.rollback()
            raise e
    
    async def delete(self, session: AsyncSession, id_value: Any) -> bool:
        """删除记录"""
        try:
            result = await session.execute(
                delete(self.model).where(self.model.id == id_value)
            )
            await session.commit()
            return result.rowcount > 0
        except Exception as e:
            await session.rollback()
            raise e
    
    async def delete_by_field(
        self, 
        session: AsyncSession, 
        field_name: str, 
        field_value: Any
    ) -> int:
        """根据字段删除记录，返回删除的数量"""
        try:
            field = getattr(self.model, field_name)
            result = await session.execute(
                delete(self.model).where(field == field_value)
            )
            await session.commit()
            return result.rowcount
        except Exception as e:
            await session.rollback()
            raise e
    
    async def count(
        self, 
        session: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计记录数量"""
        from sqlalchemy import func
        
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
    
    # ==================== 同步操作（兼容现有代码） ====================
    
    def sync_create(self, session: Session, **kwargs) -> ModelType:
        """同步创建记录"""
        try:
            # 自动设置创建时间
            if hasattr(self.model, 'create_time') and 'create_time' not in kwargs:
                kwargs['create_time'] = now_shanghai()
            if hasattr(self.model, 'update_time') and 'update_time' not in kwargs:
                kwargs['update_time'] = now_shanghai()
            
            instance = self.model(**kwargs)
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance
        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"数据完整性错误: {str(e)}")
        except Exception as e:
            session.rollback()
            raise e
    
    def sync_get_by_id(self, session: Session, id_value: Any) -> Optional[ModelType]:
        """同步根据ID获取记录"""
        return session.query(self.model).filter(self.model.id == id_value).first()
    
    def sync_get_list(
        self, 
        session: Session,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """同步获取记录列表"""
        query = session.query(self.model)
        
        # 添加过滤条件
        if filters:
            for field_name, field_value in filters.items():
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    query = query.filter(field == field_value)
        
        # 添加分页
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
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