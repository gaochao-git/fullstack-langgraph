#!/bin/bash

# MCP服务器状态检查脚本
# 检查所有MCP服务器的运行状态

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../mcp_servers" && pwd)"
cd "$SCRIPT_DIR"

echo "检查MCP服务器状态..."
echo ""

# 服务器配置
declare -A SERVERS=(
    ["3001"]="数据库工具服务器(MySQL)"
    ["3002"]="SSH工具服务器"
    ["3003"]="Elasticsearch工具服务器"
    ["3004"]="Zabbix工具服务器"
)

declare -A PID_FILES=(
    ["3001"]="database_server"
    ["3002"]="ssh_server"
    ["3003"]="elasticsearch_server"
    ["3004"]="zabbix_server"
)

# 检查每个服务器
for port in "${!SERVERS[@]}"; do
    server_name="${SERVERS[$port]}"
    pid_file="pids/${PID_FILES[$port]}.pid"
    
    echo "🔍 检查 $server_name (端口 $port):"
    
    # 检查PID文件
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        echo "   PID文件: $pid_file (PID: $PID)"
        
        # 检查进程是否运行
        if ps -p $PID > /dev/null 2>&1; then
            echo "   进程状态: ✅ 运行中 (PID: $PID)"
        else
            echo "   进程状态: ❌ 已停止 (PID文件存在但进程不存在)"
        fi
    else
        echo "   PID文件: ❌ 不存在"
    fi
    
    # 检查端口占用
    PORT_PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PORT_PID" ]; then
        echo "   端口状态: ✅ 被进程 $PORT_PID 占用"
    else
        echo "   端口状态: ❌ 未被占用"
    fi
    
    # 检查健康状态
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "   健康检查: ✅ 正常响应"
        echo "   访问地址: http://localhost:$port/sse/"
    else
        echo "   健康检查: ❌ 无响应"
    fi
    
    echo ""
done

# 显示日志文件信息
echo "📁 日志文件目录: logs/"
if [ -d "logs" ]; then
    echo "   可用日志文件:"
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            file_size=$(du -h "$log_file" | cut -f1)
            mod_time=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$log_file" 2>/dev/null || stat -c "%y" "$log_file" 2>/dev/null | cut -d'.' -f1)
            echo "     - $(basename "$log_file") ($file_size, 修改时间: $mod_time)"
        fi
    done
else
    echo "   ❌ logs目录不存在"
fi

echo ""
echo "📁 PID文件目录: pids/"
if [ -d "pids" ]; then
    pid_count=$(ls pids/*.pid 2>/dev/null | wc -l)
    echo "   活跃PID文件数量: $pid_count"
else
    echo "   ❌ pids目录不存在"
fi

echo ""
echo "💡 使用方法:"
echo "   启动服务器: ./start_servers.sh"
echo "   停止服务器: ./stop_servers.sh"
echo "   查看日志: tail -f logs/<server_name>.log"