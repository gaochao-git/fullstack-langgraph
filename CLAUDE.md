# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

OMind (Operational Mind) 是一个基于AI的智能运维平台，集成了故障诊断、系统监控、自动化运维等功能。

## 常用开发命令

### 服务管理（标准化）

从2025年1月开始，所有组件使用标准化的 `manage.sh` 脚本管理：

```bash
# 统一管理所有服务（推荐）
./scripts/manage_omind.sh init      # 初始化所有组件
./scripts/manage_omind.sh start     # 启动所有服务
./scripts/manage_omind.sh status    # 查看服务状态
./scripts/manage_omind.sh stop      # 停止所有服务
./scripts/manage_omind.sh restart   # 重启所有服务
./scripts/manage_omind.sh cleanup   # 清理临时文件

# 单独管理各组件
cd backend && ./manage.sh {init|start|stop|restart|status|cleanup}
cd mcp_servers && ./manage.sh {init|start|stop|restart|status|cleanup}
cd mcp_gateway && ./manage.sh {init|start|stop|restart|status|cleanup}
```

### 本地开发

```bash
# 创建Python虚拟环境（初次配置）
/Users/gaochao/miniconda3/envs/py312/bin/python -m venv venv

# 安装依赖
make install              # 安装所有依赖（前后端）
make install-backend      # 仅安装后端依赖
make install-frontend     # 仅安装前端依赖

# 前端开发服务器
cd frontend && npm run dev

# 测试
make test                 # 运行后端测试
cd backend && python -m pytest tests/test_xxx.py  # 运行单个测试文件
cd backend && python -m pytest tests/test_xxx.py::test_function  # 运行单个测试函数

# 代码质量检查
cd backend && black src/     # 格式化Python代码
cd backend && flake8 src/    # 检查Python代码风格
cd frontend && npm run lint  # 检查前端代码

# 构建与部署
make build               # 构建生产部署包
make trans               # 传输部署包到远程服务器
make clean               # 清理构建产物
```

### 访问地址

- 前端开发页面: http://localhost:5173
- 后端API文档: http://localhost:8000/docs
- MCP服务器:
  - 数据库工具: http://localhost:3001/mc
  - SSH工具: http://localhost:3002/mcp
  - Elasticsearch工具: http://localhost:3003/mcp
  - Zabbix工具: http://localhost:3004/mcp

## 高层架构

### 技术栈

- **前端**: React + TypeScript + Vite + Ant Design
- **后端**: FastAPI + Python 3.12
- **AI框架**: LangGraph + LangChain
- **数据库**: PostgreSQL/MySQL (通过LangGraph Checkpoint)
- **MCP工具**: 基于FastMCP的专业工具服务器集群

### 项目结构

```
fullstack-langgraph/
├── frontend/                 # React前端应用
│   ├── src/
│   │   ├── pages/           # 页面组件（agent、ai_model、auth、kb、mcp、sop等）
│   │   ├── services/        # API服务层
│   │   ├── components/      # 通用组件
│   │   └── types/           # TypeScript类型定义
│   └── vite.config.ts       # Vite配置
│
├── backend/                  # FastAPI后端应用
│   ├── src/
│   │   ├── main.py          # 应用入口
│   │   ├── router.py        # 路由聚合
│   │   ├── apps/            # 业务模块
│   │   │   ├── agent/       # AI智能体模块（核心功能）
│   │   │   ├── auth/        # 认证授权模块
│   │   │   ├── sop/         # SOP管理模块
│   │   │   ├── mcp/         # MCP配置管理
│   │   │   ├── ai_model/    # AI模型管理
│   │   │   └── user/        # 用户和RBAC管理
│   │   └── shared/          # 共享组件
│   │       ├── core/        # 核心功能（配置、日志、中间件等）
│   │       └── db/          # 数据库配置
│   └── requirements.txt     # Python依赖
│
├── mcp_servers/             # MCP工具服务器
│   ├── servers/             # 各类工具服务器实现
│   └── start_mcp_servers.py # MCP服务器启动脚本
│
├── Unla/                    # Unla MCP网关（第三方组件）
│   └── cmd/mcp-gateway/     # MCP网关入口
│
├── celery_task/             # 异步任务模块
├── scripts/                 # 统一管理脚本
│   ├── manage_omind.sh      # 统一管理入口
│   └── common/              # 公共函数库
│       ├── colors.sh        # 颜色定义
│       ├── logger.sh        # 日志函数
│       └── utils.sh         # 工具函数
│
├── Makefile                 # 构建和开发命令
└── build_omind.sh           # 打包部署脚本
```

### 核心业务流程

1. **AI诊断流程**: 用户通过前端发起诊断请求 → 后端通过LangGraph编排AI智能体 → 调用MCP工具获取系统信息 → 返回诊断结果
2. **认证流程**: 支持本地认证和SSO单点登录，基于JWT Token的无状态认证
3. **RBAC权限控制**: 基于角色的访问控制，支持菜单权限和API权限管理
4. **MCP工具集成**: 通过MCP协议集成数据库、SSH、Elasticsearch、Zabbix等运维工具

### 关键配置文件

- `backend/src/shared/core/config.py`: 后端核心配置
- `frontend/src/utils/base_api.ts`: 前端API配置
- `mcp_servers/config.yaml`: MCP服务器配置
- `.env`: 环境变量配置（本地开发时创建）

### 环境变量

后端需要的主要环境变量：
- `CHECKPOINTER_TYPE`: postgres/mysql/memory
- `POSTGRES_URI`: PostgreSQL连接串
- `MYSQL_CHECKPOINT_URI`: MySQL连接串
- `LLM_TYPE`: 使用的LLM类型（deepseek/openai等）
- `LLM_API_KEY`: LLM API密钥

文件上传相关配置：
- `MAX_UPLOAD_SIZE_MB`: 最大上传文件大小（MB），默认10
- `UPLOAD_ALLOWED_EXTENSIONS`: 允许的文件扩展名，默认[".pdf",".docx",".txt",".md"]
- `UPLOAD_DIR`: 文件存储目录，默认uploads/documents

### 开发注意事项

1. **LangGraph状态管理**: Agent模块使用LangGraph的状态管理，注意checkpoint的配置
2. **流式输出**: 诊断对话支持SSE流式输出，前端需要正确处理流式响应
3. **MCP工具调用**: 通过langchain-mcp-adapters集成MCP工具，工具调用需要正确的权限配置
4. **认证中间件**: API路由默认需要认证，公开接口需要显式标记
5. **数据库事务**: 使用SQLAlchemy的异步事务管理，注意正确处理事务边界
6. **前端API处理**: 
   - `base_api.ts`: 只处理HTTP错误，返回原始响应
   - `services/xxxApi.ts`: 透传层，不做业务处理
   - 组件/Hook层: 处理业务逻辑错误(`status === 'error'`)和UI消息显示

### 测试策略

- 单元测试: 使用pytest，测试文件放在各模块的tests目录
- API测试: 使用FastAPI的TestClient进行集成测试
- 前端测试: 使用Vitest进行组件测试（如需要）

### 部署流程

1. 本地打包: `make build` 或 `./build_omind.sh` 生成omind-xxx.tar.gz
2. 传输到服务器: `make trans`
3. 远程部署:
   ```bash
   # 初次部署
   tar -xzf omind-xxx.tar.gz
   cd omind-xxx
   ./scripts/manage_omind.sh init --deploy-path=/data/omind
   ./scripts/manage_omind.sh start
   
   # 后续管理
   cd /data/omind
   ./scripts/manage_omind.sh status
   ./scripts/manage_omind.sh restart
   
   # 升级
   ./scripts/manage_omind.sh upgrade --package=/tmp/omind-new.tar.gz
   ```

### 管理脚本标准

所有组件的 `manage.sh` 脚本都支持以下标准命令：
- `init`: 初始化组件（创建目录、安装依赖等）
- `start`: 启动服务
- `stop`: 停止服务
- `restart`: 重启服务
- `status`: 查看服务状态
- `cleanup`: 清理临时文件和日志

## 后端开发规范

### 代码组织结构

每个业务模块必须遵循以下目录结构：
```
apps/your_module/
├── __init__.py       # 导出 router
├── endpoints.py      # API路由定义（仅负责参数接收和响应返回）
├── service/          # 业务逻辑层
│   └── xxx_service.py
├── models.py         # 数据库模型定义
└── schema.py         # Pydantic模型（请求/响应格式）
```

### 请求处理流程

1. **请求入口** → FastAPI Application (main.py)
2. **中间件处理** → CORS、请求日志、性能监控、认证等
3. **路由分发** → router.py → 具体模块的 endpoints.py
4. **参数验证** → Pydantic Schema 自动验证
5. **业务处理** → Service 层处理业务逻辑
6. **数据操作** → 使用 SQLAlchemy ORM 操作数据库
7. **统一响应** → 使用公共响应格式返回

### 公共方法使用规范

#### 1. 统一响应格式
- 成功响应使用 `success_response()`
- 分页响应使用 `paginated_response()` 
- 错误响应通过抛出 `BusinessException` 自动处理
- 不要自己构造响应JSON

#### 2. 数据库操作
- 使用依赖注入 `Depends(get_async_db)` 获取数据库会话
- 写操作必须使用 `async with db.begin()` 自动管理事务
- 不需要手动 commit 或 rollback
- 查询使用 SQLAlchemy 的 select 语法

#### 3. 日志记录
- 使用 `get_logger(__name__)` 获取日志器
- 重要操作（创建、更新、删除）必须记录日志
- 日志自动包含 request_id 便于追踪

#### 4. 异常处理
- 业务错误使用 `BusinessException`，指定 ResponseCode
- 不要使用 HTTPException
- 异常信息要用户友好
- 系统异常会自动处理

#### 5. 时间处理
- 使用 `now_shanghai()` 获取当前时间
- 所有时间存储为上海时区
- 模型的创建和更新时间会自动设置

### 开发流程

1. **设计数据模型** (models.py)
2. **定义接口格式** (schema.py) 
3. **实现业务逻辑** (service/)
4. **暴露API接口** (endpoints.py)
5. **注册到路由** (router.py)

### API设计规范

- 遵循 RESTful 风格
- 路径使用复数形式
- 版本号统一使用 /v1/
- 标准操作：
  - GET /v1/items - 列表
  - GET /v1/items/:id - 详情
  - POST /v1/items - 创建
  - PUT /v1/items/:id - 更新
  - DELETE /v1/items/:id - 删除

### 命名规范

- 文件名：小写下划线分隔 (user_service.py)
- 类名：大驼峰 (UserService)
- 函数名：小写下划线分隔 (get_user_by_id)
- 变量名：小写下划线分隔
- 常量：大写下划线分隔

### 导入规范

1. **使用绝对导入进行跨模块引用**
   - 正确：`from src.apps.auth.models import User`
   - 错误：`from ...auth.models import User`

2. **相对导入仅用于模块内部**
   - 最多允许2级相对导入
   - 正确：`from . import schema` (同级目录)
   - 正确：`from ..service import user_service` (上一级目录)
   - 错误：`from ...shared.tools import sop_tool` (3级或更多)

3. **深层相对导入必须改为绝对导入**
   - 错误：`from .....shared.tools import sop_tool, general_tool`
   - 正确：`from src.shared.tools import sop_tool, general_tool`
   
4. **标准导入顺序**
   ```python
   # 1. 标准库
   import os
   import json
   from typing import List, Dict
   
   # 2. 第三方库
   from fastapi import Depends
   from sqlalchemy import select
   
   # 3. 项目内绝对导入
   from src.shared.core.logging import get_logger
   from src.apps.auth.models import User
   
   # 4. 模块内相对导入（仅限1-2级）
   from . import schema
   from ..service import user_service
   ```

5. **禁止的导入模式**
   - 禁止3级或更深的相对导入：`from ...xxx`
   - 禁止循环导入
   - 禁止在运行时动态导入（除非必要）

### 数据库使用规范

#### 事务管理说明

本项目采用标准的SQLAlchemy事务管理模式：

**Service层必须使用 `async with db.begin()`**：
- 所有写操作（create/update/delete）都必须在事务块中
- 事务块会自动提交或回滚
- 只读操作不需要事务块

**重要**：不使用 `async with db.begin()` 的写操作不会被保存到数据库！

#### 1. 异步数据库用法（推荐）

##### 1.1 FastAPI 依赖注入（路由层）
```python
from src.shared.db.config import get_async_db

@router.post("/users")
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_async_db)):
    # 路由层调用service
    user = await user_service.create_user(db, user_data)
    return success_response(user)
```

##### 1.2 Service层数据库操作

```python
class UserService:
    # 写操作必须使用事务块
    async def create_user(self, db: AsyncSession, user_data: dict):
        async with db.begin():
            user = User(**user_data)
            db.add(user)
            await db.flush()
            await db.refresh(user)
            return user  # 事务自动提交
    
    # 更新操作也需要事务块
    async def update_user(self, db: AsyncSession, user_id: str, data: dict):
        async with db.begin():
            user = await self.get_user_by_id(db, user_id)
            for key, value in data.items():
                setattr(user, key, value)
            await db.flush()
            return user
    
    # 只读操作不需要事务块
    async def get_user_by_id(self, db: AsyncSession, user_id: str):
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()
```

##### 1.3 独立函数/后台任务（非路由环境）
```python
from src.shared.db.config import get_async_db_context

# 用于独立函数、后台任务、定时任务等非FastAPI路由环境
async with get_async_db_context() as session:
    async with db.begin():  # 这里可以使用事务块
        user = User(name="test")
        session.add(user)
        await session.flush()
        # 自动提交或回滚
```

#### 2. 同步数据库用法（仅限智能体langgraph直接查询数据库场景，如获取提示词、工具等）

```python
from src.shared.db.config import get_sync_db

# 方式1：生成器模式（用于依赖注入）
def some_sync_function(db: Session = Depends(get_sync_db)):
    agent = db.query(AgentConfig).filter(...).first()
    # 需要手动管理事务
```

#### 4. 数据库使用最佳实践

1. **新代码一律使用异步**
2. **FastAPI 端点使用 `Depends(get_async_db)`**
3. **Service 层推荐使用 `async with db.begin()`** - 事务管理更清晰
4. **复杂操作（多表、先删后增）必须在同一事务中**
5. **独立函数使用 `get_async_db_context()` 和 `async with db.begin()`**
6. **只在必要时使用同步（如 LangGraph 工具）**
7. **避免混用同步和异步会话**

#### 5. 常见场景示例

##### 5.1 多表操作（推荐方式）
```python
# Service层 - 使用 async with db.begin()
async def create_user_with_role(self, db: AsyncSession, user_data: dict, role_id: str):
    async with db.begin():
        # 创建用户
        user = RbacUser(**user_data)
        db.add(user)
        await db.flush()
        
        # 创建用户角色关联
        user_role = RbacUsersRoles(user_id=user.user_id, role_id=role_id)
        db.add(user_role)
        await db.flush()
        
        # 创建认证记录
        auth_user = AuthUser(user_id=user.user_id, password_hash=hash_password(password))
        db.add(auth_user)
        await db.flush()
        
        return user  # 事务自动提交

# 路由层 - 简单调用
@router.post("/users/with-role")
async def create_user_with_role(data: UserCreateWithRole, db: AsyncSession = Depends(get_async_db)):
    user = await user_service.create_user_with_role(db, data.dict(), data.role_id)
    return success_response(user)
```

### 注意事项

1. **不要在 endpoints.py 写业务逻辑**
2. **Service 层不处理 HTTP 相关内容**
3. **使用 BusinessException 而不是 HTTPException**
4. **所有 API 返回统一响应格式**
5. **Service层推荐使用 `async with db.begin()` 管理事务**
6. **敏感信息不要记录到日志**
7. **大量数据必须分页处理**
8. **导入使用绝对路径，相对导入限制在2级以内**
9. **数据库操作优先使用异步模式**