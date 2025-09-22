"""
子代理支持 - 简化版的 DeepAgents 子代理机制
"""
from typing import TypedDict, NotRequired, Any, Dict, List
from typing_extensions import TypedDict
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from typing import Annotated
from langgraph.types import Command
from langgraph.prebuilt import InjectedState
from .state import DeepAgentState


class SubAgentConfig(TypedDict):
    """子代理配置 - 基于 DeepAgents 的 SubAgent"""
    name: str
    description: str
    prompt: str
    tools: NotRequired[List[str]]  # 可选的工具列表


# 子任务工具描述
TASK_DESCRIPTION = """执行专门的子任务。使用此工具来：
- 执行特定领域的分析
- 处理需要不同上下文的任务
- 隔离复杂的子任务

可用的子代理类型：
{agent_types}

使用示例：
- 使用 'general-purpose' 进行一般性任务
- 使用专门的子代理进行特定领域的任务"""


def create_task_tool(sub_agents: List[SubAgentConfig] = None):
    """创建任务工具 - 简化版本，不真正创建子代理"""
    
    # 获取子代理描述
    agent_types = ["- general-purpose: 通用任务处理"]
    if sub_agents:
        for agent in sub_agents:
            agent_types.append(f"- {agent['name']}: {agent['description']}")
    
    @tool(description=TASK_DESCRIPTION.format(agent_types="\n".join(agent_types)))
    async def task(
        description: str,
        subagent_type: str,
        state: Annotated[DeepAgentState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """执行子任务 - 简化版本"""
        # 验证子代理类型
        valid_types = ["general-purpose"]
        if sub_agents:
            valid_types.extend([agent["name"] for agent in sub_agents])
        
        if subagent_type not in valid_types:
            return Command(
                update={
                    "messages": [
                        ToolMessage(
                            f"错误: 未知的子代理类型 {subagent_type}，可用类型: {valid_types}",
                            tool_call_id=tool_call_id
                        )
                    ]
                }
            )
        
        # 简化实现：仅返回任务描述作为结果
        # 在实际应用中，这里可以调用不同的处理逻辑
        result_msg = f"子代理 '{subagent_type}' 执行任务: {description}\n"
        result_msg += f"任务已完成。（这是简化版本，实际子代理功能需要更复杂的实现）"
        
        # 更新状态
        context = state.get("context", {})
        if "task_history" not in context:
            context["task_history"] = []
        context["task_history"].append({
            "type": subagent_type,
            "description": description,
            "status": "completed"
        })
        
        return Command(
            update={
                "context": context,
                "messages": [
                    ToolMessage(result_msg, tool_call_id=tool_call_id)
                ]
            }
        )
    
    return task