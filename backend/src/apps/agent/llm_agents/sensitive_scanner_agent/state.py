"""敏感数据扫描智能体状态定义"""
from typing import List, Dict, Any, Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class OverallState(TypedDict, total=False):
    """扫描器状态 - 显式定义所有字段"""
    # 消息列表 - 使用Annotated和add_messages来支持消息的追加
    messages: Annotated[list[AnyMessage], add_messages]
    
    # 输入：要扫描的文件ID列表（可选，也可以从messages中提取）
    file_ids: List[str]
    
    # 输入：用户输入的文本内容（从messages中提取）
    user_input_text: str
    
    # 中间状态：从数据库获取的文件内容
    file_contents: Dict[str, Dict[str, Any]]  # {file_id: {content, file_name, file_size}}
    
    # 输出：扫描结果
    scan_results: Dict[str, List[Dict[str, Any]]]  # {file_id/user_input: [敏感数据列表]}
    
    # 错误信息
    errors: List[str]


