#!/bin/bash

# Celery Task 管理脚本
# 用于管理 Celery Beat 和 Worker 进程

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 配置
PROJECT_NAME="celery_task"
VENV_PATH="/Users/gaochao/gaochao-git/gaochao_repo/fullstack-langgraph/venv"
SUPERVISORD_CONF="supervisord.conf"
SUPERVISORCTL="supervisorctl -c $SUPERVISORD_CONF"
LOG_DIR="logs"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        return 1
    fi
    return 0
}

# 检查 supervisord 是否运行
check_supervisord() {
    if pgrep -f "supervisord.*$SUPERVISORD_CONF" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 初始化
init() {
    print_info "初始化 $PROJECT_NAME..."
    
    # 创建日志目录
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        print_success "创建日志目录: $LOG_DIR"
    fi
    
    # 检查虚拟环境
    if ! check_venv; then
        return 1
    fi
    
    # 检查依赖
    print_info "检查 Python 依赖..."
    source "$VENV_PATH/bin/activate"
    
    if ! pip show celery > /dev/null 2>&1; then
        print_info "安装依赖..."
        pip install -r requirements.txt
    else
        print_success "依赖已安装"
    fi
    
    deactivate
    
    # 检查配置文件
    if [ ! -f "$SUPERVISORD_CONF" ]; then
        print_error "Supervisor 配置文件不存在: $SUPERVISORD_CONF"
        return 1
    fi
    
    print_success "初始化完成"
}

# 启动服务
start() {
    print_info "启动 $PROJECT_NAME 服务..."
    
    if ! check_venv; then
        return 1
    fi
    
    # 检查 supervisord 是否已运行
    if check_supervisord; then
        print_info "Supervisord 已在运行，启动服务..."
        $SUPERVISORCTL start all
    else
        print_info "启动 Supervisord..."
        supervisord -c "$SUPERVISORD_CONF"
        sleep 2
    fi
    
    # 检查状态
    status
}

# 停止服务
stop() {
    print_info "停止 $PROJECT_NAME 服务..."
    
    if check_supervisord; then
        $SUPERVISORCTL stop all
        print_success "服务已停止"
    else
        print_warning "Supervisord 未运行"
    fi
}

# 重启服务
restart() {
    print_info "重启 $PROJECT_NAME 服务..."
    stop
    sleep 2
    start
}

# 查看状态
status() {
    print_info "$PROJECT_NAME 服务状态:"
    
    if check_supervisord; then
        $SUPERVISORCTL status
    else
        print_warning "Supervisord 未运行"
        return 1
    fi
}

# 查看日志
logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "查看所有日志..."
        tail -f logs/*.log
    else
        case $service in
            beat)
                print_info "查看 Celery Beat 日志..."
                $SUPERVISORCTL tail -f celery_beat
                ;;
            worker)
                print_info "查看 Celery Worker 日志..."
                $SUPERVISORCTL tail -f celery_worker
                ;;
            app)
                print_info "查看应用日志..."
                tail -f logs/celery_*.log
                ;;
            *)
                print_error "未知的服务: $service"
                echo "可用选项: beat, worker, app"
                return 1
                ;;
        esac
    fi
}

# 清理日志和临时文件
cleanup() {
    print_info "清理日志和临时文件..."
    
    # 清理旧日志（保留最近7天）
    find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null
    
    # 清理 Python 缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    
    print_success "清理完成"
}

# 完全关闭（包括 supervisord）
shutdown() {
    print_info "关闭所有服务..."
    
    if check_supervisord; then
        $SUPERVISORCTL shutdown
        print_success "Supervisord 已关闭"
    else
        print_warning "Supervisord 未运行"
    fi
}

# 显示帮助
usage() {
    echo "使用方法: $0 {init|start|stop|restart|status|logs|cleanup|shutdown}"
    echo
    echo "命令说明:"
    echo "  init      - 初始化项目（创建目录、检查依赖）"
    echo "  start     - 启动 Celery Beat 和 Worker"
    echo "  stop      - 停止 Celery Beat 和 Worker"
    echo "  restart   - 重启服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看日志 (可选: beat/worker/app)"
    echo "  cleanup   - 清理日志和临时文件"
    echo "  shutdown  - 完全关闭（包括 supervisord）"
    echo
    echo "示例:"
    echo "  $0 start           # 启动所有服务"
    echo "  $0 logs worker     # 查看 worker 日志"
    echo "  $0 status          # 查看服务状态"
}

# 主函数
main() {
    case "$1" in
        init)
            init
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            logs "$2"
            ;;
        cleanup)
            cleanup
            ;;
        shutdown)
            shutdown
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"