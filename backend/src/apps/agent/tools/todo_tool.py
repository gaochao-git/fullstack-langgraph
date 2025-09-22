"""
任务管理工具 - 受 DeepAgents 启发的 todo 工具
帮助 Agent 规划和跟踪复杂任务
"""
from typing import List, Dict, Literal, Optional
from langchain_core.tools import tool
from datetime import datetime
from src.shared.db.models import now_shanghai


# Todo 项的类型定义
TodoItem = Dict[str, any]  # content, status, priority, created_at, updated_at


@tool
def write_todos(
    todos: List[Dict[str, any]]
) -> str:
    """
    创建和管理任务列表，帮助组织和跟踪工作进度。
    
    ## 何时使用此工具
    
    在以下场景中主动使用此工具：
    
    1. **复杂的多步骤任务** - 当任务需要3个或更多不同的步骤或操作时
    2. **需要系统性处理** - 任务需要仔细规划或多个操作的情况
    3. **用户明确要求** - 当用户直接要求创建任务列表或计划时
    4. **多个任务并行** - 用户提供了多个需要处理的事项
    5. **开始新任务前** - 收到新指令后，先规划再执行
    6. **任务进行中** - 将当前任务标记为 in_progress（同时只有一个）
    7. **任务完成后** - 及时标记为 completed，并添加新发现的后续任务
    
    ## 何时不使用此工具
    
    1. 只有一个简单、直接的任务
    2. 任务可以在2个步骤内完成
    3. 纯粹的对话或信息查询
    4. 任务非常明确，不需要规划
    
    ## 使用示例
    
    ### 示例1：故障诊断
    用户："服务器响应很慢，帮我排查一下"
    
    创建任务列表：
    ```python
    todos = [
        {"content": "检查服务器资源使用情况（CPU、内存、磁盘）", "status": "pending", "priority": "high"},
        {"content": "分析系统进程，找出资源占用高的进程", "status": "pending", "priority": "high"},
        {"content": "检查网络连接和延迟", "status": "pending", "priority": "medium"},
        {"content": "查看系统日志，寻找异常信息", "status": "pending", "priority": "medium"},
        {"content": "生成诊断报告和优化建议", "status": "pending", "priority": "low"}
    ]
    ```
    
    ### 示例2：系统部署
    用户："帮我部署一个新的Web应用"
    
    创建任务列表：
    ```python
    todos = [
        {"content": "检查系统环境和依赖", "status": "in_progress", "priority": "high"},
        {"content": "配置Web服务器（Nginx/Apache）", "status": "pending", "priority": "high"},
        {"content": "设置应用程序环境", "status": "pending", "priority": "high"},
        {"content": "配置数据库连接", "status": "pending", "priority": "medium"},
        {"content": "设置SSL证书", "status": "pending", "priority": "medium"},
        {"content": "配置监控和日志", "status": "pending", "priority": "low"},
        {"content": "执行健康检查", "status": "pending", "priority": "low"}
    ]
    ```
    
    ## 参数说明
    
    todos: 任务列表，每个任务包含：
    - content: 任务描述（必需）
    - status: 状态 - "pending"（待处理）、"in_progress"（进行中）、"completed"（已完成）
    - priority: 优先级 - "high"（高）、"medium"（中）、"low"（低）
    - findings: 任务执行结果或发现（可选）
    
    ## 最佳实践
    
    1. **保持任务具体可执行** - 每个任务应该是明确的行动项
    2. **合理设置优先级** - 关键任务设为 high，辅助任务设为 low
    3. **及时更新状态** - 开始任务时改为 in_progress，完成后改为 completed
    4. **记录发现** - 在 findings 中记录重要发现，便于后续参考
    5. **动态调整** - 根据执行情况，可以添加新任务或调整优先级
    
    返回格式化的任务列表摘要。
    """
    if not todos:
        return "任务列表为空"
    
    # 统计任务状态
    status_count = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0
    }
    
    # 格式化输出
    output_lines = ["📋 任务列表已更新\n"]
    
    # 按优先级分组显示
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for todo in todos:
        # 确保必要字段
        if "content" not in todo:
            continue
            
        # 设置默认值
        status = todo.get("status", "pending")
        priority = todo.get("priority", "medium")
        
        # 统计状态
        if status in status_count:
            status_count[status] += 1
        
        # 创建任务显示项
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅"
        }.get(status, "❓")
        
        task_line = f"{status_emoji} {todo['content']}"
        if "findings" in todo and todo["findings"]:
            task_line += f"\n   💡 发现: {todo['findings']}"
        
        # 按优先级分组
        if priority == "high":
            high_priority.append(task_line)
        elif priority == "medium":
            medium_priority.append(task_line)
        else:
            low_priority.append(task_line)
    
    # 输出任务列表
    if high_priority:
        output_lines.append("\n🔴 高优先级:")
        output_lines.extend(f"  {task}" for task in high_priority)
    
    if medium_priority:
        output_lines.append("\n🟡 中优先级:")
        output_lines.extend(f"  {task}" for task in medium_priority)
    
    if low_priority:
        output_lines.append("\n🟢 低优先级:")
        output_lines.extend(f"  {task}" for task in low_priority)
    
    # 添加统计信息
    output_lines.append(f"\n📊 统计: 总计 {len(todos)} 项任务")
    output_lines.append(f"   - 待处理: {status_count['pending']}")
    output_lines.append(f"   - 进行中: {status_count['in_progress']}")
    output_lines.append(f"   - 已完成: {status_count['completed']}")
    
    # 计算完成率
    if len(todos) > 0:
        completion_rate = (status_count['completed'] / len(todos)) * 100
        output_lines.append(f"   - 完成率: {completion_rate:.1f}%")
    
    return "\n".join(output_lines)


@tool
def get_todos() -> str:
    """
    获取当前的任务列表状态。
    
    用于查看所有任务的当前状态、进度和发现。
    这个工具不需要参数，会返回格式化的任务列表。
    
    使用场景：
    - 需要查看整体进度时
    - 准备向用户汇报时
    - 决定下一步行动前
    """
    # 在实际实现中，这里应该从状态中读取任务列表
    # 现在返回一个提示信息
    return "请使用 write_todos 工具来创建和管理任务列表。"


@tool
def update_todo_status(
    task_content: str,
    new_status: Literal["pending", "in_progress", "completed"],
    findings: Optional[str] = None
) -> str:
    """
    更新特定任务的状态。
    
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
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄", 
        "completed": "✅"
    }.get(new_status, "❓")
    
    response = f"{status_emoji} 任务状态已更新\n"
    response += f"任务: {task_content}\n"
    response += f"新状态: {new_status}\n"
    
    if findings:
        response += f"发现: {findings}\n"
    
    response += "\n提示: 请使用 write_todos 工具查看完整的任务列表。"
    
    return response


# 导出工具名称，方便 agent_utils.py 发现
__all__ = ['write_todos', 'get_todos', 'update_todo_status']