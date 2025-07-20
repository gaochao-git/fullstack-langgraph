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
