"""
定时任务相关的Pydantic模型定义
用于API请求和响应的数据验证
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ScheduledTaskBase(BaseModel):
    """定时任务基础模型"""
    task_name: str = Field(..., description="任务名称")
    task_path: str = Field(..., description="任务路径，如 'app.tasks.example_task'")
    task_description: Optional[str] = Field(None, description="任务描述")
    task_extra_config: Optional[str] = Field(None, description="任务配置JSON字符串")
    task_interval: Optional[int] = Field(None, description="间隔秒数（用于间隔调度）")
    task_crontab_minute: Optional[str] = Field(None, description="Crontab分钟")
    task_crontab_hour: Optional[str] = Field(None, description="Crontab小时")
    task_crontab_day_of_week: Optional[str] = Field(None, description="Crontab星期")
    task_crontab_day_of_month: Optional[str] = Field(None, description="Crontab日期")
    task_crontab_month_of_year: Optional[str] = Field(None, description="Crontab月份")
    task_args: Optional[str] = Field(None, description="任务参数（JSON格式）")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数（JSON格式）")
    task_enabled: bool = Field(True, description="是否启用任务")


class ScheduledTaskCreate(ScheduledTaskBase):
    """创建定时任务的请求模型"""
    pass


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务的请求模型"""
    task_name: Optional[str] = None
    task_path: Optional[str] = None
    task_description: Optional[str] = None
    task_extra_config: Optional[str] = None
    task_interval: Optional[int] = None
    task_crontab_minute: Optional[str] = None
    task_crontab_hour: Optional[str] = None
    task_crontab_day_of_week: Optional[str] = None
    task_crontab_day_of_month: Optional[str] = None
    task_crontab_month_of_year: Optional[str] = None
    task_args: Optional[str] = None
    task_kwargs: Optional[str] = None
    task_enabled: Optional[bool] = None


class ScheduledTaskResponse(ScheduledTaskBase):
    """定时任务响应模型"""
    id: int
    task_last_run_time: Optional[datetime]
    task_run_count: int
    create_time: datetime
    update_time: datetime
    create_by: Optional[str]
    update_by: Optional[str]

    class Config:
        from_attributes = True


class TaskExecutionLogResponse(BaseModel):
    """任务执行日志响应模型"""
    id: int
    task_name: str
    task_schedule_time: datetime
    task_execute_time: datetime
    task_status: str
    task_result: Optional[str]
    create_time: datetime

    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_name: str
    status: str
    message: Optional[str]
    last_run: Optional[datetime]
    next_run: Optional[datetime]

    class Config:
        from_attributes = True


class SimpleTask(BaseModel):
    """简化的任务模型"""
    id: int
    task_name: str
    task_path: str
    task_description: Optional[str]
    task_enabled: bool
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    total: int
    items: List[Dict[str, Any]]
    skip: int
    limit: int


class TaskOperationResponse(BaseModel):
    """任务操作响应模型"""
    success: bool
    message: str
    task_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class SchedulerStatusResponse(BaseModel):
    """调度器状态响应模型"""
    status: str
    message: Optional[str]
    scheduler_type: str
    last_check: datetime
    active_tasks: Optional[int] = None
    pending_tasks: Optional[int] = None