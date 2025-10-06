# Mem0 记忆层级深度调研报告

基于Mem0官方文档和业界最佳实践的完整指南

---

## 一、Mem0 记忆架构概述

### 1.1 核心概念

Mem0 ("mem-zero") 是一个智能记忆层，为AI智能体提供持久化、个性化的记忆能力。它通过多层级记忆架构，实现了跨会话、跨时间的上下文保持和个性化交互。

**核心优势**:
- 🎯 **高精度**: 比OpenAI Memory准确率提升26%
- ⚡ **低延迟**: 延迟降低91%，平均1.44秒响应
- 💰 **省Token**: Token使用量减少90%

### 1.2 记忆作用域层级

Mem0 提供4个层级的记忆作用域（从大到小）:

```
Application (app_id)          # 应用级别
    ├── Agent (agent_id)      # 智能体级别
    ├── User (user_id)        # 用户级别
    └── Thread (run_id)       # 会话/线程级别
```

---

## 二、记忆层级详解

### 2.1 强制规则

**至少必须提供一个标识符**: `user_id`、`agent_id` 或 `run_id`

源码验证:
```python
if not any(key in effective_filters for key in ("user_id", "agent_id", "run_id")):
    raise ValueError("At least one identifier must be specified")
```

### 2.2 四种记忆层级组合

根据官方文档和源码分析，Mem0支持以下层级组合:

| 层级 | 参数组合 | 作用域 | 持久性 | 典型用途 |
|------|---------|--------|--------|----------|
| **1. 用户全局记忆** | `user_id` | 跨所有智能体和会话 | 永久 | 用户画像、偏好、个人信息 |
| **2. 智能体全局记忆** | `agent_id` | 跨所有用户和会话 | 永久 | 智能体知识库、通用规则 |
| **3. 用户-智能体交互记忆** | `user_id` + `agent_id` | 特定用户与智能体 | 长期 | 个性化交互历史 |
| **4. 会话记忆** | `user_id` + `agent_id` + `run_id` | 单次会话线程 | 短期 | 会话上下文、临时状态 |

---

## 三、各层级应该存储什么内容

### ⚠️ 重要说明：内容提取由Mem0内部LLM自动决定

**关键发现**: 存储什么内容**不是我们手动控制的**，而是Mem0内部的LLM根据以下逻辑自动决定：

1. **基于消息角色过滤**:
   - `user_id`层：主要从**user角色消息**中提取，但可能受assistant消息影响以获取上下文
   - `agent_id`层：主要从**assistant/system角色消息**中提取，但可能受user消息影响

2. **基于FACT_RETRIEVAL_PROMPT**:
   - Mem0使用内置的`FACT_RETRIEVAL_PROMPT`指导LLM提取7类信息
   - 可以通过`custom_fact_extraction_prompt`自定义提取规则

3. **自动推理（infer=True）**:
   - LLM自动决定ADD（新增）、UPDATE（更新）、DELETE（删除）操作
   - 自动去重、合并相似记忆

**源码验证**:
```python
# 官方文档说明
"When passing user_id, memories are primarily created based on user messages,
but may be influenced by assistant messages for contextual understanding."

"When using agent_id, assistant messages are prioritized,
but user messages might influence the agent's memories based on context."
```

---

### 3.1 用户全局记忆 (`user_id`)

**定义**: 仅使用`user_id`参数，不指定`agent_id`

**Mem0内部逻辑**:
- 主要从**"role": "user"**的消息中提取
- LLM会分析上下文，可能也参考assistant消息来理解用户意图

**存储内容示例**:
- ✅ **个人信息**: 姓名、年龄、职业、地理位置
- ✅ **偏好设置**:
  - "我是素食主义者，对坚果过敏"
  - "我更喜欢靠窗的座位"
  - "我需要视频字幕，是视觉学习者"
- ✅ **长期目标**:
  - "体重72kg，目标蛋白质130g/天"
  - "目标20个引体向上"
- ✅ **历史事件**: 重要的个人经历、决策

**官方示例**:
```python
messages = [
    {"role": "user", "content": "I'm Sarah. I prefer visual learning and need closed captions for videos."},
    {"role": "assistant", "content": "Hi Sarah! I understand you're a visual learner and require closed captions."}
]
client.add(messages, user_id="sarah", output_format="v1.1")
```

**最佳实践**:
- 存储**跨智能体通用**的用户属性
- 关注**长期稳定**的特征
- 避免存储会话临时信息

---

### 3.2 智能体全局记忆 (`agent_id`)

**定义**: 仅使用`agent_id`参数，`user_id=None`

**Mem0内部逻辑**:
- 主要从**"role": "assistant"**或**"role": "system"**的消息中提取
- LLM可能也参考user消息来理解智能体学习的上下文

**存储内容示例**:
- ✅ **领域知识**: 智能体学习的专业知识
- ✅ **工作规则**:
  - 诊断流程、SOP步骤
  - 工具使用规范
- ✅ **常见模式**:
  - 频繁出现的问题和解决方案
  - 最佳实践总结
- ✅ **能力边界**: 智能体能做和不能做的事情

**官方示例**:
```python
# 共享知识库场景 - 仅指定agent_id
memory.add(
    messages=conversation,
    agent_id="work_assistant",
    user_id=None  # 明确设置为None
)
```

**最佳实践**:
- 存储**所有用户共享**的知识
- 关注智能体的**持续学习**和**能力提升**
- 避免用户特定信息

---

### 3.3 用户-智能体交互记忆 (`user_id` + `agent_id`)

**定义**: 同时指定`user_id`和`agent_id`，不指定`run_id`

**Mem0内部逻辑**:
- **user角色**和**assistant角色**消息**都会被LLM分析**
- LLM会提取两者交互中的关键信息

**官方说明**:
> "When you provide both `user_id` and `agent_id`, Mem0 will store memories for both identifiers separately"

**存储内容示例**:
- ✅ **个性化交互历史**:
  - 特定用户与智能体的对话模式
  - 用户在该智能体中的偏好
- ✅ **问题解决记录**:
  - 该用户遇到的问题和解决方案
  - 反复出现的话题
- ✅ **上下文积累**:
  - 长期对话中建立的共识
  - 用户特定的术语或缩写

**应用场景**:
- 🏥 **医疗**: 患者与医疗助手的历史记录
- 💼 **销售**: 客户与销售助手的沟通历史
- 🎓 **教育**: 学生与教学助手的学习轨迹

**最佳实践**:
- 存储**跨会话但特定于用户-智能体关系**的信息
- 关注**长期交互模式**和**个性化适应**
- 避免单次会话的临时内容

---

### 3.4 会话记忆 (`user_id` + `agent_id` + `run_id`)

**定义**: 同时指定`user_id`、`agent_id`和`run_id`（即thread_id）

**作用域**: 短期会话/线程上下文

**官方说明**:
> "For short term memories, you need to include either a user_id or agent_id and a run_id"

**存储内容示例**:
- ✅ **会话上下文**:
  - 当前讨论的主题
  - 会话中的临时决策
- ✅ **任务进度**:
  - 多步骤任务的执行状态
  - 中间结果和临时数据
- ✅ **会话特定偏好**:
  - "本次对话请用英文回复"
  - "这次先分析A方案"

**官方示例**:
```python
# 会话级记忆 - 短期存储
client.add(
    messages,
    user_id="alex123",
    run_id="trip-planning-2024",  # 特定会话ID
    output_format="v1.1"
)
```

**应用场景**:
- 📞 **客户支持**: 单次支持会话的问题细节
- 🗺️ **旅行规划**: 特定行程规划会话的偏好
- 🔧 **故障诊断**: 单次诊断会话的步骤和发现

**最佳实践**:
- 存储**仅在本会话有效**的信息
- 会话结束后可能被清理
- 关注**临时状态**和**上下文连续性**

**注意**: 在我们的系统中，`run_id` 即 `thread_id`（LangGraph的会话线程ID）

---

## 四、Mem0内部工作原理

### 4.1 FACT_RETRIEVAL_PROMPT

Mem0使用内置的`FACT_RETRIEVAL_PROMPT`来指导LLM提取记忆，包含7大类别：

1. **个人偏好** (Personal Preferences): 食物、活动、娱乐
2. **重要细节** (Important Details): 个人关键信息
3. **计划与意图** (Plans and Intentions): 未来目标和计划
4. **服务偏好** (Service Preferences): 对服务的偏好
5. **健康信息** (Health): 健康和健身相关
6. **职业上下文** (Professional): 工作相关信息
7. **其他细节** (Miscellaneous): 其他个人细节

**提取示例**:
```
Input: "Yesterday, I had a meeting with John at 3pm. We discussed the new project."
Extracted Facts:
- "Had a meeting with John at 3pm"
- "Discussed the new project"
```

### 4.2 自定义提取规则（Custom Prompts）

**是的！Mem0支持两种自定义prompt来控制记忆管理流程。**

#### 两种自定义Prompt的区别

| Prompt类型 | 作用时机 | 功能 | 输出 |
|-----------|---------|------|------|
| `custom_fact_extraction_prompt` | **提取阶段** | 从对话中提取哪些事实 | `{"facts": [...]}` |
| `custom_update_memory_prompt` | **更新阶段** | 如何处理提取的事实（ADD/UPDATE/DELETE） | `{"id": "...", "event": "ADD/UPDATE/DELETE/NONE"}` |

**工作流程**：
```
对话消息
  ↓
【提取阶段】custom_fact_extraction_prompt → 提取事实
  ↓
【更新阶段】custom_update_memory_prompt → 决定ADD/UPDATE/DELETE
  ↓
存储到向量数据库
```

---

#### 4.2.1 Custom Fact Extraction Prompt（提取规则）

**作用**：控制从对话中提取**哪些**事实

**基本用法**

```python
from mem0 import Memory

# 定义自定义提取规则
custom_prompt = """
请只提取包含客户支持信息、订单详情和用户信息的实体。

以下是一些few-shot示例：

Input: Hi.
Output: {"facts": []}

Input: The weather is nice today.
Output: {"facts": []}

Input: My order #12345 hasn't arrived yet.
Output: {"facts": ["Order #12345 not received"]}

Input: I'm John Doe, and I'd like to return the shoes I bought last week.
Output: {"facts": ["Customer name: John Doe", "Wants to return shoes", "Purchase made last week"]}

Input: I ordered a red shirt, size medium, but received a blue one instead.
Output: {"facts": ["Ordered red shirt, size medium", "Received blue shirt instead"]}

请以JSON格式返回事实和客户信息，如上所示。
"""

# 配置Memory
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o",
            "temperature": 0.2,
            "max_tokens": 1500,
        }
    },
    "custom_fact_extraction_prompt": custom_prompt,  # 关键参数
    "version": "v1.1"
}

# 初始化
memory = Memory.from_config(config=config)
```

#### 4.2.2 最佳实践

创建有效的自定义提取规则：

1. **明确指定要提取的信息类型**
   ```python
   "请只提取与[具体领域]相关的实体信息"
   ```

2. **提供充分的few-shot示例**
   - 包含**正面示例**（应该提取什么）
   - 包含**负面示例**（应该忽略什么）
   - 至少3-5个示例

3. **使用一致的JSON格式**
   ```python
   Output: {"facts": ["fact1", "fact2", ...]}
   ```

4. **指导LLM的提取策略**
   - 针对不同层级可以使用不同的prompt
   - 明确说明长期 vs 短期信息的区分

#### 4.2.3 针对不同层级的自定义（高级）

虽然Mem0目前不直接支持针对`user_id`和`agent_id`使用不同的prompt，但可以通过以下方式实现：

**方案1：在prompt中明确角色**
```python
custom_prompt = """
根据消息角色提取不同内容：
- 如果是用户消息（role: user）：提取用户的偏好、需求、个人信息
- 如果是助手消息（role: assistant）：提取助手学到的知识、规则、最佳实践

示例：
Input (role: user): "我是素食主义者"
Output: {"facts": ["User is vegetarian"]}

Input (role: assistant): "根据最佳实践，数据库连接池应该设置为20"
Output: {"facts": ["Best practice: DB connection pool should be 20"]}
"""
```

**方案2：创建多个Memory实例**
```python
# 用户记忆实例 - 侧重用户偏好
user_memory_config = {
    "custom_fact_extraction_prompt": "只提取用户的个人信息、偏好和需求...",
    ...
}
user_memory = Memory.from_config(user_memory_config)

# 智能体记忆实例 - 侧重知识和规则
agent_memory_config = {
    "custom_fact_extraction_prompt": "只提取专业知识、规则和最佳实践...",
    ...
}
agent_memory = Memory.from_config(agent_memory_config)
```

#### 4.2.4 IT运维诊断场景的自定义示例

```python
ops_diagnostic_prompt = """
请从运维诊断对话中提取以下类型的信息：

1. **系统信息**：服务器配置、软件版本、架构信息
2. **故障现象**：错误信息、性能指标、异常行为
3. **诊断结果**：问题根因、解决方案、优化建议
4. **用户偏好**：习惯使用的工具、倾向的解决方式

忽略的内容：
- 日常问候（"你好"、"谢谢"等）
- 无关话题（天气、闲聊等）

示例：

Input: "你好，在吗？"
Output: {"facts": []}

Input: "我的Nginx服务器响应很慢，CPU使用率达到90%"
Output: {"facts": ["Nginx server slow response", "CPU usage at 90%"]}

Input: "经过排查，发现是worker_processes配置过低导致的"
Output: {"facts": ["Root cause: worker_processes too low", "Performance bottleneck identified"]}

Input: "我习惯用top命令监控系统"
Output: {"facts": ["User prefers using top command for monitoring"]}

以JSON格式返回提取的事实。
"""

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o",
            "temperature": 0.2
        }
    },
    "custom_fact_extraction_prompt": ops_diagnostic_prompt,
    "version": "v1.1"
}
```

#### 4.2.5 过滤机制

**关键特性**：当消息不符合自定义prompt中定义的用例时，**记忆不会被添加**。

```python
# 配置了客户支持场景的prompt
memory.add(
    messages=[{"role": "user", "content": "The weather is nice today."}],
    user_id="user123"
)
# ✅ 结果：不会保存记忆（因为与客户支持无关）

memory.add(
    messages=[{"role": "user", "content": "My order #12345 is late."}],
    user_id="user123"
)
# ✅ 结果：会保存记忆（符合订单相关信息）
```

---

#### 4.2.6 Custom Update Memory Prompt（更新规则）

**作用**：控制提取的事实**如何**更新到现有记忆

**4种更新操作**：

| 操作 | 触发条件 | 示例 |
|------|---------|------|
| **ADD** | 新信息，记忆中不存在 | 新增"用户喜欢鸡肉披萨" |
| **UPDATE** | 信息更全面，需要合并 | "喜欢奶酪披萨" → "喜欢奶酪和鸡肉披萨" |
| **DELETE** | 新信息与旧记忆矛盾 | 删除过时或错误的记忆 |
| **NONE** | 信息完全相同 | 保持不变 |

**默认行为**（无自定义prompt）：
Mem0的LLM会自动决定执行哪种操作。

**自定义用法**：

```python
custom_update_prompt = """
根据现有记忆和新信息，决定如何更新记忆：

规则：
1. 如果新信息不在现有记忆中 → ADD
2. 如果新信息更全面，可以合并 → UPDATE（保留旧ID，更新内容）
3. 如果新信息与旧记忆矛盾 → DELETE旧记忆，ADD新记忆
4. 如果新信息完全相同 → NONE（不做任何操作）

输出格式：
{
  "id": "memory_id",
  "text": "更新后的内容",
  "event": "ADD/UPDATE/DELETE/NONE",
  "old_memory": "旧内容"  // UPDATE时可选
}

示例：
现有记忆：[{"id": "mem_001", "text": "User likes cheese pizza"}]
新信息："Loves chicken pizza"
输出：{"id": "mem_001", "text": "Loves cheese and chicken pizza", "event": "UPDATE", "old_memory": "User likes cheese pizza"}
"""

config = {
    "llm": {...},
    "custom_update_memory_prompt": custom_update_prompt,
    "version": "v1.1"
}
memory = Memory.from_config(config)
```

**何时使用**：
- ✅ 需要自定义合并逻辑（如技术配置的版本管理）
- ✅ 需要控制何时删除旧记忆（如诊断结果的时效性）
- ✅ 需要精确控制更新策略（如用户偏好的优先级）

**典型场景**（运维诊断）：

```python
ops_update_prompt = """
运维诊断记忆更新规则：

1. 配置信息：UPDATE（保留历史，记录变更）
2. 故障诊断：ADD（每次故障独立记录）
3. 性能指标：UPDATE（保留趋势，更新最新值）
4. 解决方案：如果更优，UPDATE；否则ADD作为备选
5. 过时信息：DELETE（如旧版本软件的配置）

输出格式：
{"id": "...", "text": "...", "event": "ADD/UPDATE/DELETE/NONE"}
"""
```

---

### 4.3 自动推理机制（infer=True）

当`infer=True`（默认）时，Mem0的LLM会：

1. **分析消息**: 提取关键事实
2. **语义比对**: 与已有记忆进行相似度对比
3. **决定操作**:
   - **ADD**: 新增记忆（新信息）
   - **UPDATE**: 更新记忆（修正或补充）
   - **DELETE**: 删除记忆（过时或错误）

**源码验证**:
```python
# mem0/memory/main.py
"The `infer` parameter uses an LLM to extract key facts from messages
and decide whether to add, update, or delete related memories."
```

### 4.4 消息角色过滤逻辑

| 参数 | 主要来源角色 | 次要来源角色 | 说明 |
|------|------------|------------|------|
| `user_id` | `"role": "user"` | `"role": "assistant"` | 提取用户表达的内容 |
| `agent_id` | `"role": "assistant"` | `"role": "user"` | 提取智能体学习的内容 |
| `user_id + agent_id` | 两者都重要 | - | 提取交互中的关键信息 |
| `user_id/agent_id + run_id` | 会话临时上下文 | - | 提取会话特定的临时信息 |

**官方说明**:
> "When passing user_id, memories are primarily created based on user messages, but may be influenced by assistant messages for contextual understanding."

> "When using agent_id, assistant messages are prioritized, but user messages might influence the agent's memories based on context."

> "For short term memories, you need to include either a user_id or agent_id and a run_id."

### 4.5 run_id的特殊逻辑（会话记忆）

**定义**: `run_id`用于组织会话、工作流或执行上下文的临时记忆

**内部处理**:
1. **提取内容**: LLM提取会话中的**临时上下文**，而非长期事实
2. **自动重置**: 会话结束后，这些记忆可以被清理（不必持久保留）
3. **隔离存储**: 不同`run_id`的记忆相互隔离

**提取示例**:
```python
# 客户支持会话
messages = [
    {"role": "user", "content": "I'm planning a trip to Japan next month."},
    {"role": "assistant", "content": "That's exciting! Would you like some recommendations?"}
]

client.add(
    messages,
    user_id="alex123",
    run_id="trip-planning-2024",  # 会话级记忆
    output_format="v1.1"
)
```

**LLM会提取的内容**（会话特定）:
- ✅ "用户正在规划下个月去日本的旅行"（临时意图）
- ✅ "本次会话中讨论的酒店推荐"（会话上下文）
- ✅ "用户这次询问中偏好预算住宿"（临时偏好）

**LLM不会提取的内容**（应该在user_id层）:
- ❌ "用户总是喜欢预算住宿"（长期偏好 → 应该在`user_id`层）
- ❌ "用户是日本文化爱好者"（长期特征 → 应该在`user_id`层）

**官方示例**:
> "During a customer support session, Mem0 can retain details like the customer's recent queries, issues they're facing, and preferences for communication style. Once the session ends, the memory resets."

**关键区别**:

| 特征 | `user_id`/`agent_id`（长期） | `run_id`（短期） |
|------|--------------------------|----------------|
| 持久性 | 跨会话永久保存 | 会话结束后可清理 |
| 内容类型 | 长期事实、偏好 | 临时上下文、意图 |
| LLM提取策略 | 提取稳定的模式和特征 | 提取会话临时状态 |
| 示例 | "用户是素食主义者" | "本次咨询关于胃痛" |

---

## 五、记忆类型分类

### 5.1 按持久性分类

| 类型 | 持久性 | 访问速度 | 主要用途 | Mem0映射 |
|------|--------|----------|----------|----------|
| **短期记忆** | 临时 | 即时 | 当前会话上下文 | `run_id` (会话记忆) |
| **长期记忆** | 持久 | 快速 | 跨会话的用户/智能体知识 | `user_id`, `agent_id` |

### 5.2 按内容分类

#### 1. **事实性记忆 (Factual Memory)**
- 存储具体的事实、数据、知识点
- 示例: "用户体重72kg"、"服务器IP 192.168.1.100"

#### 2. **情景记忆 (Episodic Memory)**
- 存储过去的交互和经历
- 示例: "上次诊断发现CPU过载"、"三周前用户报告登录问题"

#### 3. **语义记忆 (Semantic Memory)**
- 存储概念和它们之间的关系
- 示例: "Nginx是Web服务器"、"Redis用于缓存"

---

## 六、实际应用案例

### 6.1 医疗健康助手

```python
# 用户全局记忆 (跨所有智能体)
client.add(
    messages=[{"role": "user", "content": "我对青霉素过敏"}],
    user_id="patient_001"
)

# 智能体知识库 (诊断规则)
client.add(
    messages=[{"role": "assistant", "content": "发烧超过38.5度建议物理降温"}],
    agent_id="health_assistant"
)

# 用户-智能体交互记忆 (就诊历史)
client.add(
    messages=conversation,
    user_id="patient_001",
    agent_id="health_assistant"
)

# 会话记忆 (本次问诊)
client.add(
    messages=current_session,
    user_id="patient_001",
    agent_id="health_assistant",
    run_id="consultation_2025_01_15"
)
```

### 6.2 IT运维诊断助手（我们的场景）

```python
# 用户全局记忆
memory.add_user_memory(
    messages=[{"role": "user", "content": "我管理的是金融系统，对可用性要求极高"}],
    user_id="ops_engineer_zhang",
    metadata={"source": "user_profile"}
)

# 智能体知识库
memory.add_agent_memory(
    messages=[{"role": "assistant", "content": "Zabbix告警阈值建议设置为：CPU>80%持续5分钟"}],
    agent_id="diagnostic_agent",
    metadata={"source": "best_practice"}
)

# 用户-智能体交互记忆
memory.add_user_agent_memory(
    messages=conversation,
    user_id="ops_engineer_zhang",
    agent_id="diagnostic_agent",
    metadata={"conversation_type": "diagnostic"}
)

# 会话记忆（本次故障诊断）
memory.add_conversation_memory(
    messages=current_conversation,
    user_id="ops_engineer_zhang",
    agent_id="diagnostic_agent",
    run_id="thread_abc123",  # 即我们的thread_id
    metadata={"conversation_type": "session_specific", "thread_id": "thread_abc123"}
)
```

---

## 七、业界最佳实践

### 7.0 默认Prompt vs 自定义Prompt

#### 业界实践调研

**问题**：生产环境中应该用默认的FACT_RETRIEVAL_PROMPT还是自定义prompt？

**调研结论**：

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| **通用AI助手** | 默认prompt | 默认prompt已覆盖7大类信息（偏好、计划、健康等），足够通用 |
| **特定领域应用** | 自定义prompt | 需要专注特定类型信息（客户支持、医疗、运维等） |
| **严格数据治理** | 自定义prompt | 需要过滤敏感信息、控制存储内容 |
| **快速原型验证** | 默认prompt | 快速启动，后续根据需求优化 |

#### 生产案例

1. **Sunflower Sober** (康复支持平台)
   - 规模：80,000+ 用户
   - 使用场景：个性化康复支持
   - 推测：可能使用默认prompt（个人健康偏好类场景与默认prompt契合）

2. **教育平台** (个性化辅导)
   - 反馈：周末即完成集成
   - 使用场景：个性化学习内容推荐
   - 推测：初期使用默认prompt，快速验证价值

#### 官方建议

**默认FACT_RETRIEVAL_PROMPT覆盖**:
1. 个人偏好 (Personal Preferences)
2. 重要细节 (Important Details)
3. 计划与意图 (Plans and Intentions)
4. 服务偏好 (Service Preferences)
5. 健康信息 (Health)
6. 职业上下文 (Professional)
7. 其他细节 (Miscellaneous)

> "The default prompt is sufficient for most general use cases involving extracting user preferences and facts from conversations."

**何时需要自定义**:
- ✅ 需要专注特定领域信息（如客户支持、订单管理）
- ✅ 需要过滤无关信息（闲聊、问候等）
- ✅ 有合规要求（隐私、数据治理）
- ✅ 需要高精度的领域知识提取

#### 我们的建议

**分阶段策略**：

```python
# 阶段1：MVP阶段 - 使用默认
memory = Memory.from_config({
    "llm": {...},
    "version": "v1.1"
    # 不设置custom_fact_extraction_prompt，使用默认
})

# 阶段2：优化阶段 - 根据日志分析是否需要自定义
# 查看Mem0提取的内容，评估是否符合预期
# 如果发现大量无关信息或缺失关键信息，则自定义

# 阶段3：生产阶段 - 针对性自定义（如需要）
memory = Memory.from_config({
    "llm": {...},
    "custom_fact_extraction_prompt": ops_diagnostic_prompt,
    "version": "v1.1"
})
```

**对于运维诊断场景**：

默认prompt可能**不够精确**，因为：
- ❌ 默认侧重个人生活偏好（食物、娱乐等）
- ❌ 缺少技术信息提取（错误日志、性能指标、配置参数）
- ❌ 可能存储大量无关闲聊

**推荐**：运维场景使用自定义prompt，聚焦技术信息提取。

---

### 7.1 记忆存储原则

1. **最少必要原则**: 只存储有价值、可复用的信息
2. **层级分离原则**: 不同持久性的内容存储在对应层级
3. **自动去重原则**: 让Mem0的LLM自动处理重复内容
4. **元数据丰富原则**: 添加充足的metadata便于检索

### 7.2 检索策略

1. **语义搜索优先**: 使用用户查询进行语义搜索，而非简单列举
2. **多层并行检索**: 同时检索多个层级，构建完整上下文
3. **阈值过滤**: 设置相似度阈值（如0.5），过滤低相关度记忆
4. **限制数量**: 每层限制返回数量（如3-5条），避免信息过载

### 7.3 保存时机

**官方推荐**:
- ✅ **对话完成后保存**: 仅保存最后一轮对话（user + assistant消息对）
- ❌ **避免中间保存**: 不要在每次LLM调用时保存
- ❌ **避免全量保存**: 不要保存完整对话历史

**代码示例**:
```python
# ✅ 正确：仅保存最后一轮
last_user_msg = {"role": "user", "content": "..."}
last_ai_msg = {"role": "assistant", "content": "..."}
conversation_messages = [last_user_msg, last_ai_msg]

# ❌ 错误：保存所有消息
all_messages = state.get("messages", [])  # 不推荐
```

### 7.4 性能优化

1. **Embedding复用**: 一次生成embedding，多层检索复用
2. **并行保存**: 多层记忆并行保存，提高效率
3. **后台异步**: 保存操作不阻塞主流程
4. **Token节省**: 通过记忆减少上下文长度，节省90% Token

---

## 八、我们的实现策略

### 8.1 当前架构

基于调研结果，我们的实现完全符合Mem0最佳实践:

```python
# 检索阶段（prepare_graph_input）
memory_context = await retrieve_memory_context(
    query=request_body.query,  # 语义搜索
    config=config,
    agent_id=request_body.agent_id
)

# 保存阶段（图完成后）
await save_memory_context(
    final_state=final_state,
    config=config,
    agent_id=request_body.agent_id,
    thread_id=thread_id  # 作为run_id
)
```

### 8.2 四层保存逻辑

```python
# memory_utils.py
async def save_layered_memories(
    memory,
    messages: List[Dict[str, str]],
    user_id: str,
    agent_id: str,
    run_id: Optional[str] = None  # thread_id
):
    tasks = [
        # 1. 用户全局记忆
        ("user", memory.add_user_memory(
            messages=messages,
            user_id=user_id,
            metadata={"source": "diagnostic_conversation"}
        )),

        # 2. 智能体全局记忆
        ("agent", memory.add_agent_memory(
            messages=messages,
            agent_id=agent_id,
            metadata={"source": "diagnostic_conversation"}
        )),

        # 3. 用户-智能体交互记忆
        ("interaction", memory.add_user_agent_memory(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            metadata={"conversation_type": "diagnostic"}
        )),

        # 4. 会话记忆（如果提供了run_id/thread_id）
        ("session", memory.add_conversation_memory(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,  # thread_id
            metadata={"conversation_type": "session_specific", "thread_id": run_id}
        )) if run_id else None
    ]
```

### 8.3 优势验证

| 最佳实践 | 我们的实现 | ✓ |
|---------|-----------|---|
| 语义搜索 | `search_combined_memory(query=...)` | ✅ |
| 多层并行检索 | 并行检索3-4层 | ✅ |
| 仅保存最后一轮 | 提取last_user_msg + last_ai_msg | ✅ |
| 后台异步保存 | `threading.Thread` + 新事件循环 | ✅ |
| 不使用hooks | 检索在图前，保存在图后 | ✅ |
| Embedding复用 | `search_with_embedding()` 复用 | ✅ |
| 4层记忆架构 | user/agent/interaction/session | ✅ |

---

## 九、常见问题解答

### Q1: 为什么不用hooks？
A: Hooks在每次LLM调用时触发，会导致重复检索和保存。官方推荐在对话开始前检索，结束后保存。

### Q2: run_id和thread_id是什么关系？
A: 在我们的系统中，`run_id` 就是 `thread_id`（LangGraph的会话线程ID）。

### Q3: 是否需要4层都保存？
A: 不一定。如果没有thread_id，可以只保存前3层。会话记忆是可选的短期存储。

### Q4: 如何避免记忆冗余？
A: Mem0的LLM会自动处理去重、合并、删除过时记忆。我们只需直接保存，无需手动判断。

### Q5: 检索时应该使用哪些层级？
A: 根据需求：
- 个性化场景：user + user_agent
- 通用场景：agent
- 会话连续性：session
- 完整上下文：全部4层（我们当前实现）

### Q6: 可以自定义提取规则吗？
A: **可以！**通过`custom_fact_extraction_prompt`完全自定义。

**配置方法**:
```python
config = {
    "llm": {...},
    "custom_fact_extraction_prompt": "你的自定义prompt...",
    "version": "v1.1"
}
memory = Memory.from_config(config)
```

**最佳实践**:
- 使用few-shot示例（3-5个正面+负面示例）
- 明确指定要提取和忽略的信息类型
- 使用一致的JSON格式输出
- 可以在prompt中指导如何区分长期和短期信息

**示例**（运维场景）:
```python
ops_prompt = """
提取运维诊断信息：
1. 系统信息、故障现象、诊断结果
2. 用户使用习惯和偏好

忽略：问候、闲聊、天气等

Input: "我的Nginx服务器CPU达到90%"
Output: {"facts": ["Nginx server CPU at 90%"]}
"""
```

详见文档第四章"4.2 自定义提取规则"。

### Q7: 自定义prompt能区分user_id和agent_id层吗？
A: Mem0目前不直接支持针对不同层级使用不同prompt，但可以：

**方案1**: 在prompt中明确角色指导
```python
"根据消息角色提取不同内容：
- role: user → 提取用户偏好、需求
- role: assistant → 提取知识、规则"
```

**方案2**: 创建多个Memory实例（高级）
```python
user_memory = Memory.from_config(user_memory_config)  # 用户侧重
agent_memory = Memory.from_config(agent_memory_config)  # 智能体侧重
```

---

## 十、参考资料

### 官方文档
- Mem0 官网: https://mem0.ai/
- 官方文档: https://docs.mem0.ai/
- GitHub仓库: https://github.com/mem0ai/mem0
- 高级操作: https://docs.mem0.ai/platform/advanced-memory-operations

### 集成指南
- AutoGen集成: https://microsoft.github.io/autogen/0.2/docs/ecosystem/mem0/
- Semantic Kernel: https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-memory
- LangGraph Memory: https://langchain-ai.github.io/langgraph/concepts/memory/

### 学术论文
- ArXiv论文: https://arxiv.org/abs/2504.19413
  "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory"

---

## 十一、总结

### 核心要点

1. **4层记忆架构**: user/agent/user+agent/user+agent+run_id

2. **内容提取由Mem0内部LLM自动决定**:
   - 基于消息角色过滤（user vs assistant）
   - 基于FACT_RETRIEVAL_PROMPT（7类信息）
   - 基于infer=True自动推理（ADD/UPDATE/DELETE）
   - 基于持久性判断（长期 vs 短期）

3. **存储内容差异**:
   - **User** (`user_id`):
     - 提取来源：主要从`"role": "user"`消息
     - 内容类型：个人长期偏好、属性、目标
     - 示例："我是素食主义者"

   - **Agent** (`agent_id`):
     - 提取来源：主要从`"role": "assistant"`消息
     - 内容类型：智能体通用知识、规则、能力
     - 示例："Zabbix告警阈值：CPU>80%持续5分钟"

   - **Interaction** (`user_id + agent_id`):
     - 提取来源：user和assistant消息都重要
     - 内容类型：个性化交互历史、长期模式
     - 示例："该用户反复询问数据库优化"

   - **Session** (`user_id/agent_id + run_id`):
     - 提取来源：会话临时上下文
     - 内容类型：临时意图、会话状态（会话结束可清理）
     - 示例："本次诊断发现CPU过载"

4. **run_id的特殊性**:
   - LLM会区分**临时上下文** vs **长期事实**
   - 提取会话特定的临时信息，不提取长期特征
   - 会话结束后可重置，不必永久保留

5. **最佳实践**:
   - 语义搜索而非列举
   - 仅保存最后一轮对话
   - 后台异步保存
   - 让Mem0 LLM自动去重和分层
   - 正确传递参数组合，剩下交给Mem0

6. **性能优势**: 26%高精度、91%低延迟、90%省Token

### 我们的实现状态

✅ 完全符合Mem0官方推荐和业界最佳实践
✅ 支持4层记忆架构
✅ 语义搜索 + 多层并行检索
✅ 后台异步保存 + Embedding复用
✅ 检索在图前，保存在图后（不用hooks）

---

**文档版本**: v1.0
**更新时间**: 2025-01-15
**作者**: OMind Team
**基于**: Mem0官方文档 + 业界最佳实践调研
