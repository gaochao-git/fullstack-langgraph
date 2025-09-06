"""敏感数据扫描智能体状态定义"""

from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import MessagesState


class ChunkState(TypedDict):
    """单个分片的状态"""
    chunk_id: str
    content: str
    scan_result: Optional[Dict[str, Any]]
    error: Optional[str]


class ScannerState(MessagesState):
    """敏感数据扫描智能体的主状态"""
    # 文件相关
    file_ids: List[str]  # 从请求中直接传入的文件ID列表
    file_contents: Dict[str, Dict[str, Any]]  # file_id -> {content, file_name, file_size}
    
    # 分片相关
    chunks: List[Dict[str, Any]]
    chunk_size: int
    max_parallel_chunks: int
    
    # 扫描结果
    scan_results: Dict[str, Any]  # 汇总的扫描结果
    chunk_results: List[Dict[str, Any]]  # 各分片的扫描结果
    
    # 敏感数据类型配置
    sensitive_types: List[str]  # 要扫描的敏感数据类型
    
    # 错误处理
    errors: List[str]
    
    # 最终报告
    final_report: Optional[str]