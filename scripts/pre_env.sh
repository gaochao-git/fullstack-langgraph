#!/bin/bash

# OMind 智能运维平台环境预配置脚本
# 在远程服务器上执行，用于初始化环境
# 使用方法: ./pre_env.sh

# ====== 配置区域 ======
# 用户可根据环境修改以下Python路径
VALID_PYTHON_PATH=("/Users/gaochao/miniconda3/envs/py312" "/data/omind/venv")
# ====================

set -e

echo "🚀 开始 OMind 环境预配置..."

# 检测可用的Python环境
PYTHON_PATH=""
echo "🔍 检测Python环境..."

for python_path in "${VALID_PYTHON_PATH[@]}"; do
    if [ -d "$python_path" ]; then
        # 检查是否是虚拟环境目录
        if [ -f "$python_path/bin/python" ]; then
            echo "   发现虚拟环境: $python_path"
            PYTHON_VERSION=$($python_path/bin/python --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
                PYTHON_PATH="$python_path/bin/python"
                echo "✅ 使用虚拟环境Python: $PYTHON_PATH (版本: $PYTHON_VERSION)"
                break
            fi
        fi
    elif command -v "$python_path" >/dev/null 2>&1; then
        # 直接Python可执行文件路径
        PYTHON_VERSION=$($python_path --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        echo "   发现Python: $python_path (版本: $PYTHON_VERSION)"
        if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
            PYTHON_PATH="$python_path"
            echo "✅ 使用Python: $PYTHON_PATH (版本: $PYTHON_VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_PATH" ]; then
    echo "❌ 错误: 未找到有效的Python环境"
    echo "请检查VALID_PYTHON_PATH配置: ${VALID_PYTHON_PATH[*]}"
    exit 1
fi

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检查是否有服务正在运行
if [ -f "backend/pids/backend.pid" ]; then
    PID=$(cat backend/pids/backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "⚠️ 检测到后端服务正在运行 (PID: $PID)"
        echo "请先停止服务再执行环境初始化："
        echo "  cd scripts && ./stop_backend.sh"
        echo ""
        echo "❌ 退出以避免影响正在运行的服务"
        exit 1
    else
        echo "🧹 清理无效的后端PID文件..."
        rm -f backend/pids/backend.pid
    fi
fi

# 检查MCP服务
if [ -d "mcp_servers/pids" ] && [ "$(ls -A mcp_servers/pids 2>/dev/null)" ]; then
    echo "⚠️ 检测到MCP服务器正在运行"
    echo "请先停止服务再执行环境初始化："
    echo "  cd scripts && ./stop_mcp.sh"
    echo ""
    echo "❌ 退出以避免影响正在运行的服务"
    exit 1
fi

# 创建必要的目录
echo "📁 创建运行时目录..."
mkdir -p backend/logs backend/pids mcp_servers/logs mcp_servers/pids

# 检查是否已存在虚拟环境
if [ -d "venv" ]; then
    echo "⚠️ 检测到已存在的虚拟环境"
    read -p "是否重新创建虚拟环境? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ 删除现有虚拟环境..."
        rm -rf venv
    else
        echo "❌ 退出以避免覆盖现有环境"
        exit 1
    fi
fi

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
$PYTHON_PATH -m venv venv

# 激活虚拟环境并安装依赖
echo "📦 激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install --upgrade pip

# 安装后端依赖
echo "📦 安装后端依赖..."
if [ -f "backend/requirements.txt" ]; then
    cd backend
    # 对于老版本Python，安装兼容版本
    if [[ "$PYTHON_VERSION" =~ ^3\.6$ ]]; then
        echo "⚠️ Python 3.6 环境，安装兼容版本的依赖..."
        pip install "fastapi>=0.68.0,<0.84.0" "uvicorn>=0.15.0,<0.17.0"
        pip install httpx aiofiles python-multipart
        pip install sqlalchemy pymysql
        pip install "elasticsearch>=7.0.0,<8.0.0"
        pip install paramiko requests pyyaml
    else
        pip install -r requirements.txt
    fi
    cd ..
else
    echo "⚠️ backend/requirements.txt 不存在，跳过后端依赖安装"
fi

# 安装MCP服务器依赖
echo "📦 安装MCP服务器依赖..."
if [ -f "mcp_servers/requirements.txt" ]; then
    cd mcp_servers
    if [[ "$PYTHON_VERSION" =~ ^3\.6$ ]]; then
        echo "⚠️ Python 3.6 环境，安装兼容版本的MCP依赖..."
        pip install httpx paramiko pymysql
        pip install "elasticsearch>=7.0.0,<8.0.0"
        pip install requests pyyaml
    else
        pip install -r requirements.txt
    fi
    cd ..
else
    echo "⚠️ mcp_servers/requirements.txt 不存在，跳过MCP依赖安装"
fi

# 拷贝nginx配置文件
echo "📝 拷贝nginx配置文件..."
if [ -f "nginx.conf" ]; then
    if command -v nginx >/dev/null 2>&1; then
        sudo cp nginx.conf /etc/nginx/conf.d/omind.conf 2>/dev/null || {
            echo "⚠️ 无sudo权限，请手动拷贝nginx配置："
            echo "   sudo cp nginx.conf /etc/nginx/conf.d/omind.conf"
            echo "   sudo systemctl reload nginx"
        }
        echo "✅ nginx配置文件已拷贝"
        echo "⚠️ 请检查配置文件中的路径，然后重启nginx："
        echo "   sudo systemctl reload nginx"
    else
        echo "⚠️ nginx未安装，跳过nginx配置"
    fi
else
    echo "⚠️ nginx.conf 文件不存在，跳过nginx配置"
fi

echo ""
echo "✅ OMind 环境预配置完成!"
echo ""
echo "📊 环境信息:"
echo "  Python版本: $PYTHON_VERSION"
echo "  虚拟环境: $(pwd)/venv"
echo "  项目路径: $(pwd)"
echo ""
echo "🚀 现在可以启动服务:"
echo "  cd scripts"
echo "  ./start_mcp.sh     # 启动MCP服务器"
echo "  ./start_backend.sh # 启动后端服务"
echo ""
echo "📊 查看状态:"
echo "  ./status_mcp.sh    # 查看MCP状态"
echo "  curl http://localhost:8000/api/  # 检查后端API"