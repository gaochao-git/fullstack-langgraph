#!/bin/bash

# 远程环境预配置脚本
# 用于在远程服务器上构建Python虚拟环境和安装依赖
# 使用方法: ./pre_env.sh [PYTHON_PATH] [REMOTE_HOST] [DEPLOY_DIR]

set -e

# 默认参数
DEFAULT_PYTHON_PATH="/srv/python312/bin/python3.12"
DEFAULT_REMOTE_HOST="root@82.156.146.51"
DEFAULT_DEPLOY_DIR="/data/langgraph_prd"

# 获取参数
PYTHON_PATH=${1:-$DEFAULT_PYTHON_PATH}
REMOTE_HOST=${2:-$DEFAULT_REMOTE_HOST}
DEPLOY_DIR=${3:-$DEFAULT_DEPLOY_DIR}

echo "🚀 开始远程环境预配置..."
echo "📍 Python路径: $PYTHON_PATH"
echo "🌐 远程主机: $REMOTE_HOST"
echo "📁 部署目录: $DEPLOY_DIR"
echo ""

# 检查本地requirements.txt文件
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ 错误: 本地未找到 backend/requirements.txt 文件"
    exit 1
fi

echo "📦 上传requirements.txt到远程服务器..."
scp backend/requirements.txt $REMOTE_HOST:/tmp/requirements.txt

echo "🔧 在远程服务器上执行环境配置..."
ssh $REMOTE_HOST << EOF
set -e

echo "📍 检查Python版本..."
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 错误: Python路径不存在: $PYTHON_PATH"
    echo "请确保Python已正确安装"
    exit 1
fi

PYTHON_VERSION=\$($PYTHON_PATH --version 2>&1 | awk '{print \$2}' | cut -d. -f1,2)
echo "✅ Python版本: \$PYTHON_VERSION"

if [ "\$(printf '%s\n' "3.11" "\$PYTHON_VERSION" | sort -V | head -n1)" != "3.11" ]; then
    echo "❌ 错误: 需要 Python 3.11 或更高版本，当前版本: \$PYTHON_VERSION"
    exit 1
fi

echo "📁 创建部署目录..."
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

echo "🛑 停止现有服务..."
if [ -f backend.pid ]; then
    PID=\$(cat backend.pid)
    echo "停止进程 \$PID..."
    kill \$PID 2>/dev/null || true
    sleep 2
    kill -9 \$PID 2>/dev/null || true
    rm -f backend.pid
fi

# 备份现有虚拟环境
if [ -d "venv" ]; then
    echo "🗂️  备份现有虚拟环境..."
    mv venv venv_backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || rm -rf venv
fi

echo "🐍 创建新的Python虚拟环境..."
$PYTHON_PATH -m venv venv

echo "📦 激活虚拟环境并升级pip..."
source venv/bin/activate
pip install --upgrade pip

echo "📥 安装项目依赖..."
pip install -r /tmp/requirements.txt

echo "✅ 虚拟环境创建完成!"
echo "📊 已安装的包数量: \$(pip list | wc -l)"

# 显示关键包版本
echo ""
echo "🔍 关键包版本信息:"
pip list | grep -E "(fastapi|uvicorn|gunicorn|langgraph|psycopg)" || echo "未找到关键包"

echo ""
echo "✅ 远程环境预配置完成！"
echo "📁 虚拟环境位置: $DEPLOY_DIR/venv"
echo "🚀 现在可以上传应用代码并启动服务"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 远程环境预配置成功完成！"
    echo ""
    echo "📋 下一步操作:"
    echo "  1. 上传应用代码: ./build_production.sh"
    echo "  2. 或直接部署到远程: scp production_build/*.tar.gz $REMOTE_HOST:/tmp/"
    echo ""
    echo "🔧 环境信息:"
    echo "  - 远程主机: $REMOTE_HOST"
    echo "  - 部署目录: $DEPLOY_DIR"
    echo "  - Python路径: $PYTHON_PATH"
    echo "  - 虚拟环境: $DEPLOY_DIR/venv"
else
    echo ""
    echo "❌ 远程环境预配置失败！"
    echo "请检查网络连接和远程服务器状态"
    exit 1
fi