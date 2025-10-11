"""敏感数据扫描相关的Schema定义"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ScanTaskCreate(BaseModel):
    """创建扫描任务请求"""
    file_ids: List[str] = Field(..., min_items=1, description="要扫描的文件ID列表")
    config_id: Optional[str] = Field(None, description="使用的配置ID，不传则使用默认配置")
    max_workers: int = Field(10, ge=1, le=50, description="最大并行工作线程数")
    batch_length: int = Field(10, ge=1, le=100, description="批处理长度")
    extraction_passes: int = Field(1, ge=1, le=5, description="提取遍数")
    max_char_buffer: int = Field(2000, ge=100, le=10000, description="最大字符缓冲区大小")

    class Config:
        json_schema_extra = {
            "example": {
                "file_ids": ["file_1234567890ab", "file_abcdef123456"],
                "config_id": "config_123456789abc",
                "max_workers": 10,
                "batch_length": 10,
                "extraction_passes": 1,
                "max_char_buffer": 2000
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


# ============= 扫描配置相关 Schema =============

class ExampleExtraction(BaseModel):
    """示例中的提取项"""
    extraction_class: str = Field(..., description="敏感信息类型")
    extraction_text: str = Field(..., description="提取的文本")


class ScanExample(BaseModel):
    """Few-shot 示例"""
    text: str = Field(..., description="示例文本")
    extractions: List[ExampleExtraction] = Field(..., description="提取的敏感信息列表")


class ScanConfigCreate(BaseModel):
    """创建扫描配置请求"""
    config_name: str = Field(..., min_length=1, max_length=200, description="配置名称")
    config_description: Optional[str] = Field(None, description="配置描述")
    prompt_description: str = Field(..., min_length=1, description="扫描提示词")
    examples: Optional[List[ScanExample]] = Field(None, description="Few-shot示例列表")
    is_default: bool = Field(False, description="是否设为默认配置")

    class Config:
        json_schema_extra = {
            "example": {
                "config_name": "标准敏感信息扫描",
                "config_description": "识别常见的个人敏感信息",
                "prompt_description": "识别并提取文本中的敏感信息，包括身份证号、手机号、银行卡号等",
                "examples": [
                    {
                        "text": "客户姓名：李明，手机：13912345678",
                        "extractions": [
                            {"extraction_class": "姓名", "extraction_text": "李明"},
                            {"extraction_class": "手机号", "extraction_text": "13912345678"}
                        ]
                    }
                ],
                "is_default": False
            }
        }


class ScanConfigUpdate(BaseModel):
    """更新扫描配置请求"""
    config_name: Optional[str] = Field(None, min_length=1, max_length=200, description="配置名称")
    config_description: Optional[str] = Field(None, description="配置描述")
    prompt_description: Optional[str] = Field(None, min_length=1, description="扫描提示词")
    examples: Optional[List[ScanExample]] = Field(None, description="Few-shot示例列表")
    is_default: Optional[bool] = Field(None, description="是否设为默认配置")
    status: Optional[str] = Field(None, description="配置状态：active-启用，inactive-禁用")


class ScanConfigResponse(BaseModel):
    """扫描配置响应"""
    config_id: str
    config_name: str
    config_description: Optional[str] = None
    prompt_description: str
    examples: Optional[List[ScanExample]] = None
    is_default: bool
    status: str
    create_by: str
    update_by: Optional[str] = None
    create_time: str
    update_time: str