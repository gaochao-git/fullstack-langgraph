#!/bin/bash

echo "🚀 启动 fullstack-langgraph 生产环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要 Python 3.11 或更高版本，当前版本: $python_version"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
cd backend
pip install .
cd ..

# 启动服务
echo "🏭 启动后端服务..."
cd backend
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
echo "🌐 后端API地址: http://localhost:8000"
echo "📁 前端静态文件位置: $(pwd)/../frontend_dist"
echo ""
echo "请配置nginx代理前端静态文件和后端API"
echo "参考配置文件: nginx.conf"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待信号
trap "echo '正在停止服务...'; kill $BACKEND_PID; exit" INT TERM
wait $BACKEND_PID
