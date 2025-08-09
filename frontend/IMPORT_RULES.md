# 前端项目导入规则指南

## 导入顺序

按照以下顺序组织 import 语句，每组之间用空行分隔：

1. **React 相关导入**
2. **第三方库导入**
3. **项目内部导入（使用 @ 别名）**
4. **相对路径导入（仅限同目录文件）**
5. **样式文件导入**

## 具体规则

### 1. React 相关导入
```typescript
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
```

### 2. 第三方库导入
```typescript
import { message, Form, Button } from 'antd';
import { create } from 'zustand';
import { clsx } from 'clsx';
```

### 3. 项目内部导入（使用 @ 别名）

#### 跨目录导入必须使用 @ 别名：
```typescript
// ✅ 正确
import { authApi } from '@/services/authApi';
import { useAuth } from '@/hooks/useAuth';
import { MenuTreeNode } from '@/types/menu';
import { Button } from '@/components/ui/button';

// ❌ 错误
import { authApi } from '../../services/authApi';
import { useAuth } from '../../../hooks/useAuth';
```

#### @ 别名路径映射：
- `@/` → `src/` 目录
- `@/services` → `src/services`
- `@/hooks` → `src/hooks`
- `@/components` → `src/components`
- `@/pages` → `src/pages`
- `@/utils` → `src/utils`
- `@/types` → `src/types`

### 4. 相对路径导入（仅限同目录）

#### 同目录文件可以使用相对路径：
```typescript
// ✅ 可以接受（同目录）
import AgentDetailModal from './components/AgentDetailModal';
import { renderIcon } from './AgentIconSystem';

// ❌ 避免（跨目录）
import { SOPTemplate } from '../types/sop';
```

### 5. 样式文件导入
```typescript
import './LoginPage.css';
import styles from './Component.module.css';
```

## 完整示例

```typescript
// React 相关
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// 第三方库
import { Card, Button, message } from 'antd';
import { clsx } from 'clsx';

// 项目内部（@ 别名）
import { useAuth } from '@/hooks/useAuth';
import { agentApi } from '@/services/agentApi';
import { Agent } from '@/types/agent';
import { Button as UIButton } from '@/components/ui/button';

// 同目录文件
import AgentDetailModal from './AgentDetailModal';
import { formatAgentData } from './utils';

// 样式文件
import './AgentManagement.css';
```

## 导入分组规则

### Services 层
```typescript
// 所有 API 服务都应该从 @/services 导入
import { agentApi } from '@/services/agentApi';
import { authApi } from '@/services/authApi';
import { mcpApi } from '@/services/mcpApi';
```

### Utils 工具函数
```typescript
// 所有工具函数都应该从 @/utils 导入
import { omind_get, omind_post } from '@/utils/base_api';
import { cn } from '@/utils/lib-utils';
import { formatDate } from '@/utils/dateUtils';
```

### Hooks
```typescript
// 所有自定义 hooks 都应该从 @/hooks 导入
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/ThemeContext';
import { useMenus } from '@/hooks/useMenus';
```

### Types 类型定义
```typescript
// 所有类型定义都应该从 @/types 导入
import { Agent, MCPServer } from '@/types/agent';
import { MenuTreeNode } from '@/types/menu';
import { SOPTemplate } from '@/types/sop';
```

### Components 组件
```typescript
// 通用组件从 @/components 导入
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Button } from '@/components/ui/button';

// 页面专属组件可以使用相对路径（同目录）
import AgentEditModal from './components/AgentEditModal';
```

## 特殊情况

### 1. 循环依赖
如果遇到循环依赖，考虑：
- 将共享类型提取到 `@/types` 目录
- 重新组织代码结构
- 使用动态导入 `import()`

### 2. 懒加载
```typescript
const AgentManagement = lazy(() => import('@/pages/agent/AgentManagement'));
```

### 3. 导出聚合
在 index.ts 文件中聚合导出：
```typescript
// src/services/index.ts
export * from './agentApi';
export * from './authApi';
export * from './mcpApi';

// 使用时
import { agentApi, authApi } from '@/services';
```

## ESLint 配置建议

可以配置 ESLint 规则来强制执行这些导入规则：

```json
{
  "rules": {
    "import/order": [
      "error",
      {
        "groups": [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index"
        ],
        "pathGroups": [
          {
            "pattern": "react",
            "group": "external",
            "position": "before"
          },
          {
            "pattern": "@/**",
            "group": "internal"
          }
        ],
        "pathGroupsExcludedImportTypes": ["react"],
        "newlines-between": "always"
      }
    ]
  }
}
```