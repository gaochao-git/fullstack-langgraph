"""AI Model schemas - 增强验证"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
import json


class AIModelCreate(BaseModel):
    """创建AI模型的schema"""
    model_name: str = Field(..., description="模型名称", min_length=1, max_length=200)
    model_provider: str = Field(..., description="模型提供商", min_length=1, max_length=100)
    model_type: str = Field(..., description="模型类型", min_length=1, max_length=100)
    endpoint_url: str = Field(..., description="端点URL", min_length=1, max_length=500)
    api_key_value: Optional[str] = Field(None, description="API密钥", max_length=500)
    model_description: Optional[str] = Field(None, description="模型描述", max_length=1000)
    config_data: Optional[Dict[str, Any]] = Field(None, description="模型配置")
    
    @validator('endpoint_url')
    def validate_endpoint_url(cls, v):
        """验证端点URL格式"""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('端点URL必须是有效的HTTP/HTTPS URL')
        return v
    
    @validator('model_provider')
    def validate_model_provider(cls, v):
        """验证模型提供商"""
        allowed_providers = ['ollama', 'openai-compatible', 'deepseek', 'qwen', 'claude', 'gemini']
        if v not in allowed_providers:
            raise ValueError(f'模型提供商必须是以下之一: {", ".join(allowed_providers)}')
        return v


class AIModelUpdate(BaseModel):
    """更新AI模型的schema"""
    model_name: Optional[str] = Field(None, description="模型名称", min_length=1, max_length=200)
    model_provider: Optional[str] = Field(None, description="模型提供商", min_length=1, max_length=100)
    model_type: Optional[str] = Field(None, description="模型类型", min_length=1, max_length=100)
    endpoint_url: Optional[str] = Field(None, description="端点URL", min_length=1, max_length=500)
    api_key_value: Optional[str] = Field(None, description="API密钥", max_length=500)
    model_description: Optional[str] = Field(None, description="模型描述", max_length=1000)
    model_status: Optional[Literal["active", "inactive", "error"]] = Field(None, description="模型状态")
    config_data: Optional[Dict[str, Any]] = Field(None, description="模型配置")
    
    @validator('endpoint_url')
    def validate_endpoint_url(cls, v):
        """验证端点URL格式"""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('端点URL必须是有效的HTTP/HTTPS URL')
        return v
    
    @validator('model_provider')
    def validate_model_provider(cls, v):
        """验证模型提供商"""
        if v:
            allowed_providers = ['ollama', 'openai-compatible', 'deepseek', 'qwen', 'claude', 'gemini']
            if v not in allowed_providers:
                raise ValueError(f'模型提供商必须是以下之一: {", ".join(allowed_providers)}')
        return v


class AIModelResponse(BaseModel):
    """AI模型响应schema"""
    id: int
    model_id: str
    model_name: str
    model_provider: str
    model_type: str
    endpoint_url: str
    api_key_value: Optional[str]
    model_description: Optional[str]
    model_status: str
    config_data: Optional[str]  # JSON string
    create_by: str
    update_by: Optional[str]
    create_time: str
    update_time: str

    class Config:
        from_attributes = True


class AIModelQueryParams(BaseModel):
    """AI模型查询参数schema"""
    search: Optional[str] = Field(None, description="搜索关键词", max_length=200)
    provider: Optional[str] = Field(None, description="提供商过滤", max_length=100)
    status: Optional[Literal["active", "inactive", "error"]] = Field(None, description="状态过滤")
    model_type: Optional[str] = Field(None, description="模型类型过滤", max_length=100)
    limit: Optional[int] = Field(10, description="返回数量", ge=1, le=100)
    offset: Optional[int] = Field(0, description="偏移量", ge=0)


class AIModelTestRequest(BaseModel):
    """测试AI模型连接的请求schema"""
    model_provider: str = Field(..., description="模型提供商")
    model_type: str = Field(..., description="模型类型")
    endpoint_url: str = Field(..., description="端点URL", min_length=1, max_length=500)
    api_key_value: Optional[str] = Field(None, description="API密钥", max_length=500)
    timeout: int = Field(15, description="超时时间", ge=1, le=60)
    
    @validator('endpoint_url')
    def validate_endpoint_url(cls, v):
        """验证端点URL格式"""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('端点URL必须是有效的HTTP/HTTPS URL')
        return v
    
    @validator('model_provider')
    def validate_model_provider(cls, v):
        """验证模型提供商"""
        allowed_providers = ['ollama', 'openai-compatible', 'deepseek', 'qwen', 'claude', 'gemini']
        if v not in allowed_providers:
            raise ValueError(f'模型提供商必须是以下之一: {", ".join(allowed_providers)}')
        return v


class AIModelTestResponse(BaseModel):
    """测试AI模型连接的响应schema"""
    status: str
    message: str
    latency_ms: Optional[int] = None
    error_details: Optional[str] = None


class AIModelStatusUpdate(BaseModel):
    """更新AI模型状态的schema"""
    status: Literal["active", "inactive", "error"] = Field(..., description="模型状态")


class OllamaDiscoverRequest(BaseModel):
    """发现Ollama模型的请求schema"""
    endpoint_url: str = Field(..., description="Ollama端点URL", min_length=1, max_length=500)
    timeout: int = Field(15, description="超时时间", ge=1, le=60)
    
    @validator('endpoint_url')
    def validate_endpoint_url(cls, v):
        """验证端点URL格式"""
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('端点URL必须是有效的HTTP/HTTPS URL')
        return v


class OllamaDiscoverResponse(BaseModel):
    """发现Ollama模型的响应schema"""
    models: List[str]
    count: int