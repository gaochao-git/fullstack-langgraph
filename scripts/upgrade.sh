#!/bin/bash

# OMind 智能运维平台升级脚本
# 支持指定升级组件：前端、后端、MCP服务器
# 使用方法: ./upgrade.sh <package_name> [options]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }

# 显示使用说明
show_help() {
    echo "OMind 智能运维平台升级脚本"
    echo ""
    echo "用法: $0 <package_name> [options]"
    echo ""
    echo "参数:"
    echo "  package_name    部署包名称 (例如: omind-production-20250720_221936)"
    echo ""
    echo "升级组件选项 (可组合使用):"
    echo "  --frontend      仅升级前端"
    echo "  --backend       仅升级后端"
    echo "  --mcp          仅升级MCP服务器"
    echo "  --scripts      仅升级脚本"
    echo "  --config       仅升级配置文件"
    echo ""
    echo "其他选项:"
    echo "  --no-backup    跳过备份当前版本"
    echo "  --force        强制升级，即使检测到问题"
    echo "  --no-restart   升级后不重启服务"
    echo "  --help         显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 omind-production-20250720_221936                    # 完整升级"
    echo "  $0 omind-production-20250720_221936 --frontend         # 仅升级前端"
    echo "  $0 omind-production-20250720_221936 --backend --mcp    # 升级后端和MCP"
    echo "  $0 omind-production-20250720_221936 --no-backup        # 升级时跳过备份"
    echo ""
    echo "组件说明:"
    echo "  frontend: React前端静态文件"
    echo "  backend:  FastAPI后端服务"
    echo "  mcp:      MCP工具服务器"
    echo "  scripts:  管理脚本"
    echo "  config:   配置文件"
}

# 解析参数
PACKAGE_NAME=""
NO_BACKUP=false
FORCE=false
NO_RESTART=false

# 升级组件标志
UPGRADE_FRONTEND=false
UPGRADE_BACKEND=false
UPGRADE_MCP=false
UPGRADE_SCRIPTS=false
UPGRADE_CONFIG=false
UPGRADE_ALL=true  # 默认全部升级

while [[ $# -gt 0 ]]; do
    case $1 in
        --frontend)
            UPGRADE_FRONTEND=true
            UPGRADE_ALL=false
            shift
            ;;
        --backend)
            UPGRADE_BACKEND=true
            UPGRADE_ALL=false
            shift
            ;;
        --mcp)
            UPGRADE_MCP=true
            UPGRADE_ALL=false
            shift
            ;;
        --scripts)
            UPGRADE_SCRIPTS=true
            UPGRADE_ALL=false
            shift
            ;;
        --config)
            UPGRADE_CONFIG=true
            UPGRADE_ALL=false
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        -*)
            echo_error "未知选项: $1"
            show_help
            exit 1
            ;;
        *)
            if [ -z "$PACKAGE_NAME" ]; then
                PACKAGE_NAME="$1"
            else
                echo_error "多余的参数: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# 检查参数
if [ -z "$PACKAGE_NAME" ]; then
    echo_error "缺少部署包名称参数"
    show_help
    exit 1
fi

# 如果指定了具体组件，设置升级标志
if [ "$UPGRADE_ALL" = true ]; then
    UPGRADE_FRONTEND=true
    UPGRADE_BACKEND=true
    UPGRADE_MCP=true
    UPGRADE_SCRIPTS=true
    UPGRADE_CONFIG=true
fi

# 定义路径
DEPLOY_DIR="/data/omind_prd"
TMP_DIR="/tmp"
PACKAGE_PATH="$TMP_DIR/${PACKAGE_NAME}.tar.gz"
EXTRACT_PATH="$TMP_DIR/$PACKAGE_NAME"

echo_info "开始 OMind 智能运维平台升级"
echo_info "升级包: $PACKAGE_NAME"
echo ""

# 显示升级组件
echo_info "升级组件:"
[ "$UPGRADE_FRONTEND" = true ] && echo_info "  ✅ 前端 (React静态文件)"
[ "$UPGRADE_BACKEND" = true ] && echo_info "  ✅ 后端 (FastAPI服务)"
[ "$UPGRADE_MCP" = true ] && echo_info "  ✅ MCP服务器"
[ "$UPGRADE_SCRIPTS" = true ] && echo_info "  ✅ 管理脚本"
[ "$UPGRADE_CONFIG" = true ] && echo_info "  ✅ 配置文件"
echo ""

# 1. 检查当前环境
echo_info "步骤 1/8: 检查当前环境..."

if [ ! -d "$DEPLOY_DIR" ]; then
    echo_error "部署目录不存在: $DEPLOY_DIR"
    exit 1
fi

if [ ! -f "$PACKAGE_PATH" ]; then
    echo_error "部署包不存在: $PACKAGE_PATH"
    echo_info "请先通过scp或其他方式将部署包上传到: $PACKAGE_PATH"
    exit 1
fi

echo_success "环境检查通过"

# 2. 检查服务状态
echo_info "步骤 2/8: 检查当前服务状态..."

cd "$DEPLOY_DIR"

# 检查后端服务状态
BACKEND_RUNNING=false
if [ -f "backend/pids/backend.pid" ]; then
    PID=$(cat backend/pids/backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo_info "检测到后端服务正在运行 (PID: $PID)"
        BACKEND_RUNNING=true
    else
        echo_warning "后端PID文件存在但服务未运行，将清理PID文件"
        rm -f backend/pids/backend.pid
    fi
fi

# 检查MCP服务状态
MCP_RUNNING=false
if [ -d "mcp_servers/pids" ] && [ "$(ls -A mcp_servers/pids 2>/dev/null)" ]; then
    echo_info "检测到MCP服务器正在运行"
    MCP_RUNNING=true
fi

# 3. 解压新版本
echo_info "步骤 3/8: 解压新版本文件..."

if [ -d "$EXTRACT_PATH" ]; then
    echo_warning "清理之前的解压文件..."
    rm -rf "$EXTRACT_PATH"
fi

cd "$TMP_DIR"
tar -xzf "${PACKAGE_NAME}.tar.gz"

if [ ! -d "$EXTRACT_PATH" ]; then
    echo_error "解压失败，目录不存在: $EXTRACT_PATH"
    exit 1
fi

echo_success "解压完成"

# 4. 备份当前版本
if [ "$NO_BACKUP" = false ]; then
    echo_info "步骤 4/8: 备份当前版本..."
    
    BACKUP_NAME="omind_prd_backup_$(date +%Y%m%d_%H%M%S)"
    cd /data
    cp -r omind_prd "$BACKUP_NAME"
    
    echo_success "备份完成: /data/$BACKUP_NAME"
else
    echo_warning "步骤 4/8: 跳过备份（--no-backup）"
fi

# 5. 停止相关服务
echo_info "步骤 5/8: 停止相关服务..."

cd "$DEPLOY_DIR"

# 停止后端服务
if [ "$UPGRADE_BACKEND" = true ] && [ "$BACKEND_RUNNING" = true ]; then
    echo_info "停止后端服务..."
    if [ -f "scripts/stop_backend.sh" ]; then
        cd scripts && ./stop_backend.sh && cd ..
    fi
    sleep 2
fi

# 停止MCP服务
if [ "$UPGRADE_MCP" = true ] && [ "$MCP_RUNNING" = true ]; then
    echo_info "停止MCP服务器..."
    if [ -f "scripts/stop_mcp.sh" ]; then
        cd scripts && ./stop_mcp.sh && cd ..
    fi
    sleep 2
fi

echo_success "服务停止完成"

# 6. 更新文件
echo_info "步骤 6/8: 更新应用文件..."

cd "$EXTRACT_PATH"

# 更新前端文件
if [ "$UPGRADE_FRONTEND" = true ] && [ -d "frontend_dist" ]; then
    echo_info "更新前端文件..."
    rm -rf "$DEPLOY_DIR/frontend_dist"
    cp -r frontend_dist "$DEPLOY_DIR/"
    echo_success "前端文件更新完成"
fi

# 更新后端代码
if [ "$UPGRADE_BACKEND" = true ] && [ -d "backend" ]; then
    echo_info "更新后端代码..."
    # 保留日志和PID目录
    if [ -d "$DEPLOY_DIR/backend/logs" ]; then
        cp -r "$DEPLOY_DIR/backend/logs" "/tmp/backend_logs_backup"
    fi
    if [ -d "$DEPLOY_DIR/backend/pids" ]; then
        cp -r "$DEPLOY_DIR/backend/pids" "/tmp/backend_pids_backup"
    fi
    
    rm -rf "$DEPLOY_DIR/backend"
    cp -r backend "$DEPLOY_DIR/"
    
    # 恢复日志和PID目录
    if [ -d "/tmp/backend_logs_backup" ]; then
        cp -r "/tmp/backend_logs_backup" "$DEPLOY_DIR/backend/logs"
        rm -rf "/tmp/backend_logs_backup"
    fi
    if [ -d "/tmp/backend_pids_backup" ]; then
        cp -r "/tmp/backend_pids_backup" "$DEPLOY_DIR/backend/pids"
        rm -rf "/tmp/backend_pids_backup"
    fi
    
    echo_success "后端代码更新完成"
fi

# 更新MCP服务器
if [ "$UPGRADE_MCP" = true ] && [ -d "mcp_servers" ]; then
    echo_info "更新MCP服务器..."
    # 保留日志和PID目录
    if [ -d "$DEPLOY_DIR/mcp_servers/logs" ]; then
        cp -r "$DEPLOY_DIR/mcp_servers/logs" "/tmp/mcp_logs_backup"
    fi
    if [ -d "$DEPLOY_DIR/mcp_servers/pids" ]; then
        cp -r "$DEPLOY_DIR/mcp_servers/pids" "/tmp/mcp_pids_backup"
    fi
    
    rm -rf "$DEPLOY_DIR/mcp_servers"
    cp -r mcp_servers "$DEPLOY_DIR/"
    
    # 恢复日志和PID目录
    mkdir -p "$DEPLOY_DIR/mcp_servers/logs" "$DEPLOY_DIR/mcp_servers/pids"
    if [ -d "/tmp/mcp_logs_backup" ]; then
        cp -r "/tmp/mcp_logs_backup"/* "$DEPLOY_DIR/mcp_servers/logs/" 2>/dev/null || true
        rm -rf "/tmp/mcp_logs_backup"
    fi
    if [ -d "/tmp/mcp_pids_backup" ]; then
        cp -r "/tmp/mcp_pids_backup"/* "$DEPLOY_DIR/mcp_servers/pids/" 2>/dev/null || true
        rm -rf "/tmp/mcp_pids_backup"
    fi
    
    echo_success "MCP服务器更新完成"
fi

# 更新脚本文件
if [ "$UPGRADE_SCRIPTS" = true ] && [ -d "scripts" ]; then
    echo_info "更新管理脚本..."
    rm -rf "$DEPLOY_DIR/scripts"
    cp -r scripts "$DEPLOY_DIR/"
    chmod +x "$DEPLOY_DIR/scripts"/*.sh
    echo_success "管理脚本更新完成"
fi

# 更新配置文件
if [ "$UPGRADE_CONFIG" = true ]; then
    echo_info "更新配置文件..."
    
    # 更新nginx配置
    if [ -f "nginx.conf" ]; then
        cp nginx.conf "$DEPLOY_DIR/"
    fi
    
    # 更新systemd服务文件
    if [ -f "omind.service" ]; then
        cp omind.service "$DEPLOY_DIR/"
    fi
    
    # 更新MCP配置文件
    if [ -f "mcp_servers/config.yaml" ]; then
        # 备份现有配置
        if [ -f "$DEPLOY_DIR/mcp_servers/config.yaml" ]; then
            cp "$DEPLOY_DIR/mcp_servers/config.yaml" "$DEPLOY_DIR/mcp_servers/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        cp mcp_servers/config.yaml "$DEPLOY_DIR/mcp_servers/"
    fi
    
    echo_success "配置文件更新完成"
fi

echo_success "文件更新完成"

# 7. 更新依赖
echo_info "步骤 7/8: 检查并更新Python依赖..."

# 更新后端依赖
if [ "$UPGRADE_BACKEND" = true ] && [ -f "$DEPLOY_DIR/backend/requirements.txt" ]; then
    echo_info "更新后端Python依赖..."
    cd "$DEPLOY_DIR/backend"
    
    # 检查conda环境
    if command -v conda &> /dev/null; then
        source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
        conda activate py312 2>/dev/null || true
    elif [ -d "$DEPLOY_DIR/venv" ]; then
        source "$DEPLOY_DIR/venv/bin/activate"
    fi
    
    pip install --upgrade pip
    pip install -r requirements.txt
    echo_success "后端依赖更新完成"
fi

# 更新MCP依赖
if [ "$UPGRADE_MCP" = true ] && [ -f "$DEPLOY_DIR/mcp_servers/requirements.txt" ]; then
    echo_info "更新MCP服务器Python依赖..."
    cd "$DEPLOY_DIR/mcp_servers"
    
    # 使用相同的Python环境
    pip install -r requirements.txt
    echo_success "MCP依赖更新完成"
fi

# 8. 启动新版本服务
if [ "$NO_RESTART" = false ]; then
    echo_info "步骤 8/8: 启动升级后的服务..."
    
    cd "$DEPLOY_DIR"
    
    # 启动MCP服务器
    if [ "$UPGRADE_MCP" = true ]; then
        echo_info "启动MCP服务器..."
        if [ -f "scripts/start_mcp.sh" ]; then
            cd scripts && ./start_mcp.sh && cd ..
            sleep 3
        fi
    fi
    
    # 启动后端服务
    if [ "$UPGRADE_BACKEND" = true ]; then
        echo_info "启动后端服务..."
        if [ -f "scripts/start_backend.sh" ]; then
            cd scripts && ./start_backend.sh && cd ..
            sleep 3
        fi
    fi
    
    # 验证服务状态
    echo_info "验证服务状态..."
    
    # 检查后端服务
    if [ "$UPGRADE_BACKEND" = true ]; then
        if curl -s -f http://localhost:8000/api/ >/dev/null 2>&1; then
            echo_success "后端服务响应正常"
        else
            echo_warning "后端服务可能未完全就绪，请检查日志"
        fi
    fi
    
    # 检查MCP服务器
    if [ "$UPGRADE_MCP" = true ]; then
        if [ -f "scripts/status_mcp.sh" ]; then
            cd scripts && ./status_mcp.sh && cd ..
        fi
    fi
    
    echo_success "服务启动完成"
else
    echo_warning "步骤 8/8: 跳过服务重启（--no-restart）"
fi

# 9. 清理临时文件
echo_info "清理临时文件..."
rm -rf "$EXTRACT_PATH"

echo ""
echo_success "🎉 OMind 智能运维平台升级完成！"
echo ""
echo_info "升级信息:"
echo_info "  版本: $PACKAGE_NAME"
echo_info "  部署路径: $DEPLOY_DIR"

if [ "$UPGRADE_FRONTEND" = true ]; then
    echo_info "  前端地址: http://localhost/"
fi
if [ "$UPGRADE_BACKEND" = true ]; then
    echo_info "  后端API: http://localhost:8000/api/"
fi
if [ "$UPGRADE_MCP" = true ]; then
    echo_info "  MCP服务器: http://localhost:3001-3004/sse/"
fi

echo ""
echo_info "日志查看:"
if [ "$UPGRADE_BACKEND" = true ]; then
    echo_info "  后端日志: tail -f $DEPLOY_DIR/backend/logs/*.log"
fi
if [ "$UPGRADE_MCP" = true ]; then
    echo_info "  MCP日志: tail -f $DEPLOY_DIR/mcp_servers/logs/*.log"
fi

if [ "$NO_BACKUP" = false ]; then
    echo ""
    echo_info "回滚方法 (如果需要):"
    echo_info "  cd /data && rm -rf omind_prd && mv $BACKUP_NAME omind_prd"
    echo_info "  cd omind_prd/scripts && ./start_backend.sh && ./start_mcp.sh"
fi

echo ""
echo_success "升级脚本执行完毕！"