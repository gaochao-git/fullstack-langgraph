# API Key 使用指南

## 功能概述

API Key功能允许内部员工通过编程方式访问系统API，适用于：
- 数据自动化导入导出
- 监控脚本集成
- CI/CD流程集成
- 系统间数据同步

## 实现状态

### ✅ 已完成
1. **后端功能**
   - 数据模型：`AuthApiKey`表
   - Service层：创建、列表、撤销API Key
   - API接口：`/api/v1/auth/api-keys`
   - 认证中间件：支持Bearer Token认证

2. **前端功能**
   - API Key服务层：`apiKeyService.ts`
   - 管理界面：`APIKeyManagement.tsx`
   - 组件注册：已添加到`componentRegistry.ts`

### 📝 使用步骤

1. **在系统中创建API Key**
   - 登录系统后，进入"API密钥管理"页面
   - 点击"创建密钥"
   - 输入密钥名称、设置权限和有效期
   - 保存生成的Bearer Token（只显示一次）

2. **在代码中使用API Key**

### Python示例
```python
import requests

# API Token（从系统中获取）
API_TOKEN = "omind_ak_xxxxxxxxxxxxx"

# 设置请求头
headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# 发起请求
response = requests.get(
    "https://api.example.com/api/v1/orders",
    headers=headers
)

data = response.json()
```

### Shell脚本示例
```bash
#!/bin/bash

API_TOKEN="omind_ak_xxxxxxxxxxxxx"

# 获取数据
curl -H "Authorization: Bearer $API_TOKEN" \
     https://api.example.com/api/v1/users/export

# POST请求示例
curl -X POST \
     -H "Authorization: Bearer $API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "test"}' \
     https://api.example.com/api/v1/items
```

### Node.js示例
```javascript
const axios = require('axios');

const API_TOKEN = 'omind_ak_xxxxxxxxxxxxx';

async function fetchData() {
  const response = await axios.get('https://api.example.com/api/v1/data', {
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`
    }
  });
  
  return response.data;
}

// 使用 fetch API
async function postData() {
  const response = await fetch('https://api.example.com/api/v1/items', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ name: 'test' })
  });
  
  return response.json();
}
```

## 安全最佳实践

1. **密钥管理**
   - 不要在代码中硬编码密钥
   - 使用环境变量存储密钥
   - 定期轮换密钥

2. **权限控制**
   - 为不同用途创建不同的密钥
   - 使用最小权限原则
   - 设置合理的过期时间

3. **访问限制**
   - 设置IP白名单（如果适用）
   - 监控异常使用模式
   - 及时撤销不再使用的密钥

## 技术细节

### 认证流程
1. 客户端在请求头中发送`Authorization: Bearer <token>`
2. 服务器识别token格式（omind_ak_开头为API Key）
3. 计算token的哈希值并与数据库比对
4. 验证通过后，获取关联的用户权限
5. 执行请求的API操作

### 与JWT的区别
- **JWT**：适用于Web应用的用户会话管理，有较短的过期时间
- **API Key**：适用于程序化访问，可以设置较长的有效期或永不过期

## 待完成事项

1. **添加菜单项**
   - 需要在数据库中添加"API密钥管理"菜单
   - 路径：`/settings/api-keys`
   - 组件：`APIKeyManagement`

2. **增强功能**（可选）
   - 添加使用统计
   - 实现速率限制
   - 添加审计日志
   - 支持批量操作

## 问题排查

如果API Key认证失败，检查：
1. Token是否正确（注意没有多余空格）
2. 请求头格式是否正确：`Authorization: Bearer <token>`
3. Token必须以`omind_ak_`开头
4. API Key是否已过期或被撤销
5. IP地址是否在白名单中（如果设置了）
6. 用户账号是否仍然激活

### 测试认证
```bash
# 测试API Key是否有效
curl -H "Authorization: Bearer omind_ak_your_token_here" \
     http://localhost:8000/api/v1/auth/me
```