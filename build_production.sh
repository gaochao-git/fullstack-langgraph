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

echo "📝 复制部署脚本..."
# 复制启动脚本
cp scripts/start.sh ${BUILD_DIR}/${PACKAGE_NAME}/start.sh

# 复制停止脚本
cp scripts/stop.sh ${BUILD_DIR}/${PACKAGE_NAME}/stop.sh

# 复制环境预配置脚本
cp scripts/pre_env.sh ${BUILD_DIR}/${PACKAGE_NAME}/pre_env.sh

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
chmod +x ${BUILD_DIR}/${PACKAGE_NAME}/pre_env.sh

echo "📦 创建部署包..."
cd ${BUILD_DIR}
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}
cd ..

echo "✅ 构建完成!"
echo "📦 部署包位置: ${BUILD_DIR}/${PACKAGE_NAME}.tar.gz"
echo "📁 解压后目录: ${BUILD_DIR}/${PACKAGE_NAME}/"
echo ""
echo "🚀 部署步骤:"
echo "1. 本地开发: make dev"
echo "2. 本地打包: make build"
echo "3. 拷贝到远程: make deploy"
echo "4. 远程服务器解压: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "5. 远程服务器执行环境预配置: ./pre_env.sh 构建venv环境和安装依赖"
echo "6. 远程服务器执行启动服务: ./start.sh --prod"
echo "7. 远程服务器执行停止服务: ./stop.sh"