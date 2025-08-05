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
    DATABASE_TYPE: str = "mysql"  # 改为默认使用MySQL
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None  
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306  # MySQL默认端口
    DATABASE_NAME: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # Checkpoint配置
    CHECKPOINTER_TYPE: str = "postgres"
    CHECKPOINTER_HOST: Optional[str] = None
    CHECKPOINTER_PORT: int = 5432
    CHECKPOINTER_DB: str = "langgraph_memory"
    CHECKPOINTER_USER: Optional[str] = None
    CHECKPOINTER_PASSWORD: Optional[str] = None
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
    
    # JWT认证配置
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 登录安全配置
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # 密码策略配置
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGITS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = True
    
    # MFA配置
    MFA_ISSUER_NAME: str = "智能运维平台"
    MFA_ENABLED: bool = False    
    # DeepSeek配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "logs"

    AUTH_MOCK: str = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_database_url() -> str:
    """获取数据库连接URL"""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # 根据DATABASE_TYPE选择相应的配置
    if settings.DATABASE_TYPE == "mysql":
        # 优先使用DATABASE_*环境变量，其次使用MYSQL_*
        user = settings.DATABASE_USER or settings.MYSQL_USER
        password = settings.DATABASE_PASSWORD or settings.MYSQL_PASSWORD
        host = settings.DATABASE_HOST or settings.MYSQL_HOST or "localhost"
        port = settings.DATABASE_PORT or settings.MYSQL_PORT or 3306
        db_name = settings.DATABASE_NAME or settings.MYSQL_DB
        
        if all([user, password, db_name]):
            return f"mysql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        # PostgreSQL配置
        user = settings.DATABASE_USER or settings.POSTGRES_USER
        password = settings.DATABASE_PASSWORD or settings.POSTGRES_PASSWORD
        host = settings.DATABASE_HOST or settings.POSTGRES_HOST or "localhost"
        port = settings.DATABASE_PORT or settings.POSTGRES_PORT or 5432
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


def get_checkpoint_uri() -> str:
    """获取checkpoint连接url"""
    if not all([settings.CHECKPOINTER_HOST, settings.CHECKPOINTER_PORT, settings.CHECKPOINTER_USER, settings.CHECKPOINTER_PASSWORD, settings.CHECKPOINTER_DB]):
        return None
    return f"postgresql://{settings.CHECKPOINTER_USER}:{settings.CHECKPOINTER_PASSWORD}@{settings.CHECKPOINTER_HOST}:{settings.CHECKPOINTER_PORT}/{settings.CHECKPOINTER_DB}"
