#!/bin/bash

# OMind 智能运维平台生命周期管理脚本
# 统一管理初始化、启动、停止、升级、清理等操作
# 使用方法: ./manage_omind.sh <command> [options]

# ====== 配置区域 ======
# 用户可根据环境修改以下配置
DEFAULT_DEPLOY_PATH="/data"
VALID_PYTHON_PATH=("/Users/gaochao/miniconda3/envs/py312" "/data/omind/venv")
# ====================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }

# 默认参数
DEPLOY_PATH="$DEFAULT_DEPLOY_PATH"
CUSTOM_PYTHON_PATH=""
PACKAGE_NAME=""
CUSTOM_DEPLOY_PATH_SET=false
CUSTOM_PYTHON_PATH_SET=false

# 显示使用说明
show_help() {
    echo "OMind 智能运维平台生命周期管理"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  init         初始化OMind环境"
    echo "  start        启动OMind服务"
    echo "  stop         停止OMind服务"
    echo "  restart      重启OMind服务"
    echo "  status       查看OMind服务状态"
    echo "  upgrade      升级OMind到新版本"
    echo "  cleanup      清理OMind环境"
    echo "  help         显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --deploy-path=PATH 指定部署路径 (默认: $DEFAULT_DEPLOY_PATH)"
    echo "  --python-path=PATH 指定Python可执行文件路径"
    echo "  --package=NAME     指定升级包名称 (仅upgrade命令)"
    echo ""
    echo "示例:"
    echo "  $0 init                                              # 初始化到默认路径"
    echo "  $0 init --deploy-path=/opt --python-path=/usr/bin/python3.12"
    echo "  $0 start --deploy-path=/opt                          # 启动指定路径的服务"
    echo "  $0 status                                            # 查看默认路径的服务状态"
    echo "  $0 upgrade --package=omind-20250724_164901          # 升级到指定版本"
    echo "  $0 cleanup --deploy-path=/opt                        # 清理指定路径的环境"
    echo ""
    echo "服务管理:"
    echo "  init    -> 创建环境、安装依赖、配置服务（保存配置）"
    echo "  start   -> 启动MCP服务器和后端API"
    echo "  stop    -> 停止所有服务"
    echo "  restart -> 停止后重新启动服务"
    echo "  status  -> 显示服务运行状态"
    echo "  upgrade -> 升级到新版本并重启服务"
    echo "  cleanup -> 完全清理环境和配置"
    echo ""
    echo "配置管理:"
    echo "  init命令会将部署路径和Python路径保存到 .omind_config 文件"
    echo "  后续命令会自动读取保存的配置，无需重复指定参数"
    echo "  命令行参数具有更高优先级，可以临时覆盖保存的配置"
}

# 解析参数
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        init|start|stop|restart|status|upgrade|cleanup|help)
            if [ -z "$COMMAND" ]; then
                COMMAND="$1"
            else
                echo_error "只能指定一个命令"
                show_help
                exit 1
            fi
            shift
            ;;
        --deploy-path=*)
            DEPLOY_PATH="${1#*=}"
            CUSTOM_DEPLOY_PATH_SET=true
            shift
            ;;
        --python-path=*)
            CUSTOM_PYTHON_PATH="${1#*=}"
            CUSTOM_PYTHON_PATH_SET=true
            shift
            ;;
        --package=*)
            PACKAGE_NAME="${1#*=}"
            shift
            ;;
        *)
            echo_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必需参数
if [ -z "$COMMAND" ]; then
    echo_error "必须指定一个命令"
    show_help
    exit 1
fi

# 设置完整部署路径和配置文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/.omind_config"

# 读取现有配置文件
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        echo_info "读取现有配置: $CONFIG_FILE"
        source "$CONFIG_FILE"
        # 如果命令行没有指定，使用配置文件中的值
        if [ "$CUSTOM_DEPLOY_PATH_SET" = false ] && [ -n "$SAVED_DEPLOY_PATH" ]; then
            DEPLOY_PATH="$SAVED_DEPLOY_PATH"
            echo_info "使用保存的部署路径: $DEPLOY_PATH"
        fi
        if [ "$CUSTOM_PYTHON_PATH_SET" = false ] && [ -n "$SAVED_PYTHON_PATH" ]; then
            CUSTOM_PYTHON_PATH="$SAVED_PYTHON_PATH"
            echo_info "使用保存的Python路径: $CUSTOM_PYTHON_PATH"
        fi
    fi
}

# 保存配置到文件
save_config() {
    echo_info "保存配置到: $CONFIG_FILE"
    cat > "$CONFIG_FILE" << EOF
# OMind 配置文件 - 由 manage_omind.sh 自动生成
# 生成时间: $(date)
SAVED_DEPLOY_PATH="$DEPLOY_PATH"
SAVED_PYTHON_PATH="$CUSTOM_PYTHON_PATH"
EOF
    echo_success "配置已保存"
}

# 对于非init命令，加载保存的配置
if [ "$COMMAND" != "init" ] && [ "$COMMAND" != "help" ]; then
    load_config
fi

FULL_DEPLOY_PATH="$DEPLOY_PATH/omind"

# 显示操作信息
echo_info "🚀 OMind 智能运维平台管理"
echo_info "命令: $COMMAND"
echo_info "部署路径: $FULL_DEPLOY_PATH"
if [ -n "$CUSTOM_PYTHON_PATH" ]; then
    echo_info "指定Python路径: $CUSTOM_PYTHON_PATH"
fi
if [ -n "$PACKAGE_NAME" ]; then
    echo_info "升级包: $PACKAGE_NAME"
fi
echo ""

# 检查部署路径是否存在
check_deployment() {
    if [ ! -d "$FULL_DEPLOY_PATH" ]; then
        echo_error "OMind环境不存在: $FULL_DEPLOY_PATH"
        echo_info "请先运行初始化命令："
        echo_info "  $0 init --deploy-path=$DEPLOY_PATH"
        exit 1
    fi
}

# 初始化环境
cmd_init() {
    echo_info "初始化OMind环境..."
    
    # 保存配置到隐藏文件
    save_config
    
    # 构建pre_env.sh参数
    PRE_ENV_ARGS="--init --deploy-path=$DEPLOY_PATH"
    if [ -n "$CUSTOM_PYTHON_PATH" ]; then
        PRE_ENV_ARGS="$PRE_ENV_ARGS --python-path=$CUSTOM_PYTHON_PATH"
    fi
    
    # 调用pre_env.sh脚本
    if [ -f "$SCRIPT_DIR/scripts/pre_env.sh" ]; then
        echo_info "调用环境初始化脚本..."
        "$SCRIPT_DIR/scripts/pre_env.sh" $PRE_ENV_ARGS
    else
        echo_error "初始化脚本不存在: $SCRIPT_DIR/scripts/pre_env.sh"
        exit 1
    fi
    
    echo_success "OMind环境初始化完成！"
    echo_info "配置已保存，后续命令将自动使用相同配置"
}

# 启动服务
cmd_start() {
    echo_info "启动OMind服务..."
    check_deployment
    
    cd "$FULL_DEPLOY_PATH/scripts" || exit 1
    
    # 启动MCP服务器
    echo_info "启动MCP服务器..."
    if [ -f "./start_mcp.sh" ]; then
        ./start_mcp.sh
    else
        echo_error "MCP启动脚本不存在"
        exit 1
    fi
    
    # 启动后端服务
    echo_info "启动后端服务..."
    if [ -f "./start_backend.sh" ]; then
        ./start_backend.sh
    else
        echo_error "后端启动脚本不存在"
        exit 1
    fi
    
    echo_success "OMind服务启动完成！"
    cmd_status
}

# 停止服务
cmd_stop() {
    echo_info "停止OMind服务..."
    check_deployment
    
    cd "$FULL_DEPLOY_PATH/scripts" || exit 1
    
    # 停止MCP服务器
    echo_info "停止MCP服务器..."
    if [ -f "./stop_mcp.sh" ]; then
        ./stop_mcp.sh
    else
        echo_warning "MCP停止脚本不存在"
    fi
    
    # 停止后端服务
    echo_info "停止后端服务..."
    if [ -f "./stop_backend.sh" ]; then
        ./stop_backend.sh
    else
        echo_warning "后端停止脚本不存在"
    fi
    
    echo_success "OMind服务停止完成！"
}

# 重启服务
cmd_restart() {
    echo_info "重启OMind服务..."
    cmd_stop
    sleep 2
    cmd_start
}

# 查看状态
cmd_status() {
    echo_info "查看OMind服务状态..."
    check_deployment
    
    cd "$FULL_DEPLOY_PATH/scripts" || exit 1
    
    # 检查MCP服务器状态
    echo_info "MCP服务器状态:"
    if [ -f "./status_mcp.sh" ]; then
        ./status_mcp.sh
    else
        echo_warning "MCP状态脚本不存在"
    fi
    
    echo ""
    echo_info "后端服务状态:"
    # 检查后端服务状态
    if [ -f "../backend/pids/backend.pid" ]; then
        PID=$(cat ../backend/pids/backend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo_success "后端服务运行中 (PID: $PID)"
            echo_info "API访问: http://localhost:8000/docs"
        else
            echo_warning "后端PID文件存在但进程未运行"
        fi
    else
        echo_warning "后端服务未运行"
    fi
    
    echo ""
    echo_info "前端服务状态:"
    # 检查nginx状态
    if systemctl is-active nginx >/dev/null 2>&1; then
        echo_success "Nginx运行中"
        echo_info "前端访问: http://localhost/"
    else
        echo_warning "Nginx未运行"
    fi
}

# 升级服务
cmd_upgrade() {
    echo_info "升级OMind服务..."
    check_deployment
    
    if [ -z "$PACKAGE_NAME" ]; then
        echo_error "升级命令需要指定包名称"
        echo_info "使用: $0 upgrade --package=omind-20250724_164901"
        exit 1
    fi
    
    # 调用upgrade.sh脚本
    if [ -f "$FULL_DEPLOY_PATH/scripts/upgrade.sh" ]; then
        echo_info "调用升级脚本..."
        cd "$FULL_DEPLOY_PATH/scripts" || exit 1
        ./upgrade.sh "$PACKAGE_NAME"
    else
        echo_error "升级脚本不存在: $FULL_DEPLOY_PATH/scripts/upgrade.sh"
        exit 1
    fi
    
    echo_success "OMind服务升级完成！"
}

# 清理环境
cmd_cleanup() {
    echo_info "清理OMind环境..."
    
    # 构建pre_env.sh参数
    PRE_ENV_ARGS="--cleanup --deploy-path=$DEPLOY_PATH"
    
    # 调用pre_env.sh脚本
    if [ -f "$SCRIPT_DIR/scripts/pre_env.sh" ]; then
        echo_info "调用环境清理脚本..."
        "$SCRIPT_DIR/scripts/pre_env.sh" $PRE_ENV_ARGS
    else
        echo_error "清理脚本不存在: $SCRIPT_DIR/scripts/pre_env.sh"
        exit 1
    fi
    
    echo_success "OMind环境清理完成！"
}

# 执行对应命令
case $COMMAND in
    "init")
        cmd_init
        ;;
    "start")
        cmd_start
        ;;
    "stop")
        cmd_stop
        ;;
    "restart")
        cmd_restart
        ;;
    "status")
        cmd_status
        ;;
    "upgrade")
        cmd_upgrade
        ;;
    "cleanup")
        cmd_cleanup
        ;;
    "help")
        show_help
        ;;
    *)
        echo_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac