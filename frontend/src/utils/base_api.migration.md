# Base API 迁移指南

## 概述

本项目统一使用 `base_api` 封装的两个核心方法：
1. **omind_fetch** - 普通HTTP请求
2. **omind_fetch_stream** - 流式请求，主要与大模型通信

## 迁移步骤

### 1. 更新导入语句

**旧代码：**
```typescript
import { baseFetch } from '../utils/baseFetch';
```

**新代码：**
```typescript
import { omind_fetch, omind_fetch_stream, omind_get, omind_post, omind_put, omind_del } from '../utils/base_api';
```

### 2. 普通HTTP请求迁移

#### GET 请求

**旧代码：**
```typescript
const response = await baseFetch('/api/v1/agents');
if (!response.ok) {
  throw new Error(`获取失败: ${response.statusText}`);
}
const result = await response.json();
```

**新代码：**
```typescript
const response = await omind_get('/api/v1/agents');
const result = await response.json();
// 错误处理已内置，无需手动检查response.ok
```

#### POST 请求

**旧代码：**
```typescript
const response = await baseFetch('/api/v1/agents', {
  method: 'POST',
  body: JSON.stringify(agentData),
});
```

**新代码：**
```typescript
const response = await omind_post('/api/v1/agents', agentData);
// 自动JSON序列化，无需手动stringify
```

#### PUT 请求

**旧代码：**
```typescript
const response = await baseFetch(`/api/v1/agents/${agentId}`, {
  method: 'PUT',
  body: JSON.stringify(updateData),
});
```

**新代码：**
```typescript
const response = await omind_put(`/api/v1/agents/${agentId}`, updateData);
```

#### DELETE 请求

**旧代码：**
```typescript
const response = await baseFetch(`/api/v1/agents/${agentId}`, {
  method: 'DELETE',
});
```

**新代码：**
```typescript
const response = await omind_del(`/api/v1/agents/${agentId}`);
```

### 3. 流式请求迁移

**旧代码（fetch方式）：**
```typescript
const response = await fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  },
  body: JSON.stringify(requestBody),
});

const reader = response.body.getReader();
// 复杂的流式处理逻辑...
```

**新代码：**
```typescript
await omind_fetch_stream('/api/llm/threads/123/runs/stream', {
  body: requestBody,
  onData: (data: string) => {
    // 处理每个数据块
    console.log('接收到数据:', data);
  },
  onError: (error: Error) => {
    // 处理错误
    console.error('流式请求错误:', error);
  },
  onComplete: () => {
    // 处理完成
    console.log('流式请求完成');
  }
});
```

### 4. 自定义配置

**使用omind_fetch进行自定义请求：**
```typescript
const response = await omind_fetch('/api/custom', {
  method: 'POST',
  headers: {
    'Custom-Header': 'value',
    'Authorization': 'Bearer token',
  },
  body: customData,
  timeout: 10000, // 10秒超时
});
```

**流式请求自定义配置：**
```typescript
await omind_fetch_stream('/api/stream', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer token',
  },
  body: requestData,
  timeout: 300000, // 5分钟超时
  onData: (data) => { /* 处理数据 */ },
  onError: (error) => { /* 处理错误 */ },
  onComplete: () => { /* 处理完成 */ }
});
```

## 迁移清单

### 需要迁移的文件

1. **Services 层**
   - [ ] `/src/services/agentApi.ts` ✅ 已迁移
   - [ ] `/src/services/agentApi.real.ts`
   - [ ] `/src/services/mcpApi.ts`
   - [ ] 其他API服务文件

2. **Components 层**
   - [ ] `/src/components/UnifiedAgentChat.tsx` ✅ 部分迁移
   - [ ] `/src/components/GenericAgent.tsx`
   - [ ] 其他组件中的直接API调用

3. **Pages 层**
   - [ ] `/src/pages/AgentManagement.tsx`
   - [ ] `/src/pages/MCPManagement.tsx`
   - [ ] 其他页面组件

### 迁移优先级

**高优先级：**
- 流式聊天相关组件（使用 omind_fetch_stream）
- 主要的API服务类

**中优先级：**
- 管理页面的API调用
- 配置相关的API调用

**低优先级：**
- 一次性的工具函数
- 测试相关代码

## 注意事项

1. **错误处理**：新API已内置错误处理，无需手动检查 `response.ok`
2. **JSON序列化**：POST/PUT请求的body会自动序列化，无需手动 `JSON.stringify`
3. **超时配置**：可以为每个请求单独配置超时时间
4. **流式请求**：使用回调函数处理数据，更简洁易用
5. **类型安全**：所有方法都有完整的TypeScript类型定义

## 示例代码

参考 `/src/utils/base_api.example.ts` 文件，里面包含了完整的使用示例和最佳实践。

## 测试

迁移完成后，请确保：
1. 所有API调用正常工作
2. 错误处理符合预期
3. 流式请求能正确处理数据流
4. 超时机制正常工作