#!/bin/bash

# Fullstack LangGraph 启动脚本
# 支持开发和生产环境

set -e

# 配置参数
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
VENV_DIR="$PROJECT_DIR/venv"
PID_FILE="$PROJECT_DIR/backend.pid"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }

# 显示帮助信息
show_help() {
    echo "Fullstack LangGraph 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -d, --dev      开发模式启动（前台运行，支持热重载）"
    echo "  -p, --prod     生产模式启动（后台运行，多进程）"
    echo "  --workers N    指定worker进程数（默认2）"
    echo "  --port PORT    指定端口（默认8000）"
    echo ""
    echo "示例:"
    echo "  $0              # 自动检测环境启动"
    echo "  $0 --dev        # 开发模式启动"
    echo "  $0 --prod       # 生产模式启动"
    echo "  $0 --workers 4  # 生产模式4个进程"
}

# 解析命令行参数
MODE=""
WORKERS=2
PORT=8000

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            MODE="dev"
            shift
            ;;
        -p|--prod)
            MODE="prod"
            shift
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 自动检测环境模式
if [ -z "$MODE" ]; then
    if [ -f "$PROJECT_DIR/.env" ] && grep -q "ENV=development" "$PROJECT_DIR/.env" 2>/dev/null; then
        MODE="dev"
        echo_info "检测到开发环境配置"
    else
        MODE="prod"
        echo_info "默认使用生产环境模式"
    fi
fi

echo_info "启动模式: $MODE"

# 检查Python和虚拟环境
check_environment() {
    echo_info "检查运行环境..."
    
    if [ ! -d "$VENV_DIR" ]; then
        echo_error "虚拟环境不存在: $VENV_DIR"
        echo_info "请先运行 pre_env.sh 创建虚拟环境"
        exit 1
    fi
    
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        echo_error "虚拟环境损坏: 缺少 activate 脚本"
        exit 1
    fi
    
    if [ ! -d "$BACKEND_DIR" ]; then
        echo_error "后端目录不存在: $BACKEND_DIR"
        exit 1
    fi
    
    echo_success "环境检查通过"
}

# 检查端口占用
check_port() {
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
            echo_warning "端口 $PORT 已被占用"
            echo_info "正在检查是否为本服务..."
            
            if [ -f "$PID_FILE" ]; then
                PID=$(cat "$PID_FILE")
                if kill -0 "$PID" 2>/dev/null; then
                    echo_warning "服务已在运行 (PID: $PID)"
                    echo_info "如需重启，请先运行 stop.sh"
                    exit 1
                else
                    echo_info "PID文件存在但进程已停止，清理PID文件"
                    rm -f "$PID_FILE"
                fi
            fi
        fi
    fi
}

# 设置SSL环境变量（如果需要）
setup_ssl() {
    if [ -d "/usr/local/openssl/lib" ]; then
        export LD_LIBRARY_PATH="/usr/local/openssl/lib:$LD_LIBRARY_PATH"
        echo_info "已设置SSL库路径"
    fi
}

# 激活虚拟环境
activate_venv() {
    echo_info "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"
    echo_success "虚拟环境已激活: $(python --version)"
}

# 开发模式启动
start_dev() {
    echo_info "🚀 启动开发模式服务..."
    cd "$BACKEND_DIR"
    
    echo_info "端口: $PORT (支持热重载)"
    echo_warning "按 Ctrl+C 停止服务"
    echo ""
    
    exec uvicorn src.api.app:app \
        --host 0.0.0.0 \
        --port "$PORT" \
        --reload \
        --reload-dir src
}

# 生产模式启动
start_prod() {
    echo_info "🏭 启动生产模式服务..."
    cd "$BACKEND_DIR"
    
    echo_info "Worker进程数: $WORKERS"
    echo_info "端口: $PORT"
    
    gunicorn src.api.app:app \
        --bind "0.0.0.0:$PORT" \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers "$WORKERS" \
        --daemon \
        --pid "$PID_FILE" \
        --access-logfile "$PROJECT_DIR/access.log" \
        --error-logfile "$PROJECT_DIR/error.log"
    
    # 检查启动结果
    sleep 2
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo_success "服务已在后台启动"
            echo_info "PID: $PID"
            echo_info "访问地址: http://localhost:$PORT"
            echo_info "访问日志: tail -f $PROJECT_DIR/access.log"
            echo_info "错误日志: tail -f $PROJECT_DIR/error.log"
            echo_info "停止服务: ./stop.sh"
        else
            echo_error "服务启动失败"
            echo_info "请检查错误日志: cat $PROJECT_DIR/error.log"
            exit 1
        fi
    else
        echo_error "PID文件未创建，启动可能失败"
        echo_info "请检查错误日志: cat $PROJECT_DIR/error.log"
        exit 1
    fi
}

# 主流程
main() {
    echo_info "Fullstack LangGraph 服务启动中..."
    echo ""
    
    check_environment
    check_port
    setup_ssl
    activate_venv
    
    case $MODE in
        dev)
            start_dev
            ;;
        prod)
            start_prod
            ;;
        *)
            echo_error "未知模式: $MODE"
            exit 1
            ;;
    esac
}

# 捕获信号，优雅退出
trap 'echo_warning "收到停止信号，正在退出..."; exit 0' INT TERM

# 执行主流程
main "$@"