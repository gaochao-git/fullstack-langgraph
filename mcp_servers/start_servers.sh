#!/bin/bash

# MCP服务器启动脚本
# 启动所有MCP服务器

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "启动MCP服务器..."

# 使用conda py312环境
echo "激活conda py312环境..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py312

# 启动数据库工具服务器（MySQL）
echo "启动数据库工具服务器 (端口 3001)..."
nohup python db_mcp_server.py > db_server.log 2>&1 &
DB_PID=$!

# 启动SSH工具服务器
echo "启动SSH工具服务器 (端口 3002)..."
nohup python ssh_mcp_server.py > ssh_server.log 2>&1 &
SSH_PID=$!

# 启动Elasticsearch工具服务器
echo "启动Elasticsearch工具服务器 (端口 3003)..."
nohup python es_mcp_server.py > es_server.log 2>&1 &
ES_PID=$!

# 启动Zabbix工具服务器
echo "启动Zabbix工具服务器 (端口 3004)..."
nohup python zabbix_mcp_server.py > zabbix_server.log 2>&1 &
ZBX_PID=$!

# 保存PID到文件
echo $DB_PID > database_server.pid
echo $SSH_PID > ssh_server.pid
echo $ES_PID > elasticsearch_server.pid
echo $ZBX_PID > zabbix_server.pid

# 等待服务器启动
sleep 2

echo "所有MCP服务器已启动:"
echo "  - 数据库工具服务器(MySQL): http://localhost:3001/sse/ (PID: $DB_PID)"
echo "  - SSH工具服务器: http://localhost:3002/sse/ (PID: $SSH_PID)"  
echo "  - Elasticsearch工具服务器: http://localhost:3003/sse/ (PID: $ES_PID)"
echo "  - Zabbix工具服务器: http://localhost:3004/sse/ (PID: $ZBX_PID)"
echo ""
echo "使用 ./stop_servers.sh 停止所有服务器"