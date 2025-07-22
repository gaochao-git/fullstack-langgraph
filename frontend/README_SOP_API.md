# SOP API 切换指南

## 当前状态
- 前端界面已完成，使用Mock数据
- 数据库表结构已定义: `sop_prompt_templates`
- API接口定义已完成

## 切换到真实API的步骤

### 1. 后端API开发完成后

将以下文件中的导入从Mock API切换到真实API：

```typescript
// 在以下文件中修改导入
// src/pages/SOPManagementSimple.tsx
// src/components/SOPFormModalSimple.tsx
// src/components/SOPDetailModalSimple.tsx

// 从
import { SOPApi, SOPUtils } from '../services/sopApi';

// 改为
import { SOPApi, SOPUtils } from '../services/sopApi.real';
```

### 2. 环境变量配置

在 `.env` 文件中设置后端API地址：

```
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 后端API接口规范

需要实现以下接口：

- `POST /api/sops` - 创建SOP
- `POST /api/sops/list` - 获取SOP列表（支持搜索筛选）
- `GET /api/sops/{sop_id}` - 获取单个SOP
- `PUT /api/sops/{sop_id}` - 更新SOP
- `DELETE /api/sops/{sop_id}` - 删除SOP
- `GET /api/sops/categories` - 获取分类列表
- `GET /api/sops/teams` - 获取团队列表

### 4. 数据库操作

参考 `sop_prompt_templates` 表结构进行CRUD操作。

## 当前Mock数据位置

`src/services/sopApi.ts` - 包含完整的Mock数据和API实现