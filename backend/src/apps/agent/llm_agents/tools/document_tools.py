"""
通用文档工具 - 供所有智能体使用
"""

from typing import List
from langchain_core.tools import tool
from src.apps.agent.service.document_service import document_service
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@tool
def get_documents_content(file_ids: List[str]) -> str:
    """
    获取文档内容（支持单个或多个文档）
    
    Args:
        file_ids: 文档ID列表，可以是单个文档ID的列表如 ["file_id_1"]，
                 也可以是多个文档ID的列表如 ["file_id_1", "file_id_2"]
        
    Returns:
        文档内容，多个文档时会合并返回
    """
    try:
        if not file_ids:
            return "未提供文档ID"
            
        # 获取文档内容
        doc_context = document_service.get_document_context(file_ids)
        
        if doc_context:
            doc_count = len(file_ids)
            logger.info(f"✅ 成功获取 {doc_count} 个文档的内容，总长度: {len(doc_context)} 字符")
            return doc_context
        else:
            return f"未能获取文档内容，请检查文档ID是否正确: {file_ids}"
            
    except Exception as e:
        logger.error(f"获取文档内容失败: {e}")
        return f"获取文档内容时发生错误: {str(e)}"