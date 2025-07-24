#!/bin/bash

# MCP服务器停止脚本
# 停止所有MCP服务器

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../mcp_servers" && pwd)"
cd "$SCRIPT_DIR"

echo "停止MCP服务器..."

# 检查pids目录是否存在
if [ ! -d "pids" ]; then
    echo "pids目录不存在，创建目录..."
    mkdir -p pids
fi

# 读取并停止所有服务器进程
for pid_file in pids/*.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        SERVER_NAME=$(basename "$pid_file" .pid)
        
        if ps -p $PID > /dev/null 2>&1; then
            echo "停止 $SERVER_NAME 进程 $PID"
            kill $PID
            sleep 1
            # 如果进程仍在运行，强制杀死
            if ps -p $PID > /dev/null 2>&1; then
                echo "强制停止 $SERVER_NAME 进程 $PID"
                kill -9 $PID
            fi
            echo "  ✅ $SERVER_NAME 已停止"
        else
            echo "  ℹ️  $SERVER_NAME 进程 $PID 已经停止"
        fi
        rm "$pid_file"
    fi
done

# 检查是否有遗留的PID文件（旧格式）
for pid_file in *.pid; do
    if [ -f "$pid_file" ]; then
        echo "清理旧格式的PID文件: $pid_file"
        rm "$pid_file"
    fi
done

# 也可以通过端口杀死进程（备用清理）
echo ""
echo "检查端口占用情况:"
for port in 3001 3002 3003 3004; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "  端口 $port 仍被进程 $PID 占用，强制停止"
        kill -9 $PID 2>/dev/null
    else
        echo "  ✅ 端口 $port 已释放"
    fi
done

echo ""
echo "所有MCP服务器已停止"