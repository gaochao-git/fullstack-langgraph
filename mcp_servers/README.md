# OpenAPI MCP服务器集群

动态的OpenAPI MCP服务器，从数据库读取OpenAPI配置并自动生成MCP工具。

## 功能特点

- 🔄 **动态配置加载**: 从数据库实时读取OpenAPI配置
- 🚀 **多路由支持**: 单个端口支持多个MCP端点
- 🛠️ **自动工具生成**: 基于OpenAPI规范自动生成MCP工具
- 🔐 **认证支持**: 支持多种HTTP认证方式
- ⚡ **高性能**: 异步处理HTTP请求
- 📡 **标准协议**: 支持SSE和STDIO传输

## 架构设计

```
数据库配置 → MCP服务器 → 动态端点
     ↓            ↓           ↓
OpenAPI规范 → 工具解析 → http://host:port/{prefix}/sse
```

## 端点格式

每个OpenAPI配置对应一个唯一的端点：

- **SSE端点**: `http://localhost:8100/{prefix}/sse`
- **STDIO端点**: `http://localhost:8100/{prefix}/stdio`
- **信息页面**: `http://localhost:8100/` (查看所有可用端点)

其中 `{prefix}` 是根据配置名称生成的唯一标识符。

## 安装和运行

### 1. 安装依赖

```bash
cd mcp_servers
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
# 使用默认配置启动
python start_mcp_servers.py

# 自定义主机和端口
python start_mcp_servers.py --host 0.0.0.0 --port 8100

# 开启详细日志
python start_mcp_servers.py --verbose
```

### 3. 查看可用端点

访问 `http://localhost:8100/` 查看所有可用的MCP端点。

## 配置示例

### 数据库配置示例

```json
{
  "config_name": "jsonplaceholder_api",
  "api_base_url": "https://jsonplaceholder.typicode.com",
  "mcp_config_content": {
    "name": "jsonplaceholder_api",
    "tools": [
      {
        "name": "get_users",
        "description": "获取用户列表",
        "method": "GET",
        "path": "/users",
        "parameters": [
          {
            "name": "_limit",
            "in": "query",
            "required": false,
            "description": "限制返回数量",
            "schema": {"type": "integer", "example": 5}
          }
        ]
      }
    ]
  },
  "auth_config": null,
  "timeout_config": {
    "read_timeout": 30,
    "connect_timeout": 10
  }
}
```

### 认证配置示例

```json
{
  "auth_config": {
    "type": "api_key",
    "api_key": "your-api-key",
    "header_name": "X-API-Key"
  }
}
```

## 使用场景

1. **API测试**: 快速将REST API转换为MCP工具进行测试
2. **工具集成**: 将第三方API集成到MCP生态系统
3. **服务代理**: 作为API网关提供统一的MCP接口
4. **开发调试**: 动态加载和测试API配置

## 故障排除

### 1. 数据库连接问题
- 检查数据库配置和连接字符串
- 确保数据库表结构正确
- 服务器会自动降级到模拟数据模式

### 2. FastMCP版本问题
- 确保安装了正确版本的FastMCP
- 检查MCP协议兼容性

### 3. HTTP请求失败
- 检查目标API的可用性
- 验证认证配置
- 检查网络连接和防火墙设置