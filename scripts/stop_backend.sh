#!/bin/bash

echo "🛑 停止 OMind 后端服务..."

# 切换到项目根目录
cd "$(dirname "$0")/.."

if [ -f backend/pids/backend.pid ]; then
    PID=$(cat backend/pids/backend.pid)
    echo "正在停止进程 $PID..."
    kill $PID
    sleep 2
    if ! kill -0 $PID 2>/dev/null; then
        echo "✅ 服务已停止"
        rm -f backend/pids/backend.pid
    else
        echo "强制停止..."
        kill -9 $PID
        rm -f backend/pids/backend.pid
        echo "✅ 服务已强制停止"
    fi
else
    echo "⚠️  PID文件不存在，尝试杀死所有相关进程"
    pkill -f "gunicorn.*src.api.app:app" || true
    pkill -f "uvicorn.*src.api.app:app" || true
    echo "✅ 已尝试停止所有相关进程"
fi