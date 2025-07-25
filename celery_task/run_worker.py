import os
import sys
from celery_app.celery import app

if __name__ == '__main__':
    # 添加当前目录到 Python 路径
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # 启动 Celery Worker
    argv = [
        'worker',
        '--loglevel=INFO',
        '-n', 'worker1@%h',
    ]
    
    app.worker_main(argv) 