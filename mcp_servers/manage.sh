#!/bin/bash
# MCP Servers 管理脚本包装器
# 兼容旧的 manage.sh 调用，实际使用 Python 版本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python manage.py 是否存在
if [ ! -f "manage.py" ]; then
    echo "❌ 错误：manage.py 不存在"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

# 调用 Python 版本
python manage.py "$@"