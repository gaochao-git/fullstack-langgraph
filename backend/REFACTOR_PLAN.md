# 业务模块重构方案

## 🎯 目标架构

```
src/
├── apps/                    # 业务应用模块
│   ├── sop/                # SOP标准作业程序
│   │   ├── api/
│   │   ├── services/
│   │   ├── dao/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── tests/
│   ├── agents/             # 智能体管理
│   │   ├── api/
│   │   ├── services/
│   │   ├── dao/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── workflows/      # 智能体工作流定义
│   │   └── tests/
│   ├── mcp/                # MCP服务器管理
│   │   ├── api/
│   │   ├── services/
│   │   ├── dao/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── tests/
│   ├── ai_models/          # AI模型管理
│   │   ├── api/
│   │   ├── services/
│   │   ├── dao/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── tests/
│   ├── users/              # 用户权限管理
│   │   ├── api/
│   │   ├── services/
│   │   ├── dao/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── tests/
│   ├── workflows/          # 工作流引擎
│   │   ├── api/
│   │   ├── services/
│   │   ├── dao/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── engine/         # 工作流执行引擎
│   │   └── tests/
│   └── monitoring/         # 监控告警
│       ├── api/
│       ├── services/
│       ├── dao/
│       ├── models/
│       ├── schemas/
│       └── tests/
├── shared/                 # 共享模块
│   ├── core/              # 核心工具
│   │   ├── logging.py
│   │   ├── middleware.py
│   │   ├── security.py
│   │   ├── config.py
│   │   └── dependencies.py
│   ├── db/                # 数据库基础设施
│   │   ├── base_dao.py
│   │   ├── base_model.py
│   │   ├── config.py
│   │   ├── transaction.py
│   │   └── migrations/
│   ├── utils/             # 通用工具
│   │   ├── datetime.py
│   │   ├── crypto.py
│   │   ├── validators.py
│   │   └── helpers.py
│   ├── exceptions/        # 统一异常处理
│   │   ├── base.py
│   │   ├── business.py
│   │   └── handlers.py
│   └── tools/             # 通用工具集
│       ├── elasticsearch_tool.py
│       ├── mysql_tool.py
│       ├── ssh_tool.py
│       └── zabbix_tool.py
├── knowledge_base/        # 知识库（独立模块）
├── main.py               # 应用入口
└── scripts/              # 部署脚本
```

## 🔄 迁移映射

### 现有 → 新架构映射关系

| 现有位置 | 新位置 | 说明 |
|---------|--------|------|
| `api/endpoints/sop.py` | `apps/sop/api/endpoints.py` | SOP API |
| `services/sop_service.py` | `apps/sop/services/sop_service.py` | SOP服务 |
| `db/dao/sop_dao.py` | `apps/sop/dao/sop_dao.py` | SOP数据访问 |
| `schemas/sop.py` | `apps/sop/schemas/` | SOP数据结构 |
| `api/endpoints/agents.py` | `apps/agents/api/endpoints.py` | 智能体API |
| `services/agent_service.py` | `apps/agents/services/agent_service.py` | 智能体服务 |
| `agents/diagnostic_agent/` | `apps/agents/workflows/diagnostic/` | 诊断智能体工作流 |
| `api/endpoints/mcp.py` | `apps/mcp/api/endpoints.py` | MCP API |
| `services/mcp_service.py` | `apps/mcp/services/mcp_service.py` | MCP服务 |
| `api/endpoints/ai_models.py` | `apps/ai_models/api/endpoints.py` | AI模型API |
| `services/user_service.py` | `apps/users/services/user_service.py` | 用户服务 |
| `core/` | `shared/core/` | 核心工具共享 |
| `db/dao/base_dao.py` | `shared/db/base_dao.py` | 基础DAO共享 |
| `tools/` | `shared/tools/` | 通用工具共享 |

## 🚀 重构步骤

### 阶段1：创建新目录结构
1. 创建 `apps/` 和 `shared/` 目录
2. 按业务模块创建子目录
3. 创建各模块的标准目录结构

### 阶段2：迁移共享模块
1. 迁移 `core/` → `shared/core/`
2. 拆分 `db/` → `shared/db/` + 各模块的models
3. 迁移 `tools/` → `shared/tools/`

### 阶段3：按业务模块迁移
1. SOP模块迁移
2. Agents模块迁移
3. MCP模块迁移
4. 其他模块依次迁移

### 阶段4：更新导入路径
1. 更新所有模块的import语句
2. 调整依赖关系
3. 更新配置文件

### 阶段5：测试验证
1. 单元测试调整
2. 集成测试验证
3. API兼容性测试

## 💡 重构优势

### 多人开发
- 每个团队成员负责特定的app模块
- 减少代码冲突
- 独立的测试和CI/CD

### 微服务准备
- 每个app都是完整的业务单元
- 清晰的模块边界
- 易于提取为独立服务

### 维护性
- 业务逻辑内聚
- 依赖关系清晰
- 更容易定位问题

### 扩展性
- 新功能模块化开发
- 插件式架构
- 支持动态加载

## ⚠️ 注意事项

1. **向后兼容**：确保API端点路径不变
2. **导入路径**：需要全面更新import语句
3. **配置管理**：统一配置vs模块配置的平衡
4. **数据库**：models分散vs统一管理的权衡
5. **测试覆盖**：确保重构后测试不遗漏