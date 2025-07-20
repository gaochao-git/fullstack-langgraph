#!/bin/bash

set -e

echo "🚀 开始构建生产环境部署包..."

# 创建构建目录
BUILD_DIR="production_build"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="fullstack-langgraph-${TIMESTAMP}"

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}/${PACKAGE_NAME}

echo "📦 构建前端静态文件..."
cd frontend
npm install
# 跳过TypeScript类型检查，只构建生产文件
npx vite build --config vite.config.prod.ts
cd ..

echo "📦 准备后端文件..."
# 复制后端源码
cp -r backend ${BUILD_DIR}/${PACKAGE_NAME}/
# 复制前端构建结果
cp -r frontend/dist ${BUILD_DIR}/${PACKAGE_NAME}/frontend_dist

echo "📝 创建部署脚本..."
# 创建启动脚本
cat > ${BUILD_DIR}/${PACKAGE_NAME}/start.sh << 'EOF'
#!/bin/bash

echo "🚀 启动 fullstack-langgraph 生产环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要 Python 3.11 或更高版本，当前版本: $python_version"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
cd backend
pip install -r requirements.txt
cd ..

# 启动服务
echo "🏭 启动后端服务..."
cd backend
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
echo "🌐 后端API地址: http://localhost:8000"
echo "📁 前端静态文件位置: $(pwd)/../frontend_dist"
echo ""
echo "请配置nginx代理前端静态文件和后端API"
echo "参考配置文件: nginx.conf"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待信号
trap "echo '正在停止服务...'; kill $BACKEND_PID; exit" INT TERM
wait $BACKEND_PID
EOF

# 创建停止脚本
cat > ${BUILD_DIR}/${PACKAGE_NAME}/stop.sh << 'EOF'
#!/bin/bash

echo "🛑 停止 fullstack-langgraph 服务..."

# 查找并停止uvicorn进程
pkill -f "uvicorn src.api.app:app" || echo "未找到运行中的后端服务"

echo "✅ 服务已停止"
EOF

# 创建nginx配置
cat > ${BUILD_DIR}/${PACKAGE_NAME}/nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;  # 替换为你的域名
    
    # 前端静态文件
    location / {
        root /path/to/fullstack-langgraph/frontend_dist;  # 替换为实际路径
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
}
EOF

# 创建systemd服务文件
cat > ${BUILD_DIR}/${PACKAGE_NAME}/fullstack-langgraph.service << 'EOF'
[Unit]
Description=Fullstack LangGraph Application
After=network.target

[Service]
Type=forking
User=root
WorkingDirectory=/path/to/fullstack-langgraph  # 替换为实际路径
ExecStart=/path/to/fullstack-langgraph/start.sh  # 替换为实际路径
ExecStop=/path/to/fullstack-langgraph/stop.sh   # 替换为实际路径
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 创建部署说明
cat > ${BUILD_DIR}/${PACKAGE_NAME}/README_DEPLOY.md << 'EOF'
# 生产环境部署说明

## 系统要求
- CentOS 7/8 或 RHEL 7/8
- Python 3.11+ 
- nginx
- 至少 2GB RAM

## 部署步骤

### 1. 上传部署包
```bash
# 将整个目录上传到服务器
scp -r fullstack-langgraph-* user@server:/opt/
```

### 2. 安装系统依赖
```bash
# CentOS 7
sudo yum install -y python3 python3-pip nginx

# CentOS 8/RHEL 8
sudo dnf install -y python3 python3-pip nginx
```

### 3. 配置nginx
```bash
# 编辑nginx配置文件中的路径
sudo cp nginx.conf /etc/nginx/conf.d/fullstack-langgraph.conf
# 修改配置文件中的路径为实际部署路径
sudo vim /etc/nginx/conf.d/fullstack-langgraph.conf

# 启动nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 4. 启动应用
```bash
# 给脚本执行权限
chmod +x start.sh stop.sh

# 启动应用
./start.sh
```

### 5. 配置为系统服务（可选）
```bash
# 修改service文件中的路径
sudo cp fullstack-langgraph.service /etc/systemd/system/
sudo vim /etc/systemd/system/fullstack-langgraph.service

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable fullstack-langgraph
sudo systemctl start fullstack-langgraph
```

## 验证部署
- 访问: http://your-server-ip
- API测试: http://your-server-ip/api/

## 日志查看
```bash
# 应用日志
tail -f backend/logs/backend_*.log

# 系统服务日志
sudo journalctl -u fullstack-langgraph -f
```

## 故障排除
1. 检查端口是否被占用: `netstat -tlnp | grep 8000`
2. 检查防火墙设置: `sudo firewall-cmd --list-all`
3. 检查nginx配置: `sudo nginx -t`
EOF

# 设置执行权限
chmod +x ${BUILD_DIR}/${PACKAGE_NAME}/start.sh
chmod +x ${BUILD_DIR}/${PACKAGE_NAME}/stop.sh

echo "📦 创建部署包..."
cd ${BUILD_DIR}
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}
cd ..

echo "✅ 构建完成!"
echo "📦 部署包位置: ${BUILD_DIR}/${PACKAGE_NAME}.tar.gz"
echo "📁 解压后目录: ${BUILD_DIR}/${PACKAGE_NAME}/"
echo ""
echo "🚀 部署步骤:"
echo "1. 将 ${BUILD_DIR}/${PACKAGE_NAME}.tar.gz 上传到CentOS服务器"
echo "2. 解压: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. 进入目录: cd ${PACKAGE_NAME}"
echo "4. 查看部署说明: cat README_DEPLOY.md"
echo "5. 运行: ./start.sh"