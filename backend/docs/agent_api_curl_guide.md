# 智能体 API 调用指南 (cURL 版本)

## 概述

本文档描述了如何通过 cURL 命令调用智能体服务。所有 API 调用都需要使用 Bearer Token 认证。

## 环境变量配置

为了方便使用，建议先设置环境变量：

```bash
# API 基础配置
export AGENT_API_BASE_URL="http://localhost:8000"
export AGENT_API_KEY="agent_c794582e36607cbbdcf7fe16dffb51580d5c424f61f3b3e0e03d8494b4"
export AGENT_ID="diagnostic_agent"
```

## API 接口详解

### 1. 上传文件

上传文件供智能体对话时使用。

```bash
# 上传文件（需要提供用户名）
curl -X POST "${AGENT_API_BASE_URL}/api/chat/files/upload?user_name=api_user" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -F "file=@/path/to/document.pdf" \
  -w "\n"

# 响应示例
{
  "status": "ok",
  "msg": "文件上传成功",
  "data": {
    "file_id": "9b521165-a223-4934-8f35-ae2021a831a9",
    "file_name": "document.pdf",
    "file_size": 1024000
  },
  "code": 200
}
```

### 2. 创建会话

在开始对话前，需要先创建一个会话（thread）。

```bash
# 创建新会话
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "source": "api",
      "client_version": "1.0"
    }
  }' \
  -w "\n"

# 响应示例
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-20T10:00:00",
  "metadata": {
    "source": "api",
    "client_version": "1.0"
  }
}

# 保存 thread_id 供后续使用
export THREAD_ID="550e8400-e29b-41d4-a716-446655440000"
```

### 3. 发送对话消息（流式）

发送消息并接收流式响应。

```bash
# 发送消息（无文件）
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "你好，请介绍一下你自己",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat"
      }
    },
    "stream_mode": ["messages-tuple", "values", "updates"],
    "assistant_id": "'${AGENT_ID}'",
    "on_disconnect": "cancel"
  }' \
  --no-buffer

# 发送消息（带文件）
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "请帮我分析一下上传的文档",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat",
        "file_ids": ["9b521165-a223-4934-8f35-ae2021a831a9"]
      }
    },
    "stream_mode": ["messages-tuple", "values", "updates"],
    "assistant_id": "'${AGENT_ID}'",
    "on_disconnect": "cancel"
  }' \
  --no-buffer
```

流式响应示例：
```
event: values
data: {"messages": [{"type": "human", "content": "你好"}]}

event: updates
data: {"agent": {"messages": [{"type": "ai", "content": "你好！我是诊断助手..."}]}}

event: end
data: {"status": "completed"}
```

### 4. 发送对话消息（非流式）

如果不需要流式响应，可以使用非流式接口。

```bash
# 发送消息（非流式）
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/invoke" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "你好，请介绍一下你自己",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat"
      }
    },
    "assistant_id": "'${AGENT_ID}'"
  }' \
  -w "\n"

# 响应示例
{
  "status": "ok",
  "msg": "操作成功",
  "data": {
    "thread_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "last_message": {
      "content": "你好！我是一个智能诊断助手...",
      "type": "ai"
    }
  },
  "code": 200
}
```

### 5. 取消正在进行的对话

当需要中断正在进行的对话时使用。

```bash
# 取消对话
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/cancel" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -w "\n"

# 响应示例
{
  "status": "ok",
  "msg": "对话已取消",
  "code": 200
}
```

### 6. 获取会话历史

获取指定会话的历史消息。

```bash
# 获取历史消息
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/history" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\n"

# 响应示例（精简版）
[
  {
    "values": {
      "messages": [
        {
          "type": "human",
          "content": "你好",
          "id": "1234567890"
        },
        {
          "type": "ai",
          "content": "你好！我是诊断助手...",
          "id": "1234567891"
        }
      ]
    },
    "checkpoint": {
      "thread_id": "550e8400-e29b-41d4-a716-446655440000",
      "checkpoint_id": "xxx"
    }
  }
]
```

### 7. 获取用户的所有会话

获取特定用户的所有会话列表。

```bash
# 获取用户会话列表
curl -X GET "${AGENT_API_BASE_URL}/api/chat/users/api_user/threads?limit=20&offset=0&agent_id=${AGENT_ID}" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -w "\n"

# 响应示例
{
  "user_name": "api_user",
  "threads": [
    {
      "thread_id": "550e8400-e29b-41d4-a716-446655440000",
      "thread_title": "你好，请介绍一下你自己...",
      "create_at": "2024-01-20T10:00:00",
      "update_at": "2024-01-20T10:05:00"
    }
  ],
  "total": 1
}
```

## 完整使用示例

创建一个完整的对话流程脚本 `agent_chat.sh`：

```bash
#!/bin/bash

# 配置
export AGENT_API_BASE_URL="http://localhost:8000"
export AGENT_API_KEY="agent_c794582e36607cbbdcf7fe16dffb51580d5c424f61f3b3e0e03d8494b4"
export AGENT_ID="diagnostic_agent"

echo "🚀 开始智能体对话测试..."

# 1. 创建会话
echo -e "\n1️⃣ 创建新会话..."
THREAD_RESPONSE=$(curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {}}')

export THREAD_ID=$(echo $THREAD_RESPONSE | jq -r '.thread_id')
echo "   ✅ 会话创建成功: $THREAD_ID"

# 2. 发送消息
echo -e "\n2️⃣ 发送消息..."
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [{
        "type": "human",
        "content": "你好，请简单介绍一下你自己",
        "id": "'$(date +%s%3N)'"
      }],
      "user_name": "api_user"
    },
    "config": {
      "configurable": {
        "selected_model": "deepseek-chat"
      }
    },
    "stream_mode": ["messages-tuple", "values", "updates"],
    "assistant_id": "'${AGENT_ID}'",
    "on_disconnect": "cancel"
  }' \
  --no-buffer 2>/dev/null | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        # 提取并显示 AI 响应
        echo "$line" | sed 's/^data: //' | jq -r 'select(.messages) | .messages[] | select(.type == "ai") | .content' 2>/dev/null || true
    fi
done

# 3. 获取历史
echo -e "\n\n3️⃣ 获取会话历史..."
curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/history" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.[0].values.messages | length' | xargs -I {} echo "   ✅ 历史消息数量: {}"

echo -e "\n✅ 测试完成！"
```

## 高级用法

### 1. 使用 jq 处理响应

```bash
# 提取文件ID
FILE_ID=$(curl -s -X POST "${AGENT_API_BASE_URL}/api/v1/agents/files/upload" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -F "file=@document.pdf" | jq -r '.data.file_id')

# 提取最新的 AI 响应
curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/history" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.[0].values.messages | map(select(.type == "ai")) | last | .content'
```

### 2. 处理流式响应

```bash
# 使用 awk 处理 SSE 流
curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"assistant_id": "'${AGENT_ID}'", "input": {"messages": [{"type": "human", "content": "Hello"}]}}' \
  --no-buffer | awk '
    /^event:/ { event = $2 }
    /^data:/ { 
      if (event == "end") exit;
      gsub(/^data: /, "");
      print 
    }'
```

### 3. 并行处理多个会话

```bash
# 创建多个会话并行对话
for i in {1..3}; do
  (
    THREAD_ID=$(curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads" \
      -H "Authorization: Bearer ${AGENT_API_KEY}" \
      -H "Content-Type: application/json" \
      -d '{"metadata": {}}' | jq -r '.thread_id')
    
    echo "Thread $i: $THREAD_ID"
    
    curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/invoke" \
      -H "Authorization: Bearer ${AGENT_API_KEY}" \
      -H "Content-Type: application/json" \
      -d '{
        "assistant_id": "'${AGENT_ID}'",
        "input": {"messages": [{"type": "human", "content": "What is '${i}' + '${i}'?"}]}
      }' | jq -r '.data.last_message.content'
  ) &
done
wait
```

## 错误处理

### 检查响应状态

```bash
# 使用 -w 选项获取 HTTP 状态码
HTTP_CODE=$(curl -s -X POST "${AGENT_API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {}}' \
  -w "%{http_code}" \
  -o response.json)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 请求成功"
    THREAD_ID=$(cat response.json | jq -r '.thread_id')
else
    echo "❌ 请求失败，状态码: $HTTP_CODE"
    cat response.json | jq '.'
fi
```

### 超时处理

```bash
# 设置超时时间
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"assistant_id": "'${AGENT_ID}'", "input": {"messages": [{"type": "human", "content": "Hello"}]}}' \
  --max-time 60 \
  --connect-timeout 10
```

## 调试技巧

### 1. 详细输出

```bash
# 使用 -v 查看请求详情
curl -v -X POST "${AGENT_API_BASE_URL}/api/chat/threads" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {}}'
```

### 2. 保存请求和响应

```bash
# 保存完整的请求和响应用于调试
curl -X POST "${AGENT_API_BASE_URL}/api/chat/threads/${THREAD_ID}/runs/stream" \
  -H "Authorization: Bearer ${AGENT_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @request.json \
  --trace-ascii trace.txt \
  --output response.txt
```

### 3. 测试连通性

```bash
# 测试 API 服务是否可访问
curl -s -o /dev/null -w "状态码: %{http_code}\n响应时间: %{time_total}s\n" \
  "${AGENT_API_BASE_URL}/health"
```

## 注意事项

1. **密钥安全**：不要在脚本中硬编码 API 密钥，使用环境变量或配置文件
2. **错误处理**：始终检查响应状态码和错误信息
3. **超时设置**：流式接口建议设置较长的超时时间
4. **字符编码**：确保终端支持 UTF-8 以正确显示中文
5. **依赖工具**：需要安装 `jq` 用于 JSON 处理

## 常见问题

### Q: 如何在 Windows 上使用？
A: 可以使用 Git Bash 或 WSL，或将 curl 命令转换为 PowerShell 的 Invoke-WebRequest。

### Q: 如何处理证书问题？
A: 开发环境可以使用 `-k` 或 `--insecure` 选项跳过证书验证（生产环境不推荐）。

### Q: 如何保存会话用于后续使用？
A: 将 thread_id 保存到文件：
```bash
echo "$THREAD_ID" > .thread_id
THREAD_ID=$(cat .thread_id)
```