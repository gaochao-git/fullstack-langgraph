"""
应用配置管理模块
统一管理所有配置项，支持环境变量和默认值
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "LangGraph Platform API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "development"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # 数据库配置  
    DATABASE_URL: Optional[str] = None
    DATABASE_TYPE: str = "postgresql"
    # 支持两种命名方式：DATABASE_* 和 POSTGRES_*
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None  
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: Optional[str] = None
    # 别名支持
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None
    # Checkpoint配置
    CHECKPOINTER_TYPE: str = "postgres"
    POSTGRES_CHECKPOINT_URI: Optional[str] = None
    
    # MySQL配置
    MYSQL_HOST: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DB: Optional[str] = None
    
    # Redis配置
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # API配置
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 外部服务配置
    ELASTICSEARCH_URL: Optional[str] = None
    ZABBIX_URL: Optional[str] = None
    ZABBIX_USER: Optional[str] = None
    ZABBIX_PASSWORD: Optional[str] = None
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    
    # DeepSeek配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_database_url() -> str:
    """获取数据库连接URL"""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # 优先使用DATABASE_*环境变量
    user = settings.DATABASE_USER or settings.POSTGRES_USER
    password = settings.DATABASE_PASSWORD or settings.POSTGRES_PASSWORD
    host = settings.DATABASE_HOST or settings.POSTGRES_HOST
    port = settings.DATABASE_PORT or settings.POSTGRES_PORT
    db_name = settings.DATABASE_NAME or settings.POSTGRES_DB
    
    if all([user, password, db_name]):
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    
    raise ValueError("DATABASE_URL or database credentials must be provided")


def get_mysql_url() -> Optional[str]:
    """获取MySQL连接URL"""
    if not all([settings.MYSQL_HOST, settings.MYSQL_USER, settings.MYSQL_PASSWORD, settings.MYSQL_DB]):
        return None
    
    return (
        f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
    )


def get_redis_url() -> str:
    """获取Redis连接URL"""
    if settings.REDIS_URL:
        return settings.REDIS_URL
    
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"