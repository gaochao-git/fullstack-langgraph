"""
文档处理服务 - 负责文件解析和内容提取
"""
import os
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.shared.core.config import settings
from ..models import AgentDocumentUpload

logger = get_logger(__name__)

# 从配置中获取文件存储路径
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 从配置中获取支持的文件类型
SUPPORTED_FILE_TYPES = settings.UPLOAD_ALLOWED_EXTENSIONS

# 从配置中获取文件大小限制
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

# 处理状态枚举
class ProcessStatus:
    UPLOADED = 0
    PROCESSING = 1
    READY = 2
    FAILED = 3


class DocumentService:
    """文档处理服务"""
    
    async def upload_file(self, db: AsyncSession, file_content: bytes, filename: str, user_id: str) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            db: 数据库会话
            file_content: 文件内容
            filename: 文件名
            user_id: 用户ID
            
        Returns:
            文件信息
        """
        # 检查文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise BusinessException(
                f"文件大小超过限制（最大{settings.MAX_UPLOAD_SIZE_MB}MB）",
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
        # 安全处理：只使用生成的文件ID和扩展名，避免路径遍历
        safe_filename = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # 保存文件
        import aiofiles
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # 保存到数据库
        async with db.begin():
            doc_upload = AgentDocumentUpload(
                file_id=file_id,
                file_name=filename,
                file_size=len(file_content),
                file_type=file_ext,
                file_path=str(file_path),
                process_status=ProcessStatus.UPLOADED,
                create_by=user_id,
                update_by=user_id
            )
            db.add(doc_upload)
            await db.flush()
            
            # 获取生成的ID
            doc_id = doc_upload.id
        
        logger.info(f"文件上传成功: {filename} -> {file_id}")
        
        # 异步处理文档 - 使用后台任务，避免事务冲突
        import asyncio
        # 创建任务并保存引用，避免任务丢失
        task = asyncio.create_task(self._process_document_async(file_id))
        # 添加错误处理回调
        task.add_done_callback(lambda t: logger.error(f"文档处理任务异常: {t.exception()}") if t.exception() else None)
        
        return {
            "file_id": file_id,
            "file_name": filename,
            "file_size": len(file_content),
            "file_type": file_ext,
            "upload_time": now_shanghai().isoformat(),
            "status": "uploaded"
        }
    
    async def process_document(self, db: AsyncSession, file_id: str) -> None:
        """
        处理文档，提取内容
        
        Args:
            db: 数据库会话
            file_id: 文件ID
        """
        try:
            async with db.begin():
                # 查询文档记录
                result = await db.execute(
                    select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
                )
                doc_upload = result.scalar_one_or_none()
                
                if not doc_upload:
                    raise BusinessException("文件不存在", ResponseCode.NOT_FOUND)
                
                # 更新状态为处理中
                doc_upload.process_status = ProcessStatus.PROCESSING
                doc_upload.process_start_time = now_shanghai()
                await db.flush()
            
            file_path = Path(doc_upload.file_path)
            file_ext = doc_upload.file_type
            file_name = doc_upload.file_name
            
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
                    logger.info(f"PDF解析成功: {file_name}, 页数: {len(reader.pages)}")
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
                        
                    logger.info(f"Word文档解析成功: {file_name}")
                except Exception as e:
                    logger.error(f"Word文档解析错误: {e}")
                    full_text = f"Word文档解析失败: {str(e)}"
            else:
                # 不支持的格式
                full_text = f"[{file_ext} 文件: {file_name}]\n\n暂不支持此格式的文档解析。"
            
            # 如果没有提取到内容
            if not full_text.strip():
                full_text = f"[{file_name}]\n\n文档内容为空或无法提取文本内容。"
            
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
            
            # 更新数据库
            async with db.begin():
                # 重新查询文档记录
                result = await db.execute(
                    select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
                )
                doc_upload = result.scalar_one_or_none()
                if doc_upload:
                    doc_upload.process_status = ProcessStatus.READY
                    doc_upload.doc_content = full_text[:50000]  # 限制存储的内容长度
                    doc_upload.doc_chunks = json.dumps([{"id": i, "content": chunk} for i, chunk in enumerate(chunks[:50])])  # 限制块数
                    doc_upload.doc_metadata = json.dumps(metadata)
                    doc_upload.process_end_time = now_shanghai()
                    await db.flush()
            
            logger.info(f"文档处理完成: {file_id}, 类型: {file_ext}, 字符数: {metadata['char_count']}")
            
        except Exception as e:
            logger.error(f"文档处理失败: {file_id}, 错误: {str(e)}")
            # 更新失败状态 - 使用新的数据库会话
            from src.shared.db.config import get_async_db_context
            async with get_async_db_context() as error_db:
                result = await error_db.execute(
                    select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
                )
                doc_upload = result.scalar_one_or_none()
                if doc_upload:
                    doc_upload.process_status = ProcessStatus.FAILED
                    doc_upload.error_message = str(e)
                    doc_upload.process_end_time = now_shanghai()
                    await error_db.commit()
    
    async def get_document_content(self, db: AsyncSession, file_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取文档内容
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            文档内容
        """
        # 查询文档
        query = select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
        
        # 如果提供了用户ID，检查所有权
        if user_id:
            query = query.where(AgentDocumentUpload.create_by == user_id)
        
        result = await db.execute(query)
        doc_upload = result.scalar_one_or_none()
        
        if not doc_upload:
            return None
        
        if doc_upload.process_status != ProcessStatus.READY:
            return None
        
        # 解析JSON字段
        chunks = []
        metadata = {}
        try:
            if doc_upload.doc_chunks:
                chunks = json.loads(doc_upload.doc_chunks)
            if doc_upload.doc_metadata:
                metadata = json.loads(doc_upload.doc_metadata)
        except Exception as e:
            logger.error(f"解析JSON字段失败: {e}")
        
        return {
            "file_id": file_id,
            "file_name": doc_upload.file_name,
            "content": doc_upload.doc_content or "",
            "metadata": metadata,
            "chunks": chunks
        }
    
    async def get_file_status(self, db: AsyncSession, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文件处理状态
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            
        Returns:
            文件状态
        """
        result = await db.execute(
            select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
        )
        doc_upload = result.scalar_one_or_none()
        
        if not doc_upload:
            return None
        
        # 状态映射
        status_map = {
            ProcessStatus.UPLOADED: "uploaded",
            ProcessStatus.PROCESSING: "processing",
            ProcessStatus.READY: "ready",
            ProcessStatus.FAILED: "failed"
        }
        
        return {
            "file_id": file_id,
            "status": status_map.get(doc_upload.process_status, "unknown"),
            "message": doc_upload.error_message,
            "processed_at": doc_upload.process_end_time.isoformat() if doc_upload.process_end_time else None
        }
    
    def get_document_context(self, file_ids: List[str], max_length: int = 10000) -> str:
        """
        获取文档上下文（用于对话）
        注意：这是同步方法，因为在 streaming.py 中被同步调用
        
        Args:
            file_ids: 文件ID列表
            max_length: 最大长度限制
            
        Returns:
            文档上下文文本
        """
        from src.shared.db.config import get_sync_db
        
        context_parts = []
        current_length = 0
        
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            for file_id in file_ids:
                result = db.query(AgentDocumentUpload).filter(
                    AgentDocumentUpload.file_id == file_id,
                    AgentDocumentUpload.process_status == ProcessStatus.READY
                ).first()
                
                if not result:
                    continue
                
                content = result.doc_content or ""
                file_name = result.file_name
                
                # 如果内容太长，只取前面部分
                if current_length + len(content) > max_length:
                    remaining = max_length - current_length
                    if remaining > 100:  # 至少保留100字符
                        content = content[:remaining] + "..."
                    else:
                        break
                
                context_parts.append(f"【文档：{file_name}】\n{content}")
                current_length += len(content)
        finally:
            db.close()
        
        return "\n\n".join(context_parts)


    async def _process_document_async(self, file_id: str) -> None:
        """
        异步处理文档的包装方法
        """
        try:
            # 使用独立的数据库会话
            from src.shared.db.config import get_async_db_context
            async with get_async_db_context() as db:
                await self.process_document(db, file_id)
        except Exception as e:
            logger.error(f"异步处理文档失败: {file_id}, 错误: {str(e)}")

    async def get_file_info(self, db: AsyncSession, file_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取文件信息（用于下载）
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            文件信息字典，包含 file_path 和 file_name
        """
        # 查询文档
        query = select(AgentDocumentUpload).where(AgentDocumentUpload.file_id == file_id)
        
        # 如果提供了用户ID，检查所有权
        if user_id:
            query = query.where(AgentDocumentUpload.create_by == user_id)
        
        result = await db.execute(query)
        doc_upload = result.scalar_one_or_none()
        
        if not doc_upload:
            return None
        
        # 构建文件路径，需要加上文件扩展名
        file_path = os.path.join(UPLOAD_DIR, f"{doc_upload.file_id}{doc_upload.file_type}")
        
        return {
            "file_id": doc_upload.file_id,
            "file_name": doc_upload.file_name,
            "file_path": file_path,
            "file_type": doc_upload.file_type,
            "file_size": doc_upload.file_size,
            "upload_time": doc_upload.upload_time.isoformat() if doc_upload.upload_time else None
        }


# 全局文档服务实例
document_service = DocumentService()