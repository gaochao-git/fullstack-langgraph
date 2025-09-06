"""
通用文档工具 - 供所有智能体使用
"""

from typing import List, Dict, Any
from langchain_core.tools import tool
from src.apps.agent.service.document_service import document_service
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@tool
def get_documents_content(file_ids: List[str]) -> str:
    """
    获取多个文档的内容
    
    Args:
        file_ids: 文档ID列表
        
    Returns:
        所有文档的合并内容
    """
    try:
        if not file_ids:
            return "未提供文档ID"
            
        # 获取文档内容
        doc_context = document_service.get_document_context(file_ids)
        
        if doc_context:
            logger.info(f"成功获取 {len(file_ids)} 个文档的内容，总长度: {len(doc_context)} 字符")
            return doc_context
        else:
            return f"未能获取文档内容，请检查文档ID是否正确: {file_ids}"
            
    except Exception as e:
        logger.error(f"获取文档内容失败: {e}")
        return f"获取文档内容时发生错误: {str(e)}"


@tool  
def get_single_document_content(file_id: str) -> Dict[str, Any]:
    """
    获取单个文档的详细信息
    
    Args:
        file_id: 文档ID
        
    Returns:
        包含文档信息和内容的字典
    """
    try:
        from src.shared.db.config import get_sync_db
        from src.apps.agent.models import AgentDocumentUpload
        from sqlalchemy import select
        
        db_gen = get_sync_db()
        db = next(db_gen)
        
        try:
            # 查询文档
            result = db.execute(
                select(AgentDocumentUpload).where(
                    AgentDocumentUpload.file_id == file_id
                )
            )
            document = result.scalar_one_or_none()
            
            if not document:
                return {
                    "success": False,
                    "error": f"找不到文档ID: {file_id}"
                }
            
            # 检查处理状态
            if document.process_status != 2:  # 2 = READY
                return {
                    "success": False,
                    "error": f"文档尚未处理完成，当前状态: {document.process_status}"
                }
            
            return {
                "success": True,
                "file_id": file_id,
                "file_name": document.file_name,
                "file_size": document.file_size,
                "content": document.doc_content,
                "upload_time": str(document.upload_time)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        return {
            "success": False,
            "error": f"获取文档时发生错误: {str(e)}"
        }