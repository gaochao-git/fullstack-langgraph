#!/bin/bash

# MCP Servers 管理脚本
# 支持标准命令: init, start, stop, restart, status, cleanup

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载公共函数库
source "../scripts/common/logger.sh"
source "../scripts/common/utils.sh"

# 组件名称
COMPONENT_NAME="MCP Servers"
COMPONENT_ID="mcp_servers"

# 配置
SERVERS=("db_query" "ssh_exec" "es_search" "zabbix_monitor")
PORTS=(3001 3002 3003 3004)
PID_DIR="pids"
LOG_DIR="logs"
CONFIG_FILE="config.yaml"

# 获取服务器配置
get_server_config() {
    local server=$1
    case $server in
        db_query)
            echo "port: 3001"
            ;;
        ssh_exec)
            echo "port: 3002"
            ;;
        es_search)
            echo "port: 3003"
            ;;
        zabbix_monitor)
            echo "port: 3004"
            ;;
    esac
}

# 获取Python命令
get_mcp_python() {
    # 1. 优先使用conda环境
    if command_exists conda; then
        echo "conda run -n ${CONDA_ENV:-py312} python"
        return
    fi
    
    # 2. 使用虚拟环境
    if [ -d "../venv" ] && [ -f "../venv/bin/python" ]; then
        echo "../venv/bin/python"
        return
    fi
    
    # 3. 使用系统Python
    get_python_cmd
}

# 初始化组件
init() {
    print_title "初始化 $COMPONENT_NAME"
    
    log_step "创建必要的目录..."
    ensure_dir "$LOG_DIR"
    ensure_dir "$PID_DIR"
    ensure_dir "data"
    log_done "目录创建完成"
    
    log_step "检查Python环境..."
    local python_cmd=$(get_mcp_python)
    log_info "Python命令: $python_cmd"
    
    if ! check_python_version 3.11; then
        log_error "Python版本不满足要求"
        return 1
    fi
    log_done "Python环境检查通过"
    
    log_step "检查配置文件..."
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "配置文件不存在: $CONFIG_FILE"
        log_info "创建默认配置..."
        cat > "$CONFIG_FILE" << 'EOF'
# MCP Servers 配置文件
servers:
  db_query:
    port: 3001
    enabled: true
  ssh_exec:
    port: 3002
    enabled: true
  es_search:
    port: 3003
    enabled: true
  zabbix_monitor:
    port: 3004
    enabled: true
EOF
        log_done "默认配置已创建"
    else
        log_done "配置文件就绪"
    fi
    
    log_step "安装依赖包..."
    if [ -f "requirements.txt" ]; then
        $python_cmd -m pip install -r requirements.txt
        log_done "依赖包安装完成"
    else
        log_warning "未找到requirements.txt文件"
    fi
    
    log_success "$COMPONENT_NAME 初始化完成"
}

# 启动单个服务器
start_server() {
    local server=$1
    local port=$2
    local pid_file="$PID_DIR/${server}.pid"
    local log_file="$LOG_DIR/${server}.log"
    
    # 检查是否已经运行
    local pid=$(read_pid_file "$pid_file")
    if [ -n "$pid" ] && is_process_running "$pid"; then
        log_warning "$server 已经在运行 (PID: $pid)"
        return 0
    fi
    
    # 检查端口占用
    if is_port_in_use "$port"; then
        local occupied_pid=$(get_pid_by_port "$port")
        log_error "$server 端口 $port 已被占用 (PID: $occupied_pid)"
        return 1
    fi
    
    # 获取Python命令
    local python_cmd=$(get_mcp_python)
    
    # 启动服务器
    log_info "启动 $server (端口: $port)..."
    
    # 设置环境变量
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    export MCP_SERVER_NAME="$server"
    export MCP_SERVER_PORT="$port"
    
    nohup $python_cmd "${server}_server.py" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # 等待服务启动
    sleep 2
    
    if is_process_running "$pid"; then
        log_done "$server 启动成功 (PID: $pid, 端口: $port)"
        return 0
    else
        log_fail "$server 启动失败"
        rm -f "$pid_file"
        return 1
    fi
}

# 启动所有服务
start() {
    print_title "启动 $COMPONENT_NAME"
    
    # 确保目录存在
    ensure_dir "$LOG_DIR"
    ensure_dir "$PID_DIR"
    
    local failed=0
    for i in ${!SERVERS[@]}; do
        if ! start_server "${SERVERS[$i]}" "${PORTS[$i]}"; then
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        log_success "所有MCP服务器启动成功"
        echo
        log_info "服务地址:"
        for i in ${!SERVERS[@]}; do
            log_info "  ${SERVERS[$i]}: http://localhost:${PORTS[$i]}/sse/"
        done
    else
        log_error "$failed 个服务器启动失败"
        return 1
    fi
}

# 停止单个服务器
stop_server() {
    local server=$1
    local pid_file="$PID_DIR/${server}.pid"
    
    local pid=$(read_pid_file "$pid_file")
    if [ -z "$pid" ]; then
        log_info "$server 未运行"
        return 0
    fi
    
    if is_process_running "$pid"; then
        log_info "停止 $server (PID: $pid)..."
        if graceful_stop "$pid"; then
            log_done "$server 已停止"
        else
            log_fail "无法停止 $server"
            return 1
        fi
    else
        log_warning "$server 进程不存在"
    fi
    
    rm -f "$pid_file"
}

# 停止所有服务
stop() {
    print_title "停止 $COMPONENT_NAME"
    
    local failed=0
    for server in "${SERVERS[@]}"; do
        if ! stop_server "$server"; then
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        log_success "所有MCP服务器已停止"
    else
        log_error "$failed 个服务器停止失败"
        return 1
    fi
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
    
    local running=0
    local total=${#SERVERS[@]}
    
    echo
    for i in ${!SERVERS[@]}; do
        local server="${SERVERS[$i]}"
        local port="${PORTS[$i]}"
        local pid_file="$PID_DIR/${server}.pid"
        local pid=$(read_pid_file "$pid_file")
        
        if [ -n "$pid" ] && is_process_running "$pid"; then
            log_success "● $server 运行中"
            log_info "    PID: $pid, 端口: $port"
            running=$((running + 1))
        else
            log_error "● $server 未运行"
            if [ -f "$pid_file" ]; then
                log_warning "    PID文件存在但进程不存在"
            fi
        fi
    done
    
    echo
    if [ $running -eq $total ]; then
        log_success "所有服务器运行正常 ($running/$total)"
    elif [ $running -eq 0 ]; then
        log_error "所有服务器都未运行"
    else
        log_warning "部分服务器运行中 ($running/$total)"
    fi
    
    # 显示端口监听状态
    echo
    log_info "端口监听状态:"
    for port in "${PORTS[@]}"; do
        if is_port_in_use "$port"; then
            log_done "  端口 $port: 监听中"
        else
            log_fail "  端口 $port: 未监听"
        fi
    done
}

# 清理文件
cleanup() {
    print_title "清理 $COMPONENT_NAME"
    
    # 确保服务已停止
    local any_running=false
    for server in "${SERVERS[@]}"; do
        local pid_file="$PID_DIR/${server}.pid"
        local pid=$(read_pid_file "$pid_file")
        if [ -n "$pid" ] && is_process_running "$pid"; then
            any_running=true
            break
        fi
    done
    
    if [ "$any_running" = true ]; then
        log_error "请先停止所有服务再执行清理"
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
    rm -f "$PID_DIR"/*.pid 2>/dev/null || true
    log_done "PID文件已清理"
    
    log_step "清理缓存文件..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    log_done "缓存文件已清理"
    
    log_success "清理完成"
}

# 显示帮助
show_help() {
    echo "使用方法: $0 {init|start|stop|restart|status|cleanup}"
    echo ""
    echo "命令说明:"
    echo "  init     - 初始化组件"
    echo "  start    - 启动所有MCP服务器"
    echo "  stop     - 停止所有MCP服务器"
    echo "  restart  - 重启所有MCP服务器"
    echo "  status   - 查看服务状态"
    echo "  cleanup  - 清理临时文件和日志"
    echo ""
    echo "服务器列表:"
    for i in ${!SERVERS[@]}; do
        echo "  - ${SERVERS[$i]} (端口: ${PORTS[$i]})"
    done
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