"""敏感数据扫描相关的Schema定义"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ScanTaskCreate(BaseModel):
    """创建扫描任务请求"""
    file_ids: List[str] = Field(..., min_items=1, description="要扫描的文件ID列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_ids": ["file_1234567890ab", "file_abcdef123456"]
            }
        }


class ScanProgress(BaseModel):
    """扫描进度信息"""
    phase: str = Field(..., description="当前阶段：pending/reading/scanning/completed/failed")
    current: int = Field(..., description="当前处理数")
    total: int = Field(..., description="总数")
    message: str = Field(..., description="进度消息")


class FileStatusSummary(BaseModel):
    """文件状态摘要"""
    pending: Optional[int] = 0
    reading: Optional[int] = 0
    read_complete: Optional[int] = 0
    scanning: Optional[int] = 0
    completed: Optional[int] = 0
    failed: Optional[int] = 0


class ScanTaskProgress(BaseModel):
    """扫描任务进度响应"""
    task_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    progress: ScanProgress
    statistics: Dict[str, Any]
    file_status_summary: Optional[FileStatusSummary] = None
    errors: List[str] = []
    create_time: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class FileScanResult(BaseModel):
    """单个文件的扫描结果"""
    file_id: str
    file_name: Optional[str] = None
    status: str
    jsonl_path: Optional[str] = None
    html_path: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    sensitive_items: int = 0


class TaskSummary(BaseModel):
    """任务摘要"""
    total_files: int
    completed_files: int
    failed_files: int


class ScanTaskResult(BaseModel):
    """扫描任务结果响应"""
    task_id: str
    status: str
    summary: TaskSummary
    files: List[FileScanResult]
    completed_time: Optional[str] = None