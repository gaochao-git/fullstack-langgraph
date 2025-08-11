#!/bin/bash

# Zabbix Service 管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
LOG_DIR="${PROJECT_DIR}/logs"
PID_FILE="${LOG_DIR}/zabbix_service.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 加载环境变量
load_env() {
    if [ -f "${PROJECT_DIR}/../.env" ]; then
        source "${PROJECT_DIR}/../.env"
        echo -e "${GREEN}✓${NC} 加载环境变量文件 ../.env"
    elif [ -f "${PROJECT_DIR}/.env" ]; then
        source "${PROJECT_DIR}/.env"
        echo -e "${GREEN}✓${NC} 加载环境变量文件 .env"
    fi
}

# 初始化服务
init() {
    echo -e "${BLUE}初始化 Zabbix Service...${NC}"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "${PROJECT_DIR}/venv" ]; then
        echo "创建虚拟环境..."
        /Users/gaochao/miniconda3/envs/py312/bin/python -m venv "${PROJECT_DIR}/venv"
    fi
    
    # 激活虚拟环境并安装依赖
    echo "安装依赖..."
    source "${PROJECT_DIR}/venv/bin/activate"
    pip install -r "${PROJECT_DIR}/requirements.txt"
    
    echo -e "${GREEN}✓${NC} 初始化完成"
}

# 启动服务
start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC}  Zabbix Service 已在运行中 (PID: $(cat $PID_FILE))"
        return
    fi
    
    echo -e "${BLUE}启动 Zabbix Service...${NC}"
    
    load_env
    
    # 默认配置
    HOST=${ZABBIX_SERVICE_HOST:-0.0.0.0}
    PORT=${ZABBIX_SERVICE_PORT:-8001}
    
    # 激活虚拟环境（如果还没有激活）
    if [[ -z "$VIRTUAL_ENV" ]] || [[ "$VIRTUAL_ENV" != "${PROJECT_DIR}/venv" ]]; then
        if [ -d "${PROJECT_DIR}/venv" ]; then
            source "${PROJECT_DIR}/venv/bin/activate"
        else
            echo -e "${YELLOW}⚠${NC}  虚拟环境不存在，请先运行 ./manage.sh init"
            return 1
        fi
    fi
    
    # 设置Python路径 - 需要包含src目录
    export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"
    
    # 切换到项目目录
    cd "${PROJECT_DIR}"
    
    # 启动服务
    nohup python -m uvicorn src.main:app \
        --host $HOST \
        --port $PORT \
        > "${LOG_DIR}/zabbix_service.log" 2>&1 &
    
    # 保存PID
    echo $! > "$PID_FILE"
    
    sleep 2
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Zabbix Service 启动成功 (PID: $(cat $PID_FILE))"
        echo -e "${GREEN}✓${NC} 服务地址: http://${HOST}:${PORT}"
    else
        echo -e "${RED}✗${NC} Zabbix Service 启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠${NC}  Zabbix Service 未运行"
        return
    fi
    
    PID=$(cat "$PID_FILE")
    if kill -0 $PID 2>/dev/null; then
        echo -e "${BLUE}停止 Zabbix Service (PID: $PID)...${NC}"
        kill $PID
        sleep 2
        
        if kill -0 $PID 2>/dev/null; then
            echo "强制停止..."
            kill -9 $PID
        fi
        
        rm -f "$PID_FILE"
        echo -e "${GREEN}✓${NC} Zabbix Service 已停止"
    else
        echo -e "${YELLOW}⚠${NC}  进程不存在，清理PID文件"
        rm -f "$PID_FILE"
    fi
}

# 重启服务
restart() {
    stop
    sleep 1
    start
}

# 查看状态
status() {
    echo -e "${BLUE}Zabbix Service 状态：${NC}"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo -e "${GREEN}✓${NC} 运行中 (PID: $PID)"
            
            # 显示配置信息
            load_env
            echo -e "\n配置信息："
            echo "  服务地址: http://${ZABBIX_SERVICE_HOST:-0.0.0.0}:${ZABBIX_SERVICE_PORT:-8001}"
            echo "  Zabbix API: ${ZABBIX_API_URL:-未配置}"
            
            # 检查健康状态
            if command -v curl &> /dev/null; then
                echo -e "\n健康检查："
                HEALTH_URL="http://localhost:${ZABBIX_SERVICE_PORT:-8001}/health"
                if curl -s "$HEALTH_URL" > /dev/null; then
                    echo -e "  ${GREEN}✓${NC} 服务响应正常"
                else
                    echo -e "  ${RED}✗${NC} 服务无响应"
                fi
            fi
        else
            echo -e "${RED}✗${NC} 未运行 (PID文件存在但进程不存在)"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${RED}✗${NC} 未运行"
    fi
}

# 清理日志
cleanup() {
    echo -e "${BLUE}清理日志文件...${NC}"
    
    if [ -d "$LOG_DIR" ]; then
        find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete
        echo -e "${GREEN}✓${NC} 已清理7天前的日志文件"
    fi
}

# 显示帮助
usage() {
    echo "使用方法: $0 {init|start|stop|restart|status|cleanup}"
    echo ""
    echo "命令说明："
    echo "  init     - 初始化服务（创建虚拟环境，安装依赖）"
    echo "  start    - 启动服务"
    echo "  stop     - 停止服务"
    echo "  restart  - 重启服务"
    echo "  status   - 查看服务状态"
    echo "  cleanup  - 清理日志文件"
}

# 主逻辑
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