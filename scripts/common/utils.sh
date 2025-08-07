#!/bin/bash

# 工具函数库
# 为所有管理脚本提供通用工具函数

# 确保日志函数已加载
if [ -z "$(type -t log_info)" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/logger.sh"
fi

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查是否为root用户
is_root() {
    [ "$(id -u)" -eq 0 ]
}

# 获取操作系统类型
get_os_type() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*)    echo "cygwin";;
        MINGW*)     echo "mingw";;
        *)          echo "unknown";;
    esac
}

# 获取Linux发行版
get_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "${ID:-unknown}"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# 检查端口是否被占用
is_port_in_use() {
    local port=$1
    if command_exists lsof; then
        lsof -i :$port >/dev/null 2>&1
    elif command_exists netstat; then
        netstat -an | grep -q ":$port.*LISTEN"
    else
        return 1
    fi
}

# 获取进程PID（通过端口）
get_pid_by_port() {
    local port=$1
    if command_exists lsof; then
        lsof -ti :$port 2>/dev/null | head -1
    elif command_exists netstat; then
        netstat -tlnp 2>/dev/null | grep ":$port" | awk '{print $7}' | cut -d'/' -f1
    fi
}

# 检查进程是否运行
is_process_running() {
    local pid=$1
    [ -n "$pid" ] && ps -p "$pid" >/dev/null 2>&1
}

# 安全地读取PID文件
read_pid_file() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$pid" ] && [ "$pid" -gt 0 ] 2>/dev/null; then
            echo "$pid"
        fi
    fi
}

# 创建必要的目录
ensure_dir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        log_debug "创建目录: $dir"
        mkdir -p "$dir" || {
            log_error "无法创建目录: $dir"
            return 1
        }
    fi
}

# 备份文件
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$file" "$backup" && log_info "文件已备份: $backup"
    fi
}

# 从.env文件读取配置
get_env_value() {
    local key=$1
    local default=$2
    local env_file=${3:-.env}
    
    if [ -f "$env_file" ]; then
        local value=$(grep "^${key}=" "$env_file" | cut -d'=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"//;s/"$//')
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# 等待服务启动
wait_for_service() {
    local check_cmd=$1
    local timeout=${2:-30}
    local interval=${3:-1}
    
    log_info "等待服务启动..."
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if eval "$check_cmd" >/dev/null 2>&1; then
            log_success "服务已启动"
            return 0
        fi
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    echo
    log_error "服务启动超时"
    return 1
}

# 获取Python解释器路径
get_python_cmd() {
    # 优先使用环境变量
    if [ -n "$PYTHON_CMD" ]; then
        echo "$PYTHON_CMD"
        return
    fi
    
    # 检查常见的Python命令
    for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
        if command_exists "$cmd"; then
            echo "$cmd"
            return
        fi
    done
    
    # 检查conda环境
    if command_exists conda; then
        echo "conda run -n ${CONDA_ENV:-py312} python"
        return
    fi
    
    echo "python3"
}

# 检查Python版本
check_python_version() {
    local python_cmd=$(get_python_cmd)
    local required_version=${1:-3.8}
    
    local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    if [ -z "$version" ]; then
        log_error "无法获取Python版本"
        return 1
    fi
    
    if [ "$(printf '%s\n' "$required_version" "$version" | sort -V | head -n1)" != "$required_version" ]; then
        log_error "Python版本过低: $version (需要 >= $required_version)"
        return 1
    fi
    
    log_info "Python版本: $version"
    return 0
}

# 优雅地停止进程
graceful_stop() {
    local pid=$1
    local timeout=${2:-10}
    
    if ! is_process_running "$pid"; then
        return 0
    fi
    
    # 发送SIGTERM信号
    kill "$pid" 2>/dev/null
    
    # 等待进程退出
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if ! is_process_running "$pid"; then
            return 0
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    # 强制终止
    log_warning "进程未响应SIGTERM，强制终止..."
    kill -9 "$pid" 2>/dev/null
    sleep 1
    
    # 检查是否已停止
    if is_process_running "$pid"; then
        log_error "无法停止进程: $pid"
        return 1
    fi
    
    return 0
}

# 导出所有函数
export -f command_exists is_root get_os_type get_linux_distro
export -f is_port_in_use get_pid_by_port is_process_running
export -f read_pid_file ensure_dir backup_file get_env_value
export -f wait_for_service get_python_cmd check_python_version
export -f graceful_stop