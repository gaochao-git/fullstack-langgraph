# 智能体 API 完整测试指南

本文档提供了使用 cURL 命令测试智能体 API 的完整流程，包括认证、文件上传、对话等功能。

## 前置准备

### 1. 设置环境变量

```bash
# API 基础配置
export API_BASE_URL="http://localhost:8000"
export AGENT_KEY="sk-abcdefghijklmnopqrstuvwxyz123"
export AGENT_ID="diagnostic_agent"
```

### 2. 认证说明

系统支持两种认证方式：

1. **agent_key 认证**（API调用）
   - Bearer token 格式：`Bearer sk-xxxxx`
   - 必须在请求中提供 `user_name` 参数
   - 用于程序化API调用

2. **JWT 认证**（页面调用）
   - Bearer token 格式：`Bearer eyJhbGci...`
   - `user_name` 参数可选，默认使用当前登录用户
   - 用于前端页面调用

## 完整测试流程

### Step 1: 创建会话（Thread）

```bash
# 创建新会话
curl -X POST "${API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"source": "api", "version": "1.0"}}' | jq .

# 响应示例
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-20T10:00:00",
  "metadata": {
    "source": "api",
    "version": "1.0"
  }
}

# 保存 thread_id 供后续使用
export THREAD_ID="550e8400-e29b-41d4-a716-446655440000"
```

### Step 2: 上传文件（可选）

```bash
# 创建测试文件
cat > test_document.txt << EOF
这是一个测试文档。
包含了一些需要分析的内容。
EOF

# 上传文件（注意：agent_key认证必须提供user_name）
curl -X POST "${API_BASE_URL}/api/chat/files/upload?user_name=api_test_user" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -F "file=@test_document.txt" | jq .

# 响应示例
{
  "status": "ok",
  "msg": "文件上传成功",
  "data": {
    "file_id": "9b521165-a223-4934-8f35-ae2021a831a9",
    "file_name": "test_document.txt",
    "file_size": 89,
    "file_type": ".txt",
    "upload_time": "2025-01-20T10:01:00",
    "status": "uploaded"
  },
  "code": 200
}

# 保存文件ID
export FILE_ID="9b521165-a223-4934-8f35-ae2021a831a9"
```

### Step 3: 发送对话消息（流式响应）

#### 3.1 不带文件的对话

```bash
# 发送简单消息（注意user_name在input中）
curl -X POST "${API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "你好，请介绍一下你自己",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_test_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat"
      }
    },
    "stream_mode": ["values"],
    "assistant_id": "'${AGENT_ID}'",
    "on_disconnect": "cancel"
  }' \
  --no-buffer

# 流式响应示例
event: checkpoints
data: {"config": {"configurable": {"checkpoint_ns": "", "thread_id": "..."}}}

event: updates
data: {"agent": {"messages": [{"type": "ai", "content": "你好！我是诊断助手..."}]}}

event: end
data: {"status": "completed"}
```

#### 3.2 带文件的对话

```bash
# 发送带文件引用的消息
curl -X POST "${API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "请分析一下上传的文档内容",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_test_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat",
        "file_ids": ["'${FILE_ID}'"]
      }
    },
    "stream_mode": ["values"],
    "assistant_id": "'${AGENT_ID}'",
    "on_disconnect": "cancel"
  }' \
  --no-buffer
```

### Step 4: 非流式调用（可选）

如果不需要流式响应，可以使用 invoke 接口：

```bash
# 非流式调用
curl -X POST "${API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/invoke" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "计算 1+1 等于多少",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_test_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat"
      }
    },
    "assistant_id": "'${AGENT_ID}'"
  }' | jq .

# 响应示例
{
  "status": "ok",
  "msg": "操作成功",
  "data": {
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "last_message": {
      "content": "1+1 等于 2",
      "type": "ai"
    }
  },
  "code": 200
}
```

### Step 5: 获取会话历史

```bash
# 获取会话历史
curl -X POST "${API_BASE_URL}/api/chat/threads/${THREAD_ID}/history" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .

# 响应包含所有历史消息
[
  {
    "values": {
      "messages": [
        {
          "type": "human",
          "content": "你好，请介绍一下你自己",
          "id": "1234567890"
        },
        {
          "type": "ai",
          "content": "你好！我是一个诊断助手...",
          "id": "1234567891"
        }
      ]
    }
  }
]
```

### Step 6: 获取用户的所有会话

```bash
# 获取特定用户的会话列表
curl -X GET "${API_BASE_URL}/api/chat/users/api_test_user/threads?limit=10&offset=0&agent_id=${AGENT_ID}" \
  -H "Authorization: Bearer ${AGENT_KEY}" | jq .

# 响应示例
{
  "user_name": "api_test_user",
  "threads": [
    {
      "thread_id": "550e8400-e29b-41d4-a716-446655440000",
      "thread_title": "你好，请介绍一下你自己...",
      "create_at": "2025-01-20T10:00:00",
      "update_at": "2025-01-20T10:05:00"
    }
  ],
  "total": 1
}
```

## 错误处理示例

### 1. 缺少 user_name（agent_key 认证）

```bash
# 错误示例：agent_key认证未提供user_name
curl -X POST "${API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{"type": "human", "content": "test"}]
    },
    "assistant_id": "'${AGENT_ID}'"
  }'

# 错误响应
event: error
data: {"error": "使用agent_key认证时必须提供user_name"}
```

### 2. 无效的 agent_key

```bash
# 错误的 agent_key
curl -X POST "${API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer sk_invalid_key" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {}}'

# 错误响应
{
  "status": "error",
  "msg": "未提供有效的认证凭据",
  "code": 401
}
```

### 3. 文件上传错误

```bash
# 错误：文件太大
curl -X POST "${API_BASE_URL}/api/chat/files/upload?user_name=api_test_user" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -F "file=@large_file.pdf"

# 错误响应
{
  "status": "error",
  "msg": "文件大小超过限制（最大10MB）",
  "code": 400
}
```

## 完整测试脚本

创建 `test_agent_api.sh`：

```bash
#!/bin/bash

# 配置
API_BASE_URL="http://localhost:8000"
AGENT_KEY="sk-abcdefghijklmnopqrstuvwxyz123"
AGENT_ID="diagnostic_agent"
USER_NAME="api_test_user"

echo "🚀 开始测试智能体 API..."

# 1. 创建会话
echo -e "\n1️⃣ 创建会话..."
THREAD_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {}}')

THREAD_ID=$(echo $THREAD_RESPONSE | jq -r '.thread_id')
echo "✅ 会话创建成功: $THREAD_ID"

# 2. 上传文件
echo -e "\n2️⃣ 上传文件..."
echo "这是测试文档内容" > test.txt
FILE_RESPONSE=$(curl -s -X POST "${API_BASE_URL}/api/chat/files/upload?user_name=${USER_NAME}" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -F "file=@test.txt")

FILE_ID=$(echo $FILE_RESPONSE | jq -r '.data.file_id')
echo "✅ 文件上传成功: $FILE_ID"

# 3. 发送消息
echo -e "\n3️⃣ 发送消息..."
curl -X POST "${API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "分析一下上传的文档",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "'${USER_NAME}'"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat",
        "file_ids": ["'${FILE_ID}'"]
      }
    },
    "stream_mode": ["values"],
    "assistant_id": "'${AGENT_ID}'"
  }' \
  --no-buffer | head -20

# 清理
rm -f test.txt

echo -e "\n\n✅ 测试完成！"
```

## 注意事项

1. **认证要求**
   - agent_key 认证必须提供 `user_name` 参数
   - JWT 认证可选提供 `user_name`，默认使用登录用户

2. **文件处理**
   - 上传的文件需要时间处理，建议等待1-2秒
   - 文件大小限制默认为 10MB

3. **流式响应**
   - 使用 `--no-buffer` 参数实时接收流式数据
   - 设置合适的超时时间（建议60秒以上）

4. **错误处理**
   - 所有错误响应都使用统一格式
   - HTTP 状态码始终为 200，通过响应体中的 `code` 判断实际状态

5. **并发限制**
   - 建议控制并发请求数量
   - 大量请求时注意添加适当延迟