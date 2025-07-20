#!/bin/bash

# 环境预配置脚本
# 在远程服务器上执行，用于初始化环境
# 使用方法: ./pre_env.sh

set -e

echo "🚀 开始环境预配置..."

# 默认Python路径
PYTHON_PATH="/srv/python312/bin/python3.12"

# 检查Python是否存在
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 错误: Python路径不存在: $PYTHON_PATH"
    echo "请先安装Python 3.12+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_PATH --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "✅ Python版本: $PYTHON_VERSION"

# 检查是否有服务正在运行
if [ -f backend.pid ]; then
    PID=$(cat backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "⚠️  检测到服务正在运行 (PID: $PID)"
        echo "请先停止服务再执行环境初始化："
        echo "  ./stop.sh"
        echo ""
        echo "❌ 退出以避免影响正在运行的服务"
        exit 1
    else
        echo "🧹 清理无效的PID文件..."
        rm -f backend.pid
    fi
fi

# 检查是否已存在虚拟环境
if [ -d "venv" ]; then
    echo "⚠️  检测到已存在的虚拟环境"
    echo "如需重新初始化，请先手动删除或备份现有的 venv 目录："
    echo "  mv venv venv_backup_$(date +%Y%m%d_%H%M%S)"
    echo "  rm -rf venv"
    echo ""
    echo "❌ 退出以避免覆盖现有环境"
    exit 1
fi

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
$PYTHON_PATH -m venv venv

# 激活虚拟环境并安装依赖
echo "📦 激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# 拷贝nginx配置文件
echo "📝 拷贝nginx配置文件..."
if [ -f "nginx.conf" ]; then
    sudo cp nginx.conf /etc/nginx/conf.d/fullstack-langgraph.conf
    echo "✅ nginx配置文件已拷贝到 /etc/nginx/conf.d/"
    echo "⚠️  请手动编辑配置文件中的路径，然后重启nginx"
    echo "   sudo systemctl reload nginx"
else
    echo "⚠️  nginx.conf 文件不存在，跳过nginx配置"
fi

echo ""
echo "✅ 环境预配置完成!"
echo "📁 虚拟环境位置: $(pwd)/venv"
echo "🚀 现在可以执行 ./start.sh 启动服务"