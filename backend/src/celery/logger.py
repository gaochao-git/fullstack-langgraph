"""
统一的日志配置模块
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 日志配置
from src.shared.core.config import settings

LOG_LEVEL = os.getenv('CELERY_LOG_LEVEL', 'INFO')
# 使用项目统一的日志目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
LOG_DIR = os.path.join(BASE_DIR, settings.LOG_DIR, 'celery')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger(name=None):
    """
    设置并返回logger实例
    
    Args:
        name: logger名称，默认使用调用模块的名称
        
    Returns:
        logging.Logger: 配置好的logger实例
    """
    logger = logging.getLogger(name)
    
    # 如果logger已经有handler，说明已经配置过了
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # 文件处理器 - 按日期分割
    log_filename = f"celery_{datetime.now().strftime('%Y%m%d')}.log"
    file_path = os.path.join(LOG_DIR, log_filename)
    
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    file_handler.setFormatter(console_formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 防止日志传播到根logger
    logger.propagate = False
    
    return logger

# 获取logger的便捷函数
def get_logger(name=None):
    """获取配置好的logger"""
    return setup_logger(name)

# 初始化根logger
root_logger = setup_logger('celery_app')