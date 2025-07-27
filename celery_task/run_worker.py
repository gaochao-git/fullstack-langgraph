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

WORKER_NAME = 'multi_queue_worker'  # Worker名称
LOG_LEVEL = 'INFO'                # 日志级别: DEBUG, INFO, WARNING, ERROR
CONCURRENCY = 6                   # 并发数（处理多队列需要更多并发）
POOL_TYPE = 'threads'             # 池类型: threads, processes, gevent, eventlet
MAX_TASKS_PER_CHILD = 1000        # 每个子进程最大任务数
TIME_LIMIT = 3600                 # 任务硬超时(秒)
SOFT_TIME_LIMIT = 1800            # 任务软超时(秒)
QUEUES = 'system,priority_high,priority_low,celery'  # 队列优先级顺序（高到低）

# ================================================

if __name__ == '__main__':
    # 添加当前目录到 Python 路径
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    print("🚀 启动多队列 Celery Worker")
    print(f"配置: {WORKER_NAME}, 并发={CONCURRENCY}, 池={POOL_TYPE}")
    print(f"队列: {QUEUES} (按优先级顺序: system > priority_high > priority_low > celery)")
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
        '-Q', QUEUES,  # 处理多个队列，按优先级顺序
    ]
    
    app.worker_main(argv) 