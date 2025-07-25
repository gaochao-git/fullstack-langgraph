#!/usr/bin/env python
"""
Celery Beat 启动脚本
用于启动 Celery Beat 服务，负责定时任务的调度
"""
import os
import sys
import logging
from celery_app.celery import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("正在启动 Celery Beat 服务...")
    
    # 添加当前目录到 Python 路径
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # 构建 Celery Beat 命令参数
    argv = [
        'beat',
        '--loglevel=INFO',
    ]
    
    # 如果提供了 PID 文件路径参数
    if len(sys.argv) > 1:
        pid_file = sys.argv[1]
        argv.extend(['--pidfile', pid_file])
        logger.info(f"PID 文件将保存到: {pid_file}")
    
    # 如果提供了调度数据库文件路径参数
    if len(sys.argv) > 2:
        schedule_db = sys.argv[2]
        argv.extend(['--schedule', schedule_db])
        logger.info(f"调度数据库将保存到: {schedule_db}")
    
    logger.info("Celery Beat 服务启动命令: " + " ".join(argv))
    
    # 启动 Celery Beat，使用与worker相同的方式
    app.start(argv) 