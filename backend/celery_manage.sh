#!/bin/bash

# Celery服务管理脚本
# 用于启动、停止和管理Celery worker和beat服务

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到backend目录
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志目录
LOG_DIR="$SCRIPT_DIR/logs/celery"
mkdir -p "$LOG_DIR"

# PID文件目录
PID_DIR="$SCRIPT_DIR/pids"
mkdir -p "$PID_DIR"

# 虚拟环境路径
VENV_PATH="$PROJECT_ROOT/venv"

# Celery配置
CELERY_APP="src.celery"
WORKER_CONCURRENCY=4
WORKER_LOGLEVEL="info"
BEAT_LOGLEVEL="info"

# 函数：打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 函数：激活虚拟环境
activate_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
        print_message $GREEN "✓ 虚拟环境已激活"
    else
        print_message $RED "✗ 虚拟环境未找到: $VENV_PATH"
        exit 1
    fi
}

# 函数：检查服务状态
check_service() {
    local service_name=$1
    local pid_file="$PID_DIR/celery_${service_name}.pid"
    
    # 首先通过进程名检查
    local actual_pid=""
    if [ "$service_name" = "worker" ]; then
        actual_pid=$(pgrep -f "celery.*$CELERY_APP.*worker" | head -1)
    elif [ "$service_name" = "beat" ]; then
        actual_pid=$(pgrep -f "celery.*$CELERY_APP.*beat" | head -1)
    fi
    
    if [ -n "$actual_pid" ]; then
        print_message $GREEN "✓ Celery $service_name 正在运行 (PID: $actual_pid)"
        # 不要在这里写入PID文件，让Celery自己管理
        return 0
    elif [ -f "$pid_file" ]; then
        # 如果进程不存在但PID文件存在，清理PID文件
        print_message $YELLOW "! Celery $service_name PID文件存在但进程未运行"
        rm -f "$pid_file"
        return 1
    else
        print_message $RED "✗ Celery $service_name 未运行"
        return 1
    fi
}

# 函数：启动Worker
start_worker() {
    print_message $BLUE "正在启动 Celery Worker..."
    
    local pid_file="$PID_DIR/celery_worker.pid"
    local log_file="$LOG_DIR/worker.log"
    
    if check_service "worker" > /dev/null 2>&1; then
        print_message $YELLOW "! Celery Worker 已在运行"
        return 0
    fi
    
    # 启动worker，指定队列优先级
    nohup celery -A $CELERY_APP worker \
        --loglevel=$WORKER_LOGLEVEL \
        --concurrency=$WORKER_CONCURRENCY \
        --pidfile="$pid_file" \
        --logfile="$log_file" \
        -Q system,priority_high,priority_low,celery \
        > "$LOG_DIR/worker_startup.log" 2>&1 &
    
    # 等待启动并检查
    local max_wait=10
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        sleep 1
        wait_time=$((wait_time + 1))
        
        # 检查进程是否存在（不依赖PID文件）
        if pgrep -f "celery.*$CELERY_APP.*worker" > /dev/null; then
            print_message $GREEN "✓ Celery Worker 启动成功"
            # 让Celery自己管理PID文件，不要干预
            return 0
        fi
    done
    
    print_message $RED "✗ Celery Worker 启动失败（等待${max_wait}秒后）"
    cat "$LOG_DIR/worker_startup.log"
    return 1
}

# 函数：启动Beat
start_beat() {
    print_message $BLUE "正在启动 Celery Beat..."
    
    local pid_file="$PID_DIR/celery_beat.pid"
    local log_file="$LOG_DIR/beat.log"
    local schedule_file="$SCRIPT_DIR/celerybeat-schedule"
    
    if check_service "beat" > /dev/null 2>&1; then
        print_message $YELLOW "! Celery Beat 已在运行"
        return 0
    fi
    
    # 启动beat
    nohup celery -A $CELERY_APP beat \
        --loglevel=$BEAT_LOGLEVEL \
        --pidfile="$pid_file" \
        --logfile="$log_file" \
        --schedule="$schedule_file" \
        > "$LOG_DIR/beat_startup.log" 2>&1 &
    
    # 等待启动并检查
    local max_wait=10
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        sleep 1
        wait_time=$((wait_time + 1))
        
        # 检查进程是否存在（不依赖PID文件）
        if pgrep -f "celery.*$CELERY_APP.*beat" > /dev/null; then
            print_message $GREEN "✓ Celery Beat 启动成功"
            # 让Celery自己管理PID文件，不要干预
            return 0
        fi
    done
    
    print_message $RED "✗ Celery Beat 启动失败（等待${max_wait}秒后）"
    cat "$LOG_DIR/beat_startup.log"
    return 1
}

# 函数：停止服务
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/celery_${service_name}.pid"
    
    print_message $BLUE "正在停止 Celery $service_name..."
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            kill -TERM $pid
            sleep 2
            
            # 如果进程还在运行，强制终止
            if ps -p $pid > /dev/null 2>&1; then
                print_message $YELLOW "! 进程未正常退出，强制终止..."
                kill -9 $pid
            fi
            
            rm -f "$pid_file"
            print_message $GREEN "✓ Celery $service_name 已停止"
        else
            rm -f "$pid_file"
            print_message $YELLOW "! Celery $service_name 进程不存在"
        fi
    else
        print_message $YELLOW "! Celery $service_name 未运行"
    fi
}

# 函数：查看日志
view_logs() {
    local service=$1
    local lines=${2:-50}
    
    case $service in
        worker)
            tail -n $lines -f "$LOG_DIR/worker.log"
            ;;
        beat)
            tail -n $lines -f "$LOG_DIR/beat.log"
            ;;
        *)
            print_message $YELLOW "查看最近的日志文件..."
            ls -la "$LOG_DIR/"
            ;;
    esac
}

# 主函数
main() {
    case "$1" in
        start)
            activate_venv
            if [ "$2" = "worker" ]; then
                start_worker
            elif [ "$2" = "beat" ]; then
                start_beat
            else
                start_worker && start_beat
            fi
            ;;
        stop)
            if [ "$2" = "worker" ]; then
                stop_service "worker"
            elif [ "$2" = "beat" ]; then
                stop_service "beat"
            else
                stop_service "worker"
                stop_service "beat"
            fi
            ;;
        restart)
            $0 stop $2
            sleep 2
            $0 start $2
            ;;
        status)
            check_service "worker"
            check_service "beat"
            ;;
        logs)
            activate_venv
            view_logs $2 $3
            ;;
        purge)
            activate_venv
            print_message $BLUE "正在清理所有任务队列..."
            celery -A $CELERY_APP purge -f
            print_message $GREEN "✓ 队列已清理"
            ;;
        inspect)
            activate_venv
            case "$2" in
                active)
                    celery -A $CELERY_APP inspect active
                    ;;
                scheduled)
                    celery -A $CELERY_APP inspect scheduled
                    ;;
                stats)
                    celery -A $CELERY_APP inspect stats
                    ;;
                *)
                    print_message $YELLOW "用法: $0 inspect {active|scheduled|stats}"
                    ;;
            esac
            ;;
        *)
            print_message $YELLOW "用法: $0 {start|stop|restart|status|logs|purge|inspect} [worker|beat]"
            print_message $YELLOW ""
            print_message $YELLOW "命令说明:"
            print_message $YELLOW "  start [worker|beat]  - 启动服务（默认启动所有）"
            print_message $YELLOW "  stop [worker|beat]   - 停止服务（默认停止所有）"
            print_message $YELLOW "  restart [worker|beat] - 重启服务"
            print_message $YELLOW "  status              - 查看服务状态"
            print_message $YELLOW "  logs [worker|beat] [lines] - 查看日志"
            print_message $YELLOW "  purge               - 清理所有任务队列"
            print_message $YELLOW "  inspect {active|scheduled|stats} - 检查任务状态"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"