#!/bin/bash
# Celery 快速启动脚本

echo "🚀 启动 Celery 任务调度系统"
echo "=================================="

cd "$(dirname "$0")"

# 启动 supervisor
python supervisor_manager.py start

echo ""
echo "✅ Celery 系统已启动!"
echo ""
echo "📋 常用命令:"
echo "   查看状态: python supervisor_manager.py status"
echo "   查看日志: python supervisor_manager.py logs"  
echo "   重启服务: python supervisor_manager.py restart-celery"
echo "   停止服务: python supervisor_manager.py stop"
echo ""
echo "📁 日志文件位置:"
echo "   Beat:   /tmp/celery-beat.log"
echo "   Worker: /tmp/celery-worker.log"