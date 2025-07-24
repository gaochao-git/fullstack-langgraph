#!/bin/bash

# MCP服务器启动脚本
# 启动所有MCP服务器

# ====== 配置区域 ======
# 用户可根据环境修改以下Python路径
VALID_PYTHON_PATH=("/Users/gaochao/miniconda3/envs/py312" "/data/omind/venv")
# ====================

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 检测可用的Python环境
PYTHON_CMD=""
echo "🔍 检测Python环境..."

for python_path in "${VALID_PYTHON_PATH[@]}"; do
    if [ -d "$python_path" ]; then
        # 检查是否是虚拟环境目录
        if [ -f "$python_path/bin/python" ]; then
            echo "   发现虚拟环境: $python_path"
            source "$python_path/bin/activate"
            if python --version &> /dev/null; then
                PYTHON_CMD="python"
                echo "✅ 使用虚拟环境: $python_path ($(python --version))"
                break
            fi
        fi
    elif command -v "$python_path" >/dev/null 2>&1; then
        # 直接Python可执行文件路径
        PYTHON_VERSION=$($python_path --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
        echo "   发现Python: $python_path (版本: $PYTHON_VERSION)"
        if [[ "$PYTHON_VERSION" =~ ^3\.(1[0-9]|[6-9])$ ]]; then
            PYTHON_CMD="$python_path"
            echo "✅ 使用Python: $python_path (版本: $PYTHON_VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 错误: 未找到有效的Python环境"
    echo "请检查VALID_PYTHON_PATH配置: ${VALID_PYTHON_PATH[*]}"
    exit 1
fi

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
echo "  - 数据库工具服务器(MySQL): http://localhost:3001/sse/ (PID: $DB_PID)"
echo "  - SSH工具服务器: http://localhost:3002/sse/ (PID: $SSH_PID)"  
echo "  - Elasticsearch工具服务器: http://localhost:3003/sse/ (PID: $ES_PID)"
echo "  - Zabbix工具服务器: http://localhost:3004/sse/ (PID: $ZBX_PID)"
echo ""
echo "日志文件: logs/"
echo "PID文件: pids/"
echo ""
echo "使用 ./stop_servers.sh 停止所有服务器"
echo "使用 ./status_servers.sh 查看服务器状态"