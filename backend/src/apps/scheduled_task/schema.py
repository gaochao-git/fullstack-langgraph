"""定时任务 schemas - 增强验证"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
import json


class ScheduledTaskCreate(BaseModel):
    """创建定时任务的schema"""
    task_name: str = Field(..., description="任务名称", min_length=1, max_length=200)
    task_path: str = Field(..., description="任务路径", min_length=1, max_length=500)
    task_description: Optional[str] = Field(None, description="任务描述", max_length=1000)
    task_extra_config: Optional[str] = Field(None, description="任务配置JSON字符串")
    task_interval: Optional[int] = Field(None, description="间隔秒数", ge=1, le=86400)
    task_crontab_minute: Optional[str] = Field(None, description="Crontab分钟", max_length=100)
    task_crontab_hour: Optional[str] = Field(None, description="Crontab小时", max_length=100)
    task_crontab_day_of_week: Optional[str] = Field(None, description="Crontab星期", max_length=100)
    task_crontab_day_of_month: Optional[str] = Field(None, description="Crontab日期", max_length=100)
    task_crontab_month_of_year: Optional[str] = Field(None, description="Crontab月份", max_length=100)
    task_args: Optional[str] = Field(None, description="任务参数JSON")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数JSON")
    task_enabled: bool = Field(True, description="是否启用任务")
    
    @validator('task_args', 'task_kwargs', 'task_extra_config')
    def validate_json_fields(cls, v):
        """验证JSON字段格式"""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('必须是有效的JSON格式')
        return v
    
    @validator('task_extra_config')
    def validate_agent_task_config(cls, v, values):
        """验证智能体任务的额外配置"""
        if v is not None:
            try:
                config = json.loads(v)
                # 如果是智能体任务，验证必需的字段
                if config.get('task_type') == 'agent':
                    if not config.get('agent_url'):
                        raise ValueError('智能体任务必须提供agent_url')
                    if not config.get('agent_key'):
                        raise ValueError('智能体任务必须提供agent_key')
                    if not config.get('agent_id'):
                        raise ValueError('智能体任务必须提供agent_id')
            except json.JSONDecodeError:
                pass  # 前面已经验证过JSON格式
        return v
    
    @validator('task_path')
    def validate_task_path(cls, v):
        """验证任务路径格式"""
        if not ('.' in v and not v.startswith('.') and not v.endswith('.')):
            raise ValueError('任务路径必须是有效的Python模块路径格式，如 "app.tasks.example_task"')
        return v


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务的schema"""
    task_name: Optional[str] = Field(None, description="任务名称", min_length=1, max_length=200)
    task_path: Optional[str] = Field(None, description="任务路径", min_length=1, max_length=500)
    task_description: Optional[str] = Field(None, description="任务描述", max_length=1000)
    task_extra_config: Optional[str] = Field(None, description="任务配置JSON字符串")
    task_interval: Optional[int] = Field(None, description="间隔秒数", ge=1, le=86400)
    task_crontab_minute: Optional[str] = Field(None, description="Crontab分钟", max_length=100)
    task_crontab_hour: Optional[str] = Field(None, description="Crontab小时", max_length=100)
    task_crontab_day_of_week: Optional[str] = Field(None, description="Crontab星期", max_length=100)
    task_crontab_day_of_month: Optional[str] = Field(None, description="Crontab日期", max_length=100)
    task_crontab_month_of_year: Optional[str] = Field(None, description="Crontab月份", max_length=100)
    task_args: Optional[str] = Field(None, description="任务参数JSON")
    task_kwargs: Optional[str] = Field(None, description="任务关键字参数JSON")
    task_enabled: Optional[bool] = Field(None, description="是否启用任务")
    
    @validator('task_args', 'task_kwargs', 'task_extra_config')
    def validate_json_fields(cls, v):
        """验证JSON字段格式"""
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('必须是有效的JSON格式')
        return v
    
    @validator('task_path')
    def validate_task_path(cls, v):
        """验证任务路径格式"""
        if v is not None:
            if not ('.' in v and not v.startswith('.') and not v.endswith('.')):
                raise ValueError('任务路径必须是有效的Python模块路径格式，如 "app.tasks.example_task"')
        return v


class ScheduledTaskResponse(BaseModel):
    """定时任务响应schema"""
    id: int
    name: str
    task: str
    description: Optional[str]
    enabled: bool
    args: Optional[str]
    kwargs: Optional[str]
    extra: Optional[str]
    interval: Optional[int]
    crontab_minute: Optional[str]
    crontab_hour: Optional[str]
    crontab_day_of_week: Optional[str]
    crontab_day_of_month: Optional[str]
    crontab_month_of_year: Optional[str]
    date_created: str
    date_changed: str

    class Config:
        from_attributes = True


class ScheduledTaskQueryParams(BaseModel):
    """定时任务查询参数schema"""
    search: Optional[str] = Field(None, description="搜索关键词", max_length=200)
    enabled_only: bool = Field(False, description="仅显示启用的任务")
    agent_id: Optional[str] = Field(None, description="智能体ID过滤", max_length=100)
    limit: Optional[int] = Field(10, description="返回数量", ge=1, le=100)
    offset: Optional[int] = Field(0, description="偏移量", ge=0)


class TaskExecutionLogResponse(BaseModel):
    """任务执行日志响应schema"""
    task_id: str
    task_name: str
    status: str
    result: Optional[str]
    date_created: str
    date_done: Optional[str]
    traceback: Optional[str]

    class Config:
        from_attributes = True


class CeleryTaskRecordResponse(BaseModel):
    """Celery任务记录响应schema"""
    id: int
    task_id: str
    task_name: str
    task_status: str
    task_args: Optional[str]
    task_kwargs: Optional[str]
    task_result: Optional[str]
    task_traceback: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class CeleryTaskRecordQueryParams(BaseModel):
    """Celery任务记录查询参数schema"""
    task_name: Optional[str] = Field(None, description="任务名称过滤", max_length=200)
    task_status: Optional[str] = Field(None, description="任务状态过滤", max_length=50)
    limit: Optional[int] = Field(10, description="返回数量", ge=1, le=100)
    offset: Optional[int] = Field(0, description="偏移量", ge=0)


class TaskStatusUpdate(BaseModel):
    """任务状态更新schema"""
    enabled: bool = Field(..., description="是否启用")


class TaskTriggerResponse(BaseModel):
    """任务触发响应schema"""
    message: str
    task_id: int
    trigger_time: datetime


class TaskStatisticsResponse(BaseModel):
    """任务统计响应schema"""
    task_statistics: List[Dict[str, Any]]
    record_statistics: List[Dict[str, Any]]