# MCP Gateway 独立部署目录

这是 MCP Gateway 的独立部署目录，包含了所有必要的二进制文件、配置和启动脚本。

## 目录结构

```
mcp_gateway/
├── mcp-gateway-darwin-amd64   # macOS x86_64 二进制文件
├── mcp-gateway-linux-amd64    # Linux x86_64 二进制文件
├── gateway.sh                 # 启动管理脚本
├── .env                       # 环境变量配置
├── config/                    # 配置文件目录
│   └── mcp-gateway.yaml      # MCP Gateway 配置
├── data/                      # 数据目录（PID文件、数据库等）
└── logs/                      # 日志目录

```

## 快速开始

### 1. 配置环境变量

编辑 `.env` 文件，根据需要修改配置：

```bash
# 主要配置项
GATEWAY_STORAGE_TYPE=disk     # 存储类型：disk/db/api
GATEWAY_STORAGE_DISK_PATH=./data  # 磁盘存储路径
#GATEWAY_STORAGE_API_URL=http://172.20.10.2:8000/api/v1/mcp/gateway/configs/all # API 模式下的配置 URL
TZ=Asia/Shanghai              # 时区
```

### 2. 启动服务

```bash
# 启动 MCP Gateway
./gateway.sh start

# 查看服务状态
./gateway.sh status

# 查看实时日志
./gateway.sh logs
```

### 3. 管理命令

```bash
# 停止服务
./gateway.sh stop

# 重启服务
./gateway.sh restart

# 重新加载配置（热更新）
./gateway.sh reload
```

## 跨平台支持

启动脚本会自动检测操作系统和架构，选择正确的二进制文件：

- macOS x86_64: `mcp-gateway-darwin-amd64`
- Linux x86_64: `mcp-gateway-linux-amd64`

如需其他平台支持，请编译对应的二进制文件并放入此目录。

## 故障排查

1. **服务无法启动**
   - 检查端口是否被占用
   - 查看日志文件：`tail -f logs/mcp-gateway.log`
   - 确认配置文件语法正确

2. **配置不生效**
   - 使用 `./gateway.sh reload` 热更新配置
   - 或重启服务：`./gateway.sh restart`

3. **权限问题**
   - 确保二进制文件有执行权限
   - 确保 data 和 logs 目录可写

## 集成说明

MCP Gateway 可以独立运行，也可以与 OMind 平台集成：

- 独立运行：使用磁盘或数据库存储配置
- 集成运行：使用 API 模式连接到 OMind 后端

默认访问地址：http://localhost:5235