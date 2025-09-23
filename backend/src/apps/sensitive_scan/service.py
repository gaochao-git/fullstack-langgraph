"""敏感数据扫描任务服务层 - 使用原生langextract实现"""

import asyncio
import uuid
import json
import difflib
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

import langextract as lx

from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.config import settings
from .models import ScanTask, ScanFile
from .langextract_scanner import LangExtractSensitiveScanner
from src.apps.agent.models import AgentDocumentUpload

logger = get_logger(__name__)


class LangExtractScanTaskService:
    """扫描任务服务层 - 使用langextract实现"""
    
    def __init__(self):
        # 确保扫描结果目录存在
        # 使用 DOCUMENT_DIR 而不是 UPLOAD_DIR，将 scan_results 放在文档根目录下
        self.scan_results_dir = Path(settings.DOCUMENT_DIR) / "scan_results"
        self.scan_results_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化扫描器
        # 从settings读取配置，必须配置
        if not settings.LLM_MODEL or not settings.LLM_API_KEY or not settings.LLM_BASE_URL:
            raise ValueError("必须在配置文件中设置 LLM_MODEL, LLM_API_KEY 和 LLM_BASE_URL")
        
        # 扫描器会自动从settings获取配置
        self.scanner = LangExtractSensitiveScanner()
    
    async def create_scan_task(
        self, 
        db: AsyncSession,
        file_ids: List[str],
        create_by: str = "system"
    ) -> Dict[str, Any]:
        """创建扫描任务"""
        async with db.begin():
            # 生成任务ID
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            
            # 创建任务记录
            task = ScanTask(
                task_id=task_id,
                task_status='pending',
                task_errors=None,
                create_by=create_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            db.add(task)
            
            # 创建文件记录
            for file_id in file_ids:
                file_record = ScanFile(
                    task_id=task_id,
                    file_id=file_id,
                    file_status='pending',
                    create_by=create_by,
                    create_time=now_shanghai(),
                    update_time=now_shanghai()
                )
                db.add(file_record)
            
            await db.flush()
            await db.refresh(task)
            
            # 使用 Celery 启动后台扫描任务
            from .tasks import scan_files_task
            scan_files_task.delay(task_id, file_ids)
            
            return {
                "task_id": task.task_id,
                "status": task.task_status,
                "total_files": len(file_ids),
                "create_time": task.create_time.isoformat()
            }
    
    async def _process_scan_task(self, task_id: str, file_ids: List[str]):
        """后台处理扫描任务"""
        from src.shared.db.config import get_async_db_context
        
        logger.info(f"开始处理扫描任务: {task_id}")
        
        try:
            async with get_async_db_context() as db:
                # 更新任务状态为处理中
                async with db.begin():
                    await db.execute(
                        update(ScanTask)
                        .where(ScanTask.task_id == task_id)
                        .values(
                            task_status='processing',
                            start_time=now_shanghai(),
                            update_time=now_shanghai()
                        )
                    )
                
                # 处理每个文件
                for file_id in file_ids:
                    await self._scan_file_with_langextract(task_id, file_id)
                
                # 更新任务状态为完成
                async with db.begin():
                    await db.execute(
                        update(ScanTask)
                        .where(ScanTask.task_id == task_id)
                        .values(
                            task_status='completed',
                            end_time=now_shanghai(),
                            update_time=now_shanghai()
                        )
                    )
                    
        except Exception as e:
            logger.error(f"扫描任务失败 {task_id}: {str(e)}")
            async with get_async_db_context() as db:
                async with db.begin():
                    await db.execute(
                        update(ScanTask)
                        .where(ScanTask.task_id == task_id)
                        .values(
                            task_status='failed',
                            task_errors=str(e),
                            end_time=now_shanghai(),
                            update_time=now_shanghai()
                        )
                    )
    
    async def _scan_file_with_langextract(self, task_id: str, file_id: str):
        """使用langextract扫描单个文件"""
        from src.shared.db.config import get_async_db_context
        
        try:
            # 使用独立的数据库会话
            async with get_async_db_context() as scan_db:
                # 更新文件状态为读取中
                async with scan_db.begin():
                    await scan_db.execute(
                        update(ScanFile)
                        .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                        .values(
                            file_status='reading',
                            start_time=now_shanghai(),
                            update_time=now_shanghai()
                        )
                    )
                
                # 构建文件路径
                file_path = Path(settings.UPLOAD_DIR) / f"{file_id}.txt"
                
                if not file_path.exists() or not file_path.is_file():
                    # 尝试解析后的文件
                    file_path = Path(settings.UPLOAD_DIR) / f"{file_id}.parse.txt"
                    
                if not file_path.exists() or not file_path.is_file():
                    raise Exception(f"文件不存在: {file_path}")
                
                # 获取文件名
                original_filename = file_path.name
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 更新文件状态为扫描中
                async with scan_db.begin():
                    await scan_db.execute(
                        update(ScanFile)
                        .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                        .values(
                            file_status='scanning',
                            update_time=now_shanghai()
                        )
                    )
                
                # 使用langextract进行扫描
                logger.info(f"开始使用langextract扫描文件: {file_id}")
                
                # 在异步上下文中运行同步代码
                loop = asyncio.get_event_loop()
                
                def scan_sync():
                    # 使用scanner进行扫描
                    result = self.scanner.scan_document(file_id, content)
                    return result
                
                # 在线程池中执行同步操作
                scan_result = await loop.run_in_executor(None, scan_sync)
                
                if not scan_result["success"]:
                    raise Exception(f"扫描失败: {scan_result.get('error', '未知错误')}")
                
                logger.info(f"langextract扫描完成: {file_id}, 发现 {scan_result['extractions']} 个敏感信息")
                
                # 创建任务目录
                task_dir = self.scan_results_dir / task_id
                task_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成输出文件路径
                base_name = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                jsonl_path = task_dir / f"{base_name}.jsonl"
                html_path = task_dir / f"{base_name}.html"
                
                # 保存JSONL结果
                if scan_result["document"]:
                    # 保存langextract格式的JSONL
                    self.scanner.save_results([scan_result["document"]], str(jsonl_path))
                else:
                    # 如果没有提取到任何内容，保存空结果
                    with open(jsonl_path, 'w', encoding='utf-8') as f:
                        empty_result = {
                            "document_id": file_id,
                            "text": content[:200] + "..." if len(content) > 200 else content,
                            "extractions": []
                        }
                        f.write(json.dumps(empty_result, ensure_ascii=False) + '\n')
                
                # 修复JSONL中的char_interval
                await self._fix_jsonl_char_intervals(str(jsonl_path), content)
                
                # 生成可视化HTML
                def generate_html_sync():
                    return self.scanner.generate_visualization(str(jsonl_path), str(html_path))
                
                await loop.run_in_executor(None, generate_html_sync)
                
                # 返回相对路径
                jsonl_relative = f"scan_results/{task_id}/{base_name}.jsonl"
                html_relative = f"scan_results/{task_id}/{base_name}.html"
                
                # 更新文件状态为完成
                async with scan_db.begin():
                    await scan_db.execute(
                        update(ScanFile)
                        .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                        .values(
                            file_status='completed',
                            jsonl_path=jsonl_relative,
                            html_path=html_relative,
                            end_time=now_shanghai(),
                            update_time=now_shanghai()
                        )
                    )
                    
        except Exception as e:
            logger.error(f"扫描文件失败 {file_id}: {str(e)}")
            async with get_async_db_context() as error_db:
                async with error_db.begin():
                    await error_db.execute(
                        update(ScanFile)
                        .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                        .values(
                            file_status='failed',
                            file_error=str(e),
                            end_time=now_shanghai(),
                            update_time=now_shanghai()
                        )
                    )
    
    async def get_task_progress(
        self,
        db: AsyncSession,
        task_id: str
    ) -> Dict[str, Any]:
        """获取任务进度"""
        # 查询任务
        result = await db.execute(
            select(ScanTask).where(ScanTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise BusinessException(f"任务不存在: {task_id}", ResponseCode.NOT_FOUND)
        
        # 获取文件状态统计
        file_status_result = await db.execute(
            select(
                ScanFile.file_status,
                func.count(ScanFile.id).label('count')
            )
            .where(ScanFile.task_id == task_id)
            .group_by(ScanFile.file_status)
        )
        
        file_status_summary = {}
        total_files = 0
        processed_files = 0
        failed_files = 0
        
        for row in file_status_result:
            status = row.file_status
            count = row.count
            file_status_summary[status] = count
            total_files += count
            
            if status in ['completed', 'failed']:
                processed_files += count
            if status == 'failed':
                failed_files += count
        
        # 构建进度信息
        progress = {
            "phase": task.task_status,
            "current": processed_files,
            "total": total_files,
            "message": self._get_progress_message(task.task_status, processed_files, total_files)
        }
        
        # 解析错误信息
        errors = []
        if task.task_errors:
            try:
                errors = json.loads(task.task_errors)
            except:
                errors = [task.task_errors]
        
        return {
            "task_id": task.task_id,
            "status": task.task_status,
            "total_files": total_files,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "progress": progress,
            "statistics": {
                "processed_files": processed_files,
                "sensitive_items": await self._count_sensitive_items(db, task_id)
            },
            "file_status_summary": file_status_summary,
            "errors": errors,
            "create_time": task.create_time.isoformat(),
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None
        }
    
    async def _count_sensitive_items(self, db: AsyncSession, task_id: str) -> int:
        """统计敏感数据项数量"""
        # 查询所有完成的文件
        result = await db.execute(
            select(ScanFile.jsonl_path)
            .where(and_(
                ScanFile.task_id == task_id,
                ScanFile.file_status == 'completed',
                ScanFile.jsonl_path.isnot(None)
            ))
        )
        
        total_items = 0
        for row in result:
            jsonl_path = row.jsonl_path
            if jsonl_path:
                full_path = Path(settings.DOCUMENT_DIR) / jsonl_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        # langextract生成的JSONL格式
                        for line in f:
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    # 计算提取的敏感数据数量
                                    if 'extractions' in data:
                                        total_items += len(data['extractions'])
                                except:
                                    pass
        
        return total_items
    
    async def get_task_result(
        self,
        db: AsyncSession,
        task_id: str
    ) -> Dict[str, Any]:
        """获取任务结果"""
        # 查询任务
        result = await db.execute(
            select(ScanTask).where(ScanTask.task_id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise BusinessException(f"任务不存在: {task_id}", ResponseCode.NOT_FOUND)
        
        if task.task_status not in ['completed', 'failed']:
            raise BusinessException(
                f"任务未完成，当前状态: {task.task_status}", 
                ResponseCode.BAD_REQUEST
            )
        
        # 使用 LEFT JOIN 一次查询获取所有文件信息和文件名
        files_result = await db.execute(
            select(ScanFile, AgentDocumentUpload.file_name)
            .outerjoin(
                AgentDocumentUpload,
                ScanFile.file_id == AgentDocumentUpload.file_id
            )
            .where(ScanFile.task_id == task_id)
        )
        files_with_names = files_result.all()
        
        # 统计信息 - 使用聚合查询优化
        stats_result = await db.execute(
            select(
                ScanFile.file_status,
                func.count(ScanFile.id).label('count')
            )
            .where(ScanFile.task_id == task_id)
            .group_by(ScanFile.file_status)
        )
        
        status_counts = {row.file_status: row.count for row in stats_result}
        completed_files = status_counts.get('completed', 0)
        failed_files = status_counts.get('failed', 0)
        
        return {
            "task_id": task.task_id,
            "status": task.task_status,
            "summary": {
                "total_files": len(files_with_names),
                "completed_files": completed_files,
                "failed_files": failed_files
            },
            "files": [
                {
                    "file_id": scan_file.file_id,
                    "file_name": file_name,  # 从 JOIN 结果获取
                    "status": scan_file.file_status,
                    "jsonl_path": scan_file.jsonl_path,
                    "html_path": scan_file.html_path,
                    "error": scan_file.file_error,
                    "start_time": scan_file.start_time.isoformat() if scan_file.start_time else None,
                    "end_time": scan_file.end_time.isoformat() if scan_file.end_time else None
                }
                for scan_file, file_name in files_with_names
            ],
            "completed_time": task.end_time.isoformat() if task.end_time else None
        }
    
    async def list_tasks(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        create_by: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """查询任务列表"""
        # 构建查询条件
        conditions = []
        if create_by:
            conditions.append(ScanTask.create_by == create_by)
        if task_id:
            conditions.append(ScanTask.task_id.contains(task_id))
        
        # 查询总数
        count_query = select(func.count(ScanTask.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        offset = (page - 1) * size
        query = select(ScanTask).order_by(ScanTask.create_time.desc())
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(offset).limit(size)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # 转换为字典列表
        task_list = []
        for task in tasks:
            # 获取文件统计
            file_stats = await self._get_task_file_stats(db, task.task_id)
            
            # 获取敏感项统计（仅对已完成的任务）
            sensitive_items = 0
            if task.task_status == 'completed':
                sensitive_items = await self._count_sensitive_items(db, task.task_id)
            
            task_list.append({
                "task_id": task.task_id,
                "status": task.task_status,
                "total_files": file_stats['total'],
                "completed_files": file_stats['completed'],
                "failed_files": file_stats['failed'],
                "sensitive_items": sensitive_items,
                "create_by": task.create_by,
                "create_time": task.create_time.isoformat(),
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None
            })
        
        return task_list, total
    
    async def _get_task_file_stats(self, db: AsyncSession, task_id: str) -> Dict[str, int]:
        """获取任务文件统计"""
        result = await db.execute(
            select(
                ScanFile.file_status,
                func.count(ScanFile.id).label('count')
            )
            .where(ScanFile.task_id == task_id)
            .group_by(ScanFile.file_status)
        )
        
        stats = {'total': 0, 'completed': 0, 'failed': 0}
        for row in result:
            status = row.file_status
            count = row.count
            stats['total'] += count
            if status == 'completed':
                stats['completed'] = count
            elif status == 'failed':
                stats['failed'] = count
        
        return stats
    
    def _get_progress_message(self, status: str, processed: int, total: int) -> str:
        """生成进度消息"""
        if status == 'pending':
            return "任务已创建，等待处理..."
        elif status == 'processing':
            return f"正在扫描中... ({processed}/{total})"
        elif status == 'completed':
            return f"扫描完成 ({processed}/{total})"
        elif status == 'failed':
            return "任务失败"
        else:
            return "未知状态"
    
    async def get_result_jsonl_content(
        self,
        db: AsyncSession,
        task_id: str,
        file_id: str
    ) -> str:
        """获取JSONL结果文件内容"""
        # 查询文件记录
        result = await db.execute(
            select(ScanFile).where(and_(
                ScanFile.task_id == task_id,
                ScanFile.file_id == file_id
            ))
        )
        scan_file = result.scalar_one_or_none()
        
        if not scan_file:
            raise BusinessException(
                f"扫描文件不存在: task_id={task_id}, file_id={file_id}", 
                ResponseCode.NOT_FOUND
            )
        
        if not scan_file.jsonl_path:
            raise BusinessException(
                "该文件尚未完成扫描或扫描失败",
                ResponseCode.BAD_REQUEST
            )
        
        # 构建完整路径
        full_path = Path(settings.DOCUMENT_DIR) / scan_file.jsonl_path
        
        if not full_path.exists():
            raise BusinessException(
                "结果文件不存在",
                ResponseCode.NOT_FOUND
            )
        
        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    async def get_result_html_content(
        self,
        db: AsyncSession,
        task_id: str,
        file_id: str
    ) -> str:
        """获取HTML报告文件内容"""
        # 查询文件记录
        result = await db.execute(
            select(ScanFile).where(and_(
                ScanFile.task_id == task_id,
                ScanFile.file_id == file_id
            ))
        )
        scan_file = result.scalar_one_or_none()
        
        if not scan_file:
            raise BusinessException(
                f"扫描文件不存在: task_id={task_id}, file_id={file_id}", 
                ResponseCode.NOT_FOUND
            )
        
        if not scan_file.html_path:
            raise BusinessException(
                "该文件尚未完成扫描或扫描失败",
                ResponseCode.BAD_REQUEST
            )
        
        # 构建完整路径
        full_path = Path(settings.DOCUMENT_DIR) / scan_file.html_path
        
        if not full_path.exists():
            raise BusinessException(
                "报告文件不存在",
                ResponseCode.NOT_FOUND
            )
        
        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    async def _fix_jsonl_char_intervals(self, jsonl_path: str, original_text: str) -> None:
        """
        修复JSONL文件中缺失的char_interval
        
        Args:
            jsonl_path: JSONL文件路径
            original_text: 原始文本内容
        """
        try:
            # 读取JSONL
            documents = []
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        documents.append(json.loads(line))
            
            fixed_count = 0
            
            # 修复每个文档
            for doc in documents:
                text = doc.get('text', original_text)  # 使用原始文本
                extractions = doc.get('extractions', [])
                
                for extraction in extractions:
                    # 检查是否需要修复
                    char_interval = extraction.get('char_interval')
                    if char_interval is None or (isinstance(char_interval, dict) and char_interval.get('start_pos') is None):
                        # 尝试找到位置
                        extraction_text = extraction.get('extraction_text', '')
                        position = self._find_text_position(text, extraction_text)
                        
                        if position:
                            extraction['char_interval'] = {
                                'start_pos': position[0],
                                'end_pos': position[1]
                            }
                            extraction['alignment_status'] = 'match_fuzzy'
                            fixed_count += 1
            
            # 保存修复后的JSONL
            if fixed_count > 0:
                with open(jsonl_path, 'w', encoding='utf-8') as f:
                    for doc in documents:
                        json.dump(doc, f, ensure_ascii=False)
                        f.write('\n')
                logger.info(f"修复了 {fixed_count} 个提取的位置信息")
                
        except Exception as e:
            logger.warning(f"修复JSONL失败: {e}")
    
    def _find_text_position(self, text: str, extraction_text: str) -> Optional[Tuple[int, int]]:
        """
        尝试在文本中找到提取文本的位置
        
        Returns:
            (start_pos, end_pos) 或 None
        """
        # 只进行精确匹配
        pos = text.find(extraction_text)
        if pos >= 0:
            return (pos, pos + len(extraction_text))
        
        return None


# 创建服务实例
scan_task_service = LangExtractScanTaskService()