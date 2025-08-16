"""
文档处理服务 - 负责文件解析和内容提取
"""
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# 文档解析库
try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    
try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.db.models import now_shanghai

logger = get_logger(__name__)

# 文件存储路径
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 支持的文件类型
SUPPORTED_FILE_TYPES = ['.pdf', '.docx', '.txt', '.md']  # 暂时移除 .doc，因为需要额外的库

# 文件大小限制（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentService:
    """文档处理服务"""
    
    def __init__(self):
        # 存储处理后的文档内容（实际应用中应该使用数据库）
        self.document_store: Dict[str, Dict[str, Any]] = {}
    
    async def upload_file(self, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            user_id: 用户ID
            
        Returns:
            文件信息
        """
        # 检查文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise BusinessException(
                f"文件大小超过限制（最大{MAX_FILE_SIZE/1024/1024}MB）",
                ResponseCode.BAD_REQUEST
            )
        
        # 检查文件类型
        file_ext = Path(filename).suffix.lower()
        if file_ext not in SUPPORTED_FILE_TYPES:
            raise BusinessException(
                f"不支持的文件类型：{file_ext}",
                ResponseCode.BAD_REQUEST
            )
        
        # 生成文件ID和保存路径
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_DIR / f"{file_id}{file_ext}"
        
        # 保存文件
        import aiofiles
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # 记录文件信息
        file_info = {
            "file_id": file_id,
            "file_name": filename,
            "file_size": len(file_content),
            "file_type": file_ext,
            "file_path": str(file_path),
            "upload_time": now_shanghai().isoformat(),
            "upload_by": user_id,
            "status": "uploaded"
        }
        
        self.document_store[file_id] = file_info
        logger.info(f"文件上传成功: {filename} -> {file_id}")
        
        # 异步处理文档
        # 实际应用中应该使用消息队列或后台任务
        await self.process_document(file_id)
        
        return file_info
    
    async def process_document(self, file_id: str) -> None:
        """
        处理文档，提取内容
        
        Args:
            file_id: 文件ID
        """
        try:
            file_info = self.document_store.get(file_id)
            if not file_info:
                raise BusinessException("文件不存在", ResponseCode.NOT_FOUND)
            
            # 更新状态为处理中
            file_info["status"] = "processing"
            
            file_path = Path(file_info["file_path"])
            file_ext = file_info["file_type"]
            
            # 根据文件类型提取文本
            full_text = ""
            
            if file_ext == '.txt' or file_ext == '.md':
                # 文本文件直接读取
                with open(file_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
                    
            elif file_ext == '.pdf' and HAS_PDF:
                # PDF文件解析
                try:
                    reader = PdfReader(str(file_path))
                    text_parts = []
                    for page_num, page in enumerate(reader.pages):
                        text = page.extract_text()
                        if text:
                            text_parts.append(f"[第{page_num + 1}页]\n{text}")
                    full_text = "\n\n".join(text_parts)
                    logger.info(f"PDF解析成功: {file_info['file_name']}, 页数: {len(reader.pages)}")
                except Exception as e:
                    logger.error(f"PDF解析错误: {e}")
                    full_text = f"PDF文件解析失败: {str(e)}"
                    
            elif file_ext == '.docx' and HAS_DOCX:
                # Word文档解析
                try:
                    doc = docx.Document(str(file_path))
                    paragraphs = []
                    for para in doc.paragraphs:
                        if para.text.strip():
                            paragraphs.append(para.text)
                    full_text = "\n\n".join(paragraphs)
                    
                    # 也提取表格内容
                    for table in doc.tables:
                        table_text = "\n[表格]\n"
                        for row in table.rows:
                            row_text = " | ".join([cell.text.strip() for cell in row.cells])
                            table_text += row_text + "\n"
                        full_text += "\n" + table_text
                        
                    logger.info(f"Word文档解析成功: {file_info['file_name']}")
                except Exception as e:
                    logger.error(f"Word文档解析错误: {e}")
                    full_text = f"Word文档解析失败: {str(e)}"
            else:
                # 不支持的格式
                full_text = f"[{file_ext} 文件: {file_info['file_name']}]\n\n暂不支持此格式的文档解析。"
            
            # 如果没有提取到内容
            if not full_text.strip():
                full_text = f"[{file_info['file_name']}]\n\n文档内容为空或无法提取文本内容。"
            
            # 分块处理
            chunk_size = 1000
            chunk_overlap = 200
            chunks = []
            
            if len(full_text) <= chunk_size:
                chunks = [full_text]
            else:
                for i in range(0, len(full_text), chunk_size - chunk_overlap):
                    chunk = full_text[i:i + chunk_size]
                    chunks.append(chunk)
            
            # 提取元数据
            metadata = {
                "char_count": len(full_text),
                "chunk_count": len(chunks),
                "file_type": file_ext
            }
            
            # 更新文档内容
            file_info.update({
                "status": "ready",
                "content": full_text[:50000],  # 限制存储的内容长度
                "chunks": [{"id": i, "content": chunk} for i, chunk in enumerate(chunks[:50])],  # 限制块数
                "metadata": metadata,
                "processed_at": now_shanghai().isoformat()
            })
            
            logger.info(f"文档处理完成: {file_id}, 类型: {file_ext}, 字符数: {metadata['char_count']}")
            
        except Exception as e:
            logger.error(f"文档处理失败: {file_id}, 错误: {str(e)}")
            if file_id in self.document_store:
                self.document_store[file_id].update({
                    "status": "failed",
                    "message": str(e)
                })
    
    async def get_document_content(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档内容
        
        Args:
            file_id: 文件ID
            
        Returns:
            文档内容
        """
        file_info = self.document_store.get(file_id)
        if not file_info:
            return None
        
        if file_info["status"] != "ready":
            return None
        
        return {
            "file_id": file_id,
            "file_name": file_info["file_name"],
            "content": file_info.get("content", ""),
            "metadata": file_info.get("metadata", {}),
            "chunks": file_info.get("chunks", [])
        }
    
    async def get_file_status(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件处理状态
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件状态
        """
        file_info = self.document_store.get(file_id)
        if not file_info:
            return None
        
        return {
            "file_id": file_id,
            "status": file_info["status"],
            "message": file_info.get("message"),
            "processed_at": file_info.get("processed_at")
        }
    
    def get_document_context(self, file_ids: List[str], max_length: int = 10000) -> str:
        """
        获取文档上下文（用于对话）
        
        Args:
            file_ids: 文件ID列表
            max_length: 最大长度限制
            
        Returns:
            文档上下文文本
        """
        context_parts = []
        current_length = 0
        
        for file_id in file_ids:
            file_info = self.document_store.get(file_id)
            if not file_info or file_info["status"] != "ready":
                continue
            
            content = file_info.get("content", "")
            file_name = file_info["file_name"]
            
            # 如果内容太长，只取前面部分
            if current_length + len(content) > max_length:
                remaining = max_length - current_length
                if remaining > 100:  # 至少保留100字符
                    content = content[:remaining] + "..."
                else:
                    break
            
            context_parts.append(f"【文档：{file_name}】\n{content}")
            current_length += len(content)
        
        return "\n\n".join(context_parts)


# 全局文档服务实例
document_service = DocumentService()