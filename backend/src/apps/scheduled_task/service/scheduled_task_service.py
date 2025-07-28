"""定时任务服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import json
from datetime import datetime

from ..dao.scheduled_task_dao import ScheduledTaskDAO, TaskResultDAO, CeleryTaskRecordDAO
from src.shared.db.models import PeriodicTask, TaskResult, CeleryTaskRecord
from src.shared.db.transaction import transactional
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class ScheduledTaskService:
    """定时任务服务 - 清晰的单一职责实现"""
    
    def __init__(self):
        self._dao = ScheduledTaskDAO()
        self._result_dao = TaskResultDAO()
        self._record_dao = CeleryTaskRecordDAO()
    
    @transactional()
    async def create_task(
        self, 
        session: AsyncSession, 
        task_data: Dict[str, Any]
    ) -> PeriodicTask:
        """创建定时任务"""
        # 业务验证
        existing = await self._dao.get_by_task_name(session, task_data['task_name'])
        if existing:
            raise ValueError(f"Task with name {task_data['task_name']} already exists")
        
        # 验证JSON字段
        self._validate_json_fields(task_data)
        
        # 验证调度配置
        self._validate_schedule_config(task_data)
        
        # 转换数据
        data = self._prepare_task_data(task_data)
        
        logger.info(f"Creating scheduled task: {task_data['task_name']}")
        return await self._dao.create(session, data)
    
    async def get_task_by_id(
        self, 
        session: AsyncSession, 
        task_id: int
    ) -> Optional[PeriodicTask]:
        """根据ID获取定时任务"""
        return await self._dao.get_by_id(session, task_id)
    
    async def get_task_by_name(
        self, 
        session: AsyncSession, 
        task_name: str
    ) -> Optional[PeriodicTask]:
        """根据名称获取定时任务"""
        return await self._dao.get_by_task_name(session, task_name)
    
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
        # 构建过滤条件
        filters = {}
        if enabled_only:
            filters['enabled'] = True
        
        # 搜索功能
        if search:
            tasks = await self._dao.search_by_name(
                session,
                search,
                enabled_only=enabled_only,
                agent_id=agent_id,
                limit=size,
                offset=(page - 1) * size
            )
            # 获取搜索总数
            all_results = await self._dao.search_by_name(
                session, 
                search,
                enabled_only=enabled_only,
                agent_id=agent_id
            )
            total = len(all_results)
        else:
            # 普通查询
            tasks = await self._dao.get_list(
                session,
                filters=filters if filters else None,
                limit=size,
                offset=(page - 1) * size,
                order_by='date_changed'
            )
            total = await self._dao.count(session, filters=filters if filters else None)
        
        return tasks, total
    
    @transactional()
    async def update_task(
        self, 
        session: AsyncSession, 
        task_id: int, 
        task_data: Dict[str, Any]
    ) -> Optional[PeriodicTask]:
        """更新定时任务"""
        # 检查是否存在
        existing = await self._dao.get_by_id(session, task_id)
        if not existing:
            raise ValueError(f"Task with ID {task_id} not found")
        
        # 验证JSON字段
        self._validate_json_fields(task_data)
        
        # 转换数据
        data = task_data.copy()
        
        # 移除不可更新字段
        data.pop('id', None)
        data.pop('date_created', None)
        
        logger.info(f"Updating scheduled task: {task_id}")
        return await self._dao.update_by_field(session, 'id', task_id, data)
    
    @transactional()
    async def delete_task(
        self, 
        session: AsyncSession, 
        task_id: int
    ) -> bool:
        """删除定时任务"""
        existing = await self._dao.get_by_id(session, task_id)
        if not existing:
            return False
        
        logger.info(f"Deleting scheduled task: {task_id}")
        return await self._dao.delete_by_field(session, 'id', task_id) > 0
    
    @transactional()
    async def enable_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> bool:
        """启用定时任务"""
        updated_task = await self._dao.update_task_status(session, task_id, True)
        return updated_task is not None
    
    @transactional()
    async def disable_task(
        self,
        session: AsyncSession,
        task_id: int
    ) -> bool:
        """禁用定时任务"""
        updated_task = await self._dao.update_task_status(session, task_id, False)
        return updated_task is not None
    
    async def get_enabled_tasks(self, session: AsyncSession) -> List[PeriodicTask]:
        """获取启用的任务（兼容性方法）"""
        return await self._dao.get_enabled_tasks(session)
    
    async def get_task_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取任务统计"""
        return await self._dao.get_task_statistics(session)
    
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
        task = await self._dao.get_by_id(session, task_id)
        if not task:
            return []
        
        # 根据任务名称获取执行结果
        return await self._result_dao.get_by_task_name(
            session, 
            task.name,
            limit=limit,
            offset=skip
        )
    
    async def get_task_result_by_id(
        self,
        session: AsyncSession,
        result_id: str
    ) -> Optional[TaskResult]:
        """根据ID获取任务执行结果"""
        return await self._result_dao.get_by_task_id_str(session, result_id)
    
    async def get_recent_task_results(
        self,
        session: AsyncSession,
        limit: int = 50
    ) -> List[TaskResult]:
        """获取最近的任务执行结果"""
        return await self._result_dao.get_recent_results(session, limit)
    
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
        if task_name:
            records = await self._record_dao.search_by_name(
                session,
                task_name,
                status=task_status,
                limit=size,
                offset=(page - 1) * size
            )
            # 获取搜索总数
            all_results = await self._record_dao.search_by_name(
                session, 
                task_name,
                status=task_status
            )
            total = len(all_results)
        else:
            # 构建过滤条件
            filters = {}
            if task_status:
                filters['task_status'] = task_status
            
            records = await self._record_dao.get_list(
                session,
                filters=filters if filters else None,
                limit=size,
                offset=(page - 1) * size,
                order_by='create_time'
            )
            total = await self._record_dao.count(session, filters=filters if filters else None)
        
        return records, total
    
    async def get_task_record_by_id(
        self,
        session: AsyncSession,
        record_id: int
    ) -> Optional[CeleryTaskRecord]:
        """根据ID获取任务执行记录"""
        return await self._record_dao.get_by_id(session, record_id)
    
    async def get_record_statistics(
        self,
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取任务记录状态统计"""
        return await self._record_dao.get_status_statistics(session)
    
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
        data.setdefault('enabled', True)
        data.setdefault('date_created', datetime.utcnow())
        data.setdefault('date_changed', datetime.utcnow())
        
        # 映射字段名
        field_mapping = {
            'task_name': 'name',
            'task_path': 'task',
            'task_description': 'description',
            'task_enabled': 'enabled',
            'task_args': 'args',
            'task_kwargs': 'kwargs',
            'task_extra_config': 'extra'
        }
        
        for old_key, new_key in field_mapping.items():
            if old_key in data:
                data[new_key] = data.pop(old_key)
        
        return data


# 全局实例
scheduled_task_service = ScheduledTaskService()