"""敏感数据扫描任务服务层"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, delete
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.config import settings
from .models import ScanTask, ScanFile, TaskStatus, FileStatus
from .scanner import sensitive_scanner

logger = get_logger(__name__)

# 创建线程池用于执行CPU密集型的扫描任务
executor = ThreadPoolExecutor(max_workers=settings.SCAN_EXECUTOR_WORKERS)


class ScanTaskService:
    """扫描任务服务层"""
    
    async def create_scan_task(
        self, 
        db: AsyncSession,
        file_ids: List[str],
        create_by: str = "system"
    ) -> Dict[str, Any]:
        """创建扫描任务并启动后台处理"""
        async with db.begin():
            # 生成任务ID
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            
            # 创建任务记录
            progress_data = {
                "phase": "pending",
                "current": 0,
                "total": len(file_ids),
                "message": "任务已创建，等待处理..."
            }
            statistics_data = {
                "processed_files": 0,
                "sensitive_items": 0
            }
            
            task = ScanTask(
                task_id=task_id,
                status=TaskStatus.PENDING,
                total_files=len(file_ids),
                processed_files=0,
                failed_files=0,
                progress=json.dumps(progress_data, ensure_ascii=False),
                statistics=json.dumps(statistics_data, ensure_ascii=False),
                errors=json.dumps([], ensure_ascii=False),
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
                    status=FileStatus.PENDING,
                    create_by=create_by,
                    create_time=now_shanghai(),
                    update_time=now_shanghai()
                )
                db.add(file_record)
            
            await db.flush()
            await db.refresh(task)
            
            # 启动后台任务处理
            asyncio.create_task(self._process_scan_task(task_id, file_ids, create_by))
            
            return self._task_to_dict(task)
    
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
        
        # 获取文件状态摘要
        file_status_summary = await self._get_file_status_summary(db, task_id)
        
        task_dict = self._task_to_dict(task)
        task_dict["file_status_summary"] = file_status_summary
        
        return task_dict
    
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
        
        if task.status != TaskStatus.COMPLETED:
            raise BusinessException(
                f"任务未完成，当前状态: {task.status.value}", 
                ResponseCode.BAD_REQUEST
            )
        
        # 获取所有文件的扫描结果
        files_result = await db.execute(
            select(ScanFile).where(ScanFile.task_id == task_id)
        )
        files = files_result.scalars().all()
        
        task_dict = self._task_to_dict(task)
        task_dict["files"] = [self._file_to_dict(f) for f in files]
        
        return task_dict
    
    async def list_tasks(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        create_by: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """查询任务列表"""
        # 构建查询条件
        query = select(ScanTask)
        
        if create_by:
            query = query.where(ScanTask.create_by == create_by)
        
        # 查询总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        
        # 分页查询
        query = query.order_by(ScanTask.create_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return [self._task_to_dict(task) for task in tasks], total
    
    async def _process_scan_task(self, task_id: str, file_ids: List[str], create_by: str):
        """后台处理扫描任务"""
        from src.shared.db.config import get_async_db_context
        
        try:
            async with get_async_db_context() as db:
                # 更新任务状态为处理中
                async with db.begin():
                    await self._update_task_status(
                        db, task_id, TaskStatus.PROCESSING, update_by=create_by
                    )
                
                # 从文档服务读取文件内容
                from src.apps.agent.service.document_service import document_service
                
                file_contents = []
                for i, file_id in enumerate(file_ids, 1):
                    try:
                        # 更新进度
                        progress = {
                            "phase": "reading",
                            "current": i,
                            "total": len(file_ids),
                            "message": f"读取文件 {i}/{len(file_ids)}: {file_id[:8]}..."
                        }
                        async with db.begin():
                            await self._update_task_progress(db, task_id, progress, create_by)
                            await self._update_file_status(
                                db, task_id, file_id, FileStatus.READING, update_by=create_by
                            )
                        
                        # 读取文件内容
                        doc_info = await document_service.get_document_by_id(db, file_id)
                        if doc_info and doc_info.get("doc_content"):
                            file_contents.append({
                                "file_id": file_id,
                                "content": doc_info["doc_content"]
                            })
                            
                            async with db.begin():
                                await self._update_file_status(
                                    db, task_id, file_id, FileStatus.READ_COMPLETE, update_by=create_by
                                )
                        else:
                            raise Exception("文件内容为空")
                            
                    except Exception as e:
                        logger.error(f"读取文件 {file_id} 失败: {e}")
                        async with db.begin():
                            await self._update_file_status(
                                db, task_id, file_id, FileStatus.FAILED,
                                error=str(e), update_by=create_by
                            )
                            await self._add_task_error(
                                db, task_id, f"读取文件 {file_id} 失败: {str(e)}", create_by
                            )
                
                if not file_contents:
                    raise Exception("没有可扫描的文件")
                
                # 执行扫描
                output_dir = getattr(settings, 'SCAN_OUTPUT_DIR', '/tmp/scan_visualizations')
                
                for i, file_item in enumerate(file_contents, 1):
                    file_id = file_item['file_id']
                    try:
                        # 更新进度
                        progress = {
                            "phase": "scanning",
                            "current": i,
                            "total": len(file_contents),
                            "message": f"扫描文件 {i}/{len(file_contents)}: {file_id[:8]}..."
                        }
                        async with db.begin():
                            await self._update_task_progress(db, task_id, progress, create_by)
                            await self._update_file_status(
                                db, task_id, file_id, FileStatus.SCANNING, update_by=create_by
                            )
                        
                        # 在线程池中执行扫描（避免阻塞事件循环）
                        loop = asyncio.get_event_loop()
                        scan_result = await loop.run_in_executor(
                            executor,
                            sensitive_scanner.scan_document,
                            file_id,
                            file_item["content"],
                            output_dir,
                            task_id
                        )
                        
                        # 处理扫描结果
                        if scan_result["status"] == "ok":
                            async with db.begin():
                                await self._update_file_status(
                                    db, task_id, file_id, FileStatus.COMPLETED,
                                    jsonl_path=scan_result["jsonl_path"],
                                    html_path=scan_result["html_path"],
                                    update_by=create_by
                                )
                            logger.info(f"文件 {file_id} 扫描完成")
                        else:
                            raise Exception(scan_result.get("error", "扫描失败"))
                            
                    except Exception as e:
                        logger.error(f"扫描文件 {file_id} 时出错: {e}")
                        async with db.begin():
                            await self._update_file_status(
                                db, task_id, file_id, FileStatus.FAILED,
                                error=str(e), update_by=create_by
                            )
                            await self._add_task_error(
                                db, task_id, f"扫描文件 {file_id} 失败: {str(e)}", create_by
                            )
                
                # 更新任务为完成状态
                async with db.begin():
                    # 获取统计信息
                    file_status_summary = await self._get_file_status_summary(db, task_id)
                    completed_count = file_status_summary.get("completed", 0)
                    failed_count = file_status_summary.get("failed", 0)
                    
                    summary = {
                        "total_files": len(file_ids),
                        "completed_files": completed_count,
                        "failed_files": failed_count
                    }
                    
                    progress = {
                        "phase": "completed",
                        "current": len(file_ids),
                        "total": len(file_ids),
                        "message": f"扫描完成: {completed_count} 成功, {failed_count} 失败"
                    }
                    
                    await self._update_task_status(
                        db, task_id, TaskStatus.COMPLETED,
                        summary=summary,
                        progress=progress,
                        update_by=create_by
                    )
                    
        except Exception as e:
            logger.error(f"任务 {task_id} 处理失败: {e}")
            async with get_async_db_context() as db:
                async with db.begin():
                    progress = {
                        "phase": "failed",
                        "current": 0,
                        "total": 0,
                        "message": f"任务失败: {str(e)}"
                    }
                    await self._update_task_status(
                        db, task_id, TaskStatus.FAILED,
                        progress=progress,
                        errors=[str(e)],
                        update_by=create_by
                    )
    
    # 辅助方法
    async def _update_task_status(self, db: AsyncSession, task_id: str, 
                                  status: TaskStatus, update_by: str = "system", **kwargs):
        """更新任务状态"""
        update_data = {
            "status": status,
            "update_by": update_by,
            "update_time": now_shanghai()
        }
        
        # 更新时间戳
        if status == TaskStatus.PROCESSING and "start_time" not in kwargs:
            update_data["start_time"] = now_shanghai()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and "end_time" not in kwargs:
            update_data["end_time"] = now_shanghai()
        
        # 处理JSON字段
        for key in ["progress", "statistics", "summary", "errors"]:
            if key in kwargs:
                if isinstance(kwargs[key], (dict, list)):
                    update_data[key] = json.dumps(kwargs[key], ensure_ascii=False)
                else:
                    update_data[key] = kwargs[key]
        
        stmt = update(ScanTask).where(
            ScanTask.task_id == task_id
        ).values(**update_data)
        
        await db.execute(stmt)
    
    async def _update_task_progress(self, db: AsyncSession, task_id: str,
                                   progress: Dict[str, Any], update_by: str = "system"):
        """更新任务进度"""
        progress_json = json.dumps(progress, ensure_ascii=False)
        
        stmt = update(ScanTask).where(
            ScanTask.task_id == task_id
        ).values(
            progress=progress_json,
            update_by=update_by,
            update_time=now_shanghai()
        )
        
        await db.execute(stmt)
    
    async def _update_file_status(self, db: AsyncSession, task_id: str, file_id: str,
                                 status: FileStatus, update_by: str = "system", **kwargs):
        """更新文件状态"""
        update_data = {
            "status": status,
            "update_by": update_by,
            "update_time": now_shanghai()
        }
        
        # 更新时间戳
        if status in [FileStatus.READING, FileStatus.SCANNING] and "start_time" not in kwargs:
            update_data["start_time"] = now_shanghai()
        elif status in [FileStatus.COMPLETED, FileStatus.FAILED] and "end_time" not in kwargs:
            update_data["end_time"] = now_shanghai()
        
        # 更新其他字段
        for key in ["jsonl_path", "html_path", "error", "start_time", "end_time"]:
            if key in kwargs:
                update_data[key] = kwargs[key]
        
        # 更新文件状态
        stmt = update(ScanFile).where(
            and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id)
        ).values(**update_data)
        
        await db.execute(stmt)
        
        # 如果是完成或失败，更新任务统计
        if status == FileStatus.COMPLETED:
            task_stmt = update(ScanTask).where(
                ScanTask.task_id == task_id
            ).values(
                processed_files=ScanTask.processed_files + 1,
                update_time=now_shanghai()
            )
            await db.execute(task_stmt)
        elif status == FileStatus.FAILED:
            task_stmt = update(ScanTask).where(
                ScanTask.task_id == task_id
            ).values(
                failed_files=ScanTask.failed_files + 1,
                update_time=now_shanghai()
            )
            await db.execute(task_stmt)
    
    async def _add_task_error(self, db: AsyncSession, task_id: str,
                             error_msg: str, update_by: str = "system"):
        """添加任务错误信息"""
        # 查询现有错误
        result = await db.execute(
            select(ScanTask.errors).where(ScanTask.task_id == task_id)
        )
        errors_json = result.scalar_one_or_none()
        
        if errors_json:
            try:
                errors = json.loads(errors_json) if errors_json else []
            except:
                errors = []
            
            errors.append(error_msg)
            
            stmt = update(ScanTask).where(
                ScanTask.task_id == task_id
            ).values(
                errors=json.dumps(errors, ensure_ascii=False),
                update_by=update_by,
                update_time=now_shanghai()
            )
            
            await db.execute(stmt)
    
    async def _get_file_status_summary(self, db: AsyncSession, task_id: str) -> Dict[str, int]:
        """获取文件状态摘要"""
        result = await db.execute(
            select(
                ScanFile.status,
                func.count(ScanFile.id).label('count')
            )
            .where(ScanFile.task_id == task_id)
            .group_by(ScanFile.status)
        )
        
        summary = {}
        for row in result:
            summary[row.status.value] = row.count
        
        return summary
    
    def _task_to_dict(self, task: ScanTask) -> Dict[str, Any]:
        """将任务对象转换为字典"""
        # 解析JSON字段
        def parse_json_field(field_value):
            if field_value:
                try:
                    return json.loads(field_value)
                except:
                    return field_value
            return None
        
        return {
            "id": task.id,
            "task_id": task.task_id,
            "status": task.status.value if task.status else None,
            "total_files": task.total_files,
            "processed_files": task.processed_files,
            "failed_files": task.failed_files,
            "progress": parse_json_field(task.progress) or {},
            "statistics": parse_json_field(task.statistics) or {},
            "summary": parse_json_field(task.summary),
            "errors": parse_json_field(task.errors) or [],
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "create_by": task.create_by,
            "update_by": task.update_by,
            "create_time": task.create_time.isoformat() if task.create_time else None,
            "update_time": task.update_time.isoformat() if task.update_time else None
        }
    
    def _file_to_dict(self, file: ScanFile) -> Dict[str, Any]:
        """将文件对象转换为字典"""
        return {
            "id": file.id,
            "file_id": file.file_id,
            "status": file.status.value if file.status else None,
            "jsonl_path": file.jsonl_path,
            "html_path": file.html_path,
            "error": file.error,
            "start_time": file.start_time.isoformat() if file.start_time else None,
            "end_time": file.end_time.isoformat() if file.end_time else None,
            "create_by": file.create_by,
            "update_by": file.update_by,
            "create_time": file.create_time.isoformat() if file.create_time else None,
            "update_time": file.update_time.isoformat() if file.update_time else None
        }


# 创建全局服务实例
scan_task_service = ScanTaskService()