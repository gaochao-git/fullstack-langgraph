#!/bin/bash

# 生产环境启动脚本
# 使用方法: ./start.sh [--workers N] [--port PORT]

set -e

# 默认参数
WORKERS=2
PORT=8000

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--workers N] [--port PORT]"
            exit 1
            ;;
    esac
done

echo "🚀 启动 Fullstack LangGraph 生产服务..."
echo "端口: $PORT, Worker进程数: $WORKERS"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 ./pre_env.sh"
    exit 1
fi

# 停止现有服务
if [ -f "backend.pid" ]; then
    echo "🛑 停止现有服务..."
    PID=$(cat backend.pid)
    kill $PID 2>/dev/null || true
    sleep 2
    kill -9 $PID 2>/dev/null || true
    rm -f backend.pid
fi

# 激活虚拟环境
source venv/bin/activate

# 切换到后端目录
cd backend

# 启动生产模式服务
echo "🏭 启动gunicorn服务..."

gunicorn src.api.app:app \
    --bind 0.0.0.0:$PORT \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --daemon \
    --pid ../backend.pid \
    --access-logfile ../access.log \
    --error-logfile ../error.log

# 检查启动结果
sleep 2
if [ -f "../backend.pid" ]; then
    PID=$(cat ../backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "✅ 服务已启动 (PID: $PID)"
        echo "🌐 访问地址: http://localhost:$PORT"
        echo "📊 访问日志: tail -f ../access.log"
        echo "❌ 错误日志: tail -f ../error.log"
        echo "🛑 停止服务: ./stop.sh"
    else
        echo "❌ 启动失败，请检查日志: cat ../error.log"
        exit 1
    fi
else
    echo "❌ 启动失败，PID文件未创建"
    exit 1
fi