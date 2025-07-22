#!/bin/bash

# MCP服务器停止脚本
# 停止所有MCP服务器

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "停止MCP服务器..."

# 读取并停止所有服务器进程
for pid_file in *.pid; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo "停止进程 $PID ($pid_file)"
            kill $PID
            sleep 1
            # 如果进程仍在运行，强制杀死
            if ps -p $PID > /dev/null 2>&1; then
                echo "强制停止进程 $PID"
                kill -9 $PID
            fi
        else
            echo "进程 $PID 已经停止"
        fi
        rm "$pid_file"
    fi
done

# 也可以通过端口杀死进程
for port in 3001 3002 3003 3004; do
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "停止端口 $port 上的进程 $PID"
        kill $PID 2>/dev/null
    fi
done

echo "所有MCP服务器已停止"