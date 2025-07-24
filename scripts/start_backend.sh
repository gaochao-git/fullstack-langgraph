#!/bin/bash

# 生产环境启动脚本
# 使用方法: ./start.sh [--workers N] [--port PORT]

# ====== 配置区域 ======
# Python环境将使用部署时创建的venv环境
# ====================

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

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 停止现有服务
if [ -f "backend/pids/backend.pid" ]; then
    echo "🛑 停止现有服务..."
    PID=$(cat backend/pids/backend.pid)
    kill $PID 2>/dev/null || true
    sleep 2
    kill -9 $PID 2>/dev/null || true
    rm -f backend/pids/backend.pid
fi

# 检测可用的Python环境
PYTHON_CMD=""
echo "🔍 检测Python环境..."

# 优先使用部署目录下的venv环境
VENV_PYTHON="$(pwd)/venv/bin/python3"
if [ -f "$VENV_PYTHON" ]; then
    echo "   发现部署venv环境: $VENV_PYTHON"
    source "$(pwd)/venv/bin/activate"
    if python --version &> /dev/null; then
        PYTHON_CMD="python"
        echo "✅ 使用部署venv环境: $(pwd)/venv ($(python --version))"
    else
        echo "⚠️ 部署venv环境激活失败"
    fi
else
    echo "⚠️ 未找到部署venv环境: $VENV_PYTHON"
fi

# 如果venv环境不可用，尝试系统Python
if [ -z "$PYTHON_CMD" ]; then
    echo "🔍 尝试系统Python环境..."
    for python_cmd in python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6 python3 python; do
        if command -v "$python_cmd" >/dev/null 2>&1; then
            PYTHON_VERSION=$($python_cmd --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            echo "   发现Python: $python_cmd (版本: $PYTHON_VERSION)"
            if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
                PYTHON_CMD="$python_cmd"
                echo "✅ 使用系统Python: $python_cmd (版本: $PYTHON_VERSION)"
                break
            fi
        fi
    done
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 错误: 未找到有效的Python环境"
    echo "请确保存在以下之一:"
    echo "  1. 部署目录下的venv环境: $(pwd)/venv/bin/python3"
    echo "  2. 系统Python 3.6+ 环境"
    exit 1
fi

# 切换到后端目录
cd backend

# 创建必要目录
mkdir -p logs pids

# 启动生产模式服务
echo "🏭 启动gunicorn服务..."

$PYTHON_CMD -m gunicorn src.api.app:app \
    --bind 0.0.0.0:$PORT \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers $WORKERS \
    --daemon \
    --pid pids/backend.pid \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log

# 检查启动结果  
sleep 2
if [ -f "pids/backend.pid" ]; then
    PID=$(cat pids/backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "✅ 服务已启动 (PID: $PID)"
        echo "🌐 访问地址: http://localhost:$PORT"
        echo "📊 访问日志: tail -f logs/access.log"
        echo "❌ 错误日志: tail -f logs/error.log"
        echo "🛑 停止服务: ./stop_backend.sh"
    else
        echo "❌ 启动失败，请检查日志: cat logs/error.log"
        exit 1
    fi
else
    echo "❌ 启动失败，PID文件未创建"
    exit 1
fi