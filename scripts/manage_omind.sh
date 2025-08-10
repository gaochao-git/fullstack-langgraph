#!/bin/bash

# OMind 智能运维平台统一管理脚本
# 负责管理所有组件的生命周期

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 加载公共函数库
source "$SCRIPT_DIR/common/colors.sh"
source "$SCRIPT_DIR/common/logger.sh"
source "$SCRIPT_DIR/common/utils.sh"

# 平台信息
PLATFORM_NAME="OMind 智能运维平台"
VERSION="1.0.0"

# 组件列表
COMPONENTS=("backend" "mcp_servers" "mcp_gateway")
COMPONENT_NAMES=(
    "Backend API"
    "MCP Servers"
    "MCP Gateway"
)

# 默认配置
DEFAULT_DEPLOY_PATH="/data/omind"
DEFAULT_PYTHON_PATH=""
DEFAULT_PACKAGE=""

# 部署路径（从配置文件读取）
DEPLOY_PATH=""
PYTHON_PATH=""
CONFIG_FILE="$HOME/.omind/config"

# 加载配置
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    fi
}

# 保存配置
save_config() {
    ensure_dir "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" << EOF
# OMind 配置文件
DEPLOY_PATH="$DEPLOY_PATH"
PYTHON_PATH="$PYTHON_PATH"
LAST_UPDATE=$(date +%Y-%m-%d_%H:%M:%S)
EOF
}

# 检查组件管理脚本
check_component_script() {
    local component=$1
    local script_path="$component/manage.sh"
    
    if [ ! -f "$script_path" ]; then
        log_error "组件管理脚本不存在: $script_path"
        return 1
    fi
    
    if [ ! -x "$script_path" ]; then
        log_warning "组件管理脚本无执行权限，正在修复..."
        chmod +x "$script_path"
    fi
    
    return 0
}

# 执行组件命令
execute_component_command() {
    local component=$1
    local command=$2
    shift 2
    
    local script_path="$component/manage.sh"
    
    if ! check_component_script "$component"; then
        return 1
    fi
    
    log_step "执行: $component/manage.sh $command"
    
    cd "$component"
    
    # 如果是开发环境启动后端，设置 DEV_MODE
    if [ "$component" = "backend" ] && [ "$command" = "start" ] && [ "${OMIND_DEV_MODE:-false}" = "true" ]; then
        DEV_MODE=true ./manage.sh "$command" "$@"
    else
        ./manage.sh "$command" "$@"
    fi
    
    local result=$?
    cd "$PROJECT_ROOT"
    
    return $result
}

# 初始化项目
init_project() {
    print_title "初始化 $PLATFORM_NAME"
    
    # 解析参数
    local deploy_path="$DEFAULT_DEPLOY_PATH"
    local python_path="$DEFAULT_PYTHON_PATH"
    local package="$DEFAULT_PACKAGE"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --deploy-path)
                deploy_path="$2"
                shift 2
                ;;
            --python-path)
                python_path="$2"
                shift 2
                ;;
            --package)
                package="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                return 1
                ;;
        esac
    done
    
    log_info "初始化参数:"
    log_info "  部署路径: $deploy_path"
    log_info "  Python路径: ${python_path:-自动检测}"
    log_info "  安装包: ${package:-当前目录}"
    
    # 保存配置
    DEPLOY_PATH="$deploy_path"
    PYTHON_PATH="$python_path"
    save_config
    
    # 如果提供了安装包，先解压
    if [ -n "$package" ] && [ -f "$package" ]; then
        log_step "解压安装包..."
        local temp_dir="/tmp/omind_install_$$"
        mkdir -p "$temp_dir"
        tar -xzf "$package" -C "$temp_dir"
        
        # 找到解压后的目录
        local extracted_dir=$(ls -d "$temp_dir"/* | head -1)
        
        log_step "复制文件到部署目录..."
        ensure_dir "$DEPLOY_PATH"
        rsync -av --exclude='logs/' --exclude='pids/' "$extracted_dir/" "$DEPLOY_PATH/"
        
        # 清理临时目录
        rm -rf "$temp_dir"
        
        # 切换到部署目录
        cd "$DEPLOY_PATH"
        PROJECT_ROOT="$DEPLOY_PATH"
    fi
    
    # 设置Python环境变量
    if [ -n "$PYTHON_PATH" ]; then
        export PYTHON_CMD="$PYTHON_PATH"
    fi
    
    # 初始化各组件
    log_info "开始初始化各组件..."
    
    local failed=0
    for i in ${!COMPONENTS[@]}; do
        local component="${COMPONENTS[$i]}"
        local name="${COMPONENT_NAMES[$i]}"
        
        echo
        log_progress "初始化 $name..."
        
        if execute_component_command "$component" "init"; then
            log_done "$name 初始化成功"
        else
            log_fail "$name 初始化失败"
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -eq 0 ]; then
        log_success "所有组件初始化成功"
        log_info "部署路径: $DEPLOY_PATH"
        log_info "配置文件: $CONFIG_FILE"
    else
        log_error "$failed 个组件初始化失败"
        return 1
    fi
}

# 启动所有服务
start_all() {
    print_title "启动 $PLATFORM_NAME"
    
    load_config
    
    if [ -n "$DEPLOY_PATH" ] && [ -d "$DEPLOY_PATH" ]; then
        cd "$DEPLOY_PATH"
        PROJECT_ROOT="$DEPLOY_PATH"
    fi
    
    local failed=0
    
    # 按顺序启动服务
    # 1. 先启动 MCP Servers
    log_progress "启动 MCP Servers..."
    if execute_component_command "mcp_servers" "start"; then
        log_done "MCP Servers 启动成功"
    else
        log_fail "MCP Servers 启动失败"
        failed=$((failed + 1))
    fi
    
    # 2. 启动 Backend API
    log_progress "启动 Backend API..."
    if execute_component_command "backend" "start"; then
        log_done "Backend API 启动成功"
    else
        log_fail "Backend API 启动失败"
        failed=$((failed + 1))
    fi
    
    # 3. 启动 MCP Gateway
    log_progress "启动 MCP Gateway..."
    if execute_component_command "mcp_gateway" "start"; then
        log_done "MCP Gateway 启动成功"
    else
        log_fail "MCP Gateway 启动失败"
        failed=$((failed + 1))
    fi
    
    echo
    if [ $failed -eq 0 ]; then
        log_success "所有服务启动成功"
        show_access_info
    else
        log_error "$failed 个服务启动失败"
        return 1
    fi
}

# 停止所有服务
stop_all() {
    print_title "停止 $PLATFORM_NAME"
    
    load_config
    
    if [ -n "$DEPLOY_PATH" ] && [ -d "$DEPLOY_PATH" ]; then
        cd "$DEPLOY_PATH"
        PROJECT_ROOT="$DEPLOY_PATH"
    fi
    
    local failed=0
    
    # 按逆序停止服务
    # 1. 先停止 MCP Gateway
    log_progress "停止 MCP Gateway..."
    if execute_component_command "mcp_gateway" "stop"; then
        log_done "MCP Gateway 已停止"
    else
        log_fail "MCP Gateway 停止失败"
        failed=$((failed + 1))
    fi
    
    # 2. 停止 Backend API
    log_progress "停止 Backend API..."
    if execute_component_command "backend" "stop"; then
        log_done "Backend API 已停止"
    else
        log_fail "Backend API 停止失败"
        failed=$((failed + 1))
    fi
    
    # 3. 停止 MCP Servers
    log_progress "停止 MCP Servers..."
    if execute_component_command "mcp_servers" "stop"; then
        log_done "MCP Servers 已停止"
    else
        log_fail "MCP Servers 停止失败"
        failed=$((failed + 1))
    fi
    
    echo
    if [ $failed -eq 0 ]; then
        log_success "所有服务已停止"
    else
        log_error "$failed 个服务停止失败"
        return 1
    fi
}

# 重启所有服务
restart_all() {
    print_title "重启 $PLATFORM_NAME"
    
    if ! stop_all; then
        log_error "停止服务失败"
        return 1
    fi
    
    log_info "等待服务完全停止..."
    sleep 3
    
    if ! start_all; then
        log_error "启动服务失败"
        return 1
    fi
}

# 查看所有服务状态
status_all() {
    print_title "$PLATFORM_NAME 状态"
    
    load_config
    
    if [ -n "$DEPLOY_PATH" ] && [ -d "$DEPLOY_PATH" ]; then
        cd "$DEPLOY_PATH"
        PROJECT_ROOT="$DEPLOY_PATH"
        log_info "部署路径: $DEPLOY_PATH"
    else
        log_info "工作路径: $PROJECT_ROOT"
    fi
    
    echo
    
    # 检查各组件状态
    for i in ${!COMPONENTS[@]}; do
        local component="${COMPONENTS[$i]}"
        local name="${COMPONENT_NAMES[$i]}"
        
        if check_component_script "$component"; then
            execute_component_command "$component" "status"
        else
            log_error "● $name - 管理脚本不可用"
        fi
        echo
    done
    
    # 显示系统资源使用情况
    print_separator
    log_info "系统资源使用:"
    log_info "  CPU负载: $(uptime | awk -F'load average:' '{print $2}')"
    log_info "  内存使用: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    log_info "  磁盘使用: $(df -h . | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
}

# 升级项目
upgrade_project() {
    print_title "升级 $PLATFORM_NAME"
    
    load_config
    
    if [ -z "$DEPLOY_PATH" ] || [ ! -d "$DEPLOY_PATH" ]; then
        log_error "未找到部署路径，请先执行 init 命令"
        return 1
    fi
    
    # 解析参数
    local package=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --package)
                package="$2"
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                return 1
                ;;
        esac
    done
    
    if [ -z "$package" ] || [ ! -f "$package" ]; then
        log_error "请提供升级包路径: --package <path>"
        return 1
    fi
    
    log_info "升级参数:"
    log_info "  升级包: $package"
    log_info "  部署路径: $DEPLOY_PATH"
    
    # 备份当前版本
    log_step "备份当前版本..."
    local backup_name="omind_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    local backup_path="/tmp/$backup_name"
    
    cd "$DEPLOY_PATH"
    tar -czf "$backup_path" \
        --exclude='logs' \
        --exclude='pids' \
        --exclude='uploads' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        .
    
    log_done "备份完成: $backup_path"
    
    # 停止所有服务
    log_step "停止所有服务..."
    if ! stop_all; then
        log_error "停止服务失败，升级中止"
        return 1
    fi
    
    # 解压新版本
    log_step "解压升级包..."
    local temp_dir="/tmp/omind_upgrade_$$"
    mkdir -p "$temp_dir"
    tar -xzf "$package" -C "$temp_dir"
    
    # 找到解压后的目录
    local extracted_dir=$(ls -d "$temp_dir"/* | head -1)
    
    # 更新文件
    log_step "更新文件..."
    rsync -av \
        --exclude='logs/' \
        --exclude='pids/' \
        --exclude='uploads/' \
        --exclude='data/' \
        --exclude='.env' \
        --exclude='config.yaml' \
        "$extracted_dir/" "$DEPLOY_PATH/"
    
    # 清理临时目录
    rm -rf "$temp_dir"
    
    # 重新初始化（安装新依赖等）
    log_step "重新初始化组件..."
    cd "$DEPLOY_PATH"
    PROJECT_ROOT="$DEPLOY_PATH"
    
    for component in "${COMPONENTS[@]}"; do
        if execute_component_command "$component" "init"; then
            log_done "$component 初始化成功"
        else
            log_error "$component 初始化失败"
            log_info "恢复备份..."
            tar -xzf "$backup_path" -C "$DEPLOY_PATH"
            return 1
        fi
    done
    
    # 启动服务
    log_step "启动服务..."
    if ! start_all; then
        log_error "启动服务失败"
        log_info "服务未启动，但升级已完成"
        log_info "请手动检查并启动服务"
        return 1
    fi
    
    log_success "升级完成"
    log_info "备份文件: $backup_path"
}

# 清理项目
cleanup_project() {
    print_title "清理 $PLATFORM_NAME"
    
    load_config
    
    if [ -n "$DEPLOY_PATH" ] && [ -d "$DEPLOY_PATH" ]; then
        cd "$DEPLOY_PATH"
        PROJECT_ROOT="$DEPLOY_PATH"
    fi
    
    # 确保所有服务已停止
    log_info "检查服务状态..."
    local any_running=false
    
    for component in "${COMPONENTS[@]}"; do
        if [ -d "$component" ] && [ -f "$component/manage.sh" ]; then
            # 静默检查状态
            if cd "$component" && ./manage.sh status 2>&1 | grep -q "运行中"; then
                any_running=true
                break
            fi
            cd "$PROJECT_ROOT"
        fi
    done
    
    if [ "$any_running" = true ]; then
        log_error "检测到服务仍在运行"
        read -p "是否先停止所有服务? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_all
        else
            log_info "清理已取消"
            return 1
        fi
    fi
    
    # 执行各组件的清理
    log_info "开始清理各组件..."
    
    for i in ${!COMPONENTS[@]}; do
        local component="${COMPONENTS[$i]}"
        local name="${COMPONENT_NAMES[$i]}"
        
        echo
        log_progress "清理 $name..."
        
        if execute_component_command "$component" "cleanup"; then
            log_done "$name 清理完成"
        else
            log_fail "$name 清理失败"
        fi
    done
    
    # 询问是否删除部署目录
    if [ -n "$DEPLOY_PATH" ] && [ "$PWD" = "$DEPLOY_PATH" ]; then
        echo
        log_warning "当前在部署目录中: $DEPLOY_PATH"
        read -p "是否完全删除部署目录? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cd /
            rm -rf "$DEPLOY_PATH"
            log_success "部署目录已删除"
            
            # 清除配置
            rm -f "$CONFIG_FILE"
            log_info "配置文件已清除"
        fi
    fi
    
    log_success "清理完成"
}

# 显示访问信息
show_access_info() {
    echo
    print_separator
    log_info "访问信息:"
    log_info "  前端界面: http://localhost/"
    log_info "  后端API: http://localhost:8000"
    log_info "  API文档: http://localhost:8000/docs"
    log_info "  MCP Gateway: http://localhost:5235"
    echo
    log_info "MCP服务器:"
    log_info "  数据库查询: http://localhost:3001/mcp"
    log_info "  SSH执行: http://localhost:3002/mcp"
    log_info "  ES搜索: http://localhost:3003/mcp"
    log_info "  Zabbix监控: http://localhost:3004/mcp"
    print_separator
}

# 显示帮助信息
show_help() {
    echo "$PLATFORM_NAME 管理脚本 v$VERSION"
    echo ""
    echo "使用方法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  init      初始化项目"
    echo "            --deploy-path PATH   部署路径 (默认: $DEFAULT_DEPLOY_PATH)"
    echo "            --python-path PATH   Python路径 (默认: 自动检测)"
    echo "            --package FILE       安装包路径 (默认: 当前目录)"
    echo ""
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  status    查看服务状态"
    echo ""
    echo "  upgrade   升级项目"
    echo "            --package FILE       升级包路径 (必需)"
    echo ""
    echo "  cleanup   清理项目"
    echo ""
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  # 初始化项目"
    echo "  $0 init --deploy-path /data/omind --package omind-20240101.tar.gz"
    echo ""
    echo "  # 启动所有服务"
    echo "  $0 start"
    echo ""
    echo "  # 查看状态"
    echo "  $0 status"
    echo ""
    echo "  # 升级项目"
    echo "  $0 upgrade --package omind-20240102.tar.gz"
}

# 主函数
main() {
    case "${1:-help}" in
        init)
            shift
            init_project "$@"
            ;;
        start)
            start_all
            ;;
        stop)
            stop_all
            ;;
        restart)
            restart_all
            ;;
        status)
            status_all
            ;;
        upgrade)
            shift
            upgrade_project "$@"
            ;;
        cleanup)
            cleanup_project
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"