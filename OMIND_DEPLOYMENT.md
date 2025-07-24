# OMind 智能运维平台部署指南

## 🎯 项目简介

**OMind** (Operational Mind) 是一个基于AI的智能运维平台，集成了故障诊断、系统监控、自动化运维等功能。

### 平台特性
- 🤖 **智能故障诊断**: 基于LangGraph的AI诊断助手
- 🔄 **多模型支持**: 支持DeepSeek、Qwen、GPT等多种AI模型
- 🛠️ **MCP工具集成**: 内置数据库、SSH、ES、Zabbix等专业工具
- 💻 **可视化界面**: 基于React的现代化前端界面
- 🚀 **一键部署**: 统一的打包和部署解决方案

## 📁 项目结构

```
omind/
├── build_omind.sh              # 统一打包脚本 ⭐
├── frontend/                   # React前端界面
│   ├── src/                   # 源代码
│   ├── package.json           # 依赖配置
│   └── vite.config.ts         # 构建配置
├── backend/                    # FastAPI后端服务
│   ├── src/                   # 源代码
│   │   ├── api/              # API路由
│   │   ├── agents/           # AI智能体
│   │   ├── database/         # 数据库模型
│   │   └── services/         # 业务服务
│   └── requirements.txt       # Python依赖
├── mcp_servers/                # MCP工具服务器集群
│   ├── servers/               # 服务器实现
│   │   ├── db_mcp_server.py  # 数据库工具服务器
│   │   ├── ssh_mcp_server.py # SSH工具服务器
│   │   ├── es_mcp_server.py  # ES工具服务器
│   │   └── zabbix_mcp_server.py # Zabbix工具服务器
│   ├── scripts/               # 管理脚本
│   ├── config.yaml           # 配置文件
│   ├── config.production.yaml # 生产环境配置
│   └── requirements.txt       # Python依赖
├── scripts/                    # 部署脚本
│   ├── start.sh              # 后端启动脚本
│   ├── stop.sh               # 后端停止脚本
│   └── pre_env.sh            # 环境预配置脚本
└── dist/                      # 打包输出目录 (生成)
    └── omind-*.tar.gz        # 部署包
```

## 🚀 部署流程

### 第一步: 本地打包

在项目根目录执行：

```bash
# 生产环境打包 (推荐)
./build_omind.sh --production

# 基本打包
./build_omind.sh

# 自定义打包
./build_omind.sh -o /custom/path -n omind-v1.0.tar.gz
```

打包完成后会生成：
- `dist/omind-production-YYYYMMDD_HHMMSS.tar.gz` (生产环境包)
- 包含完整的前端、后端、MCP服务器和部署脚本

### 第二步: 传输部署包

```bash
# 传输到目标服务器
scp dist/omind-production-*.tar.gz user@server:/tmp/

# 或使用其他方式 (rsync, sftp等)
rsync -av dist/omind-production-*.tar.gz user@server:/tmp/
```

### 第三步: 远程部署

```bash
# 登录目标服务器
ssh user@server

# 解压部署包
cd /tmp
tar -xzf omind-production-*.tar.gz
cd omind-production-*/

# 一键部署 (默认部署到 /data/omind_prd)
./omind_deploy.sh

# 自定义部署路径
./omind_deploy.sh -p /opt/omind

# 仅部署特定组件
./omind_deploy.sh --backend-only    # 仅部署后端
./omind_deploy.sh --mcp-only        # 仅部署MCP服务器
```

## 🔧 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **磁盘**: 10GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: CentOS 7/8, Ubuntu 18.04+, RHEL 7/8
- **Python**: 3.12+ 或 Conda环境
- **Node.js**: 16+ (仅开发环境需要)
- **nginx**: 用于反向代理 (可选)

### 端口要求
- **80**: nginx前端服务 (可选)
- **8000**: 后端API服务
- **3001**: 数据库工具服务器
- **3002**: SSH工具服务器
- **3003**: Elasticsearch工具服务器
- **3004**: Zabbix工具服务器

## 🌐 服务架构

```
[用户访问]
    ↓
[nginx:80] → [前端静态文件]
    ↓
[后端API:8000] → [LangGraph智能体]
    ↓
[MCP服务器集群:3001-3004]
    ├── 数据库工具服务器:3001
    ├── SSH工具服务器:3002
    ├── ES工具服务器:3003
    └── Zabbix工具服务器:3004
```

## 🛠️ 服务管理

### 基本管理命令

```bash
# 进入部署目录
cd /data/omind_prd

# 查看所有服务状态
curl http://localhost:8000/api/          # 后端API
./scripts/status_mcp.sh                  # MCP服务器

# 启动所有服务
./start.sh                               # 后端服务
./scripts/start_mcp.sh                   # MCP服务器

# 停止所有服务
./stop.sh                                # 后端服务
./scripts/stop_mcp.sh                    # MCP服务器

# 查看日志
tail -f backend/logs/*.log               # 后端日志
tail -f mcp_servers/logs/*.log           # MCP服务器日志
```

### systemd服务管理 (可选)

```bash
# 配置为系统服务
sudo cp omind.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable omind
sudo systemctl start omind

# 管理系统服务
sudo systemctl status omind             # 查看状态
sudo systemctl restart omind            # 重启服务
sudo journalctl -u omind -f             # 查看日志
```

## 🔒 安全配置

### 防火墙设置

```bash
# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=3001-3004/tcp
sudo firewall-cmd --reload

# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 3001:3004/tcp
```

### nginx配置 (推荐)

```bash
# 复制nginx配置
sudo cp nginx.conf /etc/nginx/conf.d/omind.conf

# 修改配置文件中的路径
sudo vim /etc/nginx/conf.d/omind.conf

# 重启nginx
sudo systemctl restart nginx
```

### SSL证书 (生产环境推荐)

```bash
# 安装certbot
sudo yum install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com
```

## ✅ 验证部署

### 服务检查

```bash
# 检查端口监听
netstat -tlnp | grep -E ":(80|8000|3001|3002|3003|3004)"

# 检查进程运行
ps aux | grep -E "(uvicorn|python.*mcp_server)"

# 检查API响应
curl -s http://localhost:8000/api/ | jq .

# 检查MCP服务器
for port in 3001 3002 3003 3004; do
    echo "检查端口 $port:"
    curl -s "http://localhost:$port/health" || echo "无响应"
done
```

### 访问测试

- **前端界面**: http://your-server/ (如果配置了nginx)
- **后端API**: http://your-server:8000/api/
- **MCP服务器**: 
  - 数据库工具: http://your-server:3001/sse/
  - SSH工具: http://your-server:3002/sse/
  - ES工具: http://your-server:3003/sse/
  - Zabbix工具: http://your-server:3004/sse/

## 🆘 故障排除

### 常见问题

**问题1: 端口被占用**
```bash
# 查看端口占用
lsof -i :8000

# 停止占用进程
sudo kill -9 $(lsof -ti:8000)
```

**问题2: Python依赖问题**
```bash
# 检查Python版本
python3 --version

# 重新安装依赖
cd /data/omind_prd/backend
pip3 install -r requirements.txt --force-reinstall

cd ../mcp_servers
pip3 install -r requirements.txt --force-reinstall
```

**问题3: 权限问题**
```bash
# 修复权限
sudo chown -R $(whoami):$(whoami) /data/omind_prd
find /data/omind_prd -name "*.sh" -exec chmod +x {} \;
```

**问题4: 服务启动失败**
```bash
# 查看详细日志
tail -n 100 /data/omind_prd/backend/logs/*.log
tail -n 100 /data/omind_prd/mcp_servers/logs/*.log

# 手动启动调试
cd /data/omind_prd/backend
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

cd ../mcp_servers
python servers/db_mcp_server.py
```

### 性能优化

```bash
# 检查系统资源
free -h                                  # 内存使用
df -h                                   # 磁盘使用
top -p $(cat /data/omind_prd/*/pids/*.pid | tr '\n' ',' | sed 's/,$//')

# 优化Python进程
export PYTHONOPTIMIZE=1                 # 启用Python优化
ulimit -n 65536                        # 增加文件描述符限制
```

## 📊 监控和维护

### 日志管理

```bash
# 设置日志轮转
sudo logrotate -d /etc/logrotate.d/omind

# 清理旧日志
find /data/omind_prd/*/logs/ -name "*.log" -mtime +7 -delete
```

### 备份建议

```bash
# 配置文件备份
tar -czf omind-config-$(date +%Y%m%d).tar.gz \
    /data/omind_prd/*/config.yaml \
    /data/omind_prd/*/*.conf

# 数据库备份 (如果使用)
mysqldump -u root -p --all-databases > omind-db-$(date +%Y%m%d).sql
```

## 📞 技术支持

遇到问题时，请收集以下信息：

```bash
# 系统信息
uname -a
cat /etc/os-release

# 服务状态
./status_all.sh > status_report.txt

# 错误日志
tail -n 200 /data/omind_prd/*/logs/*.log > error_logs.txt

# 系统资源
free -h && df -h && ps aux > system_info.txt
```

---

**OMind智能运维平台** - 让AI为运维赋能 🚀

部署完成后，您将拥有一个功能完整的智能运维平台！