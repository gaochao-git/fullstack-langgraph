"""
记忆管理模块的数据模型
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class MemoryCreate(BaseModel):
    """创建记忆的请求模型"""
    namespace: str = Field(..., description="记忆命名空间，如 'user_profile'")
    content: str = Field(..., description="记忆内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    namespace_params: Dict[str, str] = Field(default_factory=dict, description="命名空间参数，如 user_id, system_id")


class MemoryUpdate(BaseModel):
    """更新记忆的请求模型"""
    namespace: str = Field(..., description="记忆命名空间")
    memory_id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="新的记忆内容")
    namespace_params: Dict[str, str] = Field(default_factory=dict, description="命名空间参数")


class MemorySearch(BaseModel):
    """搜索记忆的请求模型"""
    namespace: str = Field(..., description="记忆命名空间")
    query: str = Field(..., description="搜索查询")
    limit: Optional[int] = Field(default=10, ge=1, le=100, description="返回结果数量")
    namespace_params: Dict[str, str] = Field(default_factory=dict, description="命名空间参数")


class MemoryResponse(BaseModel):
    """记忆响应模型"""
    id: str = Field(..., description="记忆ID")
    content: str = Field(..., description="记忆内容")
    score: Optional[float] = Field(None, description="相关性分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: Optional[str] = Field(None, description="创建时间")


class SystemArchitectureCreate(BaseModel):
    """系统架构信息创建模型"""
    system_id: str = Field(..., description="系统ID")
    architecture_info: Dict[str, Any] = Field(..., description="架构信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_id": "order_system",
                "architecture_info": {
                    "service_name": "订单管理系统",
                    "technology_stack": ["Java", "Spring Boot", "MySQL", "Redis"],
                    "deployment": {
                        "environment": "生产环境",
                        "servers": ["192.168.1.10", "192.168.1.11"],
                        "load_balancer": "nginx",
                        "database": {
                            "type": "MySQL",
                            "version": "8.0",
                            "cluster": "master-slave"
                        }
                    },
                    "dependencies": ["用户服务", "库存服务", "支付服务"],
                    "monitoring": {
                        "metrics": "Prometheus",
                        "logs": "ELK Stack",
                        "tracing": "Jaeger"
                    },
                    "contacts": {
                        "owner": "张三",
                        "team": "订单组",
                        "oncall": "李四"
                    }
                }
            }
        }


class IncidentCreate(BaseModel):
    """故障案例创建模型"""
    system_id: str = Field(..., description="系统ID")
    incident: Dict[str, Any] = Field(..., description="故障信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system_id": "order_system",
                "incident": {
                    "timestamp": "2024-01-15 10:30:00",
                    "symptoms": "订单创建接口响应时间超过5秒，大量超时",
                    "root_cause": "数据库连接池耗尽，连接数达到上限",
                    "solution": "1. 临时增加连接池大小到200\n2. 优化慢查询\n3. 增加数据库读副本",
                    "impact": "影响约1000个订单创建，持续时间30分钟",
                    "prevention": "设置连接池监控告警，当使用率超过80%时预警",
                    "severity": "high",
                    "tags": ["database", "performance", "connection-pool"]
                }
            }
        }


class UserPreferenceCreate(BaseModel):
    """用户偏好创建模型"""
    user_id: str = Field(..., description="用户ID")
    preference: Dict[str, Any] = Field(..., description="偏好设置")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "zhangsan",
                "preference": {
                    "diagnosis_detail_level": "expert",  # expert/intermediate/beginner
                    "preferred_language": "zh-CN",
                    "notification_methods": ["email", "wechat"],
                    "working_hours": "09:00-18:00",
                    "expertise_areas": ["database", "network", "kubernetes"],
                    "preferred_tools": ["kubectl", "mysql-client", "tcpdump"],
                    "display_preferences": {
                        "show_commands": True,
                        "show_explanations": True,
                        "use_charts": True
                    }
                }
            }
        }


class DiagnosisContext(BaseModel):
    """诊断上下文模型"""
    system_context: List[MemoryResponse] = Field(default_factory=list, description="系统架构相关记忆")
    similar_incidents: List[MemoryResponse] = Field(default_factory=list, description="相似故障案例")
    solution_patterns: List[MemoryResponse] = Field(default_factory=list, description="解决方案模式")
    user_preferences: List[MemoryResponse] = Field(default_factory=list, description="用户偏好")
    current_issue: str = Field(..., description="当前问题")
    timestamp: str = Field(..., description="时间戳")