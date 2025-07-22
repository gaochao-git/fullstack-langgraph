# MCP服务器集合

这个目录包含了用于故障分析助手系统的MCP（Model Context Protocol）服务器实现。

## 服务器列表

### 1. 数据库工具服务器 (db_mcp_server.py)
- **端口**: 3001
- **功能**: 提供MySQL数据库相关工具
- **工具**:
  - `execute_mysql_query`: 执行MySQL诊断查询

### 2. SSH工具服务器 (ssh_mcp_server.py)
- **端口**: 3002
- **功能**: 提供SSH远程系统管理工具
- **工具**:
  - `get_system_info`: 获取系统基本信息
  - `analyze_processes`: 分析系统进程
  - `check_service_status`: 检查服务状态
  - `analyze_system_logs`: 分析系统日志
  - `execute_system_command`: 执行系统命令

### 3. Elasticsearch工具服务器 (es_mcp_server.py)
- **端口**: 3003
- **功能**: 提供Elasticsearch查询和分析工具
- **工具**:
  - `get_es_data`: 执行自定义ES查询
  - `get_es_trends_data`: 获取ES趋势数据
  - `get_es_indices`: 获取ES索引列表

### 4. Zabbix工具服务器 (zabbix_mcp_server.py)
- **端口**: 3004
- **功能**: 提供Zabbix监控数据获取工具
- **工具**:
  - `get_zabbix_metric_data`: 获取指标历史数据
  - `get_zabbix_metrics`: 获取可用监控指标

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
# 启动所有服务器
./start_servers.sh

# 或者单独启动
python database_tools_server.py    # 端口 3001
python system_monitor_server.py    # 端口 3002
python network_tools_server.py     # 端口 3003
```

### 3. 测试服务器

```bash
# 运行测试脚本
python test_servers.py
```

### 4. 停止服务器

```bash
./stop_servers.sh
```

## API端点

每个MCP服务器都提供以下通用端点：

- `GET /health` - 健康检查
- `GET /tools` - 获取可用工具列表
- `POST /tools/{tool_name}` - 调用具体工具

## 工具使用示例

### 数据库工具

```bash
# MySQL查询
curl -X POST http://localhost:3001/tools/mysql_query \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "user": "root", 
    "password": "",
    "database": "mysql",
    "query": "SHOW DATABASES"
  }'

# 数据库健康检查
curl -X POST http://localhost:3001/tools/db_health_check \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "mysql",
    "host": "localhost"
  }'
```

### 系统监控工具

```bash
# 获取系统指标
curl -X POST http://localhost:3002/tools/system_metrics

# 进程监控
curl -X POST http://localhost:3002/tools/process_monitor \
  -H "Content-Type: application/json" \
  -d '{
    "process_name": "python",
    "cpu_threshold": 50.0
  }'
```

### 网络工具

```bash
# Ping测试
curl -X POST http://localhost:3003/tools/ping_test \
  -H "Content-Type: application/json" \
  -d '{
    "host": "google.com",
    "count": 4
  }'

# 端口扫描
curl -X POST http://localhost:3003/tools/port_scan \
  -H "Content-Type: application/json" \
  -d '{
    "host": "127.0.0.1",
    "ports": "22,80,443,3306"
  }'
```

## 与前端集成

这些MCP服务器与前端的MCP管理页面完全兼容：

1. **服务器发现**: 前端可以通过连接地址（如 `mcp://localhost:3001`）连接到这些服务器
2. **工具发现**: 连接成功后，前端会自动发现每个服务器提供的工具
3. **工具配置**: 可以在前端界面中启用/禁用特定工具
4. **智能体集成**: 配置好的工具可以分配给不同的智能体使用

## 开发说明

### 添加新工具

在任何服务器中添加新工具：

```python
@mcp.tool()
async def my_new_tool(param1: str, param2: int = 10) -> Dict[str, Any]:
    """工具描述"""
    try:
        # 工具逻辑
        return {
            "success": True,
            "result": "工具执行结果"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 添加新服务器

1. 创建新的Python文件
2. 选择不同的端口号
3. 按照现有服务器的模式实现工具
4. 更新启动和停止脚本

## 注意事项

- 确保端口3001、3002、3003未被占用
- 某些工具可能需要管理员权限（如系统监控）
- 网络工具在不同操作系统下可能有不同行为
- 数据库工具需要对应的数据库服务器运行

## 故障排除

### 端口被占用
```bash
# 查看端口占用
lsof -i :3001
lsof -i :3002  
lsof -i :3003

# 杀死占用进程
kill -9 <PID>
```

### 权限问题
某些系统工具需要更高权限，可能需要：
```bash
sudo python system_monitor_server.py
```

### 依赖问题
确保安装了所有必要的系统工具：
- ping
- traceroute (macOS/Linux)
- 数据库客户端（如果需要连接真实数据库）