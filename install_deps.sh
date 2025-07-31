#!/bin/bash

echo "🔧 安装 UNLA 开发依赖..."

# 设置 Go 路径
export PATH=~/go1.24.4/go/bin:$PATH
export GOWORK=off

# 项目根目录
UNLA_DIR="./Unla-main"

echo "1. 安装 Go 模块依赖..."
cd "$UNLA_DIR" && go mod tidy
echo "Go 依赖安装完成 ✅"

echo ""
echo "2. 安装前端 Node.js 依赖..."
cd web && npm install
echo "前端依赖安装完成 ✅"

echo ""
echo "🎉 所有依赖安装完成！"
echo "现在可以运行: ./start_unla_dev.sh"