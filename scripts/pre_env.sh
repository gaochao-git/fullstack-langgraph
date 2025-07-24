#!/bin/bash

# OMind 智能运维平台环境预配置脚本
# 在远程服务器上执行，用于初始化环境或清理环境
# 使用方法: 
#   ./pre_env.sh --init --path=/data          # 初始化环境到/data/omind
#   ./pre_env.sh --cleanup --path=/data       # 清理/data/omind环境

# ====== 配置区域 ======
# Python环境将在初始化时创建，无需预配置
# ====================

set -e

# 默认参数
DEPLOY_PATH="/data"
ACTION=""
CUSTOM_PYTHON_PATH=""

# 显示使用说明
show_help() {
    echo "OMind 智能运维平台环境管理脚本"
    echo ""
    echo "用法: $0 <action> [options]"
    echo ""
    echo "动作:"
    echo "  --init      初始化OMind环境"
    echo "  --cleanup   清理OMind环境"
    echo ""
    echo "选项:"
    echo "  --deploy-path=PATH 指定部署路径 (默认: /data)"
    echo "  --python-path=PATH 指定Python可执行文件路径"
    echo "  --help             显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --init --deploy-path=/data                                        # 初始化环境到/data/omind"
    echo "  $0 --cleanup --deploy-path=/data                                     # 清理/data/omind环境"
    echo "  $0 --init --python-path=/usr/bin/python3.12                         # 使用指定Python版本初始化"
    echo "  $0 --init --deploy-path=/opt --python-path=/opt/python/bin/python3  # 自定义路径和Python版本"
    echo ""
    echo "说明:"
    echo "  初始化模式会在<deploy-path>/omind目录下创建完整的运行环境"
    echo "  清理模式会删除<deploy-path>/omind目录及相关配置"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --init)
            ACTION="init"
            shift
            ;;
        --cleanup)
            ACTION="cleanup"
            shift
            ;;
        --deploy-path=*)
            DEPLOY_PATH="${1#*=}"
            shift
            ;;
        --python-path=*)
            CUSTOM_PYTHON_PATH="${1#*=}"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ 未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必需参数
if [ -z "$ACTION" ]; then
    echo "❌ 错误: 必须指定动作 (--init 或 --cleanup)"
    show_help
    exit 1
fi

# 设置完整部署路径
FULL_DEPLOY_PATH="$DEPLOY_PATH/omind"

echo "🚀 OMind 智能运维平台环境管理"
echo "动作: $ACTION"
echo "部署路径: $FULL_DEPLOY_PATH"
if [ -n "$CUSTOM_PYTHON_PATH" ]; then
    echo "指定Python路径: $CUSTOM_PYTHON_PATH"
fi
echo ""

# 清理环境功能
cleanup_environment() {
    echo "🧹 开始清理OMind环境..."
    
    # 检查部署目录是否存在
    if [ ! -d "$FULL_DEPLOY_PATH" ]; then
        echo "⚠️ 部署目录不存在: $FULL_DEPLOY_PATH"
        echo "✅ 环境已经是干净的"
        return 0
    fi
    
    echo "📂 发现OMind部署目录: $FULL_DEPLOY_PATH"
    
    # 停止服务
    echo "🛑 停止OMind服务..."
    if [ -f "$FULL_DEPLOY_PATH/scripts/stop_mcp.sh" ]; then
        cd "$FULL_DEPLOY_PATH/scripts" && ./stop_mcp.sh 2>/dev/null || true
    fi
    if [ -f "$FULL_DEPLOY_PATH/scripts/stop_backend.sh" ]; then
        cd "$FULL_DEPLOY_PATH/scripts" && ./stop_backend.sh 2>/dev/null || true
    fi
    
    # 清理nginx配置
    echo "🗑️ 清理nginx配置..."
    if [ -f "/etc/nginx/conf.d/omind.conf" ]; then
        sudo rm -f /etc/nginx/conf.d/omind.conf 2>/dev/null || {
            echo "⚠️ 无sudo权限，请手动删除nginx配置："
            echo "   sudo rm -f /etc/nginx/conf.d/omind.conf"
            echo "   sudo systemctl reload nginx"
        }
        # 重载nginx配置
        sudo systemctl reload nginx 2>/dev/null || echo "⚠️ 请手动重载nginx配置: sudo systemctl reload nginx"
    fi
    
    # 清理systemd服务
    echo "🗑️ 清理systemd服务..."
    if systemctl is-enabled omind.service 2>/dev/null; then
        sudo systemctl stop omind.service 2>/dev/null || true
        sudo systemctl disable omind.service 2>/dev/null || true
        sudo rm -f /etc/systemd/system/omind.service 2>/dev/null || true
        sudo systemctl daemon-reload 2>/dev/null || true
    fi
    
    # 询问是否删除部署目录
    echo ""
    echo "⚠️ 即将删除以下目录及其所有内容:"
    echo "   $FULL_DEPLOY_PATH"
    echo ""
    read -p "确认删除? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ 删除部署目录..."
        rm -rf "$FULL_DEPLOY_PATH"
        echo "✅ OMind环境清理完成"
    else
        echo "❌ 取消删除，保留部署目录"
        exit 1
    fi
    
    echo ""
    echo "✅ OMind智能运维平台环境清理完成！"
    echo ""
    echo "已清理内容:"
    echo "  - OMind部署目录: $FULL_DEPLOY_PATH"
    echo "  - nginx配置: /etc/nginx/conf.d/omind.conf"
    echo "  - systemd服务: omind.service"
}

# 检测Python环境功能
detect_python_environment() {
    echo "🔍 检测Python环境..."
    
    # 如果用户指定了Python路径，优先使用
    if [ -n "$CUSTOM_PYTHON_PATH" ]; then
        echo "🔧 使用用户指定的Python路径: $CUSTOM_PYTHON_PATH"
        if command -v "$CUSTOM_PYTHON_PATH" >/dev/null 2>&1; then
            PYTHON_VERSION=$($CUSTOM_PYTHON_PATH --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
                PYTHON_PATH="$CUSTOM_PYTHON_PATH"
                echo "✅ 用户指定Python有效: $PYTHON_PATH (版本: $PYTHON_VERSION)"
                return 0
            else
                echo "❌ 用户指定的Python版本太低: $PYTHON_VERSION (需要3.6+)"
                return 1
            fi
        else
            echo "❌ 用户指定的Python路径无效: $CUSTOM_PYTHON_PATH"
            return 1
        fi
    fi
    
    # 自动检测Python环境
    echo "🔍 尝试系统Python环境..."
    for python_cmd in python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6 python3 python; do
        if command -v "$python_cmd" >/dev/null 2>&1; then
            PYTHON_VERSION=$($python_cmd --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
            echo "   发现Python: $python_cmd (版本: $PYTHON_VERSION)"
            if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
                PYTHON_PATH="$python_cmd"
                echo "✅ 使用系统Python: $PYTHON_PATH (版本: $PYTHON_VERSION)"
                return 0
            fi
        fi
    done
    
    echo "❌ 错误: 未找到有效的Python环境"
    echo "请确保系统Python 3.6+ 环境或使用--python-path指定具体路径"
    return 1
}

# 初始化环境功能
init_environment() {
    echo "🏗️ 开始初始化OMind环境..."
    
    # 检测Python环境
    PYTHON_PATH=""
    if ! detect_python_environment; then
        exit 1
    fi
    
    # 切换到脚本所在目录
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    cd "$PROJECT_ROOT"

    # 创建部署目录
    echo "📁 创建部署目录: $FULL_DEPLOY_PATH"
    mkdir -p "$FULL_DEPLOY_PATH"
    
    # 检查是否已存在部署
    if [ -d "$FULL_DEPLOY_PATH/backend" ] || [ -d "$FULL_DEPLOY_PATH/mcp_servers" ]; then
        echo "⚠️ 检测到已存在的OMind部署"
        read -p "是否重新初始化环境? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️ 清理现有部署..."
            # 停止服务
            if [ -f "$FULL_DEPLOY_PATH/scripts/stop_mcp.sh" ]; then
                cd "$FULL_DEPLOY_PATH/scripts" && ./stop_mcp.sh 2>/dev/null || true
            fi
            if [ -f "$FULL_DEPLOY_PATH/scripts/stop_backend.sh" ]; then
                cd "$FULL_DEPLOY_PATH/scripts" && ./stop_backend.sh 2>/dev/null || true
            fi
            rm -rf "$FULL_DEPLOY_PATH"/*
        else
            echo "❌ 退出以避免覆盖现有环境"
            exit 1
        fi
    fi
    
    # 复制项目文件到部署目录
    echo "📦 复制项目文件到部署目录..."
    rsync -av --exclude='logs/' --exclude='pids/' --exclude='node_modules/' --exclude='dist/' "$PROJECT_ROOT/backend/" "$FULL_DEPLOY_PATH/backend/"
    rsync -av --exclude='logs/' --exclude='pids/' "$PROJECT_ROOT/mcp_servers/" "$FULL_DEPLOY_PATH/mcp_servers/"
    rsync -av "$PROJECT_ROOT/scripts/" "$FULL_DEPLOY_PATH/scripts/"
    
    # 如果有前端构建文件，也复制
    if [ -d "$PROJECT_ROOT/frontend/dist" ]; then
        echo "📦 复制前端构建文件..."
        mkdir -p "$FULL_DEPLOY_PATH/frontend"
        rsync -av "$PROJECT_ROOT/frontend/dist/" "$FULL_DEPLOY_PATH/frontend/dist/"
    fi
    
    # 复制配置文件
    if [ -f "$PROJECT_ROOT/nginx.conf" ]; then
        cp "$PROJECT_ROOT/nginx.conf" "$FULL_DEPLOY_PATH/"
    fi
    
    # 创建必要的目录
    echo "📁 创建运行时目录..."
    mkdir -p "$FULL_DEPLOY_PATH/backend/logs" "$FULL_DEPLOY_PATH/backend/pids"
    mkdir -p "$FULL_DEPLOY_PATH/mcp_servers/logs" "$FULL_DEPLOY_PATH/mcp_servers/pids"
    
    # 创建虚拟环境
    echo "🐍 创建Python虚拟环境..."
    cd "$FULL_DEPLOY_PATH"
    $PYTHON_PATH -m venv venv
    
    # 激活虚拟环境并安装依赖
    echo "📦 激活虚拟环境并安装依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    
    # 安装后端依赖
    echo "📦 安装后端依赖..."
    if [ -f "backend/requirements.txt" ]; then
        pip install -r backend/requirements.txt
    else
        echo "⚠️ backend/requirements.txt 不存在"
        exit 1
    fi
    
    # 安装MCP服务器依赖
    echo "📦 安装MCP服务器依赖..."
    if [ -f "mcp_servers/requirements.txt" ]; then
        pip install -r mcp_servers/requirements.txt
    else
        echo "⚠️ mcp_servers/requirements.txt 不存在"
        exit 1
    fi
    
    # 更新脚本中的Python路径配置
    echo "🔧 更新脚本配置..."
    if [ -f "scripts/start_mcp.sh" ]; then
        sed -i.bak "s|VALID_PYTHON_PATH=.*|VALID_PYTHON_PATH=(\"$FULL_DEPLOY_PATH/venv\")|g" scripts/start_mcp.sh
    fi
    if [ -f "scripts/start_backend.sh" ]; then
        sed -i.bak "s|VALID_PYTHON_PATH=.*|VALID_PYTHON_PATH=(\"$FULL_DEPLOY_PATH/venv\")|g" scripts/start_backend.sh
    fi
    
    # 设置脚本执行权限
    chmod +x scripts/*.sh
    
    # 配置nginx
    echo "📝 配置nginx..."
    if [ -f "nginx.conf" ] && command -v nginx >/dev/null 2>&1; then
        # 更新nginx配置中的路径
        sed "s|/data/omind|$FULL_DEPLOY_PATH|g" nginx.conf > /tmp/omind_nginx.conf
        sudo cp /tmp/omind_nginx.conf /etc/nginx/conf.d/omind.conf 2>/dev/null || {
            echo "⚠️ 无sudo权限，请手动配置nginx："
            echo "   sudo cp /tmp/omind_nginx.conf /etc/nginx/conf.d/omind.conf"
            echo "   sudo systemctl reload nginx"
        }
        # 重载nginx配置
        sudo systemctl reload nginx 2>/dev/null || echo "⚠️ 请手动重载nginx配置: sudo systemctl reload nginx"
        echo "✅ nginx配置已更新"
    else
        echo "⚠️ nginx配置跳过 (nginx未安装或配置文件不存在)"
    fi
    
    echo ""
    echo "✅ OMind 环境初始化完成!"
    echo ""
    echo "📊 环境信息:"
    echo "  Python版本: $PYTHON_VERSION"
    echo "  虚拟环境: $FULL_DEPLOY_PATH/venv"
    echo "  部署路径: $FULL_DEPLOY_PATH"
    echo ""
    echo "🚀 启动服务:"
    echo "  cd $FULL_DEPLOY_PATH/scripts"
    echo "  ./start_mcp.sh     # 启动MCP服务器"
    echo "  ./start_backend.sh # 启动后端服务"
    echo ""
    echo "📊 查看状态:"
    echo "  ./status_mcp.sh    # 查看MCP状态"
    echo "  curl http://localhost:8000/api/  # 检查后端API"
}

# 主逻辑
case $ACTION in
    "init")
        init_environment
        ;;
    "cleanup")
        cleanup_environment
        ;;
    *)
        echo "❌ 未知动作: $ACTION"
        show_help
        exit 1
        ;;
esac