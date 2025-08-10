#!/bin/bash

# Backend API 服务管理脚本
# 支持标准命令: init, start, stop, restart, status, cleanup

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载公共函数库
source "../scripts/common/logger.sh"
source "../scripts/common/utils.sh"

# 组件名称
COMPONENT_NAME="Backend API"
COMPONENT_ID="backend"

# 配置
PORT=8000
PID_FILE="pids/backend.pid"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/backend.log"

# 直接使用当前环境的 python 和 pip
# 假设用户已经 source venv/bin/activate

# 初始化组件
init() {
    print_title "初始化 $COMPONENT_NAME"
    
    log_step "创建必要的目录..."
    ensure_dir "$LOG_DIR"
    ensure_dir "pids"
    ensure_dir "uploads"
    ensure_dir "data"
    log_done "目录创建完成"
    
    log_step "检查Python环境..."
    log_info "Python版本: $(python --version)"
    log_done "使用当前激活的Python环境"
    
    log_step "安装依赖包..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_done "依赖包安装完成"
    else
        log_warning "未找到requirements.txt文件"
    fi
    
    log_success "$COMPONENT_NAME 初始化完成"
}

# 启动服务
start() {
    print_title "启动 $COMPONENT_NAME"
    
    # 检查是否已经运行
    local pid=$(read_pid_file "$PID_FILE")
    if [ -n "$pid" ] && is_process_running "$pid"; then
        log_warning "$COMPONENT_NAME 已经在运行 (PID: $pid)"
        return 0
    fi
    
    # 检查端口占用
    if is_port_in_use "$PORT"; then
        local occupied_pid=$(get_pid_by_port "$PORT")
        log_error "端口 $PORT 已被占用 (PID: $occupied_pid)"
        return 1
    fi
    
    # 确保目录存在
    ensure_dir "$LOG_DIR"
    ensure_dir "$(dirname "$PID_FILE")"
    
    log_info "启动参数:"
    log_info "  端口: $PORT"
    log_info "  PID文件: $PID_FILE"
    
    # 设置环境变量
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    # 检查是否是开发模式（通过环境变量控制）
    if [ "${DEV_MODE:-false}" = "true" ]; then
        log_info "开发模式：启用热重载"
        # 开发模式使用 --reload，不使用 nohup，直接输出到日志
        python -m uvicorn src.main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --reload \
            > "$LOG_FILE" 2>&1 &
    else
        # 生产模式使用 workers
        nohup python -m uvicorn src.main:app \
            --host 0.0.0.0 \
            --port $PORT \
            --workers 1 \
            > "$LOG_FILE" 2>&1 &
    fi
    
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    if wait_for_service "curl -s http://localhost:$PORT/api/" 30; then
        log_success "$COMPONENT_NAME 启动成功 (PID: $pid)"
        log_info "访问地址: http://localhost:$PORT"
        log_info "API文档: http://localhost:$PORT/docs"
        log_info "查看日志: tail -f $LOG_FILE"
    else
        log_error "$COMPONENT_NAME 启动失败"
        log_info "请查看日志: $LOG_FILE"
        kill $pid 2>/dev/null || true
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    print_title "停止 $COMPONENT_NAME"
    
    local pid=$(read_pid_file "$PID_FILE")
    if [ -z "$pid" ]; then
        log_warning "$COMPONENT_NAME 未运行"
        return 0
    fi
    
    if is_process_running "$pid"; then
        log_info "停止 $COMPONENT_NAME (PID: $pid)..."
        if graceful_stop "$pid" 15; then
            log_success "$COMPONENT_NAME 已停止"
        else
            log_error "无法停止 $COMPONENT_NAME"
            return 1
        fi
    else
        log_warning "进程不存在，清理PID文件"
    fi
    
    rm -f "$PID_FILE"
}

# 重启服务
restart() {
    print_title "重启 $COMPONENT_NAME"
    
    if ! stop; then
        log_error "停止服务失败"
        return 1
    fi
    
    log_info "等待服务完全停止..."
    sleep 2
    
    if ! start; then
        log_error "启动服务失败"
        return 1
    fi
}

# 查看状态
status() {
    print_title "$COMPONENT_NAME 状态"
    
    local pid=$(read_pid_file "$PID_FILE")
    
    if [ -n "$pid" ] && is_process_running "$pid"; then
        log_success "● $COMPONENT_NAME 运行中"
        log_info "  PID: $pid"
        log_info "  端口: $PORT"
        log_info "  日志: $LOG_FILE"
        
        # API健康检查
        log_step "执行健康检查..."
        if curl -s "http://localhost:$PORT/api/" >/dev/null 2>&1; then
            log_done "API响应正常"
        else
            log_fail "API无响应"
        fi
        
        # 显示最近的日志
        if [ -f "$LOG_FILE" ]; then
            echo
            log_info "最近日志:"
            tail -5 "$LOG_FILE" | sed 's/^/  /'
        fi
    else
        log_error "● $COMPONENT_NAME 未运行"
        if [ -f "$PID_FILE" ]; then
            log_warning "  PID文件存在但进程不存在"
        fi
    fi
}

# 清理文件
cleanup() {
    print_title "清理 $COMPONENT_NAME"
    
    # 确保服务已停止
    local pid=$(read_pid_file "$PID_FILE")
    if [ -n "$pid" ] && is_process_running "$pid"; then
        log_error "请先停止服务再执行清理"
        return 1
    fi
    
    log_step "清理日志文件..."
    if [ -d "$LOG_DIR" ]; then
        local log_count=$(find "$LOG_DIR" -name "*.log*" -type f | wc -l)
        if [ $log_count -gt 0 ]; then
            log_info "发现 $log_count 个日志文件"
            read -p "确认删除所有日志文件? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -f "$LOG_DIR"/*.log*
                log_done "日志文件已清理"
            else
                log_info "跳过日志清理"
            fi
        else
            log_info "没有日志文件需要清理"
        fi
    fi
    
    log_step "清理PID文件..."
    rm -f "$PID_FILE"
    rm -f pids/*.pid 2>/dev/null || true
    log_done "PID文件已清理"
    
    log_step "清理缓存文件..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    log_done "缓存文件已清理"
    
    log_step "清理上传文件..."
    if [ -d "uploads" ]; then
        local upload_count=$(find "uploads" -type f | wc -l)
        if [ $upload_count -gt 0 ]; then
            log_info "发现 $upload_count 个上传文件"
            read -p "确认删除所有上传文件? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf uploads/*
                log_done "上传文件已清理"
            else
                log_info "跳过上传文件清理"
            fi
        fi
    fi
    
    log_success "清理完成"
}

# 显示帮助
show_help() {
    echo "使用方法: $0 {init|start|stop|restart|status|cleanup}"
    echo ""
    echo "命令说明:"
    echo "  init     - 初始化组件"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  status   - 查看服务状态"
    echo "  cleanup  - 清理临时文件和日志"
}

# 主函数
main() {
    case "${1:-help}" in
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
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"