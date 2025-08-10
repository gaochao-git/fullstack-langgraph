"""
统一日志管理模块
提供结构化日志、链路追踪、日志轮转等功能
"""

import os
import json
import logging
import uuid
import socket
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from pathlib import Path
from contextvars import ContextVar
import colorlog

"""
日志规范：
日志文件名：
  请求日志文件名：{app_name}_acc.log
  <log_time>|<trace_id>|[parentId]|<request_type>|<app_name>|[idc]|<ip>|<start_time>|<cost_time>|<error_code>|[ext1]|[ext2]
  报警日志文件名：{app_name}_alam.log
  <log_time>|<trace_id>|<alarm_id>|<request_type>|<app_name>|idc|<ip>|<error_code>|<error_msg>|[ext1]|[ext2]
  应用日志文件名：{app_name}_app.log
  <log_time>|<log_level>|<thread_id>|<trace_id>|[idc]|<ip>|<filename>|<module>|<lineno>|<msg，能够打印错误堆栈>|[ext1]|[ext2]
"""

# 请求追踪上下文
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
agent_id_ctx: ContextVar[Optional[str]] = ContextVar('agent_id', default=None)

# 获取本机IP地址
def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到一个远程地址来获取本机IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()


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


class AccessLogFormatter(logging.Formatter):
    """请求日志格式化器 - 符合企业规范的管道分隔格式"""
    
    def format(self, record):
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        trace_id = request_id_ctx.get() or "-"
        parent_id = getattr(record, 'parent_id', '-')
        request_type = getattr(record, 'request_type', 'HTTP')
        app_name_val = getattr(record, 'app_name', 'omind')
        idc = getattr(record, 'idc', 'idc0')
        ip = getattr(record, 'ip', LOCAL_IP)
        start_time = getattr(record, 'start_time', '-')
        cost_time = getattr(record, 'cost_time', '-')
        error_code = getattr(record, 'error_code', '0')
        ext1 = getattr(record, 'ext1', '-')
        ext2 = getattr(record, 'ext2', '-')
        
        return f"{log_time}|{trace_id}|{parent_id}|{request_type}|{app_name_val}|{idc}|{ip}|{start_time}|{cost_time}|{error_code}|{ext1}|{ext2}"


class AlarmLogFormatter(logging.Formatter):
    """报警日志格式化器 - 符合企业规范的管道分隔格式"""
    
    def format(self, record):
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        trace_id = request_id_ctx.get() or "-"
        alarm_id = getattr(record, 'alarm_id', str(uuid.uuid4())[:8])
        request_type = getattr(record, 'request_type', 'ALARM')
        app_name_val = getattr(record, 'app_name', 'omind')
        idc = getattr(record, 'idc', 'idc0')
        ip = getattr(record, 'ip', LOCAL_IP)
        error_code = getattr(record, 'error_code', '500')
        error_msg = record.getMessage()
        ext1 = getattr(record, 'ext1', '-')
        ext2 = getattr(record, 'ext2', '-')
        
        return f"{log_time}|{trace_id}|{alarm_id}|{request_type}|{app_name_val}|{idc}|{ip}|{error_code}|{error_msg}|{ext1}|{ext2}"


class AppLogFormatter(logging.Formatter):
    """应用日志格式化器 - 符合企业规范的管道分隔格式"""
    
    def format(self, record):
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        log_level = record.levelname
        thread_id = record.thread
        trace_id = request_id_ctx.get() or "-"
        idc = getattr(record, 'idc', 'idc0')
        ip = getattr(record, 'ip', LOCAL_IP)
        msg = record.getMessage()
        
        # 添加异常堆栈信息
        if record.exc_info:
            msg += '\n' + self.formatException(record.exc_info)
        
        return f"{log_time}|{log_level}|{thread_id}|{trace_id}|{idc}|{ip}|{msg}"


class AuditLogFormatter(logging.Formatter):
    """API审计日志格式化器 - 专用于审计日志"""
    
    def format(self, record):
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 提取审计字段
        resource = getattr(record, 'resource', 'unknown')
        resource_id = getattr(record, 'resource_id', '-')
        user_id = getattr(record, 'user_id', 'anonymous')
        client_ip = getattr(record, 'client_ip', '-')
        server_ip = getattr(record, 'server_ip', LOCAL_IP)
        status_code = getattr(record, 'status_code', '-')
        process_time = getattr(record, 'process_time', '-')
        trace_id = getattr(record, 'trace_id', request_id_ctx.get() or '-')
        method = getattr(record, 'method', '-')
        full_url = getattr(record, 'full_url', '-')
        request_params = getattr(record, 'request_params', '-')
        msg = record.getMessage()
        
        # 审计格式：时间|资源|资源ID|用户|客户端IP|服务器IP|方法|完整URL|请求参数|状态码|处理时间|跟踪ID|消息
        return f"{log_time}|{resource}|{resource_id}|{user_id}|{client_ip}|{server_ip}|{method}|{full_url}|{request_params}|{status_code}|{process_time}|{trace_id}|{msg}"


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
            context_parts.append(request_id)
        if user_id:
            context_parts.append(f"user:{user_id}")
        if agent_id:
            context_parts.append(f"agent:{agent_id}")
        
        context_str = f" | {','.join(context_parts)}" if context_parts else ""
        
        # 处理 extra 字段
        extra_info = ""
        if hasattr(record, '__dict__'):
            # 获取所有非标准字段作为 extra 信息
            standard_fields = {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'message', 'getMessage',
                'exc_info', 'exc_text', 'stack_info', 'extra_fields'
            }
            extra_fields = {}
            for key, value in record.__dict__.items():
                if key not in standard_fields and not key.startswith('_'):
                    extra_fields[key] = value
            
            # 如果有 extra_fields 属性，使用它
            if hasattr(record, 'extra_fields'):
                extra_fields.update(record.extra_fields)
            
            if extra_fields:
                extra_items = [f"{k}={v}" for k, v in extra_fields.items()]
                extra_info = f" | {', '.join(extra_items)}"
        
        # 动态设置格式，包含上下文和额外信息
        location = "%(name)s:%(lineno)d:%(funcName)s"
        self._style._fmt = f"%(log_color)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | {location}{context_str} | %(message)s{extra_info}"
        
        return super().format(record)


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self._loggers = {}
        self._access_logger = None
        self._alarm_logger = None
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
        
        # 默认四文件配置 - acc/alarm/app/audit 日志分离
        if log_files is None:
            log_files = {
                "access": {
                    "filename": f"{app_name}_acc.log",
                    "level": "INFO",
                    "formatter": "access",
                    "filter": None
                },
                "alarm": {
                    "filename": f"{app_name}_alam.log", 
                    "level": "WARNING",
                    "formatter": "alarm",
                    "filter": None
                },
                "app": {
                    "filename": f"{app_name}_app.log",
                    "level": log_level,
                    "formatter": "app",
                    "filter": None
                },
                "audit": {
                    "filename": f"{app_name}_audit.log",
                    "level": "INFO",
                    "formatter": "audit",
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
            formatter_type = config.get("formatter", "app")
            if enable_json:
                handler.setFormatter(JSONFormatter())
            elif formatter_type == "access":
                handler.setFormatter(AccessLogFormatter())
            elif formatter_type == "alarm":
                handler.setFormatter(AlarmLogFormatter())
            elif formatter_type == "audit":
                handler.setFormatter(AuditLogFormatter())
            else:  # app or default
                handler.setFormatter(AppLogFormatter())
            
            file_handlers.append(handler)
        
        # 添加所有文件处理器
        for handler in file_handlers:
            root_logger.addHandler(handler)
        
        # 创建专用logger实例
        self._access_logger = logging.getLogger('access')
        self._access_logger.setLevel(logging.INFO)
        self._access_logger.handlers.clear()
        
        self._alarm_logger = logging.getLogger('alarm') 
        self._alarm_logger.setLevel(logging.WARNING)
        self._alarm_logger.handlers.clear()
        
        # 为专用logger添加对应的文件处理器
        for log_name, config in log_files.items():
            if log_name == "access":
                handler = self._create_file_handler(
                    log_path / config["filename"], rotation_type, max_file_size, backup_count
                )
                handler.setFormatter(AccessLogFormatter())
                self._access_logger.addHandler(handler)
                self._access_logger.propagate = False  # 不传播到root logger
            elif log_name == "alarm":
                handler = self._create_file_handler(
                    log_path / config["filename"], rotation_type, max_file_size, backup_count
                )
                handler.setFormatter(AlarmLogFormatter())
                self._alarm_logger.addHandler(handler)
                self._alarm_logger.propagate = False  # 不传播到root logger
        
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
                    context_parts.append(request_id)
                if user_id:
                    context_parts.append(f"user:{user_id}")
                if agent_id:
                    context_parts.append(f"agent:{agent_id}")
                
                context_str = f" | {','.join(context_parts)}" if context_parts else ""
                
                # 处理 extra 字段
                extra_info = ""
                if hasattr(record, '__dict__'):
                    # 获取所有非标准字段作为 extra 信息
                    standard_fields = {
                        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                        'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                        'thread', 'threadName', 'processName', 'process', 'message', 'getMessage',
                        'exc_info', 'exc_text', 'stack_info', 'extra_fields'
                    }
                    extra_fields = {}
                    for key, value in record.__dict__.items():
                        if key not in standard_fields and not key.startswith('_'):
                            extra_fields[key] = value
                    
                    # 如果有 extra_fields 属性，使用它
                    if hasattr(record, 'extra_fields'):
                        extra_fields.update(record.extra_fields)
                    
                    if extra_fields:
                        extra_items = [f"{k}={v}" for k, v in extra_fields.items()]
                        extra_info = f" | {', '.join(extra_items)}"
                
                # 基础格式
                base_format = f"%(asctime)s | %(levelname)s | %(name)s:%(lineno)d:%(funcName)s{context_str} | %(message)s{extra_info}"
                formatter = logging.Formatter(base_format)
                return formatter.format(record)
        
        return FileFormatter()
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]
    
    def get_access_logger(self) -> logging.Logger:
        """获取请求日志记录器"""
        if not self._access_logger:
            raise RuntimeError("请先调用 setup_logging() 初始化日志系统")
        return self._access_logger
    
    def get_alarm_logger(self) -> logging.Logger:
        """获取报警日志记录器"""
        if not self._alarm_logger:
            raise RuntimeError("请先调用 setup_logging() 初始化日志系统")
        return self._alarm_logger
    
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
        return str(uuid.uuid4()).replace('-', '')


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


def get_access_logger() -> logging.Logger:
    """获取请求日志记录器的便捷函数"""
    return logger_manager.get_access_logger()


def get_alarm_logger() -> logging.Logger:
    """获取报警日志记录器的便捷函数"""
    return logger_manager.get_alarm_logger()


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


# 中间件辅助函数
def log_request(
    method: str,
    url: str, 
    status_code: int,
    response_time: float,
    ip: str = "-",
    user_id: str = None,
    error_code: str = "0",
    **extra_kwargs
):
    """记录请求日志的辅助函数 - 供中间件使用"""
    access_logger = get_access_logger()
    
    # 构建日志记录
    record = access_logger.makeRecord(
        access_logger.name,
        logging.INFO,
        "",
        0,
        f"{method} {url}",
        (),
        None
    )
    
    # 添加请求相关字段
    record.request_type = method
    record.ip = LOCAL_IP  # 使用本机IP，忽略传入的客户端IP
    record.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    record.cost_time = f"{response_time:.3f}ms"
    record.error_code = str(status_code) if status_code >= 400 else error_code
    record.app_name = 'omind'
    record.parent_id = extra_kwargs.get('parent_id', '-')
    record.idc = extra_kwargs.get('idc', 'idc0')
    record.ext1 = extra_kwargs.get('ext1', f"client:{extra_kwargs.get('client_ip', '-')}" if extra_kwargs.get('client_ip') else '-')
    record.ext2 = extra_kwargs.get('ext2', f"path:{url}")
    
    # 添加额外字段
    for key, value in extra_kwargs.items():
        setattr(record, key, value)
    
    # 记录日志
    access_logger.handle(record)


def log_alarm(
    error_msg: str,
    error_code: str = "500",
    alarm_id: str = None,
    ip: str = "-",
    **extra_kwargs
):
    """记录报警日志的辅助函数"""
    alarm_logger = get_alarm_logger()
    
    # 构建日志记录
    record = alarm_logger.makeRecord(
        alarm_logger.name,
        logging.ERROR,
        "",
        0,
        error_msg,
        (),
        None
    )
    
    # 添加报警相关字段
    record.alarm_id = alarm_id or str(uuid.uuid4())[:8]
    record.error_code = error_code
    record.ip = LOCAL_IP  # 使用本机IP
    record.app_name = 'omind'
    record.idc = extra_kwargs.get('idc', 'idc0')
    record.request_type = extra_kwargs.get('request_type', 'ALARM')
    record.ext1 = extra_kwargs.get('ext1', '-')
    record.ext2 = extra_kwargs.get('ext2', '-')
    
    # 添加额外字段
    for key, value in extra_kwargs.items():
        setattr(record, key, value)
    
    # 记录日志
    alarm_logger.handle(record)


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