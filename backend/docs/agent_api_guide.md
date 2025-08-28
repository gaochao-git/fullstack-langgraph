# 智能体 API 调用指南

## 概述

本文档描述了如何通过 API 调用智能体服务。所有 API 调用都需要使用 Bearer Token 认证。

## 认证方式

所有 API 请求都需要在 HTTP Header 中包含认证信息：

```python
headers = {
    "Authorization": f"Bearer {AGENT_API_KEY}",
    "Content-Type": "application/json"
}
```

其中 `AGENT_API_KEY` 格式为：`agent_xxxxxxxxxxxx`（以 `agent_` 开头的密钥）

## 基础配置

```python
import requests
import json
from datetime import datetime

# API 基础配置
AGENT_API_BASE_URL = "http://localhost:8000"  # 后端服务地址
AGENT_API_KEY = "agent_c794582e36607cbbdcf7fe16dffb51580d5c424f61f3b3e0e03d8494b4"  # 替换为您的智能体密钥

# 通用请求头
HEADERS = {
    "Authorization": f"Bearer {AGENT_API_KEY}",
    "Content-Type": "application/json"
}
```

## API 接口详解

### 1. 上传文件

上传文件供智能体对话时使用。

```python
def upload_file(file_path, user_name="api_user"):
    """上传文件到智能体"""
    url = f"{AGENT_API_BASE_URL}/api/chat/files/upload"
    
    # 添加用户名参数
    params = {"user_name": user_name}
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        headers = {"Authorization": f"Bearer {AGENT_API_KEY}"}  # 文件上传不需要 Content-Type
        
        response = requests.post(url, files=files, headers=headers, params=params, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        file_id = result['data']['file_id']
        print(f"文件上传成功，file_id: {file_id}")
        return file_id
    else:
        print(f"文件上传失败: {response.text}")
        return None

# 使用示例
file_id = upload_file("/path/to/document.pdf")
```

### 2. 创建会话

在开始对话前，需要先创建一个会话（thread）。

```python
def create_thread():
    """创建新的对话会话"""
    url = f"{AGENT_API_BASE_URL}/api/chat/threads"
    
    payload = {
        "metadata": {
            "source": "api",
            "client_version": "1.0"
        }
    }
    
    response = requests.post(url, json=payload, headers=HEADERS, timeout=10)
    
    if response.status_code == 200:
        thread_data = response.json()
        thread_id = thread_data.get("thread_id")
        print(f"会话创建成功，thread_id: {thread_id}")
        return thread_id
    else:
        print(f"会话创建失败: {response.text}")
        return None

# 使用示例
thread_id = create_thread()
```

### 3. 发送对话消息（流式）

发送消息并接收流式响应。

```python
def send_message_stream(thread_id, message, agent_id, file_ids=None, model="deepseek-chat"):
    """发送消息到智能体（流式响应）"""
    url = f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/runs/stream"
    
    # 构建配置
    config = {
        "configurable": {
            "selected_model": model
        }
    }
    
    # 如果有文件，添加文件ID
    if file_ids:
        config["configurable"]["file_ids"] = file_ids
    
    payload = {
        "input": {
            "messages": [{
                "type": "human",
                "content": message,
                "id": str(int(datetime.now().timestamp() * 1000))
            }],
            "user_name": "api_user"  # API调用的用户标识
        },
        "config": config,
        "stream_mode": ["messages-tuple", "values", "updates"],
        "assistant_id": agent_id,  # 智能体ID，如 "diagnostic_agent"
        "on_disconnect": "cancel"
    }
    
    # 发送流式请求
    response = requests.post(url, json=payload, headers=HEADERS, stream=True, timeout=60)
    
    if response.status_code == 200:
        # 处理流式响应
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        # 处理不同类型的事件
                        if 'messages' in data:
                            for msg in data['messages']:
                                if msg.get('type') == 'ai':
                                    print(f"AI: {msg.get('content', '')}")
                    except json.JSONDecodeError:
                        pass
                elif line_str.startswith('event: '):
                    event_type = line_str[7:]
                    if event_type == 'end':
                        print("对话结束")
                        break
    else:
        print(f"请求失败: {response.text}")

# 使用示例
send_message_stream(
    thread_id=thread_id,
    message="请帮我分析一下这个文档",
    agent_id="diagnostic_agent",
    file_ids=[file_id] if file_id else None
)
```

### 4. 发送对话消息（非流式）

如果不需要流式响应，可以使用非流式接口。

```python
def send_message_invoke(thread_id, message, agent_id, file_ids=None, model="deepseek-chat"):
    """发送消息到智能体（非流式响应）"""
    url = f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/runs/invoke"
    
    config = {
        "configurable": {
            "selected_model": model
        }
    }
    
    if file_ids:
        config["configurable"]["file_ids"] = file_ids
    
    payload = {
        "input": {
            "messages": [{
                "type": "human",
                "content": message,
                "id": str(int(datetime.now().timestamp() * 1000))
            }],
            "user_name": "api_user"
        },
        "config": config,
        "assistant_id": agent_id
    }
    
    response = requests.post(url, json=payload, headers=HEADERS, timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'ok':
            data = result.get('data', {})
            last_message = data.get('last_message', {})
            print(f"AI响应: {last_message.get('content', '无响应')}")
            return data
    else:
        print(f"请求失败: {response.text}")
        return None
```

### 5. 取消正在进行的对话

当需要中断正在进行的对话时使用。

```python
def cancel_conversation(thread_id):
    """取消正在进行的对话"""
    url = f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/runs/cancel"
    
    response = requests.post(url, headers=HEADERS, timeout=10)
    
    if response.status_code == 200:
        print("对话已取消")
        return True
    else:
        print(f"取消失败: {response.text}")
        return False
```

### 6. 获取会话历史

获取指定会话的历史消息。

```python
def get_thread_history(thread_id):
    """获取会话历史消息"""
    url = f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/history"
    
    response = requests.post(url, json={}, headers=HEADERS, timeout=10)
    
    if response.status_code == 200:
        history = response.json()
        if isinstance(history, list) and history:
            messages = history[0].get('values', {}).get('messages', [])
            for msg in messages:
                msg_type = msg.get('type', 'unknown')
                content = msg.get('content', '')
                print(f"{msg_type.upper()}: {content}")
        return history
    else:
        print(f"获取历史失败: {response.text}")
        return None
```

### 7. 获取用户的所有会话

获取特定用户的所有会话列表。

```python
def get_user_threads(user_name="api_user", agent_id=None, limit=20, offset=0):
    """获取用户的所有会话"""
    url = f"{AGENT_API_BASE_URL}/api/chat/users/{user_name}/threads"
    
    params = {
        "limit": limit,
        "offset": offset
    }
    
    if agent_id:
        params["agent_id"] = agent_id
    
    response = requests.get(url, params=params, headers=HEADERS, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        threads = result.get('threads', [])
        print(f"找到 {len(threads)} 个会话")
        for thread in threads:
            print(f"- {thread['thread_id']}: {thread.get('thread_title', '未命名')}")
        return threads
    else:
        print(f"获取会话列表失败: {response.text}")
        return []
```

## 完整示例

以下是一个完整的使用示例：

```python
import requests
import json
from datetime import datetime
import time

# 配置
AGENT_API_BASE_URL = "http://localhost:8000"
AGENT_API_KEY = "agent_your_key_here"
AGENT_ID = "diagnostic_agent"

# 通用请求头
HEADERS = {
    "Authorization": f"Bearer {AGENT_API_KEY}",
    "Content-Type": "application/json"
}

def main():
    # 1. 创建会话
    print("1. 创建会话...")
    thread_response = requests.post(
        f"{AGENT_API_BASE_URL}/api/chat/threads",
        json={"metadata": {}},
        headers=HEADERS
    )
    thread_id = thread_response.json().get("thread_id")
    print(f"   会话ID: {thread_id}")
    
    # 2. 上传文件（可选）
    # file_id = upload_file("document.pdf")
    
    # 3. 发送消息
    print("\n2. 发送消息...")
    payload = {
        "input": {
            "messages": [{
                "type": "human",
                "content": "你好，请介绍一下你自己",
                "id": str(int(datetime.now().timestamp() * 1000))
            }],
            "user_name": "api_user"
        },
        "config": {
            "configurable": {
                "selected_model": "deepseek-chat"
            }
        },
        "stream_mode": ["messages-tuple", "values", "updates"],
        "assistant_id": AGENT_ID,
        "on_disconnect": "cancel"
    }
    
    response = requests.post(
        f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/runs/stream",
        json=payload,
        headers=HEADERS,
        stream=True
    )
    
    # 处理流式响应
    print("\n3. 接收响应:")
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])
                    # 提取AI响应
                    if isinstance(data, list) and len(data) > 1:
                        for item in data:
                            if isinstance(item, dict) and item.get('type') == 'ai':
                                print(f"   AI: {item.get('content', '')}")
                except:
                    pass
    
    # 4. 获取历史
    print("\n4. 获取会话历史...")
    history_response = requests.post(
        f"{AGENT_API_BASE_URL}/api/chat/threads/{thread_id}/history",
        json={},
        headers=HEADERS
    )
    print("   历史消息获取成功")

if __name__ == "__main__":
    main()
```

## 错误处理

### 常见错误码

- `401`: 未授权 - 检查 Bearer Token 是否正确
- `461`: 智能体密钥错误 - 确认使用正确的 agent_key
- `404`: 资源不存在 - 检查 thread_id 或 agent_id
- `500`: 服务器内部错误

### 错误响应格式

```json
{
    "status": "error",
    "msg": "错误信息",
    "code": 461,
    "data": null
}
```

## 注意事项

1. **密钥安全**：请妥善保管您的 `agent_key`，不要在客户端代码中暴露
2. **超时设置**：流式接口建议设置较长的超时时间（60秒以上）
3. **并发限制**：请注意 API 的并发调用限制
4. **文件大小**：上传文件大小限制为 10MB
5. **会话管理**：长时间未使用的会话可能会被清理

## 支持的模型

当前支持的模型包括：
- `deepseek-chat`
- `gpt-4o`
- `gpt-4o-mini`
- 其他配置的模型

## 联系支持

如有问题，请联系技术支持团队。