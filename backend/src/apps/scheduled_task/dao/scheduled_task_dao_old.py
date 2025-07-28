"""
定时任务数据访问对象
负责数据库操作的具体实现
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ....shared.db.models import PeriodicTask, TaskResult
from ....shared.core.logging import get_logger

logger = get_logger(__name__)


class ScheduledTaskDAO:
    """定时任务DAO类"""
    
    @staticmethod
    def get_all_tasks(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        enabled_only: bool = False
    ) -> List[PeriodicTask]:
        """
        获取所有任务
        
        Args:
            session: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            enabled_only: 仅返回启用的任务
            
        Returns:
            任务列表
        """
        try:
            query = session.query(PeriodicTask)
            
            if enabled_only:
                query = query.filter(PeriodicTask.enabled == True)
            
            return query.offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"查询任务列表失败: {e}")
            return []
    
    @staticmethod
    def get_task_by_id(session: Session, task_id: int) -> Optional[PeriodicTask]:
        """
        根据ID获取任务
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在返回None
        """
        try:
            return session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return None
    
    @staticmethod
    def get_task_by_name(session: Session, task_name: str) -> Optional[PeriodicTask]:
        """
        根据名称获取任务
        
        Args:
            session: 数据库会话
            task_name: 任务名称
            
        Returns:
            任务对象，如果不存在返回None
        """
        try:
            return session.query(PeriodicTask).filter(PeriodicTask.name == task_name).first()
        except Exception as e:
            logger.error(f"查询任务失败: {e}")
            return None
    
    @staticmethod
    def create_task(session: Session, task: PeriodicTask) -> bool:
        """
        创建任务
        
        Args:
            session: 数据库会话
            task: 任务对象
            
        Returns:
            是否创建成功
        """
        try:
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.info(f"创建任务成功: {task.name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"创建任务失败: {e}")
            return False
    
    @staticmethod
    def update_task(session: Session, task: PeriodicTask) -> bool:
        """
        更新任务
        
        Args:
            session: 数据库会话
            task: 任务对象
            
        Returns:
            是否更新成功
        """
        try:
            session.commit()
            logger.info(f"更新任务成功: {task.name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"更新任务失败: {e}")
            return False
    
    @staticmethod
    def delete_task(session: Session, task: PeriodicTask) -> bool:
        """
        删除任务
        
        Args:
            session: 数据库会话
            task: 任务对象
            
        Returns:
            是否删除成功
        """
        try:
            session.delete(task)
            session.commit()
            logger.info(f"删除任务成功: {task.name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"删除任务失败: {e}")
            return False
    
    @staticmethod
    def get_task_results(
        session: Session,
        task_name: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskResult]:
        """
        获取任务执行结果
        
        Args:
            session: 数据库会话
            task_name: 任务名称
            skip: 跳过的记录数
            limit: 返回的记录数
            
        Returns:
            执行结果列表
        """
        try:
            return session.query(TaskResult).filter(
                TaskResult.task_name == task_name
            ).order_by(desc(TaskResult.date_created)).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"查询任务执行结果失败: {e}")
            return []
    
    @staticmethod
    def get_task_result_by_id(session: Session, result_id: str) -> Optional[TaskResult]:
        """
        根据ID获取任务执行结果
        
        Args:
            session: 数据库会话
            result_id: 结果ID
            
        Returns:
            执行结果对象，如果不存在返回None
        """
        try:
            return session.query(TaskResult).filter(TaskResult.task_id == result_id).first()
        except Exception as e:
            logger.error(f"查询任务执行结果失败: {e}")
            return None


# 实例化DAO对象，保持向后兼容
scheduled_task_dao = ScheduledTaskDAO()