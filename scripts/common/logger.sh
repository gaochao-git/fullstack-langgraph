#!/bin/bash

# 日志函数库
# 为所有管理脚本提供统一的日志输出

# 确保颜色定义已加载
if [ -z "$RED" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$SCRIPT_DIR/colors.sh"
fi

# 日志级别
LOG_LEVEL_DEBUG=0
LOG_LEVEL_INFO=1
LOG_LEVEL_WARNING=2
LOG_LEVEL_ERROR=3
LOG_LEVEL_SUCCESS=4

# 当前日志级别（默认为INFO）
CURRENT_LOG_LEVEL=${LOG_LEVEL:-$LOG_LEVEL_INFO}

# 时间戳格式
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 日志函数
log_debug() {
    if [ $CURRENT_LOG_LEVEL -le $LOG_LEVEL_DEBUG ]; then
        echo -e "${CYAN}[DEBUG]${NC} $(get_timestamp) $*" >&2
    fi
}

log_info() {
    if [ $CURRENT_LOG_LEVEL -le $LOG_LEVEL_INFO ]; then
        echo -e "${BLUE}[INFO]${NC} $*"
    fi
}

log_warning() {
    if [ $CURRENT_LOG_LEVEL -le $LOG_LEVEL_WARNING ]; then
        echo -e "${YELLOW}[WARNING]${NC} $*" >&2
    fi
}

log_error() {
    if [ $CURRENT_LOG_LEVEL -le $LOG_LEVEL_ERROR ]; then
        echo -e "${RED}[ERROR]${NC} $*" >&2
    fi
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

# 带图标的日志函数
log_step() {
    echo -e "${BLUE}==>${NC} $*"
}

log_done() {
    echo -e "${GREEN}✓${NC} $*"
}

log_fail() {
    echo -e "${RED}✗${NC} $*"
}

log_progress() {
    echo -e "${YELLOW}⚡${NC} $*"
}

# 分隔线
print_separator() {
    local char="${1:--}"
    local width="${2:-80}"
    printf '%*s\n' "$width" | tr ' ' "$char"
}

# 标题打印
print_title() {
    local title="$1"
    local width="${2:-80}"
    echo
    print_separator "=" "$width"
    printf "${BOLD}%*s${NC}\n" $(((${#title}+$width)/2)) "$title"
    print_separator "=" "$width"
    echo
}

# 导出所有函数
export -f log_debug log_info log_warning log_error log_success
export -f log_step log_done log_fail log_progress
export -f print_separator print_title
export -f get_timestamp