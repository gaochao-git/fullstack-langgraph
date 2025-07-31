#!/bin/bash

# MCP Gateway 管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="/tmp/mcp-gateway.pid"
LOG_FILE="/tmp/mcp-gateway.log"

# 设置Go路径
export PATH=/usr/local/go/bin:$PATH

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCP Gateway is already running (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    echo "Starting MCP Gateway..."
    cd "$SCRIPT_DIR"
    nohup go run cmd/mcp-gateway/main.go -c configs/mcp-gateway.yaml > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "MCP Gateway started (PID: $!)"
    echo "Log file: $LOG_FILE"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "PID file not found. MCP Gateway may not be running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping MCP Gateway (PID: $PID)..."
        kill "$PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing MCP Gateway..."
            kill -9 "$PID"
        fi
        rm -f "$PID_FILE"
        echo "MCP Gateway stopped"
    else
        echo "MCP Gateway is not running"
        rm -f "$PID_FILE"
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "MCP Gateway is running (PID: $(cat $PID_FILE))"
        echo "Port: 5235"
        echo "Config: configs/mcp-gateway.yaml"
    else
        echo "MCP Gateway is not running"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "Log file not found: $LOG_FILE"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start MCP Gateway"
        echo "  stop    - Stop MCP Gateway"
        echo "  restart - Restart MCP Gateway"
        echo "  status  - Show MCP Gateway status"
        echo "  logs    - Show and follow logs"
        exit 1
        ;;
esac