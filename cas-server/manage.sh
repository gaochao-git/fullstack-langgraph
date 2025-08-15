#!/bin/bash
#===============================================================================
# CAS Mock Server 管理脚本
#===============================================================================

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 加载公共函数
source ../scripts/common/colors.sh || {
    # 如果无法加载颜色脚本，定义基本颜色
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
}

# 服务配置
SERVICE_NAME="CAS Mock Server"
SERVICE_PORT=5555
PID_FILE="pids/cas-mock.pid"
LOG_FILE="logs/cas-mock.log"

# 创建必要的目录
init_directories() {
    mkdir -p logs pids
}

# 检查端口是否被占用
check_port() {
    if lsof -i:$SERVICE_PORT > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARNING]${NC} 端口 $SERVICE_PORT 已被占用"
        return 1
    fi
    return 0
}

# 检查服务是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# 初始化
init() {
    print_header "初始化 $SERVICE_NAME"
    
    echo -e "${BLUE}[INFO]${NC} 创建目录结构..."
    init_directories
    
    echo -e "${BLUE}[INFO]${NC} 检查Python环境..."
    if ! command -v python &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} 未找到Python"
        return 1
    fi
    
    echo -e "${GREEN}[SUCCESS]${NC} 初始化完成"
}

# 启动服务
start() {
    print_header "启动 $SERVICE_NAME"
    
    if is_running; then
        echo -e "${YELLOW}[WARNING]${NC} $SERVICE_NAME 已经在运行 (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    if ! check_port; then
        echo -e "${RED}[ERROR]${NC} 无法启动，端口 $SERVICE_PORT 被占用"
        return 1
    fi
    
    echo -e "${BLUE}[INFO]${NC} 启动参数:"
    echo -e "${BLUE}[INFO]${NC}   端口: $SERVICE_PORT"
    echo -e "${BLUE}[INFO]${NC}   PID文件: $PID_FILE"
    
    # 启动服务
    nohup python cas_server.py > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    # 等待服务启动
    echo -e "${BLUE}[INFO]${NC} 等待服务启动..."
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}[SUCCESS]${NC} $SERVICE_NAME 启动成功 (PID: $PID)"
        echo -e "${GREEN}[SUCCESS]${NC} 访问地址: http://localhost:$SERVICE_PORT/cas/login"
        echo ""
        echo -e "${BLUE}[INFO]${NC} 测试账号:"
        echo "  - zhangsan / 123456"
        echo "  - admin / admin123"
        echo "  - lisi / 654321"
    else
        echo -e "${RED}[ERROR]${NC} $SERVICE_NAME 启动失败"
        echo -e "${RED}[ERROR]${NC} 请查看日志: $LOG_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    print_header "停止 $SERVICE_NAME"
    
    if ! is_running; then
        echo -e "${YELLOW}[WARNING]${NC} $SERVICE_NAME 未运行"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${BLUE}[INFO]${NC} 停止 $SERVICE_NAME (PID: $PID)..."
    
    kill $PID 2>/dev/null
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
    
    # 如果进程还在，强制终止
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARNING]${NC} 进程未响应，强制终止..."
        kill -9 $PID 2>/dev/null
    fi
    
    rm -f "$PID_FILE"
    echo -e "${GREEN}[SUCCESS]${NC} $SERVICE_NAME 已停止"
}

# 重启服务
restart() {
    print_header "重启 $SERVICE_NAME"
    stop
    sleep 1
    start
}

# 查看状态
status() {
    print_header "$SERVICE_NAME 状态"
    
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}[RUNNING]${NC} $SERVICE_NAME 正在运行"
        echo -e "${BLUE}[INFO]${NC} PID: $PID"
        echo -e "${BLUE}[INFO]${NC} 端口: $SERVICE_PORT"
        echo -e "${BLUE}[INFO]${NC} 访问: http://localhost:$SERVICE_PORT/cas/login"
        
        # 显示进程信息
        echo ""
        echo -e "${BLUE}[INFO]${NC} 进程信息:"
        ps -p $PID -o pid,comm,%cpu,%mem,etime
        
        # 显示最近日志
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo -e "${BLUE}[INFO]${NC} 最近日志:"
            tail -n 5 "$LOG_FILE"
        fi
    else
        echo -e "${RED}[STOPPED]${NC} $SERVICE_NAME 未运行"
    fi
}

# 清理
cleanup() {
    print_header "清理 $SERVICE_NAME"
    
    if is_running; then
        echo -e "${YELLOW}[WARNING]${NC} 服务正在运行，请先停止服务"
        return 1
    fi
    
    echo -e "${BLUE}[INFO]${NC} 清理日志文件..."
    rm -f logs/*.log
    
    echo -e "${BLUE}[INFO]${NC} 清理PID文件..."
    rm -f pids/*.pid
    
    echo -e "${GREEN}[SUCCESS]${NC} 清理完成"
}

# 帮助信息
usage() {
    echo "用法: $0 {init|start|stop|restart|status|cleanup}"
    echo ""
    echo "命令:"
    echo "  init     - 初始化服务环境"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  status   - 查看服务状态"
    echo "  cleanup  - 清理日志和临时文件"
}

# 打印标题
print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${BOLD}                             $1${NC}"
    echo "================================================================================"
    echo ""
}

# 主程序
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
    cleanup)
        cleanup
        ;;
    *)
        usage
        exit 1
        ;;
esac