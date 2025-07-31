#!/bin/bash

# 设置 Go 路径
export PATH=~/go1.24.4/go/bin:$PATH
export GOWORK=off

# 项目根目录
UNLA_DIR="/Users/gaochao/gaochao-git/gaochao_repo/fullstack-langgraph/Unla-main"

echo "🚀 启动 UNLA 开发服务..."

# 启动 mcp-gateway (端口 5235)
echo "启动 mcp-gateway..."
cd "$UNLA_DIR" && go run cmd/mcp-gateway/main.go &
MCP_GATEWAY_PID=$!
echo "mcp-gateway 启动完成 (PID: $MCP_GATEWAY_PID)"

# 等待一下
sleep 2

# 启动 apiserver (端口 5234)
echo "启动 apiserver..."
cd "$UNLA_DIR" && go run cmd/apiserver/main.go &
APISERVER_PID=$!
echo "apiserver 启动完成 (PID: $APISERVER_PID)"

# 等待一下
sleep 2

# 启动 mock-server (端口 5236/5237)
echo "启动 mock-server..."
cd "$UNLA_DIR" && go run cmd/mock-server/main.go &
MOCK_SERVER_PID=$!
echo "mock-server 启动完成 (PID: $MOCK_SERVER_PID)"

# 等待一下
sleep 2

# 启动 web 前端开发服务
echo "启动 web 前端..."
cd "$UNLA_DIR/web" && npm run dev &
WEB_PID=$!
echo "web 前端启动完成 (PID: $WEB_PID)"

echo ""
echo "🎉 所有服务启动完成！"
echo ""
echo "访问地址："
echo "  - Web 管理界面: http://localhost:5173 (Vite 开发服务器)"
echo "  - API Server: http://localhost:5234"
echo "  - MCP Gateway: http://localhost:5235"
echo "  - Mock Server: http://localhost:5236, http://localhost:5237"
echo ""
echo "进程 ID："
echo "  - mcp-gateway: $MCP_GATEWAY_PID"
echo "  - apiserver: $APISERVER_PID"
echo "  - mock-server: $MOCK_SERVER_PID"
echo "  - web: $WEB_PID"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
wait