# Example Agent - 内置 Agent 自定义工作流示例

本示例展示了如何创建一个使用自定义工作流的内置 Agent，实现前端创建的 Agent 无法做到的复杂控制流。

## 目录结构

```
example_agent/
├── __init__.py          # 模块导出
├── graph.py             # Agent 创建主逻辑（自定义工作流）
├── configuration.py     # 配置类（使用 agent_utils）
├── prompts.py          # 提示词（使用 agent_utils）
├── tools.py            # 自定义工具定义
├── state.py            # 自定义状态定义
├── nodes.py            # 工作流节点定义（包含条件边函数）
└── README.md           # 本文档
```

## 自定义工作流特性

### 调用方式

```python
# 调用 example_agent
POST /api/v1/agents/example_agent/runs/stream
{
  "messages": [{
    "role": "user",
    "content": "分析这段文本并统计字数"
  }]
}
```

### 核心特性：
- ✅ 完全控制执行流程
- ✅ 自定义状态管理
- ✅ 多步骤工作流  
- ✅ 条件分支（条件边）
- ✅ 动态路由决策
- ✅ 错误重试机制
- ✅ 人工审核节点
- ✅ 并行处理能力

## 自定义工作流详解

### 1. 状态定义（state.py）

```python
class ExampleAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    task_type: Optional[str]
    processing_results: Dict[str, Any]
    workflow_steps: List[str]
    # ... 其他状态字段
```

### 2. 节点定义（nodes.py）

- `analyze_task_node`: 分析用户意图
- `process_task_node`: 执行具体处理
- `format_response_node`: 格式化输出

### 3. 工作流编译（graph.py）

```python
# 创建状态图
workflow = StateGraph(ExampleAgentState)

# 添加节点
workflow.add_node("analyze_task", analyze_task_node)
workflow.add_node("process_task", process_task_node)

# 定义条件边
workflow.add_conditional_edges(
    "analyze_task",
    should_continue_after_task,
    {
        "word_count_node": "word_count_node",
        "analysis_node": "analysis_node",
        "general_process": "general_process"
    }
)

# 编译
graph = workflow.compile()
```

## 何时使用自定义工作流

### 适合使用自定义工作流的场景：

1. **多步骤审批流程**
   - 需要人工确认
   - 多级审批
   - 条件判断

2. **复杂数据处理**
   - 批量处理
   - 数据转换管道
   - 并行处理

3. **特殊控制需求**
   - 自定义重试逻辑
   - 特殊错误处理
   - 状态回滚

### 不建议使用自定义工作流的场景：

1. **简单问答**：使用标准 ReAct 即可
2. **纯工具调用**：标准模式已经很好
3. **通用对话**：不需要复杂控制流

## 创建新的自定义工作流 Agent

1. **复制 example_agent 作为模板**
   ```bash
   cp -r example_agent my_workflow_agent
   ```

2. **定义状态结构**（state.py）
   - 继承 TypedDict
   - 定义需要的状态字段

3. **实现节点函数**（nodes.py）
   - 每个节点是一个异步函数
   - 接收状态，返回状态更新

4. **设计工作流**（graph.py）
   - 使用 StateGraph 创建图
   - 添加节点和边
   - 定义条件分支

5. **测试工作流**
   ```python
   from example_agent import test_custom_workflow
   result = await test_custom_workflow()
   ```

## 性能考虑

- **标准模式**：性能最优，适合 99% 场景
- **自定义模式**：灵活但稍慢，适合复杂场景

## 最佳实践

1. **优先使用标准模式**
2. **只在必要时使用自定义工作流**
3. **保持节点函数简单**
4. **合理设计状态结构**
5. **充分测试工作流逻辑**

## 与前端创建的 Agent 区别

| 特性 | 内置 Agent | 前端创建的 Agent |
|------|-----------|------------------|
| 创建方式 | 代码 + @agent | 前端界面 |
| 自定义工作流 | ✅ 支持 | ❌ 不支持 |
| 工具 | 代码定义 | 界面选择 |
| 灵活性 | 高 | 中 |
| 适用场景 | 复杂业务逻辑 | 简单对话和工具调用 |