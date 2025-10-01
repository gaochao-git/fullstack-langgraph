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
    REDIS_PASSWORD: Optional[str] = None
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
     
    # LLM通用配置
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    
    # 语音模型配置
    AUDIO_MODEL_NAME: Optional[str] = None
    AUDIO_API_BASE_URL: Optional[str] = None
    AUDIO_API_KEY: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "logs"
    
    # 报警服务配置
    ALARM_API_URL: Optional[str] = None  # 报警数据获取接口URL，从.env文件读取
    
    # 文件上传配置
    MAX_UPLOAD_SIZE_MB: int = 100  # 最大上传文件大小（MB）- 增加到100MB以支持大文档
    UPLOAD_ALLOWED_EXTENSIONS: List[str] = [
        # 文档类
        ".pdf", ".doc", ".docx", ".txt", ".md", ".pptx", ".ppt",
        # 表格类
        ".csv", ".xlsx", ".xls",
        # 图片类
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",
        # 代码和配置文件类
        ".sql", ".yaml", ".yml", ".json", ".xml", ".ini", ".conf", ".cfg",
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
        ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt", 
        ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
        ".html", ".htm", ".css", ".scss", ".sass", ".less",
        # 日志和其他文本文件
        ".log", ".out", ".err", ".trace",
        ".properties", ".env", ".toml",
        ".rst", ".org", ".tex", ".rtf"
    ]  # 允许的文件扩展名
    
    # 图片处理并发配置
    IMAGE_PROCESS_MAX_CONCURRENT: int = 5  # 图片处理最大并发数
    IMAGE_PROCESS_TIMEOUT: int = 30  # 单张图片处理超时时间（秒）
    
    # 文档目录配置
    DOCUMENT_DIR: str = "documents"  # 文档根目录，包含 uploads/, templates/, generated/ 子目录

    # CAS认证配置
    CAS_SERVER_URL: str = "http://localhost:5555/cas"
    CAS_VERSION: str = "3"
    CAS_VERIFY_SSL: bool = False
    CAS_SESSION_TIMEOUT: int = 36000
    CAS_CHECK_NEXT: bool = True
    CAS_SERVICE_URL: str = "http://localhost:3000/sso/callback"
    CAS_SINGLE_LOGOUT_ENABLED: bool = True

    NO_PROXY: str = ""  # 结局claude 本地开proxy影响httpx调用其他接口
    
    # AI 视觉模型配置
    VISION_MODEL_NAME: str = "gpt-4-vision-preview"  # 视觉模型名称
    VISION_API_BASE_URL: str = "https://api.openai.com/v1"  # API地址
    VISION_API_KEY: Optional[str] = None  # API密钥
    # AI 嵌入模型配置
    EMBEDDING_MODEL_NAME: str = "gpt-4-embedding"  # 视觉模型名称
    EMBEDDING_API_BASE_URL: str = "https://api.openai.com/v1"  # API地址
    EMBEDDING_API_KEY: Optional[str] = None  # API密钥

    # 多模态服务配置 (用于独立的多模态服务，现已集成到agent内部)
    MULTIMODAL_SERVICE_URL: Optional[str] = None
    MULTIMODAL_SERVICE_TIMEOUT: int = 30
    
    # MCP配置
    MCP_RELOAD_PID: Optional[str] = None  # MCP Gateway PID文件路径
    MCP_GATEWAY_URL: Optional[str] = None  # MCP Gateway访问地址
    
    # 消息监控配置
    MULTI_TURN_CONTEXT_THRESHOLD: float = 0.8  # 当总消息量超过模型上下文长度的多少比例时触发警告（默认 0.8 = 80%）
    MULTIMODAL_SERVICE_API_KEY: Optional[str] = None
    
    # Celery配置
    CELERY_BROKER_URL: Optional[str] = None  # Celery broker URL
    CELERY_RESULT_BACKEND: Optional[str] = None  # Celery result backend

    # 主机资源池服务环境配置
    HARDWARE_SERVICE_BASE_URL: Optional[str] = None # 主机资源池服务地址
    HARDWARE_SERVICE_TOKEN: Optional[str] = "" # 主机资源池服务token 
    HARDWARE_SERVICE_USERNAME: Optional[str] = None # 主机资源池服务用户名
    HARDWARE_SERVICE_PASSWORD: Optional[str] = None # 主机资源池服务密码
    HARDWARE_SERVICE_LOGIN_ENDPOINT: Optional[str] = None # 主机资源池服务登录地址
    TOKEN_REFRESH_MARGIN: int = 120 # 登录token刷新时间
    
    # Mem0 长期记忆配置
    MEM0_ENABLE: bool = True  # 是否启用Mem0
    MEM0_EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"  # 嵌入模型
    MEM0_EMBEDDING_DIM: int = 1024  # 嵌入维度
    
    # 向量存储配置
    MEM0_VECTOR_DB_TYPE: str = "pgvector"  # 向量数据库类型
    MEM0_VECTOR_DB_HOST: str = "82.156.146.51"  # 向量数据库主机
    MEM0_VECTOR_DB_PORT: int = 5432  # 向量数据库端口
    MEM0_VECTOR_DB_NAME: str = "omind_memory"  # 向量数据库名称
    MEM0_VECTOR_DB_USER: Optional[str] = None  # 向量数据库用户
    MEM0_VECTOR_DB_PASSWORD: Optional[str] = None  # 向量数据库密码
    MEM0_VECTOR_DB_TABLE: str = "enterprise_memories"  # 向量存储表名
    
    # 记忆配置
    MEM0_MEMORY_VERSION: str = "v1.1"  # 记忆版本控制
    MEM0_SEARCH_LIMIT: int = 10  # 默认搜索返回数量
    MEM0_RELEVANCE_THRESHOLD: float = 0.7  # 相关性阈值
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def UPLOAD_DIR(self) -> str:
        """上传文件存储目录"""
        return os.path.join(self.DOCUMENT_DIR, "uploads")


# 创建全局配置实例
settings = Settings()
