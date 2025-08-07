#!/bin/bash

# OMind 智能运维平台统一打包脚本
# 包含前端、后端、MCP服务器的完整部署包

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/dist"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="omind-${TIMESTAMP}"
TEMP_BUILD_DIR="${BUILD_DIR}/temp_build"

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

# 显示使用方法
show_usage() {
    echo "OMind 智能运维平台统一打包脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -o, --output DIR      输出目录 (默认: dist/)"
    echo "  -n, --name NAME       包名称 (默认: omind-YYYYMMDD_HHMMSS.tar.gz)"
    echo "  --production         使用生产环境配置"
    echo "  --help               显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                    # 基本打包"
    echo "  $0 --production                      # 生产环境打包"
    echo "  $0 -o /tmp -n omind-v1.0.tar.gz     # 自定义输出"
    echo ""
    echo "打包内容:"
    echo "  ✅ 前端静态文件"
    echo "  ✅ 后端API服务"
    echo "  ✅ MCP服务器集群"
    echo "  ✅ 部署脚本和配置"
    echo "  ✅ 系统服务配置"
}

# 解析命令行参数
PRODUCTION=false
CUSTOM_NAME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            BUILD_DIR="$2"
            TEMP_BUILD_DIR="${BUILD_DIR}/temp_build"
            shift 2
            ;;
        -n|--name)
            CUSTOM_NAME="$2"
            shift 2
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 设置包名称
if [ -n "$CUSTOM_NAME" ]; then
    PACKAGE_NAME="${CUSTOM_NAME%.*}"  # 移除扩展名
elif [ "$PRODUCTION" = true ]; then
    PACKAGE_NAME="omind-production-${TIMESTAMP}"
fi

log_info "🚀 开始构建 OMind 智能运维平台部署包..."
log_info "源目录: $SCRIPT_DIR"
log_info "输出目录: $BUILD_DIR"
log_info "包名称: ${PACKAGE_NAME}.tar.gz"
log_info "生产环境: $([ "$PRODUCTION" = true ] && echo "是" || echo "否")"

# 创建构建目录
mkdir -p "$BUILD_DIR"
rm -rf "$TEMP_BUILD_DIR"
mkdir -p "$TEMP_BUILD_DIR/$PACKAGE_NAME"

# 1. 构建前端
log_info "📦 构建前端静态文件..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    if ! command -v npm &> /dev/null; then
        log_error "npm未安装，请先安装Node.js和npm"
        exit 1
    fi
    
    npm install
    # 使用生产环境配置构建
    if [ -f "vite.config.prod.ts" ]; then
        npx vite build --config vite.config.prod.ts
    else
        npx vite build
    fi
    cd ..
    
    # 复制前端构建结果
    cp -r frontend/dist "$TEMP_BUILD_DIR/$PACKAGE_NAME/frontend_dist"
    log_success "前端构建完成"
else
    log_warning "未找到frontend目录，跳过前端构建"
fi

# 2. 准备后端文件
log_info "📦 准备后端文件..."
if [ -d "backend" ]; then
    # 复制后端源码，排除不必要的文件
    rsync -av --exclude='logs/' --exclude='__pycache__/' --exclude='*.pyc' \
        --exclude='*.log' --exclude='.git' backend/ "$TEMP_BUILD_DIR/$PACKAGE_NAME/backend/"
    log_success "后端文件复制完成"
else
    log_error "未找到backend目录"
    exit 1
fi

# 3. 准备MCP服务器
log_info "📦 准备MCP服务器..."
if [ -d "mcp_servers" ]; then
    # 复制MCP服务器文件
    rsync -av --exclude='logs/' --exclude='pids/' --exclude='__pycache__/' \
        --exclude='*.pyc' --exclude='*.log' --exclude='*.pid' \
        mcp_servers/ "$TEMP_BUILD_DIR/$PACKAGE_NAME/mcp_servers/"
    
    # 选择合适的配置文件
    if [ "$PRODUCTION" = true ] && [ -f "$TEMP_BUILD_DIR/$PACKAGE_NAME/mcp_servers/config.production.yaml" ]; then
        cp "$TEMP_BUILD_DIR/$PACKAGE_NAME/mcp_servers/config.production.yaml" \
           "$TEMP_BUILD_DIR/$PACKAGE_NAME/mcp_servers/config.yaml"
        log_info "  ✅ 使用生产环境MCP配置"
    fi
    
    log_success "MCP服务器文件复制完成"
else
    log_warning "未找到mcp_servers目录，跳过MCP服务器"
fi

# 4. 准备MCP Gateway
log_info "📦 准备MCP Gateway..."
if [ -d "mcp_gateway" ]; then
    # 复制MCP Gateway文件
    rsync -av --exclude='logs/' --exclude='data/' --exclude='*.log' --exclude='*.pid' \
        mcp_gateway/ "$TEMP_BUILD_DIR/$PACKAGE_NAME/mcp_gateway/"
    
    log_success "MCP Gateway文件复制完成"
else
    log_warning "未找到mcp_gateway目录，跳过MCP Gateway"
fi

# 5. 复制部署脚本和管理脚本
log_info "📝 准备部署脚本..."
# 复制scripts目录（包含manage_omind.sh和公共函数库）
if [ -d "scripts" ]; then
    cp -r scripts "$TEMP_BUILD_DIR/$PACKAGE_NAME/scripts"
    chmod +x "$TEMP_BUILD_DIR/$PACKAGE_NAME/scripts"/*.sh
    chmod +x "$TEMP_BUILD_DIR/$PACKAGE_NAME/scripts/common"/*.sh 2>/dev/null || true
    log_info "  ✅ manage_omind.sh 统一管理脚本"
    log_info "  ✅ 公共函数库"
fi

# 复制组件管理脚本
for component in backend mcp_servers mcp_gateway; do
    if [ -f "$component/manage.sh" ]; then
        cp "$component/manage.sh" "$TEMP_BUILD_DIR/$PACKAGE_NAME/$component/manage.sh"
        chmod +x "$TEMP_BUILD_DIR/$PACKAGE_NAME/$component/manage.sh"
        log_info "  ✅ $component/manage.sh"
    fi
done

# 6. 创建统一启动脚本
log_info "📝 创建统一管理脚本..."
cat > "$TEMP_BUILD_DIR/$PACKAGE_NAME/omind_deploy.sh" << 'EOF'
#!/bin/bash

# OMind 智能运维平台部署脚本
# 在目标服务器上执行此脚本进行部署

set -e

DEPLOY_PATH="${DEPLOY_PATH:-/data/omind}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

show_usage() {
    echo "OMind 智能运维平台部署脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -p, --path PATH       部署路径 (默认: /data/omind)"
    echo "  --backend-only        仅部署后端服务"
    echo "  --mcp-only           仅部署MCP服务器"
    echo "  --no-install         跳过依赖安装"
    echo "  --no-start           跳过服务启动"
    echo "  --help               显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                           # 完整部署"
    echo "  $0 -p /opt/omind            # 自定义路径"
    echo "  $0 --backend-only           # 仅部署后端"
    echo "  $0 --mcp-only               # 仅部署MCP服务器"
}

# 解析参数
BACKEND_ONLY=false
MCP_ONLY=false
INSTALL_DEPS=true
START_SERVICES=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--path)
            DEPLOY_PATH="$2"
            shift 2
            ;;
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --mcp-only)
            MCP_ONLY=true
            shift
            ;;
        --no-install)
            INSTALL_DEPS=false
            shift
            ;;
        --no-start)
            START_SERVICES=false
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            show_usage
            exit 1
            ;;
    esac
done

log_info "🚀 开始 OMind 智能运维平台部署..."
log_info "部署路径: $DEPLOY_PATH"
log_info "源路径: $SCRIPT_DIR"

# 检查权限
if [ ! -w "$(dirname "$DEPLOY_PATH")" ]; then
    log_error "没有权限写入 $(dirname "$DEPLOY_PATH")"
    log_info "请使用sudo执行或更改部署路径"
    exit 1
fi

# 停止现有服务
if [ -d "$DEPLOY_PATH" ]; then
    log_info "停止现有服务..."
    
    # 停止后端服务
    if [ -f "$DEPLOY_PATH/scripts/stop_backend.sh" ]; then
        cd "$DEPLOY_PATH/scripts"
        ./stop_backend.sh || log_warning "停止后端服务时出现警告"
    fi
    
    # 停止MCP服务器
    if [ -f "$DEPLOY_PATH/scripts/stop_mcp.sh" ]; then
        cd "$DEPLOY_PATH/scripts"
        ./stop_mcp.sh || log_warning "停止MCP服务器时出现警告"
    fi
fi

# 创建部署目录
log_info "创建部署目录..."
mkdir -p "$DEPLOY_PATH"

# 备份现有配置
if [ -f "$DEPLOY_PATH/config.yaml" ]; then
    BACKUP_TIME=$(date +%Y%m%d_%H%M%S)
    cp "$DEPLOY_PATH/config.yaml" "$DEPLOY_PATH/config.yaml.backup.$BACKUP_TIME"
    log_info "配置文件已备份: config.yaml.backup.$BACKUP_TIME"
fi

# 复制文件
log_info "复制文件到部署目录..."

if [ "$MCP_ONLY" = true ]; then
    # 仅部署MCP服务器
    if [ -d "$SCRIPT_DIR/mcp_servers" ]; then
        rsync -av --exclude='logs/' --exclude='pids/' "$SCRIPT_DIR/mcp_servers/" "$DEPLOY_PATH/mcp_servers/"
        log_success "MCP服务器文件复制完成"
    fi
elif [ "$BACKEND_ONLY" = true ]; then
    # 仅部署后端
    if [ -d "$SCRIPT_DIR/backend" ]; then
        rsync -av --exclude='logs/' "$SCRIPT_DIR/backend/" "$DEPLOY_PATH/backend/"
        log_success "后端文件复制完成"
    fi
    if [ -d "$SCRIPT_DIR/frontend_dist" ]; then
        rsync -av "$SCRIPT_DIR/frontend_dist/" "$DEPLOY_PATH/frontend_dist/"
        log_success "前端文件复制完成"
    fi
    # scripts目录已经在上面复制了，这里不需要再复制
else
    # 完整部署
    rsync -av --exclude='logs/' --exclude='pids/' "$SCRIPT_DIR/" "$DEPLOY_PATH/"
    log_success "所有文件复制完成"
fi

# 创建运行时目录
mkdir -p "$DEPLOY_PATH/backend/logs"
mkdir -p "$DEPLOY_PATH/mcp_servers"/{logs,pids}

# 设置权限
find "$DEPLOY_PATH" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
find "$DEPLOY_PATH" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true

# 安装Python依赖
if [ "$INSTALL_DEPS" = true ]; then
    log_info "安装Python依赖..."
    
    # 检查Python环境
    if command -v conda &> /dev/null; then
        log_info "使用conda环境"
        source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null || true
        
        if conda env list | grep -q py312; then
            conda activate py312
        else
            log_info "创建conda环境: py312"
            conda create -n py312 python=3.12 -y
            conda activate py312
        fi
    elif command -v python3 &> /dev/null; then
        log_info "使用Python虚拟环境"
        cd "$DEPLOY_PATH"
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
    else
        log_error "未找到Python环境"
        exit 1
    fi
    
    # 安装后端依赖
    if [ -f "$DEPLOY_PATH/backend/requirements.txt" ]; then
        cd "$DEPLOY_PATH/backend"
        pip install --upgrade pip
        pip install -r requirements.txt
        log_success "后端依赖安装完成"
    fi
    
    # 安装MCP服务器依赖
    if [ -f "$DEPLOY_PATH/mcp_servers/requirements.txt" ]; then
        cd "$DEPLOY_PATH/mcp_servers"
        pip install -r requirements.txt
        log_success "MCP服务器依赖安装完成"
    fi
fi

# 启动服务
if [ "$START_SERVICES" = true ]; then
    log_info "启动OMind服务..."
    
    if [ "$MCP_ONLY" = true ]; then
        # 仅启动MCP服务器
        if [ -f "$DEPLOY_PATH/scripts/start_mcp.sh" ]; then
            cd "$DEPLOY_PATH/scripts"
            ./start_mcp.sh
        fi
    elif [ "$BACKEND_ONLY" = true ]; then
        # 仅启动后端服务
        if [ -f "$DEPLOY_PATH/scripts/start_backend.sh" ]; then
            cd "$DEPLOY_PATH/scripts"
            ./start_backend.sh
        fi
    else
        # 启动所有服务
        # 先启动MCP服务器
        if [ -f "$DEPLOY_PATH/scripts/start_mcp.sh" ]; then
            cd "$DEPLOY_PATH/scripts"
            ./start_mcp.sh
            sleep 3
        fi
        
        # 再启动后端服务
        if [ -f "$DEPLOY_PATH/scripts/start_backend.sh" ]; then
            cd "$DEPLOY_PATH/scripts"
            ./start_backend.sh
        fi
    fi
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    log_info "检查服务状态..."
    
    # 检查MCP服务器
    if [ "$BACKEND_ONLY" = false ] && [ -f "$DEPLOY_PATH/scripts/status_mcp.sh" ]; then
        cd "$DEPLOY_PATH/scripts"
        ./status_mcp.sh
    fi
    
    # 检查后端服务
    if [ "$MCP_ONLY" = false ]; then
        if curl -s http://localhost:8000/api/ > /dev/null 2>&1; then
            log_success "后端API服务运行正常"
        else
            log_warning "后端API服务可能未正常启动"
        fi
    fi
fi

log_success "🎉 OMind 智能运维平台部署完成！"

echo ""
log_info "部署信息:"
log_info "  平台名称: OMind 智能运维平台"
log_info "  部署路径: $DEPLOY_PATH"
log_info "  前端地址: http://localhost:3000"
log_info "  后端API: http://localhost:8000/api/"

echo ""
log_info "MCP服务器地址:"
for port in 3001 3002 3003 3004; do
    echo "  http://localhost:$port/sse/"
done

echo ""
log_info "管理命令:"
log_info "  查看后端状态: curl http://localhost:8000/api/"
log_info "  查看MCP状态: cd $DEPLOY_PATH/scripts && ./status_mcp.sh"
log_info "  查看后端日志: tail -f $DEPLOY_PATH/backend/logs/*.log"
log_info "  查看MCP日志: tail -f $DEPLOY_PATH/mcp_servers/logs/*.log"
log_info "  停止所有服务: cd $DEPLOY_PATH/scripts && ./stop_backend.sh && ./stop_mcp.sh"
EOF

chmod +x "$TEMP_BUILD_DIR/$PACKAGE_NAME/omind_deploy.sh"

# 7. 创建nginx配置
log_info "📝 创建nginx配置..."
cat > "$TEMP_BUILD_DIR/$PACKAGE_NAME/nginx.conf" << 'EOF'
server {
    listen 80;
    server_name localhost;  # 替换为你的域名
    
    # 前端静态文件
    location / {
        root /data/omind/frontend_dist;  # 替换为实际路径
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 静态文件缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # MCP服务器代理
    location /mcp/ {
        rewrite ^/mcp/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 8. 创建systemd服务文件
log_info "📝 创建systemd服务配置..."
cat > "$TEMP_BUILD_DIR/$PACKAGE_NAME/omind.service" << 'EOF'
[Unit]
Description=OMind 智能运维平台
Documentation=https://github.com/your-org/omind
After=network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/data/omind
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/data/omind

# 启动和停止命令
ExecStart=/data/omind/scripts/start_backend.sh
ExecStop=/data/omind/scripts/stop_backend.sh
ExecReload=/bin/bash -c '/data/omind/scripts/stop_backend.sh && /data/omind/scripts/start_backend.sh'

# 重启策略
Restart=on-failure
RestartSec=10
KillMode=mixed
TimeoutStartSec=120
TimeoutStopSec=60

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=omind

[Install]
WantedBy=multi-user.target
EOF

# 9. 创建安装说明
log_info "📝 创建安装文档..."
cat > "$TEMP_BUILD_DIR/$PACKAGE_NAME/INSTALL.md" << 'EOF'
# OMind 智能运维平台安装指南

## 🎯 平台简介

**OMind** 是一个基于AI的智能运维平台，集成了故障诊断、系统监控、自动化运维等功能。

## 🚀 快速安装

### 1. 解压部署包
```bash
tar -xzf omind-*.tar.gz
cd omind-*/
```

### 2. 执行一键部署
```bash
# 完整部署（推荐）
./omind_deploy.sh

# 自定义部署路径
./omind_deploy.sh -p /opt/omind

# 仅部署MCP服务器
./omind_deploy.sh --mcp-only

# 仅部署后端服务
./omind_deploy.sh --backend-only
```

## 📋 系统要求

- **操作系统**: CentOS 7/8, Ubuntu 18.04+, RHEL 7/8
- **Python**: 3.12+ 或 Conda环境
- **内存**: 至少 4GB RAM
- **磁盘**: 至少 10GB 可用空间
- **端口**: 80, 8000, 3001-3004

## 🔧 手动部署

如果自动部署失败，可以手动执行以下步骤：

### 1. 安装系统依赖
```bash
# CentOS/RHEL
sudo yum install -y python3 python3-pip nginx curl

# Ubuntu/Debian
sudo apt update && sudo apt install -y python3 python3-pip nginx curl
```

### 2. 创建部署目录
```bash
sudo mkdir -p /data/omind
sudo chown $(whoami):$(whoami) /data/omind
```

### 3. 复制文件
```bash
cp -r * /data/omind/
cd /data/omind
```

### 4. 安装Python依赖
```bash
# 后端依赖
cd backend && pip3 install -r requirements.txt

# MCP服务器依赖
cd ../mcp_servers && pip3 install -r requirements.txt
```

### 5. 启动服务
```bash
# 启动MCP服务器
cd mcp_servers && ./start_servers.sh

# 启动后端服务
cd .. && ./start.sh
```

## 🌐 配置nginx（可选）

```bash
# 复制nginx配置
sudo cp nginx.conf /etc/nginx/conf.d/omind.conf

# 修改配置文件中的路径
sudo vim /etc/nginx/conf.d/omind.conf

# 重启nginx
sudo systemctl restart nginx
```

## 🔧 配置系统服务（可选）

```bash
# 复制服务文件
sudo cp omind.service /etc/systemd/system/

# 修改服务文件中的路径
sudo vim /etc/systemd/system/omind.service

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable omind
sudo systemctl start omind
```

## ✅ 验证安装

### 服务状态检查
```bash
# 检查后端API
curl http://localhost:8000/api/

# 检查MCP服务器
cd /data/omind/mcp_servers
./status_servers.sh
```

### 访问地址
- **前端界面**: http://your-server-ip/
- **后端API**: http://your-server-ip:8000/api/
- **MCP服务器**: http://your-server-ip:3001-3004/sse/

## 🛠️ 日常管理

```bash
# 进入部署目录
cd /data/omind

# 查看所有服务状态
./status_all.sh  # 如果存在

# 启动所有服务
./start.sh && ./mcp_servers/start_servers.sh

# 停止所有服务
./stop.sh && ./mcp_servers/stop_servers.sh

# 查看日志
tail -f backend/logs/*.log
tail -f mcp_servers/logs/*.log
```

## 🔒 安全配置

### 防火墙设置
```bash
# 开放必要端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=3001-3004/tcp
sudo firewall-cmd --reload
```

### SSL配置（生产环境推荐）
```bash
# 安装certbot
sudo yum install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

## 🆘 故障排除

### 常见问题

**Q: 端口被占用**
```bash
# 查看端口占用
netstat -tlnp | grep -E ":(80|8000|3001|3002|3003|3004)"

# 停止占用进程
sudo kill -9 $(lsof -ti:8000)
```

**Q: Python依赖问题**
```bash
# 重新安装依赖
pip3 install --upgrade pip
pip3 install -r requirements.txt --force-reinstall
```

**Q: 权限问题**
```bash
# 修复权限
sudo chown -R $(whoami):$(whoami) /data/omind
find /data/omind -name "*.sh" -exec chmod +x {} \;
```

**Q: 服务启动失败**
```bash
# 查看详细日志
tail -n 50 backend/logs/*.log
tail -n 50 mcp_servers/logs/*.log

# 检查系统资源
free -h
df -h
```

## 📞 技术支持

如遇问题，请提供以下信息：
- 操作系统版本: `cat /etc/os-release`
- Python版本: `python3 --version`
- 错误日志: 相关日志文件内容
- 系统资源: `free -h && df -h`
EOF

# 10. 创建版本信息
cat > "$TEMP_BUILD_DIR/$PACKAGE_NAME/VERSION" << EOF
OMind 智能运维平台
========================

项目名称: OMind (Operational Mind)
构建时间: $(date)
构建主机: $(hostname)
生产环境: $([ "$PRODUCTION" = true ] && echo "是" || echo "否")
Git提交: $(cd "$SCRIPT_DIR" && git rev-parse HEAD 2>/dev/null || echo "N/A")

组件清单:
- 前端界面: React + TypeScript + Vite
- 后端API: FastAPI + Python 3.12+  
- MCP服务器: 4个专业工具服务器
- 部署脚本: 自动化部署和管理
- 系统集成: nginx + systemd支持

服务端口:
- 前端: 80 (nginx)
- 后端API: 8000
- 数据库工具: 3001
- SSH工具: 3002  
- ES工具: 3003
- Zabbix工具: 3004
EOF

# 11. 创建打包清单
log_info "📝 生成打包清单..."
find "$TEMP_BUILD_DIR/$PACKAGE_NAME" -type f | sed "s|$TEMP_BUILD_DIR/$PACKAGE_NAME/||" | sort > "$TEMP_BUILD_DIR/$PACKAGE_NAME/MANIFEST"
MANIFEST_COUNT=$(wc -l < "$TEMP_BUILD_DIR/$PACKAGE_NAME/MANIFEST")
log_info "  ✅ MANIFEST ($MANIFEST_COUNT 个文件)"

# 12. 创建压缩包
log_info "📦 创建部署包..."
cd "$TEMP_BUILD_DIR"
tar -czf "../${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
cd "$SCRIPT_DIR"

# 清理临时目录
rm -rf "$TEMP_BUILD_DIR"

# 计算包信息
PACKAGE_PATH="$BUILD_DIR/${PACKAGE_NAME}.tar.gz"
PACKAGE_SIZE=$(du -h "$PACKAGE_PATH" | cut -f1)
PACKAGE_MD5=$(md5sum "$PACKAGE_PATH" 2>/dev/null | cut -d' ' -f1 || md5 -q "$PACKAGE_PATH" 2>/dev/null)

log_success "🎉 OMind 智能运维平台打包完成！"

echo ""
log_info "📊 打包信息:"
log_info "  包文件: $PACKAGE_PATH"
log_info "  文件大小: $PACKAGE_SIZE"
log_info "  MD5校验: $PACKAGE_MD5"
log_info "  文件数量: $MANIFEST_COUNT"

echo ""
log_info "🚀 部署步骤:"
log_info "1. 传输到目标服务器:"
log_info "   make trans"
log_info ""
log_info "2. 在目标服务器上解压并部署:"
log_info "   tar -xzf ${PACKAGE_NAME}.tar.gz"
log_info "   cd ${PACKAGE_NAME}"
log_info ""
log_info "3. 使用 manage_omind.sh 进行运维:"
log_info "   初始化项目:"
log_info "   ./scripts/manage_omind.sh init --deploy-path=/data/omind --package=/tmp/${PACKAGE_NAME}.tar.gz"
log_info ""
log_info "   启动所有服务:"
log_info "   ./scripts/manage_omind.sh start"
log_info ""
log_info "   查看服务状态:"
log_info "   ./scripts/manage_omind.sh status"
log_info ""
log_info "   停止所有服务:"
log_info "   ./scripts/manage_omind.sh stop"
log_info ""
log_info "   升级版本:"
log_info "   ./scripts/manage_omind.sh upgrade --package=/tmp/omind-new-version.tar.gz"

echo ""
log_info "🌐 部署后访问地址:"
log_info "  前端界面: http://TARGET_SERVER/"
log_info "  后端API: http://TARGET_SERVER:8000/api/"
log_info "  MCP服务器: http://TARGET_SERVER:3001-3004/sse/"

echo ""
log_success "OMind 智能运维平台已准备就绪！"