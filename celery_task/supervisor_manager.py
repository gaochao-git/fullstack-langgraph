#!/usr/bin/env python3
"""
Supervisor 管理脚本
用于启动、停止和管理 Celery 进程
"""

import os
import sys
import subprocess
import time
import signal

def run_command(cmd, description=""):
    """运行命令并显示结果"""
    if description:
        print(f"🔄 {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 成功: {description}")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ 失败: {description}")
            if result.stderr.strip():
                print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def start_supervisor():
    """启动 supervisord"""
    print("🚀 启动 Supervisor 管理器")
    print("=" * 50)
    
    # 检查是否已经运行
    if os.path.exists('/tmp/supervisord.pid'):
        try:
            with open('/tmp/supervisord.pid', 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)  # 检查进程是否存在
            print("⚠️  Supervisor 已经在运行")
            return True
        except (OSError, ProcessLookupError, ValueError):
            # PID 文件存在但进程不存在，删除旧文件
            os.remove('/tmp/supervisord.pid')
    
    # 启动 supervisord
    success = run_command("supervisord -c supervisord.conf", "启动 supervisord")
    if success:
        time.sleep(2)
        run_command("supervisorctl -c supervisord.conf status", "检查进程状态")
    
    return success

def stop_supervisor():
    """停止 supervisord"""
    print("🛑 停止 Supervisor 管理器")
    print("=" * 50)
    
    run_command("supervisorctl -c supervisord.conf stop all", "停止所有进程")
    time.sleep(2)
    run_command("supervisorctl -c supervisord.conf shutdown", "关闭 supervisord")

def restart_supervisor():
    """重启 supervisord"""
    print("🔄 重启 Supervisor 管理器")
    print("=" * 50)
    
    stop_supervisor()
    time.sleep(3)
    start_supervisor()

def status():
    """查看状态"""
    print("📊 Supervisor 状态")
    print("=" * 50)
    
    run_command("supervisorctl -c supervisord.conf status", "进程状态")

def logs():
    """查看日志"""
    print("📋 查看日志")
    print("=" * 50)
    
    print("=== Celery Beat 日志 ===")
    run_command("tail -20 /tmp/celery-beat.log", "Beat 标准输出")
    
    print("\n=== Celery Worker 日志 ===")
    run_command("tail -20 /tmp/celery-worker.log", "Worker 标准输出")

def restart_celery():
    """重启 Celery 进程"""
    print("🔄 重启 Celery 进程")
    print("=" * 50)
    
    run_command("supervisorctl -c supervisord.conf restart celery:*", "重启 Celery 组")
    time.sleep(2)
    run_command("supervisorctl -c supervisord.conf status", "检查状态")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
🎛️  Supervisor 管理脚本

使用方法:
    python supervisor_manager.py [命令]

可用命令:
    start      - 启动 supervisord 和所有进程
    stop       - 停止所有进程和 supervisord
    restart    - 重启 supervisord
    status     - 查看进程状态
    logs       - 查看最近日志
    restart-celery - 仅重启 Celery 进程
    
示例:
    python supervisor_manager.py start
    python supervisor_manager.py status
    python supervisor_manager.py logs
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # 切换到脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if command == 'start':
        start_supervisor()
    elif command == 'stop':
        stop_supervisor()
    elif command == 'restart':
        restart_supervisor()
    elif command == 'status':
        status()
    elif command == 'logs':
        logs()
    elif command == 'restart-celery':
        restart_celery()
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()