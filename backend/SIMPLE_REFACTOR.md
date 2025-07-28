# 简化的业务模块拆分

## 🎯 基于现有功能的拆分

只拆分现有的4个核心业务模块：

```
src/
├── apps/
│   ├── sop/              # SOP管理
│   │   ├── api/          # endpoints/sop.py
│   │   ├── services/     # sop_service.py
│   │   ├── dao/          # sop_dao.py  
│   │   ├── models/       # SOPTemplate model
│   │   ├── schemas/      # sop.py
│   │   └── tests/
│   ├── agent/            # 智能体管理
│   │   ├── api/          # endpoints/agents.py
│   │   ├── services/     # agent_service.py, agent_config_service.py
│   │   ├── dao/          # agent_dao.py
│   │   ├── models/       # AgentConfig model
│   │   ├── workflows/    # 现有的agents/目录
│   │   └── tests/
│   ├── mcp/              # MCP服务器管理
│   │   ├── api/          # endpoints/mcp.py
│   │   ├── services/     # mcp_service.py
│   │   ├── dao/          # mcp_dao.py
│   │   ├── models/       # MCPServer model
│   │   ├── schemas/      # mcp.py
│   │   └── tests/
│   └── user/             # 用户管理
│       ├── api/          # 从endpoints/agents.py中提取用户相关API
│       ├── services/     # user_service.py
│       ├── dao/          # user_dao.py
│       ├── models/       # User, UserThread models
│       └── tests/
├── shared/
│   ├── core/             # 现有core/目录
│   ├── db/               # base_dao.py, config.py, transaction.py
│   └── tools/            # 现有tools/目录
├── knowledge_base/       # 保持不变
├── main.py              # 保持不变
└── scripts/             # 保持不变
```

## 🔄 迁移计划

### 第1步：创建目录结构
### 第2步：迁移SOP模块
### 第3步：迁移Agent模块  
### 第4步：迁移MCP模块
### 第5步：迁移User模块
### 第6步：迁移共享模块
### 第7步：更新导入路径
### 第8步：测试验证