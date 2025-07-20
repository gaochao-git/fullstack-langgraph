#!/bin/bash

# 远程服务升级脚本
# 用于远程服务器上升级到新版本
# 使用方法: ./upgrade.sh <package_name>

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
    echo "远程服务升级脚本"
    echo ""
    echo "用法: $0 <package_name> [options]"
    echo ""
    echo "参数:"
    echo "  package_name    部署包名称 (例如: fullstack-langgraph-20250720_221936)"
    echo ""
    echo "选项:"
    echo "  --no-backup     跳过备份当前版本"
    echo "  --force         强制升级，即使检测到问题"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 fullstack-langgraph-20250720_221936"
    echo "  $0 fullstack-langgraph-20250720_221936 --no-backup"
}

# 解析参数
PACKAGE_NAME=""
NO_BACKUP=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
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

# 定义路径
DEPLOY_DIR="/data/langgraph_prd"
TMP_DIR="/tmp"
PACKAGE_PATH="$TMP_DIR/${PACKAGE_NAME}.tar.gz"
EXTRACT_PATH="$TMP_DIR/$PACKAGE_NAME"

echo_info "开始升级服务到版本: $PACKAGE_NAME"
echo ""

# 1. 检查当前环境
echo_info "步骤 1/8: 检查当前环境..."

if [ ! -d "$DEPLOY_DIR" ]; then
    echo_error "部署目录不存在: $DEPLOY_DIR"
    exit 1
fi

if [ ! -f "$PACKAGE_PATH" ]; then
    echo_error "部署包不存在: $PACKAGE_PATH"
    echo_info "请确保已通过 make deploy 上传部署包到远程服务器"
    exit 1
fi

echo_success "环境检查通过"

# 2. 检查服务状态
echo_info "步骤 2/8: 检查当前服务状态..."

cd "$DEPLOY_DIR"
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo_info "检测到服务正在运行 (PID: $PID)"
        SERVICE_RUNNING=true
    else
        echo_warning "PID文件存在但服务未运行，将清理PID文件"
        rm -f backend.pid
        SERVICE_RUNNING=false
    fi
else
    echo_info "当前没有服务在运行"
    SERVICE_RUNNING=false
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
    
    BACKUP_NAME="langgraph_prd_backup_$(date +%Y%m%d_%H%M%S)"
    cd /data
    cp -r langgraph_prd "$BACKUP_NAME"
    
    echo_success "备份完成: /data/$BACKUP_NAME"
else
    echo_warning "步骤 4/8: 跳过备份（--no-backup）"
fi

# 5. 停止当前服务
if [ "$SERVICE_RUNNING" = true ]; then
    echo_info "步骤 5/8: 停止当前服务..."
    
    cd "$DEPLOY_DIR"
    ./stop.sh || true
    
    # 等待服务完全停止
    sleep 3
    
    # 确认服务已停止
    if [ -f "backend.pid" ]; then
        PID=$(cat backend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo_warning "服务仍在运行，强制停止..."
            kill -9 $PID || true
            rm -f backend.pid
        fi
    fi
    
    echo_success "服务已停止"
else
    echo_info "步骤 5/8: 服务未运行，跳过停止步骤"
fi

# 6. 更新文件
echo_info "步骤 6/8: 更新应用文件..."

cd "$EXTRACT_PATH"

# 更新后端代码
if [ -d "backend" ]; then
    echo_info "更新后端代码..."
    cp -r backend "$DEPLOY_DIR/"
fi

# 更新前端文件
if [ -d "frontend_dist" ]; then
    echo_info "更新前端文件..."
    cp -r frontend_dist "$DEPLOY_DIR/"
fi

# 更新脚本文件
echo_info "更新脚本文件..."
cp *.sh "$DEPLOY_DIR/" 2>/dev/null || true

# 更新配置文件
cp *.conf "$DEPLOY_DIR/" 2>/dev/null || true
cp *.md "$DEPLOY_DIR/" 2>/dev/null || true

# 设置脚本执行权限
cd "$DEPLOY_DIR"
chmod +x *.sh

echo_success "文件更新完成"

# 7. 更新依赖
echo_info "步骤 7/8: 检查并更新Python依赖..."

if [ -f "backend/requirements.txt" ]; then
    # 检查requirements.txt是否有变化
    if [ -f "venv/requirements_installed.txt" ]; then
        if ! diff -q backend/requirements.txt venv/requirements_installed.txt >/dev/null 2>&1; then
            echo_info "检测到依赖变化，更新Python包..."
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r backend/requirements.txt
            cp backend/requirements.txt venv/requirements_installed.txt
            echo_success "依赖更新完成"
        else
            echo_info "依赖无变化，跳过更新"
        fi
    else
        echo_info "首次记录依赖版本..."
        source venv/bin/activate
        pip install -r backend/requirements.txt
        cp backend/requirements.txt venv/requirements_installed.txt
    fi
else
    echo_warning "未找到requirements.txt文件"
fi

# 8. 启动新版本服务
echo_info "步骤 8/8: 启动新版本服务..."

./start.sh

# 等待服务启动
sleep 5

# 验证服务状态
if [ -f "backend.pid" ]; then
    PID=$(cat backend.pid)
    if kill -0 $PID 2>/dev/null; then
        echo_success "新版本服务启动成功 (PID: $PID)"
        
        # 简单的健康检查
        echo_info "执行健康检查..."
        if curl -s -f http://localhost:8000/ >/dev/null 2>&1; then
            echo_success "服务响应正常"
        else
            echo_warning "服务可能未完全就绪，请检查日志"
        fi
    else
        echo_error "服务启动失败"
        echo_info "请检查错误日志: cat error.log"
        exit 1
    fi
else
    echo_error "服务启动失败，PID文件未创建"
    echo_info "请检查错误日志: cat error.log"
    exit 1
fi

# 9. 清理临时文件
echo_info "清理临时文件..."
rm -rf "$EXTRACT_PATH"

echo ""
echo_success "🎉 升级完成！"
echo ""
echo_info "服务信息:"
echo_info "  版本: $PACKAGE_NAME"
echo_info "  PID: $(cat backend.pid 2>/dev/null || echo 'N/A')"
echo_info "  访问地址: http://localhost:8000"
echo_info "  日志查看: tail -f $DEPLOY_DIR/access.log"
echo_info "  错误日志: tail -f $DEPLOY_DIR/error.log"

if [ "$NO_BACKUP" = false ]; then
    echo ""
    echo_info "回滚方法 (如果需要):"
    echo_info "  cd /data && rm -rf langgraph_prd && mv $BACKUP_NAME langgraph_prd && cd langgraph_prd && ./start.sh"
fi

echo ""
echo_success "升级脚本执行完毕！"