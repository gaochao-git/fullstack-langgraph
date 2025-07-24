#!/bin/bash

# 创建MCP服务器systemd服务
# 将MCP服务器配置为系统服务，支持开机自启动

set -e

# 配置
SERVICE_NAME="mcp-servers"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../mcp_servers" && pwd)"
MCP_DIR="$(dirname "$SCRIPT_DIR")"
USER="${USER:-root}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查权限
if [ "$EUID" -ne 0 ]; then
    log_error "需要root权限执行此脚本"
    log_info "请使用: sudo $0"
    exit 1
fi

log_info "创建MCP服务器systemd服务..."
log_info "部署目录: $MCP_DIR"
log_info "运行用户: $USER"

# 创建systemd服务文件
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

log_info "创建服务文件: $SERVICE_FILE"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MCP Servers for LangGraph
Documentation=https://github.com/your-org/fullstack-langgraph
After=network.target

[Service]
Type=forking
User=$USER
Group=$USER
WorkingDirectory=$MCP_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$MCP_DIR

# 启动和停止命令
ExecStart=$MCP_DIR/start_servers.sh
ExecStop=$MCP_DIR/stop_servers.sh
ExecReload=/bin/bash -c '$MCP_DIR/stop_servers.sh && $MCP_DIR/start_servers.sh'

# 重启策略
Restart=on-failure
RestartSec=10
KillMode=mixed
TimeoutStartSec=60
TimeoutStopSec=30

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mcp-servers

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
log_info "重新加载systemd配置..."
systemctl daemon-reload

# 启用服务
log_info "启用MCP服务器服务..."
systemctl enable "$SERVICE_NAME"

log_success "MCP服务器systemd服务创建完成！"

echo ""
log_info "服务管理命令:"
log_info "  启动服务: sudo systemctl start $SERVICE_NAME"
log_info "  停止服务: sudo systemctl stop $SERVICE_NAME"
log_info "  重启服务: sudo systemctl restart $SERVICE_NAME"
log_info "  查看状态: sudo systemctl status $SERVICE_NAME"
log_info "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
log_info "  禁用服务: sudo systemctl disable $SERVICE_NAME"

echo ""
read -p "是否立即启动MCP服务器服务? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "启动MCP服务器服务..."
    systemctl start "$SERVICE_NAME"
    
    # 等待启动
    sleep 3
    
    # 检查状态
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "MCP服务器服务启动成功"
        systemctl status "$SERVICE_NAME" --no-pager
    else
        log_error "MCP服务器服务启动失败"
        log_info "查看日志: sudo journalctl -u $SERVICE_NAME -n 20"
        exit 1
    fi
fi