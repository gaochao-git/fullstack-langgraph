"""
定时任务服务层
处理定时任务相关的业务逻辑
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ....shared.db.models import PeriodicTask, TaskResult
from ....shared.core.logging import get_logger
from ..dao.scheduled_task_dao import ScheduledTaskDAO

logger = get_logger(__name__)


class ScheduledTaskService:
    """定时任务服务类"""
    
    @staticmethod
    def get_tasks_list(
        session: Session,
        skip: int = 0, 
        limit: int = 100,
        enabled_only: bool = False,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取定时任务列表
        
        Args:
            session: 数据库会话
            skip: 跳过的记录数
            limit: 返回的记录数
            enabled_only: 仅显示启用的任务
            agent_id: 按智能体ID过滤
            
        Returns:
            任务列表
        """
        tasks = ScheduledTaskDAO.get_all_tasks(
            session=session,
            skip=skip,
            limit=limit,
            enabled_only=enabled_only
        )
        return [task.to_dict() for task in tasks]
    
    @staticmethod
    def get_task_by_id(session: Session, task_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取单个任务
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            
        Returns:
            任务信息字典，如果不存在返回None
        """
        task = ScheduledTaskDAO.get_task_by_id(session, task_id)
        if task:
            return task.to_dict()
        return None
    
    @staticmethod
    def get_task_execution_logs(
        session: Session, 
        task_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取任务执行日志
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            skip: 跳过的记录数
            limit: 返回的记录数
            
        Returns:
            执行日志列表
        """
        # 首先验证任务是否存在
        task = ScheduledTaskDAO.get_task_by_id(session, task_id)
        if not task:
            return []
        
        # 查询该任务的执行结果
        results = ScheduledTaskDAO.get_task_results(
            session=session,
            task_name=task.name,
            skip=skip,
            limit=limit
        )
        
        # 转换为响应格式
        logs = []
        for result in results:
            log_data = result.to_dict()
            logs.append({
                "id": log_data["id"],
                "task_name": log_data["task_name"],
                "task_schedule_time": log_data["task_schedule_time"],
                "task_execute_time": log_data["task_execute_time"], 
                "task_status": log_data["task_status"],
                "task_result": log_data["task_result"],
                "create_time": log_data["create_time"]
            })
        
        return logs
    
    @staticmethod
    def create_task(session: Session, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        创建新的定时任务
        
        Args:
            session: 数据库会话
            task_data: 任务数据
            
        Returns:
            创建结果
        """
        try:
            # 创建新任务实例
            new_task = PeriodicTask(
                name=task_data["task_name"],
                task=task_data["task_path"],
                description=task_data.get("task_description", ""),
                args=task_data.get("task_args", "[]"),
                kwargs=task_data.get("task_kwargs", "{}"),
                enabled=task_data.get("task_enabled", True),
                create_by=task_data.get("create_by", "system"),
                update_by=task_data.get("update_by", "system")
            )
            
            session.add(new_task)
            session.commit()
            session.refresh(new_task)
            
            logger.info(f"创建任务成功: {task_data['task_name']}")
            
            return {
                "id": new_task.id,
                "message": "任务创建成功",
                "task_name": new_task.name,
                "status": "created"
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"创建任务失败: {e}")
            return None
    
    @staticmethod
    def update_task(session: Session, task_id: int, task_data: Dict[str, Any]) -> bool:
        """
        更新定时任务
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            task_data: 更新数据
            
        Returns:
            是否更新成功
        """
        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                return False
            
            # 更新字段
            for key, value in task_data.items():
                if hasattr(task, key) and value is not None:
                    setattr(task, key, value)
            
            task.update_by = task_data.get("update_by", "system")
            
            session.commit()
            logger.info(f"更新任务成功: {task.name}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新任务失败: {e}")
            return False
    
    @staticmethod
    def delete_task(session: Session, task_id: int) -> bool:
        """
        删除定时任务
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                return False
            
            session.delete(task)
            session.commit()
            logger.info(f"删除任务成功: {task.name}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"删除任务失败: {e}")
            return False
    
    @staticmethod
    def enable_task(session: Session, task_id: int) -> bool:
        """
        启用定时任务
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            
        Returns:
            是否启用成功
        """
        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                return False
            
            task.enabled = True
            session.commit()
            logger.info(f"启用任务成功: {task.name}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"启用任务失败: {e}")
            return False
    
    @staticmethod
    def disable_task(session: Session, task_id: int) -> bool:
        """
        禁用定时任务
        
        Args:
            session: 数据库会话
            task_id: 任务ID
            
        Returns:
            是否禁用成功
        """
        try:
            task = session.query(PeriodicTask).filter(PeriodicTask.id == task_id).first()
            if not task:
                return False
            
            task.enabled = False
            session.commit()
            logger.info(f"禁用任务成功: {task.name}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"禁用任务失败: {e}")
            return False
    
    @staticmethod
    def validate_json_field(field_name: str, value: Optional[str]) -> bool:
        """
        验证JSON字段格式
        
        Args:
            field_name: 字段名
            value: 字段值
            
        Returns:
            是否为有效JSON
        """
        if value:
            try:
                json.loads(value)
                return True
            except json.JSONDecodeError:
                logger.warning(f"{field_name}格式无效: {value}")
                return False
        return True
    
    @staticmethod
    def validate_schedule_config(task_data: Dict[str, Any]) -> bool:
        """
        验证调度配置
        
        Args:
            task_data: 任务数据
            
        Returns:
            配置是否有效
        """
        has_interval = task_data.get("task_interval") is not None
        has_crontab = any([
            task_data.get("task_crontab_minute"),
            task_data.get("task_crontab_hour"),
            task_data.get("task_crontab_day_of_week"),
            task_data.get("task_crontab_day_of_month"),
            task_data.get("task_crontab_month_of_year")
        ])
        
        if not has_interval and not has_crontab:
            logger.warning("缺少调度配置")
            return False
        
        return True


# 实例化服务对象，保持向后兼容
scheduled_task_service = ScheduledTaskService()