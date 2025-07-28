"""
统一日志管理模块
提供结构化日志、链路追踪、日志轮转等功能
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pathlib import Path
from contextvars import ContextVar
import colorlog

# 请求追踪上下文
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
agent_id_ctx: ContextVar[Optional[str]] = ContextVar('agent_id', default=None)


class JSONFormatter(logging.Formatter):
    """JSON格式化器，输出结构化日志"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 添加请求追踪信息
        request_id = request_id_ctx.get()
        if request_id:
            log_entry['request_id'] = request_id
            
        user_id = user_id_ctx.get()
        if user_id:
            log_entry['user_id'] = user_id
            
        agent_id = agent_id_ctx.get()
        if agent_id:
            log_entry['agent_id'] = agent_id
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredConsoleFormatter(colorlog.ColoredFormatter):
    """使用colorlog的彩色控制台格式化器"""
    
    def format(self, record):
        # 获取上下文信息
        request_id = request_id_ctx.get()
        user_id = user_id_ctx.get()
        agent_id = agent_id_ctx.get()
        
        # 构建上下文部分
        context_parts = []
        if request_id:
            context_parts.append(f"req:{request_id[:8]}")
        if user_id:
            context_parts.append(f"user:{user_id}")
        if agent_id:
            context_parts.append(f"agent:{agent_id}")
        
        context_str = f" | [{','.join(context_parts)}]" if context_parts else ""
        
        # 动态设置格式，包含上下文
        location = "%(name)s:%(lineno)d:%(funcName)s"
        self._style._fmt = f"%(log_color)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | {location}{context_str} | %(message)s"
        
        return super().format(record)


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self._loggers = {}
        self._configured = False
    
    def setup_logging(
        self,
        log_level: str = "INFO",
        log_dir: str = "logs",
        app_name: str = "langgraph-platform",
        enable_json: bool = False,
        rotation_type: str = "time",  # "size" 或 "time"
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        log_files: Dict[str, Dict] = None  # 支持多文件配置
    ):
        """配置日志系统"""
        if self._configured:
            return
        
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 控制台处理器 - 使用colorlog
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = ColoredConsoleFormatter(
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'purple'
            }
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 默认单文件配置
        if log_files is None:
            log_files = {
                "app": {
                    "filename": f"{app_name}.log",
                    "level": log_level,
                    "filter": None
                }
            }
        
        # 创建文件处理器
        file_handlers = []
        for log_name, config in log_files.items():
            log_file = log_path / config["filename"]
            handler = self._create_file_handler(
                log_file, rotation_type, max_file_size, backup_count
            )
            handler.setLevel(getattr(logging, config["level"].upper()))
            
            # 添加过滤器（如果有）
            if config.get("filter"):
                handler.addFilter(config["filter"])
            
            # 设置格式化器
            if enable_json:
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(self._create_file_formatter())
            
            file_handlers.append(handler)
        
        # 添加所有文件处理器
        for handler in file_handlers:
            root_logger.addHandler(handler)
        
        # 配置第三方库日志级别
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)  # 关闭uvicorn访问日志
        logging.getLogger('uvicorn').setLevel(logging.WARNING)
        logging.getLogger('fastapi').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)  # 减少HTTP请求日志
        logging.getLogger('openai').setLevel(logging.WARNING)  # 减少OpenAI日志
        logging.getLogger('langchain').setLevel(logging.WARNING)  # 减少LangChain日志
        
        self._configured = True
        
        # 记录配置完成日志
        logger = self.get_logger(__name__)
        log_file_names = [config["filename"] for config in log_files.values()]
        logger.info(f"📝 日志系统配置完成", extra={
            'log_level': log_level,
            'log_dir': str(log_path),
            'enable_json': enable_json,
            'rotation_type': rotation_type,
            'log_files': log_file_names
        })
    
    def _create_file_handler(self, log_file, rotation_type, max_file_size, backup_count):
        """创建文件处理器的辅助方法"""
        if rotation_type == "size":
            # 按大小轮转
            handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            # 按时间轮转
            handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            # 设置备份文件的日期后缀格式
            handler.suffix = "%Y%m%d"
        
        return handler
    
    def _create_file_formatter(self):
        """创建带上下文的文件格式化器"""
        class FileFormatter(logging.Formatter):
            def format(self, record):
                # 获取上下文信息
                request_id = request_id_ctx.get()
                user_id = user_id_ctx.get()
                agent_id = agent_id_ctx.get()
                
                # 构建上下文字符串
                context_parts = []
                if request_id:
                    context_parts.append(f"req:{request_id[:8]}")
                if user_id:
                    context_parts.append(f"user:{user_id}")
                if agent_id:
                    context_parts.append(f"agent:{agent_id}")
                
                context_str = f" | [{','.join(context_parts)}]" if context_parts else ""
                
                # 基础格式
                base_format = f"%(asctime)s | %(levelname)s | %(name)s:%(lineno)d:%(funcName)s{context_str} | %(message)s"
                formatter = logging.Formatter(base_format)
                return formatter.format(record)
        
        return FileFormatter()
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    def set_request_context(
        self,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        """设置请求上下文"""
        if request_id:
            request_id_ctx.set(request_id)
        if user_id:
            user_id_ctx.set(user_id)
        if agent_id:
            agent_id_ctx.set(agent_id)
    
    def clear_request_context(self):
        """清除请求上下文"""
        request_id_ctx.set(None)
        user_id_ctx.set(None)
        agent_id_ctx.set(None)
    
    def generate_request_id(self) -> str:
        """生成请求ID"""
        return str(uuid.uuid4())


# 全局日志管理器实例
logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return logger_manager.get_logger(name)


def setup_logging(**kwargs):
    """设置日志系统的便捷函数"""
    return logger_manager.setup_logging(**kwargs)


def set_request_context(**kwargs):
    """设置请求上下文的便捷函数"""
    return logger_manager.set_request_context(**kwargs)


def clear_request_context():
    """清除请求上下文的便捷函数"""
    return logger_manager.clear_request_context()


def log_with_context(logger: logging.Logger, level: str, message: str, **extra_fields):
    """带上下文的日志记录"""
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None
    )
    record.extra_fields = extra_fields
    logger.handle(record)


class LoggerMixin:
    """日志混入类，为其他类提供日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志记录器"""
        return get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def log_info(self, message: str, **extra):
        """记录信息日志"""
        log_with_context(self.logger, 'INFO', message, **extra)
    
    def log_error(self, message: str, **extra):
        """记录错误日志"""
        log_with_context(self.logger, 'ERROR', message, **extra)
    
    def log_warning(self, message: str, **extra):
        """记录警告日志"""
        log_with_context(self.logger, 'WARNING', message, **extra)
    
    def log_debug(self, message: str, **extra):
        """记录调试日志"""
        log_with_context(self.logger, 'DEBUG', message, **extra)


# 装饰器：自动记录函数执行时间
def log_execution_time(logger_name: Optional[str] = None):
    """记录函数执行时间的装饰器"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Function {func.__name__} executed successfully", extra={
                    'function': func.__name__,
                    'execution_time': f"{execution_time:.3f}s",
                    'status': 'success'
                })
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Function {func.__name__} failed", extra={
                    'function': func.__name__,
                    'execution_time': f"{execution_time:.3f}s",
                    'status': 'error',
                    'error': str(e)
                })
                raise
        
        return wrapper
    return decorator


# 装饰器：自动记录异步函数执行时间
def log_async_execution_time(logger_name: Optional[str] = None):
    """记录异步函数执行时间的装饰器"""
    def decorator(func):
        import functools
        import time
        import asyncio
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Async function {func.__name__} executed successfully", extra={
                    'function': func.__name__,
                    'execution_time': f"{execution_time:.3f}s",
                    'status': 'success'
                })
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Async function {func.__name__} failed", extra={
                    'function': func.__name__,
                    'execution_time': f"{execution_time:.3f}s",
                    'status': 'error',
                    'error': str(e)
                })
                raise
        
        return wrapper
    return decorator