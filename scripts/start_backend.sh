#!/bin/bash

# 生产环境启动脚本
# 使用方法: ./start.sh [--workers N] [--port PORT]

# ====== 配置区域 ======
# 用户可根据环境修改以下Python路径
VALID_PYTHON_PATH=("/Users/gaochao/miniconda3/envs/py312" "/data/omind/venv")
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

for python_path in "${VALID_PYTHON_PATH[@]}"; do
    if [ -d "$python_path" ]; then
        # 检查是否是虚拟环境目录
        if [ -f "$python_path/bin/python" ]; then
            echo "   发现虚拟环境: $python_path"
            source "$python_path/bin/activate"
            if python --version &> /dev/null; then
                PYTHON_CMD="python"
                echo "✅ 使用虚拟环境: $python_path ($(python --version))"
                break
            fi
        fi
    elif command -v "$python_path" >/dev/null 2>&1; then
        # 直接Python可执行文件路径
        PYTHON_VERSION=$($python_path --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        echo "   发现Python: $python_path (版本: $PYTHON_VERSION)"
        if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
            PYTHON_CMD="$python_path"
            echo "✅ 使用Python: $python_path (版本: $PYTHON_VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 错误: 未找到有效的Python环境"
    echo "请检查VALID_PYTHON_PATH配置: ${VALID_PYTHON_PATH[*]}"
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