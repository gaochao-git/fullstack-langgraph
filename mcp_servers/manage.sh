#!/bin/bash

# MCP Servers 管理脚本
# 支持标准命令: init, start, stop, restart, status, cleanup

set -e

# 获取脚本所在目录（保存原始路径）
MCP_SERVERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$MCP_SERVERS_DIR"
cd "$SCRIPT_DIR"

# 加载公共函数库
source "../scripts/common/logger.sh"
source "../scripts/common/utils.sh"

# 恢复正确的脚本目录
SCRIPT_DIR="$MCP_SERVERS_DIR"

# 组件名称
COMPONENT_NAME="MCP Servers"
COMPONENT_ID="mcp_servers"

# 配置
SERVERS=("db_query" "ssh_exec" "es_search" "zabbix_monitor" "sop_server")
SERVICE_NAMES=("mysql" "ssh" "elasticsearch" "zabbix" "sop")
PORTS=(3001 3002 3003 3004 3005)
PID_DIR="pids"
LOG_DIR="logs"


# 直接使用当前环境的 python
# 假设用户已经 source ../venv/bin/activate

# 检查配置文件是否存在
check_config_file() {
    local config_file="$SCRIPT_DIR/config.yaml"
    
    # 调试信息（如需要可以取消注释）
    # echo "[DEBUG] 检查配置文件: $config_file"
    # echo "[DEBUG] 当前目录: $(pwd)"
    # echo "[DEBUG] SCRIPT_DIR: $SCRIPT_DIR"
    # ls -la "$config_file" 2>/dev/null && echo "[DEBUG] 配置文件存在" || echo "[DEBUG] 配置文件不存在"
    
    if [ ! -f "$config_file" ]; then
        log_error "配置文件不存在: $config_file"
        echo "请执行以下命令创建配置文件："
        echo "  cd $SCRIPT_DIR"
        echo "  cp config.yaml.template config.yaml"
        echo "  vim config.yaml  # 编辑配置文件"
        exit 1
    fi
}

# 检查服务是否启用
# 简化版本：检查配置文件中的服务开关
is_service_enabled() {
    local service_name=$1
    
    # 使用 grep 检查服务是否启用
    # 查找 services 部分下的服务配置
    if grep -A 10 "^services:" "$SCRIPT_DIR/config.yaml" | grep -E "^[[:space:]]+${service_name}:[[:space:]]+(true|false)" | grep -q "true"; then
        return 0
    elif grep -A 10 "^services:" "$SCRIPT_DIR/config.yaml" | grep -E "^[[:space:]]+${service_name}:[[:space:]]+(true|false)" | grep -q "false"; then
        return 1
    else
        # 如果没有找到配置，默认启用
        return 0
    fi
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

# 启动单个服务器
start_server() {
    local server=$1
    local port=$2
    local pid_file="$PID_DIR/${server}.pid"
    local log_file="$LOG_DIR/${server}.log"
    
    echo "--------------------------------------------------------------------------------"
    
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
    
    # 使用当前环境的Python
    
    # 启动服务器
    log_info "启动 $server (端口: $port)..."
    
    # 设置环境变量
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    export MCP_SERVER_NAME="$server"
    export MCP_SERVER_PORT="$port"
    
    # 根据服务器名称确定实际的Python文件
    local py_file=""
    case $server in
        db_query)
            py_file="servers/db_mcp_server.py"
            ;;
        ssh_exec)
            py_file="servers/ssh_mcp_server.py"
            ;;
        es_search)
            py_file="servers/es_mcp_server.py"
            ;;
        zabbix_monitor)
            py_file="servers/zabbix_mcp_server.py"
            ;;
        sop_server)
            py_file="servers/sop_mcp_server.py"
            ;;
    esac
    
    nohup python "$py_file" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # 等待服务启动
    sleep 2
    
    if is_process_running "$pid"; then
        log_done "$server 启动成功 (PID: $pid)"
        log_info "MCP地址: http://localhost:$port/mcp"
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
    
    # 检查配置文件
    check_config_file
    
    # 确保目录存在
    ensure_dir "$LOG_DIR"
    ensure_dir "$PID_DIR"
    
    local failed=0
    local started=0
    local skipped=0
    
    for i in ${!SERVERS[@]}; do
        local service_name="${SERVICE_NAMES[$i]}"
        
        # 检查服务是否启用
        if is_service_enabled "$service_name"; then
            if start_server "${SERVERS[$i]}" "${PORTS[$i]}"; then
                started=$((started + 1))
            else
                failed=$((failed + 1))
            fi
        else
            log_info "跳过未启用的服务: ${SERVERS[$i]} ($service_name)"
            skipped=$((skipped + 1))
        fi
    done
    
    echo "================================================================================"
    echo
    if [ $started -gt 0 ]; then
        log_success "成功启动 $started 个服务"
    fi
    if [ $skipped -gt 0 ]; then
        log_info "跳过 $skipped 个未启用的服务"
    fi
    if [ $failed -gt 0 ]; then
        log_error "$failed 个服务启动失败"
    fi
    echo "================================================================================"
    
    [ $failed -eq 0 ]
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
    local enabled=0
    local disabled=0
    
    echo
    for i in ${!SERVERS[@]}; do
        local server="${SERVERS[$i]}"
        local service_name="${SERVICE_NAMES[$i]}"
        local port="${PORTS[$i]}"
        local pid_file="$PID_DIR/${server}.pid"
        
        if is_service_enabled "$service_name"; then
            enabled=$((enabled + 1))
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
        else
            log_info "○ $server 未启用"
            disabled=$((disabled + 1))
        fi
    done
    
    echo
    if [ $enabled -eq 0 ]; then
        log_warning "没有启用的服务"
    elif [ $running -eq $enabled ]; then
        log_success "所有已启用的服务运行正常 ($running/$enabled 启用, $disabled 禁用)"
    elif [ $running -eq 0 ]; then
        log_error "所有已启用的服务都未运行 ($enabled 启用, $disabled 禁用)"
    else
        log_warning "部分服务运行中 ($running/$enabled 运行, $disabled 禁用)"
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