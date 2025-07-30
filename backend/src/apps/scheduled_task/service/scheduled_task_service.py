"""定时任务服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, case, distinct
import json
from datetime import datetime

from src.apps.scheduled_task.models import PeriodicTask, TaskResult, CeleryTaskRecord
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class ScheduledTaskService:
    """定时任务服务 - 清晰的单一职责实现"""
    
    async def create_task(
        self, 
        session: AsyncSession, 
        task_data: Dict[str, Any]
    ) -> PeriodicTask:
        """创建定时任务"""
        async with session.begin():
            # 业务验证
            result = await session.execute(
                select(PeriodicTask).where(PeriodicTask.task_name == task_data['task_name'])
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise ValueError(f"Task with name {task_data['task_name']} already exists")
            
            # 验证JSON字段
            self._validate_json_fields(task_data)
            
            # 验证调度配置
            self._validate_schedule_config(task_data)
            
            # 转换数据
            data = self._prepare_task_data(task_data)
            data.setdefault('create_time', now_shanghai())
            data.setdefault('update_time', now_shanghai())
            
            logger.info(f"Creating scheduled task: {task_data['task_name']}")
            instance = PeriodicTask(**data)
            session.add(instance)
            await session.flush()
            await session.refresh(instance)
            return instance
    
    async def get_task_by_id(
        self, 
        session: AsyncSession, 
        task_id: int
    ) -> Optional[PeriodicTask]:
        """根据ID获取定时任务"""
        result = await session.execute(
            select(PeriodicTask).where(PeriodicTask.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_task_by_name(
        self, 
        session: AsyncSession, 
        task_name: str
    ) -> Optional[PeriodicTask]:
        """根据名称获取定时任务"""
        result = await session.execute(
            select(PeriodicTask).where(PeriodicTask.task_name == task_name)
        )
        return result.scalar_one_or_none()
    
    async def list_tasks(
        self, 
        session: AsyncSession, 
        page: int = 1,
        size: int = 10,
        enabled_only: bool = False,
        agent_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[PeriodicTask], int]:
        """列出定时任务"""
        offset = (page - 1) * size
        
        # 搜索功能
        if search:
            query = select(PeriodicTask).where(
                PeriodicTask.task_name.contains(search)
            )
            conditions = []
            if enabled_only:
                conditions.append(PeriodicTask.task_enabled == True)
            # Note: agent_id filtering would need to be implemented based on your schema
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.offset(offset).limit(size)
            result = await session.execute(query)
            tasks = list(result.scalars().all())
            
            # 获取搜索总数
            count_query = select(func.count(PeriodicTask.id)).where(
                PeriodicTask.task_name.contains(search)
            )
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar()
        else:
            # 普通查询
            query = select(PeriodicTask)
            conditions = []
            if enabled_only:
                conditions.append(PeriodicTask.task_enabled == True)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(PeriodicTask.update_time.desc())
            query = query.offset(offset).limit(size)
            result = await session.execute(query)
            tasks = list(result.scalars().all())
            
            # 计算总数
            count_query = select(func.count(PeriodicTask.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar()
        
        return tasks, total
    
    async def update_task(
        self, 
        session: AsyncSession, 
        task_id: int, 
        task_data: Dict[str, Any]
    ) -> Optional[PeriodicTask]:
        """更新定时任务"""
        async with session.begin():
            # 检查是否存在
            result = await session.execute(
                select(PeriodicTask).where(PeriodicTask.id == task_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise ValueError(f"Task with ID {task_id} not found")
            
            # 验证JSON字段
            self._validate_json_fields(task_data)
            
            # 转换数据
            data = task_data.copy()
            
            # 移除不可更新字段
            data.pop('id', None)
            data.pop('create_time', None)
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating scheduled task: {task_id}")
            await session.execute(
                update(PeriodicTask).where(PeriodicTask.id == task_id).values(**data)
            )
            
            # 返回更新后的数据
            result = await session.execute(
                select(PeriodicTask).where(PeriodicTask.id == task_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_task(
        self, 
        session: AsyncSession, 
        task_id: int
    ) -> bool:
        """删除定时任务"""
        async with session.begin():
            # 检查是否存在
            result = await session.execute(
                select(PeriodicTask).where(PeriodicTask.id == task_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                return False
            
            logger.info(f"Deleting scheduled task: {task_id}")
            result = await session.execute(
                delete(PeriodicTask).where(PeriodicTask.id == task_id)
            )
            return result.rowcount > 0
    
    async def enable_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> bool:
        """启用定时任务"""
        async with session.begin():
            result = await session.execute(
                update(PeriodicTask)
                .where(PeriodicTask.id == task_id)
                .values(task_enabled=True, update_time=now_shanghai())
            )
            return result.rowcount > 0
    
    async def disable_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> bool:
        """禁用定时任务"""
        async with session.begin():
            result = await session.execute(
                update(PeriodicTask)
                .where(PeriodicTask.id == task_id)
                .values(task_enabled=False, update_time=now_shanghai())
            )
            return result.rowcount > 0
    
    async def get_enabled_tasks(self, session: AsyncSession) -> List[PeriodicTask]:
        """获取启用的任务（兼容性方法）"""
        result = await session.execute(
            select(PeriodicTask).where(PeriodicTask.task_enabled == True)
        )
        return list(result.scalars().all())
    
    async def get_task_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取任务统计"""
        result = await session.execute(
            select(
                func.count(PeriodicTask.id).label('total'),
                func.sum(
                    case(
                        (PeriodicTask.task_enabled == True, 1),
                        else_=0
                    )
                ).label('enabled')
            )
        )
        row = result.first()
        return [{'total': row.total or 0, 'enabled': row.enabled or 0}]
    
    # TaskResult相关方法
    async def get_task_execution_logs(
        self,
        session: AsyncSession,
        task_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskResult]:
        """获取任务执行日志"""
        # 先获取任务信息
        task_result = await session.execute(
            select(PeriodicTask).where(PeriodicTask.id == task_id)
        )
        task = task_result.scalar_one_or_none()
        if not task:
            return []
        
        # 根据任务名称获取执行结果
        result = await session.execute(
            select(TaskResult)
            .where(TaskResult.task_name == task.task_name)
            .offset(skip)
            .limit(limit)
            .order_by(TaskResult.task_execute_time.desc())
        )
        return list(result.scalars().all())
    
    async def get_task_result_by_id(
        self,
        session: AsyncSession,
        result_id: int
    ) -> Optional[TaskResult]:
        """根据ID获取任务执行结果"""
        result = await session.execute(
            select(TaskResult).where(TaskResult.id == result_id)
        )
        return result.scalar_one_or_none()
    
    async def get_recent_task_results(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[TaskResult]:
        """获取最近的任务执行结果"""
        result = await session.execute(
            select(TaskResult)
            .order_by(TaskResult.task_execute_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # CeleryTaskRecord相关方法
    async def list_task_records(
        self,
        session: AsyncSession,
        page: int = 1,
        size: int = 10,
        task_name: Optional[str] = None,
        task_status: Optional[str] = None
    ) -> Tuple[List[CeleryTaskRecord], int]:
        """列出任务执行记录"""
        offset = (page - 1) * size
        
        if task_name:
            query = select(CeleryTaskRecord).where(
                CeleryTaskRecord.task_name.contains(task_name)
            )
            conditions = []
            if task_status:
                conditions.append(CeleryTaskRecord.task_status == task_status)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.offset(offset).limit(size)
            result = await session.execute(query)
            records = list(result.scalars().all())
            
            # 获取搜索总数
            count_query = select(func.count(CeleryTaskRecord.id)).where(
                CeleryTaskRecord.task_name.contains(task_name)
            )
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar()
        else:
            # 普通查询
            query = select(CeleryTaskRecord)
            conditions = []
            if task_status:
                conditions.append(CeleryTaskRecord.task_status == task_status)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(CeleryTaskRecord.create_time.desc())
            query = query.offset(offset).limit(size)
            result = await session.execute(query)
            records = list(result.scalars().all())
            
            # 计算总数
            count_query = select(func.count(CeleryTaskRecord.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar()
        
        return records, total
    
    async def get_task_record_by_id(
        self,
        session: AsyncSession,
        record_id: int
    ) -> Optional[CeleryTaskRecord]:
        """根据ID获取任务执行记录"""
        result = await session.execute(
            select(CeleryTaskRecord).where(CeleryTaskRecord.id == record_id)
        )
        return result.scalar_one_or_none()
    
    async def get_record_statistics(
        self,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取任务记录状态统计"""
        result = await session.execute(
            select(
                CeleryTaskRecord.task_status.label('status'),
                func.count(CeleryTaskRecord.id).label('count')
            ).group_by(CeleryTaskRecord.task_status)
        )
        return [{'status': row.status, 'count': row.count} for row in result.fetchall()]
    
    # 私有方法
    def _validate_json_fields(self, task_data: Dict[str, Any]) -> None:
        """验证JSON字段"""
        json_fields = ['task_args', 'task_kwargs', 'task_extra_config']
        
        for field in json_fields:
            if field in task_data and task_data[field] is not None:
                try:
                    if isinstance(task_data[field], str):
                        json.loads(task_data[field])
                except json.JSONDecodeError:
                    raise ValueError(f"{field} must be valid JSON format")
    
    def _validate_schedule_config(self, task_data: Dict[str, Any]) -> None:
        """验证调度配置"""
        has_interval = task_data.get('task_interval') is not None
        has_crontab = any([
            task_data.get('task_crontab_minute'),
            task_data.get('task_crontab_hour'),
            task_data.get('task_crontab_day_of_week'),
            task_data.get('task_crontab_day_of_month'),
            task_data.get('task_crontab_month_of_year')
        ])
        
        if not has_interval and not has_crontab:
            raise ValueError("Must provide either interval schedule (task_interval) or crontab schedule configuration")
    
    def _prepare_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备任务数据"""
        data = task_data.copy()
        
        # 设置默认值
        data.setdefault('task_enabled', True)
        
        # 字段名已经匹配数据库模型，不需要映射
        
        return data


# 全局实例
scheduled_task_service = ScheduledTaskService()