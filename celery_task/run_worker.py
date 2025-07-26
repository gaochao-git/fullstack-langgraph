#!/usr/bin/env python3
"""
Celery Worker 启动脚本
直接运行: python run_worker.py
"""

import os
import sys
from celery_app.celery import app

# ==================== 配置区域 ====================
# 可以根据需要修改以下配置

WORKER_NAME = 'agent_worker'      # Worker名称
LOG_LEVEL = 'INFO'                # 日志级别: DEBUG, INFO, WARNING, ERROR
CONCURRENCY = 4                   # 并发数
POOL_TYPE = 'threads'             # 池类型: threads, processes, gevent, eventlet
MAX_TASKS_PER_CHILD = 1000        # 每个子进程最大任务数
TIME_LIMIT = 3600                 # 任务硬超时(秒)
SOFT_TIME_LIMIT = 300             # 任务软超时(秒)

# ================================================

if __name__ == '__main__':
    # 添加当前目录到 Python 路径
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    print("🚀 启动 Celery Worker")
    print(f"配置: {WORKER_NAME}, 并发={CONCURRENCY}, 池={POOL_TYPE}")
    print("=" * 50)
    
    # 启动 Celery Worker
    argv = [
        'worker',
        f'--loglevel={LOG_LEVEL}',
        '-n', f'{WORKER_NAME}@%h',
        f'--concurrency={CONCURRENCY}',
        f'--pool={POOL_TYPE}',
        f'--max-tasks-per-child={MAX_TASKS_PER_CHILD}',
        f'--time-limit={TIME_LIMIT}',
        f'--soft-time-limit={SOFT_TIME_LIMIT}',
    ]
    
    app.worker_main(argv) 