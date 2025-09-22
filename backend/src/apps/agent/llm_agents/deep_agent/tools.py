"""
Deep Agent 工具集 - 基于 DeepAgents 的工具实现
"""
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from typing import Annotated
from langgraph.prebuilt import InjectedState

from .state import Todo, DeepAgentState
from .prompts import WRITE_TODOS_DESCRIPTION


@tool(description=WRITE_TODOS_DESCRIPTION)
def write_todos(
    todos: list[Todo], 
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """更新待办事项列表 - 与 DeepAgents 一致"""
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"已更新任务列表，共 {len(todos)} 项任务", tool_call_id=tool_call_id)
            ],
        }
    )


@tool
def ls(state: Annotated[DeepAgentState, InjectedState]) -> list[str]:
    """列出所有文件 - 与 DeepAgents 一致"""
    return list(state.get("files", {}).keys())


@tool
def read_file(
    file_path: str,
    state: Annotated[DeepAgentState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    """读取文件 - 与 DeepAgents 一致"""
    mock_filesystem = state.get("files", {})
    if file_path not in mock_filesystem:
        return f"错误: 文件 '{file_path}' 不存在"

    # 获取文件内容
    content = mock_filesystem[file_path]

    # 处理空文件
    if not content or content.strip() == "":
        return "系统提示: 文件存在但内容为空"

    # 按行分割
    lines = content.splitlines()

    # 应用行偏移和限制
    start_idx = offset
    end_idx = min(start_idx + limit, len(lines))

    # 处理偏移超出文件长度的情况
    if start_idx >= len(lines):
        return f"错误: 行偏移 {offset} 超出文件长度 ({len(lines)} 行)"

    # 格式化输出（cat -n 格式）
    result_lines = []
    for i in range(start_idx, end_idx):
        line_content = lines[i]

        # 截断超长行
        if len(line_content) > 2000:
            line_content = line_content[:2000]

        # 行号从1开始
        line_number = i + 1
        result_lines.append(f"{line_number:6d}\t{line_content}")

    return "\n".join(result_lines)


@tool
def write_file(
    file_path: str,
    content: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """写入文件 - 与 DeepAgents 一致"""
    files = state.get("files", {})
    files[file_path] = content
    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(f"已更新文件 {file_path}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    replace_all: bool = False,
) -> Command | str:
    """编辑文件 - 与 DeepAgents 一致"""
    mock_filesystem = state.get("files", {})
    
    # 检查文件是否存在
    if file_path not in mock_filesystem:
        return f"错误: 文件 '{file_path}' 不存在"

    # 获取当前文件内容
    content = mock_filesystem[file_path]

    # 检查 old_string 是否存在
    if old_string not in content:
        return f"错误: 在文件中找不到字符串: '{old_string}'"

    # 如果不是替换所有，检查唯一性
    if not replace_all:
        occurrences = content.count(old_string)
        if occurrences > 1:
            return f"错误: 字符串 '{old_string}' 在文件中出现 {occurrences} 次。使用 replace_all=True 替换所有实例，或提供更具体的上下文。"
        elif occurrences == 0:
            return f"错误: 在文件中找不到字符串: '{old_string}'"

    # 执行替换
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacement_count = content.count(old_string)
        result_msg = f"成功在 '{file_path}' 中替换了 {replacement_count} 处字符串"
    else:
        new_content = content.replace(old_string, new_string, 1)  # 只替换第一个
        result_msg = f"成功在 '{file_path}' 中替换了字符串"

    # 更新文件系统
    mock_filesystem[file_path] = new_content
    return Command(
        update={
            "files": mock_filesystem,
            "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)],
        }
    )