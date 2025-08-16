"""
系统配置相关的Schema定义
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class UploadConfig(BaseModel):
    """文件上传配置"""
    max_upload_size_mb: int
    allowed_extensions: List[str]
    

class FeatureFlags(BaseModel):
    """功能开关"""
    enable_sso: bool = True
    enable_cas: bool = True
    enable_mcp: bool = True
    enable_scheduled_tasks: bool = True
    

class UIConfig(BaseModel):
    """UI配置"""
    theme: str = "light"
    logo_url: Optional[str] = None
    app_title: str = "OMind"
    

class SystemConfig(BaseModel):
    """系统配置"""
    upload: UploadConfig
    features: Optional[FeatureFlags] = None
    ui: Optional[UIConfig] = None
    custom: Optional[Dict[str, Any]] = None  # 保留扩展字段