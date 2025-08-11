#!/bin/bash

# Zabbix Service 启动脚本

# 设置工作目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 加载环境变量
if [ -f "../.env" ]; then
    source "../.env"
    echo "加载环境变量文件 ../.env"
elif [ -f ".env" ]; then
    source ".env"
    echo "加载环境变量文件 .env"
fi

# 设置Python路径
export PYTHONPATH="${PROJECT_DIR}/src:${PYTHONPATH}"

# 默认配置
HOST=${ZABBIX_SERVICE_HOST:-0.0.0.0}
PORT=${ZABBIX_SERVICE_PORT:-8001}

echo "启动 Zabbix Service..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Zabbix API URL: ${ZABBIX_API_URL:-未配置}"

# 启动服务
cd "$PROJECT_DIR"
python -m uvicorn src.main:app --host $HOST --port $PORT --reload