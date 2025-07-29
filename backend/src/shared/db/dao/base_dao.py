"""
基础DAO类
提供纯数据访问操作，不包含业务逻辑
"""

from typing import Type, Optional, List, Dict, Any, Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, func, literal, case, distinct
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from src.shared.db.models import now_shanghai

# 泛型类型变量
ModelType = TypeVar('ModelType')


class BaseDAO(Generic[ModelType]):
    """基础数据访问对象，提供纯CRUD操作"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    # ==================== 异步CRUD操作 ====================
    
    async def create(self, db: AsyncSession, entity_data: Dict[str, Any]) -> ModelType:
        """创建实体"""
        # 自动设置时间戳
        if hasattr(self.model, 'create_time') and 'create_time' not in entity_data:entity_data['create_time'] = now_shanghai()
        if hasattr(self.model, 'update_time') and 'update_time' not in entity_data:entity_data['update_time'] = now_shanghai()
        instance = self.model(**entity_data)
        db.add(instance)
        await db.flush()  # 获取ID但不提交事务
        await db.refresh(instance)
        return instance
    
    async def get_by_id(self, db: AsyncSession, id_value: Any) -> Optional[ModelType]:
        """根据ID查询实体"""
        result = await db.execute(
            select(self.model).where(self.model.id == id_value)
        )
        return result.scalar_one_or_none()
    
    async def get_by_field(
        self, 
        db: AsyncSession, 
        field_name: str, 
        field_value: Any
    ) -> Optional[ModelType]:
        """根据字段查询实体"""
        field = getattr(self.model, field_name)
        result = await db.execute(
            select(self.model).where(field == field_value)
        )
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        db: AsyncSession,
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
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_by_id(
        self,
        db: AsyncSession,
        id_value: Any,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """根据ID更新实体"""
        # 自动设置更新时间
        if hasattr(self.model, 'update_time'):
            update_data['update_time'] = now_shanghai()
        
        result = await db.execute(
            update(self.model)
            .where(self.model.id == id_value)
            .values(**update_data)
        )
        
        updated_instance = result.scalar_one_or_none()
        if updated_instance: await db.refresh(updated_instance)
        return updated_instance
    
    async def update_by_field(
        self,
        db: AsyncSession,
        field_name: str,
        field_value: Any,
        update_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """根据字段更新实体"""
        # 自动设置更新时间
        if hasattr(self.model, 'update_time'):update_data['update_time'] = now_shanghai()
        field = getattr(self.model, field_name)
        result = await db.execute(
            update(self.model)
            .where(field == field_value)
            .values(**update_data)
        )
        result = await db.execute(select(self.model).where(field == field_value))
        return result.scalar_one_or_none()

    
    async def delete_by_id(self, db: AsyncSession, id_value: Any) -> bool:
        """根据ID删除实体"""
        result = await db.execute(
            delete(self.model).where(self.model.id == id_value)
        )
        return result.rowcount > 0
    
    async def delete_by_field(
        self,
        db: AsyncSession,
        field_name: str,
        field_value: Any
    ) -> int:
        """根据字段删除实体，返回删除数量"""
        field = getattr(self.model, field_name)
        result = await db.execute(
            delete(self.model).where(field == field_value)
        )
        return result.rowcount
    
    async def count(
        self,
        db: AsyncSession,
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
        
        result = await db.execute(query)
        return result.scalar()
    
    async def exists(
        self,
        db: AsyncSession,
        field_name: str,
        field_value: Any
    ) -> bool:
        """检查实体是否存在"""
        field = getattr(self.model, field_name)
        result = await db.execute(
            select(self.model.id).where(field == field_value)
        )
        return result.first() is not None
    
    # ==================== 同步CRUD操作（兼容） ====================
    
    def sync_create(self, db: Session, entity_data: Dict[str, Any]) -> ModelType:
        """同步创建实体"""
        # 自动设置时间戳
        if hasattr(self.model, 'create_time') and 'create_time' not in entity_data:
            entity_data['create_time'] = now_shanghai()
        if hasattr(self.model, 'update_time') and 'update_time' not in entity_data:
            entity_data['update_time'] = now_shanghai()
        
        instance = self.model(**entity_data)
        db.add(instance)
        db.flush()
        db.refresh(instance)
        return instance
    
    def sync_get_by_id(self, db: Session, id_value: Any) -> Optional[ModelType]:
        """同步根据ID查询实体"""
        return db.query(self.model).filter(self.model.id == id_value).first()
    
    def sync_get_list(
        self,
        db: Session,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelType]:
        """同步查询实体列表"""
        query = db.query(self.model)
        
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
    
    # ==================== 简单工具方法 ====================
    
    def to_dict_list(self, result) -> List[Dict[str, Any]]:
        """
        简单：把查询结果转为 [{}] 格式
        
        Args:
            result: SQLAlchemy查询结果
            
        Returns:
            [{"字段名": "值", ...}]
        """
        # SQLAlchemy 2.0 官方推荐：直接用 mappings()
        return [dict(row) for row in result.mappings()]