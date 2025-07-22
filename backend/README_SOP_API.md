# SOP API 后端接口文档

## 概述

这是一个基于 FastAPI + SQLAlchemy 的 SOP（标准操作程序）管理系统后端API。支持PostgreSQL和MySQL数据库。

## 功能特性

- ✅ 完整的SOP CRUD操作
- ✅ 支持PostgreSQL和MySQL数据库
- ✅ 异步数据库操作
- ✅ 数据验证和错误处理
- ✅ 搜索和筛选功能
- ✅ 分页支持
- ✅ 自动数据库表创建
- ✅ 示例数据初始化

## 安装和配置

### 1. 安装依赖

```bash
# 安装新增的依赖
pip install sqlalchemy==2.0.36 alembic==1.14.0
```

### 2. 环境变量配置

复制 `.env.example` 到 `.env` 并配置数据库连接：

```bash
# PostgreSQL配置示例
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=langgraph_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password

# MySQL配置示例
DATABASE_TYPE=mysql
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=langgraph_db
DATABASE_USER=root
DATABASE_PASSWORD=your_password
```

### 3. 数据库初始化

```bash
# 运行数据库初始化脚本（创建表并插入示例数据）
cd backend
python -m src.scripts.init_sop_data
```

### 4. 启动服务

```bash
# 开发模式
uvicorn src.api.app:app --reload --port 8000

# 生产模式
gunicorn src.api.app:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API 接口文档

### 基础信息

- **基础URL**: `http://localhost:8000`
- **API前缀**: `/api/sops`
- **响应格式**: JSON

### 通用响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "error": null
}
```

### 接口列表

#### 1. 创建SOP

**POST** `/api/sops/`

**请求体**:
```json
{
  "sop_id": "SOP-DB-001",
  "sop_title": "MySQL数据库诊断",
  "sop_category": "database",
  "sop_description": "MySQL性能问题诊断流程",
  "sop_severity": "high",
  "steps": [
    {
      "step": 1,
      "description": "检查慢查询日志",
      "ai_generated": false,
      "tool": "execute_mysql_query",
      "args": "SHOW VARIABLES LIKE 'slow_query_log';",
      "requires_approval": false
    }
  ],
  "tools_required": ["execute_mysql_query", "get_es_data"],
  "sop_recommendations": "建议优化慢查询",
  "team_name": "ops-team"
}
```

#### 2. 获取SOP列表

**POST** `/api/sops/list`

**请求体**:
```json
{
  "search": "数据库",
  "category": "database",
  "severity": "high",
  "team_name": "ops-team",
  "limit": 10,
  "offset": 0
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": 1,
        "sop_id": "SOP-DB-001",
        "sop_title": "MySQL数据库响应耗时升高诊断",
        "sop_category": "database",
        "sop_severity": "high",
        "sop_steps": "[{\"step\":1,\"description\":\"...\"}]",
        "tools_required": "[\"execute_mysql_query\"]",
        "team_name": "ops-team",
        "create_time": "2025-01-12 10:00:00",
        "update_time": "2025-01-12 10:00:00"
      }
    ],
    "total": 1
  }
}
```

#### 3. 获取单个SOP

**GET** `/api/sops/{sop_id}`

#### 4. 更新SOP

**PUT** `/api/sops/{sop_id}`

**请求体**: 同创建SOP，但字段为可选

#### 5. 删除SOP

**DELETE** `/api/sops/{sop_id}`

#### 6. 获取分类列表

**GET** `/api/sops/meta/categories`

#### 7. 获取团队列表

**GET** `/api/sops/meta/teams`

## 数据库表结构

### sop_prompt_templates 表

```sql
CREATE TABLE sop_prompt_templates (
    id SERIAL PRIMARY KEY,
    sop_id VARCHAR(100) UNIQUE NOT NULL,
    sop_title VARCHAR(500) NOT NULL,
    sop_category VARCHAR(100) NOT NULL,
    sop_description TEXT,
    sop_severity VARCHAR(20) NOT NULL,
    sop_steps JSONB NOT NULL,  -- PostgreSQL使用JSONB，MySQL使用JSON
    tools_required JSONB,
    sop_recommendations TEXT,
    team_name VARCHAR(100) NOT NULL,
    create_by VARCHAR(100) NOT NULL,
    update_by VARCHAR(100),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 前端集成

### 切换到真实API

修改前端文件中的导入：

```typescript
// 在以下文件中修改
// frontend/src/pages/SOPManagementSimple.tsx
// frontend/src/components/SOPFormModalSimple.tsx  
// frontend/src/components/SOPDetailModalSimple.tsx

// 从Mock API切换到真实API
import { SOPApi, SOPUtils } from '../services/sopApi.real';
```

### 环境变量

在前端 `.env` 文件中设置：
```
VITE_API_BASE_URL=http://localhost:8000
```

## 错误处理

### 常见错误码

- `400`: 请求参数错误（如SOP ID已存在）
- `404`: SOP不存在
- `500`: 服务器内部错误

### 错误响应格式

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "SOP ID 'SOP-DB-001' already exists"
}
```

## 日志

- 应用日志存储在 `logs/backend_YYYYMMDD.log`
- 数据库操作日志会记录在应用日志中
- 日志级别可通过环境变量 `LOG_LEVEL` 配置

## 测试

### 使用 curl 测试

```bash
# 创建SOP
curl -X POST http://localhost:8000/api/sops/ \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-TEST-001",
    "sop_title": "测试SOP",
    "sop_category": "test",
    "sop_severity": "low",
    "steps": [
      {
        "step": 1,
        "description": "测试步骤",
        "ai_generated": false,
        "tool": "test_tool",
        "args": "test args",
        "requires_approval": false
      }
    ],
    "team_name": "test-team"
  }'

# 获取SOP列表
curl -X POST http://localhost:8000/api/sops/list \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "offset": 0}'
```

## 生产部署注意事项

1. **数据库连接池**: 生产环境建议配置合适的连接池大小
2. **安全性**: 添加身份认证和授权机制
3. **监控**: 添加健康检查接口和监控指标
4. **备份**: 定期备份SOP数据
5. **版本控制**: SOP变更建议添加版本控制机制