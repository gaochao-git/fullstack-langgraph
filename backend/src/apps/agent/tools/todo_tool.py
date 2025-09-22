"""
任务管理工具 - 受 DeepAgents 启发的 todo 工具
帮助 Agent 规划和跟踪复杂任务
"""
from typing import List, Dict, Literal, Optional, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from datetime import datetime
from src.shared.db.models import now_shanghai


# Todo 项的类型定义
TodoItem = Dict[str, any]  # content, status, findings

WRITE_TODOS_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:

1. Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. After receiving new instructions - Immediately capture user requirements as todos
6. When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
7. After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation

## When NOT to Use This Tool

Skip using this tool when:
1. There is only a single, straightforward task
2. The task is trivial and tracking it provides no organizational benefit
3. The task can be completed in less than 3 trivial steps
4. The task is purely conversational or informational

NOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.

## Examples of When to Use the Todo List

<example>
User: I want to add a dark mode toggle to the application settings. Make sure you run the tests and build when you're done!
Assistant: I'll help add a dark mode toggle to your application settings. Let me create a todo list to track this implementation.
*Creates todo list with the following items:*
1. Create dark mode toggle component in Settings page
2. Add dark mode state management (context/store)
3. Implement CSS-in-JS styles for dark theme
4. Update existing components to support theme switching
5. Run tests and build process, addressing any failures or errors that occur
*Begins working on the first task*

<reasoning>
The assistant used the todo list because:
1. Adding dark mode is a multi-step feature requiring UI, state management, and styling changes
2. The user explicitly requested tests and build be run afterward
3. The assistant inferred that tests and build need to pass by adding "Ensure tests and build succeed" as the final task
</reasoning>
</example>

<example>
User: Help me plan a comprehensive marketing campaign for our new product launch, including social media, email marketing, and press releases.
Assistant: I'll help you plan a comprehensive marketing campaign for your product launch. Let me create a todo list to organize all the components.
*Creates todo list with the following items:*
1. Define target audience and key messaging
2. Create social media content calendar and posting schedule
3. Design email marketing sequence and automation flows
4. Draft press release and identify media contacts
5. Set up tracking and analytics for campaign performance
6. Create visual assets and brand materials
7. Coordinate launch timeline and deliverables
*Begins working on the first task*

<reasoning>
The assistant used the todo list because:
1. Marketing campaign planning involves multiple distinct channels and activities
2. Each component requires careful coordination and planning
3. The systematic approach ensures all aspects of the launch are covered
4. Progress tracking helps maintain timeline and deliverables
</reasoning>
</example>

<example>
User: Help me rename the function getCwd to getCurrentWorkingDirectory across my project
Assistant: Let me first search through your codebase to find all occurrences of 'getCwd'.
*Uses search tools to locate all instances of getCwd in the codebase*
Assistant: I've found 15 instances of 'getCwd' across 8 different files. Let me create a todo list to track these changes.
*Creates todo list with specific items for each file that needs updating*

<reasoning>
The assistant used the todo list because:
1. First, the assistant searched to understand the scope of the task
2. Upon finding multiple occurrences across different files, it determined this was a complex task with multiple steps
3. The todo list helps ensure every instance is tracked and updated systematically
4. This approach prevents missing any occurrences and maintains consistency
</reasoning>
</example>

<example>
User: I need help organizing my home office: decluttering the desk, setting up a filing system, organizing digital files, and creating a daily workflow.
Assistant: I'll help you organize your home office systematically. Let me create a todo list to track each area of organization.
*Creates todo list with items like: 1) Sort and declutter desk items, 2) Set up physical filing system for documents, 3) Organize digital files and folders, 4) Create daily workflow and productivity systems, 5) Establish maintenance routines*
Let's start with decluttering your desk space to create a clean foundation for the other organizational systems.

<reasoning>
The assistant used the todo list because:
1. The user provided multiple distinct organizational tasks
2. Each area requires different approaches and careful planning
3. Home organization benefits from systematic, step-by-step completion
4. Progress tracking ensures all areas are addressed thoroughly
</reasoning>
</example>

## Examples of When NOT to Use the Todo List

<example>
User: How do I print 'Hello World' in Python?
Assistant: In Python, you can print "Hello World" with this simple code:

python
print("Hello World")

This will output the text "Hello World" to the console when executed.</assistant>

<reasoning>
The assistant did not use the todo list because this is a single, trivial task that can be completed in one step. There's no need to track multiple tasks or steps for such a straightforward request.
</reasoning>
</example>

<example>
User: What's the best way to water houseplants?
Assistant: The best way to water houseplants depends on the specific plant type, but here are some general guidelines:

- Check soil moisture by inserting your finger about 1-2 inches into the soil
- Water thoroughly when the top inch feels dry, allowing water to drain from the bottom
- Use room temperature water and water in the morning when possible
- Avoid overwatering, which is more harmful than underwatering for most plants

Different plants have different needs, so it's important to research your specific varieties for optimal care.

<reasoning>
The assistant did not use the todo list because this is an informational request with no actual tasks to complete. The user is simply asking for advice and explanation, not for the assistant to perform multiple steps or activities.
</reasoning>
</example>

<example>
User: Can you add a comment to the calculateTotal function to explain what it does?
Assistant: Sure, let me add a comment to the calculateTotal function to explain what it does.
* Uses the Edit tool to add a comment to the calculateTotal function *

<reasoning>
The assistant did not use the todo list because this is a single, straightforward task confined to one location. Adding a comment doesn't require tracking multiple steps or systematic organization.
</reasoning>
</example>

<example>
User: What time is it in Tokyo right now?
Assistant: I'll check the current time in Tokyo for you.

*Searches for current time in Tokyo*

The current time in Tokyo, Japan is [current time]. Tokyo is in the Japan Standard Time (JST) zone, which is UTC+9.

<reasoning>
The assistant did not use the todo list because this is a single information lookup with immediate results. There are no multiple steps to track or organize, making the todo list unnecessary for this straightforward request.
</reasoning>
</example>

<example>
User: 服务器响应很慢，帮我排查一下
Assistant: 我来帮您排查服务器响应慢的问题。让我创建一个任务列表来系统地进行故障诊断。
*创建任务列表：*
1. 检查服务器资源使用情况（CPU、内存、磁盘）
2. 分析系统进程，找出资源占用高的进程
3. 检查网络连接和延迟
4. 查看系统日志，寻找异常信息
5. 分析数据库慢查询日志
6. 检查应用程序性能指标
7. 生成诊断报告和优化建议
*开始第一个任务*

<reasoning>
助手使用任务列表是因为：
1. 服务器性能问题需要多方面系统性排查
2. 每个检查项都需要不同的工具和方法
3. 任务列表确保不遗漏任何重要的排查点
4. 便于跟踪每个检查项的结果和发现
</reasoning>
</example>

<example>
User: 数据库连接超时了，怎么办
Assistant: 我来帮您诊断数据库连接超时问题。让我创建一个系统的排查任务列表。
*创建任务列表：*
1. 检查数据库服务状态和进程
2. 验证网络连接（ping和telnet数据库端口）
3. 查看数据库错误日志
4. 检查数据库连接数和连接池配置
5. 分析慢查询和锁等待情况
6. 检查防火墙和安全组规则
7. 验证数据库用户权限和认证
8. 生成问题总结和解决方案
*开始执行第一个任务*

<reasoning>
助手使用任务列表是因为：
1. 数据库连接问题涉及多个层面（网络、服务、配置等）
2. 需要按优先级逐步排查各种可能原因
3. 系统性的方法有助于快速定位问题
4. 记录每步的发现便于后续分析
</reasoning>
</example>

<example>
User: 系统日志里出现大量错误，帮我分析一下
Assistant: 我来帮您分析系统日志中的错误。让我创建一个任务列表来系统地进行分析。
*创建任务列表：*
1. 收集和汇总错误日志（最近24小时）
2. 按错误类型和频率进行分类统计
3. 识别错误模式和时间规律
4. 追踪错误源头和调用链
5. 分析错误对系统的影响范围
6. 查找相关配置和代码问题
7. 制定修复方案和优先级
8. 生成错误分析报告
*开始第一个任务*

<reasoning>
助手使用任务列表是因为：
1. 日志分析需要多步骤的数据处理和分析
2. 从收集、分类到根因分析是一个复杂过程
3. 任务列表帮助组织分析流程
4. 便于生成结构化的分析报告
</reasoning>
</example>

## Task States and Management

1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time)
   - completed: Task finished successfully

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Only have ONE task in_progress at any time
   - Complete current tasks before starting new ones
   - Remove tasks that are no longer relevant from the list entirely

3. **Task Completion Requirements**:
   - ONLY mark a task as completed when you have FULLY accomplished it
   - If you encounter errors, blockers, or cannot finish, keep the task as in_progress
   - When blocked, create a new task describing what needs to be resolved
   - Never mark a task as completed if:
     - There are unresolved issues or errors
     - Work is partial or incomplete
     - You encountered blockers that prevent completion
     - You couldn't find necessary resources or dependencies
     - Quality standards haven't been met

4. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names

When in doubt, use this tool. Being proactive with task management demonstrates attentiveness and ensures you complete all requirements successfully.

## Fault Diagnosis Examples
"""

@tool(description=WRITE_TODOS_DESCRIPTION)
def write_todos(
    todos: List[Dict[str, any]],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    if not todos:
        return "任务列表为空"
    
    # 统计任务状态
    status_count = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0
    }
    
    # 格式化输出
    output_lines = ["任务列表已更新\n"]
    
    # 显示任务列表
    for i, todo in enumerate(todos, 1):
        # 确保必要字段
        if "content" not in todo:
            continue
            
        # 设置默认值
        status = todo.get("status", "pending")
        
        # 统计状态
        if status in status_count:
            status_count[status] += 1
        
        # 创建任务显示项
        status_emoji = {
            "pending": "[待处理]",
            "in_progress": "[进行中]",
            "completed": "[已完成]"
        }.get(status, "[未知]")
        
        task_line = f"{i}. {status_emoji} {todo['content']}"
        if "findings" in todo and todo["findings"]:
            task_line += f"\n   发现: {todo['findings']}"
        
        output_lines.append(task_line)
    
    # 添加统计信息
    output_lines.append(f"\n统计: 总计 {len(todos)} 项任务")
    output_lines.append(f"   - 待处理: {status_count['pending']}")
    output_lines.append(f"   - 进行中: {status_count['in_progress']}")
    output_lines.append(f"   - 已完成: {status_count['completed']}")
    
    # 计算完成率
    if len(todos) > 0:
        completion_rate = (status_count['completed'] / len(todos)) * 100
        output_lines.append(f"   - 完成率: {completion_rate:.1f}%")
    
    # 返回 Command 对象，同时更新状态和消息
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(
                    content="\n".join(output_lines),
                    tool_call_id=tool_call_id
                )
            ]
        }
    )


GET_TODOS_DESCRIPTION = """获取当前的任务列表状态。

用于查看所有任务的当前状态、进度和发现。
这个工具不需要参数，会返回格式化的任务列表。

使用场景：
- 需要查看整体进度时
- 准备向用户汇报时
- 决定下一步行动前
"""

@tool(description=GET_TODOS_DESCRIPTION)
def get_todos(
    state: Annotated[Dict, InjectedState]
) -> str:
    """获取当前任务列表"""
    # 从状态中读取任务列表
    todos = state.get("todos", [])
    
    if not todos:
        return "当前没有任务。请使用 write_todos 工具来创建任务列表。"
    
    # 格式化输出已有的任务
    output_lines = ["当前任务列表\n"]
    
    # 显示任务列表
    for i, todo in enumerate(todos, 1):
        if "content" not in todo:
            continue
            
        status = todo.get("status", "pending")
        
        status_emoji = {
            "pending": "[待处理]",
            "in_progress": "[进行中]",
            "completed": "[已完成]"
        }.get(status, "[未知]")
        
        task_line = f"{i}. {status_emoji} {todo['content']}"
        if "findings" in todo and todo["findings"]:
            task_line += f"\n   发现: {todo['findings']}"
        
        output_lines.append(task_line)
    
    # 添加统计信息
    status_count = {"pending": 0, "in_progress": 0, "completed": 0}
    for todo in todos:
        status = todo.get("status", "pending")
        if status in status_count:
            status_count[status] += 1
    
    output_lines.append(f"\n统计: 总计 {len(todos)} 项任务")
    output_lines.append(f"   - 待处理: {status_count['pending']}")
    output_lines.append(f"   - 进行中: {status_count['in_progress']}")
    output_lines.append(f"   - 已完成: {status_count['completed']}")
    
    if len(todos) > 0:
        completion_rate = (status_count['completed'] / len(todos)) * 100
        output_lines.append(f"   - 完成率: {completion_rate:.1f}%")
    
    return "\n".join(output_lines)


UPDATE_TODO_STATUS_DESCRIPTION = """更新特定任务的状态。

参数:
- task_content: 任务内容（用于匹配任务）
- new_status: 新状态 - "pending", "in_progress", "completed"
- findings: 任务执行的发现或结果（可选）

使用场景：
- 开始执行某个任务时，将状态改为 "in_progress"
- 完成任务后，将状态改为 "completed" 并记录发现
- 需要重新处理时，将状态改回 "pending"

注意：同一时间只应有一个任务处于 "in_progress" 状态。
"""

@tool(description=UPDATE_TODO_STATUS_DESCRIPTION)
def update_todo_status(
    task_content: str,
    new_status: Literal["pending", "in_progress", "completed"],
    state: Annotated[Dict, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    findings: Optional[str] = None
) -> Command:
    """更新任务状态"""
    status_emoji = {
        "pending": "[待处理]",
        "in_progress": "[进行中]", 
        "completed": "[已完成]"
    }.get(new_status, "[未知]")
    
    response = f"{status_emoji} 任务状态已更新\n"
    response += f"任务: {task_content}\n"
    response += f"新状态: {new_status}\n"
    
    if findings:
        response += f"发现: {findings}\n"
    
    response += "\n提示: 请使用 write_todos 工具查看完整的任务列表。"
    
    # 从状态中获取当前的任务列表
    todos = state.get("todos", [])
    
    # 查找并更新匹配的任务
    updated = False
    for todo in todos:
        if todo.get("content") == task_content:
            todo["status"] = new_status
            if findings:
                todo["findings"] = findings
            todo["updated_at"] = str(now_shanghai())
            updated = True
            break
    
    if not updated:
        response += "\n警告: 未找到匹配的任务，无法更新状态。"
    
    # 返回 Command 更新状态
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(
                    content=response,
                    tool_call_id=tool_call_id
                )
            ]
        }
    )


# 导出工具名称，方便 agent_utils.py 发现
__all__ = ['write_todos', 'get_todos', 'update_todo_status']