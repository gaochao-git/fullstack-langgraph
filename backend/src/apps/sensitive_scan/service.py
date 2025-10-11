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

    def _count_jsonl_extractions(self, jsonl_path: Path) -> int:
        """
        从单个JSONL文件中计算唯一敏感项数量（辅助方法）
        统计去重后的敏感项数量，与HTML报告保持一致

        Args:
            jsonl_path: JSONL文件的完整路径

        Returns:
            唯一敏感项数量
        """
        unique_items = set()
        try:
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if 'extractions' in data:
                                for extraction in data['extractions']:
                                    # 使用(extraction_class, extraction_text)作为唯一标识去重
                                    ext_class = extraction.get('extraction_class', '')
                                    ext_text = extraction.get('extraction_text', '')
                                    if ext_class and ext_text:
                                        unique_items.add((ext_class, ext_text))
                        except:
                            pass
        except Exception as e:
            logger.warning(f"读取JSONL文件失败 {jsonl_path}: {e}")
        return len(unique_items)

    async def create_scan_task(
        self,
        db: AsyncSession,
        file_ids: List[str],
        config_id: Optional[str] = None,
        max_workers: int = 10,
        batch_length: int = 10,
        extraction_passes: int = 1,
        max_char_buffer: int = 2000,
        create_by: str = "system"
    ) -> Dict[str, Any]:
        """创建扫描任务"""
        async with db.begin():
            # 检查文件是否都已解析完成
            result = await db.execute(
                select(AgentDocumentUpload.file_id, AgentDocumentUpload.process_status, AgentDocumentUpload.file_name)
                .where(AgentDocumentUpload.file_id.in_(file_ids))
            )
            files = result.all()

            # 验证文件存在性
            found_file_ids = {f.file_id for f in files}
            missing_files = set(file_ids) - found_file_ids
            if missing_files:
                raise BusinessException(
                    f"文件不存在: {', '.join(missing_files)}",
                    ResponseCode.NOT_FOUND
                )

            # 检查文件解析状态 (0->uploaded, 1->processing, 2->ready, 3->failed)
            not_ready_files = []
            failed_files = []
            for f in files:
                if f.process_status == 3:  # failed
                    failed_files.append(f.file_name)
                elif f.process_status != 2:  # not ready
                    not_ready_files.append(f.file_name)

            if failed_files:
                raise BusinessException(
                    f"以下文件解析失败，无法扫描: {', '.join(failed_files)}",
                    ResponseCode.BAD_REQUEST
                )

            if not_ready_files:
                raise BusinessException(
                    f"以下文件尚未解析完成，请稍后再试: {', '.join(not_ready_files)}",
                    ResponseCode.BAD_REQUEST
                )

            logger.info(f"文件状态检查通过，共 {len(files)} 个文件，全部已解析完成")

            # 生成任务ID
            task_id = f"task_{uuid.uuid4().hex[:12]}"

            # 创建任务记录
            task = ScanTask(
                task_id=task_id,
                task_status='pending',
                task_errors=None,
                notify_status='pending',
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

            # 使用 Celery 启动后台扫描任务，传递配置和参数
            from .tasks import scan_files_task
            scan_files_task.delay(
                task_id,
                file_ids,
                config_id,
                max_workers,
                batch_length,
                extraction_passes,
                max_char_buffer
            )

            return {
                "task_id": task.task_id,
                "status": task.task_status,
                "total_files": len(file_ids),
                "create_time": task.create_time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    
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
            "notify_status": task.notify_status,
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
            "create_time": task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
            "start_time": task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else None,
            "end_time": task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else None
        }
    
    async def _count_sensitive_items(self, db: AsyncSession, task_id: str) -> int:
        """统计任务的所有敏感数据项数量"""
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
                    total_items += self._count_jsonl_extractions(full_path)

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

        logger.info(f"查询到任务: {task.task_id}, 状态: {task.task_status}")

        # 所有状态都查询文件列表，显示实时状态
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

        # 为每个文件计算敏感项数量
        files_data = []
        for scan_file, file_name in files_with_names:
            file_dict = {
                "file_id": scan_file.file_id,
                "file_name": file_name,  # 从 JOIN 结果获取
                "status": scan_file.file_status,
                "jsonl_path": scan_file.jsonl_path,
                "html_path": scan_file.html_path,
                "error": scan_file.file_error,
                "start_time": scan_file.start_time.strftime('%Y-%m-%d %H:%M:%S') if scan_file.start_time else None,
                "end_time": scan_file.end_time.strftime('%Y-%m-%d %H:%M:%S') if scan_file.end_time else None,
                "sensitive_items": 0  # 默认值
            }

            # 如果文件已完成且有JSONL结果，读取敏感项数量
            if scan_file.file_status == 'completed' and scan_file.jsonl_path:
                try:
                    jsonl_file_path = Path(settings.DOCUMENT_DIR) / scan_file.jsonl_path
                    if jsonl_file_path.exists():
                        file_dict["sensitive_items"] = self._count_jsonl_extractions(jsonl_file_path)
                except Exception as e:
                    logger.warning(f"读取JSONL文件失败 {scan_file.jsonl_path}: {e}")

            files_data.append(file_dict)

        return {
            "task_id": task.task_id,
            "status": task.task_status,
            "notify_status": task.notify_status,
            "summary": {
                "total_files": len(files_with_names),
                "completed_files": completed_files,
                "failed_files": failed_files
            },
            "files": files_data,
            "completed_time": task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else None
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
                "notify_status": task.notify_status,
                "total_files": file_stats['total'],
                "completed_files": file_stats['completed'],
                "failed_files": file_stats['failed'],
                "sensitive_items": sensitive_items,
                "create_by": task.create_by,
                "create_time": task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else None,
                "start_time": task.start_time.strftime('%Y-%m-%d %H:%M:%S') if task.start_time else None,
                "end_time": task.end_time.strftime('%Y-%m-%d %H:%M:%S') if task.end_time else None
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


# 创建服务实例
scan_task_service = LangExtractScanTaskService()