#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到脚本所在目录
cd "$SCRIPT_DIR"

# 激活虚拟环境（如果存在）
if [ -f ../venv/bin/activate ]; then
    source ../venv/bin/activate
fi

# 调用 Python 管理脚本
exec python manage.py "$@"