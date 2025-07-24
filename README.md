# OMind 智能运维平台

**OMind** (Operational Mind) 是一个基于AI的智能运维平台，集成了故障诊断、系统监控、自动化运维等功能。

## 🎯 平台特性

- **智能故障诊断**: 基于LangGraph的AI诊断助手
- **多模型支持**: 支持DeepSeek、Qwen、GPT等多种AI模型
- **MCP工具集成**: 内置数据库、SSH、ES、Zabbix等专业工具
- **可视化界面**: 基于React的现代化前端界面
- **一键部署**: 统一的打包和部署解决方案

```bash
# 一键打包
./build_omind.sh --production
# 传输到服务器
scp manage_omind.sh user@server:/tmp/
scp dist/omind-production-*.tar.gz user@server:/tmp/
```


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