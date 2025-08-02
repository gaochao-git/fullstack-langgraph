#!/bin/bash

# MCP服务器启动脚本
# 启动所有MCP服务器

# ====== 配置区域 ======
# Python环境将使用部署时创建的venv环境
# ====================

# 切换到项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查venv环境
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ 错误: 未找到venv环境: $VENV_PYTHON"
    echo "请先在项目根目录创建venv环境"
    exit 1
fi

echo "✅ 使用venv环境: $VENV_PYTHON"
PYTHON_CMD="$VENV_PYTHON"

# 创建必要的目录
mkdir -p mcp_servers/logs mcp_servers/pids

echo "🚀 启动MCP服务器..."
cd mcp_servers

# 启动数据库工具服务器（MySQL）
echo "启动数据库工具服务器 (端口 3001)..."
nohup $PYTHON_CMD servers/db_mcp_server.py > logs/db_server.log 2>&1 &
DB_PID=$!

# 启动SSH工具服务器
echo "启动SSH工具服务器 (端口 3002)..."
nohup $PYTHON_CMD servers/ssh_mcp_server.py > logs/ssh_server.log 2>&1 &
SSH_PID=$!

# 启动Elasticsearch工具服务器
echo "启动Elasticsearch工具服务器 (端口 3003)..."
nohup $PYTHON_CMD servers/es_mcp_server.py > logs/es_server.log 2>&1 &
ES_PID=$!

# 启动Zabbix工具服务器
echo "启动Zabbix工具服务器 (端口 3004)..."
nohup $PYTHON_CMD servers/zabbix_mcp_server.py > logs/zabbix_server.log 2>&1 &
ZBX_PID=$!

# 保存PID到文件
echo $DB_PID > pids/database_server.pid
echo $SSH_PID > pids/ssh_server.pid
echo $ES_PID > pids/elasticsearch_server.pid
echo $ZBX_PID > pids/zabbix_server.pid

# 等待服务器启动
echo "等待服务器启动..."
sleep 3

# 检查服务器状态
echo ""
echo "检查服务器状态:"
for port in 3001 3002 3003 3004; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ 端口 $port: 运行正常"
    else
        echo "  ❌ 端口 $port: 启动失败"
    fi
done

echo ""
echo "所有MCP服务器已启动:"
echo "  - 数据库工具服务器(MySQL): http://localhost:3001/sse (PID: $DB_PID)"
echo "  - SSH工具服务器: http://localhost:3002/sse (PID: $SSH_PID)"
echo "  - Elasticsearch工具服务器: http://localhost:3003/sse (PID: $ES_PID)"
echo "  - Zabbix工具服务器: http://localhost:3004/sse (PID: $ZBX_PID)"
echo ""
echo "日志文件: logs/"
echo "PID文件: pids/"
echo ""
echo "使用 ./stop_servers.sh 停止所有服务器"
echo "使用 ./status_servers.sh 查看服务器状态"