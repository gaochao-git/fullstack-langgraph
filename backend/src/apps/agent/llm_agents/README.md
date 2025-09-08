# LLM Agents 目录说明

本目录包含两类 Agent：

## 1. 内置 Agent（带 @agent 装饰器）

所有使用 `@agent` 装饰器的都是**内置 Agent**，具有以下特点：

- ✅ 系统预置的功能性 Agent
- ✅ 启动时自动注册到系统
- ✅ 同步到数据库，标记为 `is_builtin=yes`
- ✅ 不可被前端用户修改核心逻辑

示例：
```python
from src.apps.agent.llm_agents.decorators import agent

# 在 configuration.py 中定义
INIT_AGENT_CONFIG = {
    "agent_id": "diagnostic_agent",
    "description": "智能运维诊断助手",
    "agent_type": "内置",
    "capabilities": ["故障诊断", "性能分析"],
    "version": "1.0.0",
    "icon": "MedicineBoxOutlined",
    "owner": "system"
}

# 在 graph.py 中使用
@agent(**INIT_AGENT_CONFIG)
async def create_diagnostic_agent(config):
    # Agent 实现
    pass
```

## 2. 模板 Agent（不带 @agent 装饰器）

**generic_agent** 是唯一的模板 Agent，具有以下特点：

- 🔧 作为前端创建自定义 Agent 的模板
- 🔧 不被注册到系统
- 🔧 运行时从数据库读取配置（提示词、工具等）
- 🔧 支持用户在前端页面进行编排

## Agent 调用流程

1. API 请求到达 → `AgentRegistry.create_agent(agent_id)`
2. 如果 `agent_id` 在注册表中（内置 Agent）→ 使用注册的 Agent
3. 如果 `agent_id` 不在注册表中（用户创建的 Agent）→ 使用 generic_agent 模板 + 数据库配置

## 创建新的内置 Agent

1. 创建目录：`llm_agents/your_agent/`
2. 创建 `graph.py` 文件
3. 使用 `@agent` 装饰器注册
4. 系统启动时会自动发现并注册

详细指南请参考 [CREATE_CUSTOM_AGENT.md](./CREATE_CUSTOM_AGENT.md)

## LangGraph 消息管理

- **节点返回消息**：只返回新增消息 `{"messages": [new_msg]}`，不要包含 `state["messages"]`
- **自动合并**：`add_messages` reducer 会自动合并消息到状态中
- **持久化**：通过 return 返回的消息会被 checkpoint 持久化

## 重要提示

- ⚠️ **不要修改 generic_agent**：它是系统模板，用于支持前端创建的自定义 Agent
- ⚠️ **内置 Agent 使用装饰器**：所有需要预置到系统的 Agent 都必须使用 `@agent` 装饰器
- ⚠️ **前端 Agent 不用装饰器**：前端创建的 Agent 通过 generic_agent 模板运行，配置存储在数据库