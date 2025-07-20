#!/bin/bash

echo "🛑 停止 fullstack-langgraph 服务..."

# 查找并停止uvicorn进程
pkill -f "uvicorn src.api.app:app" || echo "未找到运行中的后端服务"

echo "✅ 服务已停止"
