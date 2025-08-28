# OMind 智能运维平台

**OMind** (Operational Mind) 是一个基于AI的智能运维平台，集成了故障诊断、系统监控、自动化运维等功能。

## 🚀 本地开发

### 1. 创建 Python 虚拟环境

在项目根目录下创建 venv 环境：

```bash
/Users/gaochao/miniconda3/envs/py312/bin/python -m venv venv
```

### 2. 安装 Python 依赖包

```bash
# 安装后端依赖
./venv/bin/pip install -r backend/requirements.txt

# 安装 MCP 服务器依赖
./venv/bin/pip install -r mcp_servers/requirements.txt
```

### 3. 启动开发环境

```bash
make dev
```

这个命令会同时启动：
- 前端开发服务器 (Vite)
- 后端 API 服务器 (FastAPI)
- MCP 服务器集群 (4个专业工具服务器)

### 4. 访问地址

- **前端开发页面**: http://localhost:5173
- **后端 API 文档**: http://localhost:8000/docs
- **MCP 服务器**:
  - 数据库工具: http://localhost:3001/sse/
  - SSH 工具: http://localhost:3002/sse/
  - Elasticsearch 工具: http://localhost:3003/sse/
  - Zabbix 工具: http://localhost:3004/sse/

## 🏭 生产部署

### 1. 本地打包

```bash
make build
```

### 2. 传输到远程服务器

```bash
make trans
```

### 3. 远程服务器部署

```bash
# 初始化环境（首次部署）
./manage_omind.sh init --deploy-path=/data --python-path=/usr/bin/python3 --package=/tmp/omind-xxx.tar.gz

# 启动所有服务
./manage_omind.sh start

# 查看服务状态
./manage_omind.sh status

# 升级版本
./manage_omind.sh upgrade --package=/tmp/omind-new.tar.gz

# 停止服务
./manage_omind.sh stop

# 清理环境
./manage_omind.sh cleanup
```

## 🎯 平台特性

- **智能故障诊断**: 基于LangGraph的AI诊断助手
- **多模型支持**: 支持DeepSeek、Qwen、GPT等多种AI模型
- **MCP工具集成**: 内置数据库、SSH、ES、Zabbix等专业工具
- **可视化界面**: 基于React的现代化前端界面
- **一键部署**: 统一的打包和部署解决方案

### 架构组件

#### 前端界面
- 基于React + TypeScript + Vite
- 支持模型切换和实时对话
- 响应式设计，支持移动端

#### 后端API
- FastAPI框架，高性能异步API
- LangGraph智能体编排
- 支持流式输出和中断处理

#### MCP服务器
- **数据库工具** (3001): MySQL诊断查询
- **SSH工具** (3002): 远程系统管理
- **Elasticsearch工具** (3003): 日志查询分析
- **Zabbix工具** (3004): 监控数据获取

## 🛠️ 其他命令

```bash
# 安装依赖
make install

# 运行测试
make test

# 清理构建产物
make clean

# 查看所有可用命令
make help
```

## 📋 系统要求

- **操作系统**: macOS, Linux, Windows (WSL)
- **Python**: 3.8+ (推荐 3.12)
- **Node.js**: 16+ (用于前端开发)
- **内存**: 至少 2GB RAM
- **磁盘**: 至少 5GB 可用空间

## 🔧 开发工具

- **前端**: React + TypeScript + Vite
- **后端**: FastAPI + Python
- **MCP服务器**: 专业工具服务器集群
- **构建**: Make + Bash脚本

## 📖 开发文档

参考项目开发过程中的相关文档：

### LangGraph官方文档
https://langchain-ai.github.io/langgraph/

### FastMCP实现参考
https://gofastmcp.com/getting-started/welcome

## 📞 问题反馈

如遇问题，请检查：
1. Python 版本是否正确
2. 虚拟环境是否正确创建和激活
3. 依赖包是否完整安装
4. 端口是否被占用

更多帮助请查看项目文档或提交 Issue。

## api调用
1.agent调用
- 初始化会话
```python
import requests
import json
from datetime import datetime
AGENT_API_BASE_URL = "http://localhost:8000"
AGENT_API_KEY = "your_api_key"
response = requests.post(
    f"{AGENT_API_BASE_URL}/api/chat/threads",
    json={"metadata": {}},
    headers={"Content-Type": "application/json"},
    timeout=10
)
thread_data = response.json()
thread_id = thread_data.get("thread_id")
```
- 调用agent
```python
payload = {
    "input": {
        "messages": [{"type": "human", "content": "你好", "id": str(int(datetime.now().timestamp() * 1000))}],
        "user_name": "gaochao",
    },
    "config": {"configurable": {"selected_model": "deepseek-chat"}},
    "stream_mode": ["messages-tuple", "values", "updates"],
    "assistant_id": "diagnostic_agent",
    "on_disconnect": "cancel",
}
api_url = f"{AGENT_API_BASE_URL}/api/chat/threads/{conversation_id}/runs/stream"
response = requests.post(
    f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/messages",
    json={"content": "你好"},
    headers={"Content-Type": "application/json"},
    timeout=10
)
```