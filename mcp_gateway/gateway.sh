#!/bin/bash

# MCP Gateway 管理脚本
# 支持 macOS 和 Linux

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 配置文件路径
CONFIG_FILE="config/mcp-gateway.yaml"
ENV_FILE=".env"

# 检测操作系统和架构
detect_platform() {
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case "$OS" in
        darwin)
            PLATFORM="darwin"
            ;;
        linux)
            PLATFORM="linux"
            ;;
        *)
            echo -e "${RED}不支持的操作系统: $OS${NC}"
            exit 1
            ;;
    esac
    
    case "$ARCH" in
        x86_64|amd64)
            ARCH="amd64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        *)
            echo -e "${RED}不支持的架构: $ARCH${NC}"
            exit 1
            ;;
    esac
    
    BINARY="mcp-gateway-${PLATFORM}-${ARCH}"
    
    if [ ! -f "$BINARY" ]; then
        echo -e "${RED}错误: 未找到可执行文件 $BINARY${NC}"
        echo -e "${YELLOW}请先编译对应平台的二进制文件${NC}"
        exit 1
    fi
}

# 从 .env 文件获取配置值
get_env_value() {
    local key=$1
    local default=$2
    if [ -f "$ENV_FILE" ]; then
        # 从文件中提取值，处理注释和空格
        local value=$(grep "^${key}=" "$ENV_FILE" | cut -d'=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"//;s/"$//')
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# 启动服务
start() {
    # 从 .env 文件获取 PID 文件路径
    PID_FILE=$(get_env_value "MCP_GATEWAY_PID" "data/mcp-gateway.pid")
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}MCP Gateway 已经在运行 (PID: $PID)${NC}"
            return
        fi
    fi
    
    echo -e "${GREEN}启动 MCP Gateway...${NC}"
    echo -e "二进制文件: $BINARY"
    echo -e "配置文件: $CONFIG_FILE"
    
    # 确保日志目录存在
    mkdir -p data logs
    
    # 启动服务
    nohup ./"$BINARY" -c "$CONFIG_FILE" > logs/mcp-gateway.log 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MCP Gateway 启动成功 (PID: $PID)${NC}"
        echo -e "日志文件: logs/mcp-gateway.log"
        PORT=$(get_env_value "MCP_GATEWAY_PORT" "5235")
        echo -e "访问地址: http://localhost:${PORT}"
        echo -e "健康检测: curl -s http://localhost:${PORT}/health_check"
    else
        echo -e "${RED}✗ MCP Gateway 启动失败${NC}"
        echo -e "请查看日志: tail -f logs/mcp-gateway.log"
        exit 1
    fi
}

# 停止服务
stop() {
    # 从 .env 文件获取 PID 文件路径
    PID_FILE=$(get_env_value "MCP_GATEWAY_PID" "data/mcp-gateway.pid")
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}MCP Gateway 未运行${NC}"
        return
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}停止 MCP Gateway (PID: $PID)...${NC}"
        kill $PID
        rm -f "$PID_FILE"
        echo -e "${GREEN}✓ MCP Gateway 已停止${NC}"
    else
        echo -e "${YELLOW}进程不存在，清理 PID 文件${NC}"
        rm -f "$PID_FILE"
    fi
}

# 重启服务
restart() {
    stop
    sleep 2
    start
}

# 查看状态
status() {
    # 从 .env 文件获取 PID 文件路径
    PID_FILE=$(get_env_value "MCP_GATEWAY_PID" "data/mcp-gateway.pid")
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}● MCP Gateway 运行中 (PID: $PID)${NC}"
            echo -e "  平台: $PLATFORM-$ARCH"
            echo -e "  配置: $CONFIG_FILE"
            PORT=$(get_env_value "MCP_GATEWAY_PORT" "5235")
            echo -e "  端口: ${PORT}"
        else
            echo -e "${RED}● MCP Gateway 未运行${NC}"
            echo -e "  PID 文件存在但进程不存在"
        fi
    else
        echo -e "${RED}● MCP Gateway 未运行${NC}"
    fi
}

# 查看日志
logs() {
    if [ -f "logs/mcp-gateway.log" ]; then
        tail -f logs/mcp-gateway.log
    else
        echo -e "${YELLOW}日志文件不存在${NC}"
    fi
}

# 重新加载配置
reload() {
    # 从 .env 文件获取 PID 文件路径
    PID_FILE=$(get_env_value "MCP_GATEWAY_PID" "data/mcp-gateway.pid")
    
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${RED}MCP Gateway 未运行${NC}"
        return
    fi
    
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}重新加载配置...${NC}"
        kill -HUP $PID
        echo -e "${GREEN}✓ 配置已重新加载${NC}"
    else
        echo -e "${RED}进程不存在${NC}"
    fi
}

# 主函数
main() {
    detect_platform
    
    case "$1" in
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
        logs)
            logs
            ;;
        reload)
            reload
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|status|logs|reload}"
            echo ""
            echo "命令说明:"
            echo "  start    - 启动 MCP Gateway"
            echo "  stop     - 停止 MCP Gateway"
            echo "  restart  - 重启 MCP Gateway"
            echo "  status   - 查看运行状态"
            echo "  logs     - 查看实时日志"
            echo "  reload   - 重新加载配置（热更新）"
            exit 1
            ;;
    esac
}

main "$@"