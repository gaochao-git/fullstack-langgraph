"""定时任务数据访问对象 - 纯异步实现"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from src.shared.db.dao.base_dao import BaseDAO
from src.shared.db.models import PeriodicTask, TaskResult, CeleryTaskRecord


class ScheduledTaskDAO(BaseDAO[PeriodicTask]):
    """定时任务数据访问对象 - 纯异步实现"""
    
    def __init__(self):
        super().__init__(PeriodicTask)
    
    async def get_by_task_name(self, session: AsyncSession, task_name: str) -> Optional[PeriodicTask]:
        """根据任务名称查询定时任务"""
        return await self.get_by_field(session, 'name', task_name)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        name_keyword: str,
        enabled_only: bool = False,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[PeriodicTask]:
        """根据名称关键词搜索定时任务"""
        query = select(self.model).where(
            self.model.name.contains(name_keyword)
        )
        
        if enabled_only:
            query = query.where(self.model.enabled == True)
        
        if agent_id:
            # 假设有agent_id字段，实际根据数据库模型调整
            query = query.where(self.model.task_kwargs.contains(f'"agent_id":"{agent_id}"'))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_enabled_tasks(self, session: AsyncSession) -> List[PeriodicTask]:
        """获取启用的定时任务"""
        filters = {'enabled': True}
        return await self.get_list(session, filters=filters, order_by='date_changed')
    
    async def get_tasks_by_type(
        self, 
        session: AsyncSession, 
        task_type: str
    ) -> List[PeriodicTask]:
        """根据任务类型获取定时任务"""
        query = select(self.model).where(
            self.model.task.contains(task_type)
        )
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_task_statistics(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取任务状态统计"""
        result = await session.execute(
            select(
                self.model.enabled,
                func.count(self.model.id).label('count')
            )
            .group_by(self.model.enabled)
            .order_by(func.count(self.model.id).desc())
        )
        
        return [
            {'enabled': row.enabled, 'count': row.count}
            for row in result.fetchall()
        ]
    
    async def update_task_status(
        self, 
        session: AsyncSession, 
        task_id: int, 
        enabled: bool
    ) -> Optional[PeriodicTask]:
        """更新任务启用状态"""
        update_data = {'enabled': enabled}
        return await self.update_by_field(session, 'id', task_id, update_data)


class TaskResultDAO(BaseDAO[TaskResult]):
    """任务执行结果数据访问对象"""
    
    def __init__(self):
        super().__init__(TaskResult)
    
    async def get_by_task_name(
        self, 
        session: AsyncSession, 
        task_name: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[TaskResult]:
        """根据任务名称获取执行结果"""
        query = select(self.model).where(
            self.model.task_name == task_name
        ).order_by(self.model.date_created.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_by_task_id_str(self, session: AsyncSession, task_id: str) -> Optional[TaskResult]:
        """根据任务ID字符串查询执行结果"""
        return await self.get_by_field(session, 'task_id', task_id)
    
    async def get_recent_results(
        self, 
        session: AsyncSession, 
        limit: int = 50
    ) -> List[TaskResult]:
        """获取最近的执行结果"""
        query = select(self.model).order_by(
            self.model.date_created.desc()
        ).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()


class CeleryTaskRecordDAO(BaseDAO[CeleryTaskRecord]):
    """Celery任务记录数据访问对象"""
    
    def __init__(self):
        super().__init__(CeleryTaskRecord)
    
    async def search_by_name(
        self, 
        session: AsyncSession, 
        task_name: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[CeleryTaskRecord]:
        """根据任务名称搜索记录"""
        query = select(self.model).where(
            self.model.task_name.contains(task_name)
        )
        
        if status:
            query = query.where(self.model.task_status == status)
        
        query = query.order_by(self.model.create_time.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def get_by_status(
        self, 
        session: AsyncSession, 
        status: str
    ) -> List[CeleryTaskRecord]:
        """根据状态获取任务记录"""
        filters = {'task_status': status}
        return await self.get_list(session, filters=filters, order_by='create_time')
    
    async def get_status_statistics(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取任务状态统计"""
        result = await session.execute(
            select(
                self.model.task_status,
                func.count(self.model.id).label('count')
            )
            .group_by(self.model.task_status)
            .order_by(func.count(self.model.id).desc())
        )
        
        return [
            {'status': row.task_status, 'count': row.count}
            for row in result.fetchall()
        ]