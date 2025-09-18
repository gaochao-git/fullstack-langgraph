#!/usr/bin/env python
"""
后端服务管理脚本
使用 Gunicorn 管理后端进程
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

# 获取脚本所在目录
BASE_DIR = Path(__file__).parent.absolute()
os.chdir(BASE_DIR)

# 加载 .env 文件
def load_env():
    """加载 .env 文件中的环境变量"""
    from dotenv import load_dotenv
    load_dotenv()

# 读取配置
def get_config():
    """从环境变量中获取配置"""
    return {
        'env': os.getenv('ENV', 'production'),
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': os.getenv('PORT', '8000'),
        'workers': os.getenv('WORKERS', '2'),
        'pid_file': 'pids/gunicorn.pid',
        'log_file': 'logs/gunicorn.log'
    }

def ensure_dirs():
    """确保必要的目录存在"""
    dirs = ['pids', 'logs']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def start():
    """启动服务"""
    ensure_dirs()
    config = get_config()
    
    # 检查是否已在运行
    pid_file = Path(config['pid_file'])
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)  # 检查进程是否存在
            print(f"服务已经在运行 (PID: {pid})")
            return
        except (ValueError, ProcessLookupError):
            # PID文件存在但进程不存在，删除PID文件
            pid_file.unlink()
    
    # 使用 gunicorn 启动
    cmd = [
        sys.executable, '-m', 'gunicorn',
        'src.main:omind_app',
        '--bind', f"{config['host']}:{config['port']}",
        '--workers', config['workers'],
        '--worker-class', 'uvicorn.workers.UvicornWorker',
        '--pid', config['pid_file'],
        '--daemon',
        '--access-logfile', config['log_file'],
        '--error-logfile', config['log_file']
    ]
    
    # 开发环境添加 reload
    if config['env'].lower() == 'development':
        cmd.insert(-2, '--reload')
        print(f"启动开发服务器 (自动重载): {config['host']}:{config['port']}")
    else:
        print(f"启动生产服务器: {config['host']}:{config['port']}")
    
    # 启动服务
    subprocess.run(cmd, check=True)
    print("服务已启动")

def stop():
    """停止服务"""
    config = get_config()
    pid_file = Path(config['pid_file'])
    
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"停止服务 (PID: {pid})")
            pid_file.unlink()
        except (ValueError, ProcessLookupError):
            print("PID文件存在但进程已经不存在")
            pid_file.unlink()
    else:
        # 尝试通过进程名停止
        print("PID文件不存在，尝试通过进程名停止")
        subprocess.run(['pkill', '-f', 'gunicorn.*src.main:omind_app'])
    

def status():
    """查看服务状态"""
    config = get_config()
    pid_file = Path(config['pid_file'])
    
    print(f"环境: {config['env']}")
    
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"服务运行中 (PID: {pid})")
            print(f"端口: {config['port']}")
            print(f"工作进程数: {config['workers']}")
            if config['env'].lower() == 'development':
                print("自动重载: 已启用")
        except (ValueError, ProcessLookupError):
            print("服务未运行 (PID文件存在但进程不存在)")
    else:
        print("服务未运行")

def restart():
    """重启服务"""
    stop()
    print("等待服务停止...")
    import time
    time.sleep(2)
    start()

def sync_permissions():
    """同步API权限到数据库"""
    print("同步API权限...")
    cmd = [sys.executable, '-m', 'src.scripts.sync_permissions']
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print("权限同步成功")
    else:
        print("权限同步失败")
        sys.exit(1)

def main():
    """主函数"""
    # 加载环境变量
    load_env()
    
    # 解析命令
    if len(sys.argv) < 2:
        print("使用方法: python manage.py {start|stop|restart|status|sync-permissions}")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'start':
        start()
    elif command == 'stop':
        stop()
    elif command == 'restart':
        restart()
    elif command == 'status':
        status()
    elif command == 'sync-permissions':
        sync_permissions()
    else:
        print(f"未知命令: {command}")
        print("使用方法: python manage.py {start|stop|restart|status|sync-permissions}")
        sys.exit(1)

if __name__ == '__main__':
    main()