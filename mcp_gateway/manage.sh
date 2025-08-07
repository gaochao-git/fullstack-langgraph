#!/bin/bash

# MCP Gateway 管理脚本
# 支持标准命令: init, start, stop, restart, status, cleanup

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载公共函数库
source "../scripts/common/logger.sh"
source "../scripts/common/utils.sh"

# 组件名称
COMPONENT_NAME="MCP Gateway"
COMPONENT_ID="mcp_gateway"

# 配置文件
CONFIG_FILE="config/mcp-gateway.yaml"
ENV_FILE=".env"

# 从环境变量读取配置
PID_FILE=$(get_env_value "MCP_GATEWAY_PID" "./data/mcp-gateway.pid" "$ENV_FILE")
PORT=$(get_env_value "MCP_GATEWAY_PORT" "5235" "$ENV_FILE")
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/mcp-gateway.log"

# 检测平台和二进制文件
detect_binary() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)
    
    case "$os" in
        darwin) PLATFORM="darwin";;
        linux) PLATFORM="linux";;
        *) log_error "不支持的操作系统: $os"; return 1;;
    esac
    
    case "$arch" in
        x86_64|amd64) ARCH="amd64";;
        aarch64|arm64) ARCH="arm64";;
        *) log_error "不支持的架构: $arch"; return 1;;
    esac
    
    BINARY="mcp-gateway-${PLATFORM}-${ARCH}"
    
    if [ ! -f "$BINARY" ]; then
        log_error "未找到可执行文件: $BINARY"
        log_info "请先编译对应平台的二进制文件"
        return 1
    fi
    
    # 确保可执行
    chmod +x "$BINARY" 2>/dev/null || true
}

# 初始化组件
init() {
    print_title "初始化 $COMPONENT_NAME"
    
    log_step "创建必要的目录..."
    ensure_dir "$LOG_DIR"
    ensure_dir "$(dirname "$PID_FILE")"
    ensure_dir "data"
    ensure_dir "config"
    log_done "目录创建完成"
    
    log_step "检查配置文件..."
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        return 1
    fi
    log_done "配置文件就绪"
    
    log_step "检查环境文件..."
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境文件不存在，使用默认配置"
    else
        log_done "环境文件就绪"
    fi
    
    log_step "检测运行环境..."
    if ! detect_binary; then
        return 1
    fi
    log_done "二进制文件: $BINARY"
    
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
    
    # 检测二进制文件
    if ! detect_binary; then
        return 1
    fi
    
    # 确保目录存在
    ensure_dir "$LOG_DIR"
    ensure_dir "$(dirname "$PID_FILE")"
    
    log_info "启动参数:"
    log_info "  二进制文件: $BINARY"
    log_info "  配置文件: $CONFIG_FILE"
    log_info "  端口: $PORT"
    log_info "  PID文件: $PID_FILE"
    
    # 启动服务
    nohup ./"$BINARY" -c "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    log_progress "等待服务启动..."
    sleep 2
    
    if is_process_running "$pid"; then
        log_success "$COMPONENT_NAME 启动成功 (PID: $pid)"
        log_info "访问地址: http://localhost:$PORT"
        log_info "健康检查: curl -s http://localhost:$PORT/health_check"
        log_info "查看日志: tail -f $LOG_FILE"
    else
        log_error "$COMPONENT_NAME 启动失败"
        log_info "请查看日志: $LOG_FILE"
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
        if graceful_stop "$pid"; then
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
        log_info "  平台: $PLATFORM-$ARCH"
        log_info "  配置: $CONFIG_FILE"
        log_info "  日志: $LOG_FILE"
        
        # 健康检查
        log_step "执行健康检查..."
        if curl -s "http://localhost:$PORT/health_check" >/dev/null 2>&1; then
            log_done "健康检查通过"
        else
            log_fail "健康检查失败"
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
    log_done "PID文件已清理"
    
    log_step "清理临时文件..."
    rm -f data/*.tmp 2>/dev/null || true
    log_done "临时文件已清理"
    
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