# OMind 智能运维平台

**OMind** (Operational Mind) 是一个基于AI的智能运维平台，集成了故障诊断、系统监控、自动化运维等功能。

## 🎯 平台特性

- **智能故障诊断**: 基于LangGraph的AI诊断助手
- **多模型支持**: 支持DeepSeek、Qwen、GPT等多种AI模型
- **MCP工具集成**: 内置数据库、SSH、ES、Zabbix等专业工具
- **可视化界面**: 基于React的现代化前端界面
- **一键部署**: 统一的打包和部署解决方案

## 🚀 快速开始

### 1. 开发环境

```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# 前端开发
cd frontend
npm install
npm run dev

# MCP服务器
cd scripts
./start_mcp.sh
```

### 2. 生产部署

```bash
# 一键打包
./build_omind.sh --production

# 传输到服务器
scp dist/omind-production-*.tar.gz user@server:/tmp/

# 服务器上部署
ssh user@server
cd /tmp && tar -xzf omind-production-*.tar.gz
cd omind-production-*/ && ./omind_deploy.sh
```

## 📁 项目结构

```
omind/
├── build_omind.sh              # 统一打包脚本
├── frontend/                   # React前端
├── backend/                    # FastAPI后端
├── mcp_servers/                # MCP工具服务器
│   ├── servers/               # 服务器实现
│   ├── scripts/               # 管理脚本
│   └── config.yaml           # 配置文件
├── scripts/                    # 部署脚本
└── dist/                      # 打包输出
```

## 🔧 组件说明

### 前端界面
- 基于React + TypeScript + Vite
- 支持模型切换和实时对话
- 响应式设计，支持移动端

### 后端API
- FastAPI框架，高性能异步API
- LangGraph智能体编排
- 支持流式输出和中断处理

### MCP服务器
- **数据库工具** (3001): MySQL诊断查询
- **SSH工具** (3002): 远程系统管理
- **Elasticsearch工具** (3003): 日志查询分析
- **Zabbix工具** (3004): 监控数据获取

## 📖 开发文档

参考项目开发过程中的相关文档：

### LangGraph官方文档
https://langchain-ai.github.io/langgraph/

### FastMCP实现参考
https://gofastmcp.com/getting-started/welcome

## 🛠️ 管理命令

```bash
# 查看服务状态
cd /data/omind_prd/scripts
./status_backend.sh  # 如果有的话
./status_mcp.sh

# 查看日志
tail -f backend/logs/*.log
tail -f mcp_servers/logs/*.log

# 重启服务
./scripts/stop_backend.sh && ./scripts/start_backend.sh
./scripts/stop_mcp.sh && ./scripts/start_mcp.sh
```

## 🔒 生产环境

默认部署路径: `/data/omind_prd`

访问地址:
- **前端**: http://your-server/
- **后端API**: http://your-server:8000/api/
- **MCP服务器**: http://your-server:3001-3004/sse/

## 📄 许可证

本项目采用开源许可证，详见LICENSE文件。

---

**OMind智能运维平台** - 让AI为运维赋能 🚀