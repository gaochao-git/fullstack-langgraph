"""敏感数据扫描任务服务层 - 使用原生langextract实现"""

import os
import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

import json
import langextract as lx

from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.config import settings
from .models import ScanTask, ScanFile

logger = get_logger(__name__)


class LangExtractScanTaskService:
    """扫描任务服务层 - 使用langextract实现"""
    
    def __init__(self):
        # 确保扫描结果目录存在
        self.scan_results_dir = Path(settings.UPLOAD_DIR) / "scan_results"
        self.scan_results_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置langextract提供者
        # 使用环境变量或默认配置
        provider = os.getenv("LLM_TYPE", "openai")
        api_key = os.getenv("LLM_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        
        if provider == "openai":
            # 配置OpenAI兼容的provider（如DeepSeek）
            os.environ["OPENAI_API_KEY"] = api_key
            if base_url:
                os.environ["OPENAI_BASE_URL"] = base_url
    
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
            
            # 启动后台扫描任务
            asyncio.create_task(self._process_scan_task(task_id, file_ids))
            
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
                # 创建任务目录
                task_dir = self.scan_results_dir / task_id
                task_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成输出文件路径
                base_name = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                jsonl_path = task_dir / f"{base_name}.jsonl"
                html_path = task_dir / f"{base_name}.html"
                
                # 创建文档对象
                doc = lx.Document(
                    text=content,
                    document_id=file_id,
                    metadata={"filename": original_filename}
                )
                
                # 定义要提取的敏感数据模式
                extraction_schema = lx.Extraction(
                    names=["sensitive_data"],
                    descriptions=[
                        """Extract all sensitive data including:
                        - Personal ID numbers (身份证号)
                        - Phone numbers (手机号) 
                        - Bank card numbers (银行卡号)
                        - Email addresses (邮箱地址)
                        - Social credit codes (统一社会信用代码)
                        - License plate numbers (车牌号)
                        - Passport numbers (护照号)
                        - IP addresses (IP地址)
                        - Passwords (密码)
                        - API keys (API密钥)
                        
                        For each found item, extract:
                        - type: The type of sensitive data
                        - value: The actual value (will be masked later)
                        - context: 20 characters before and after the value
                        - line_number: The line number where it appears
                        """
                    ]
                )
                
                # 执行提取
                logger.info(f"开始使用langextract扫描文件: {file_id}")
                
                # 使用同步方式调用langextract
                # 在异步上下文中运行同步代码
                loop = asyncio.get_event_loop()
                
                def extract_sync():
                    return lx.extract(
                        documents=[doc],
                        extraction=extraction_schema,
                        output_jsonl_path=str(jsonl_path),
                        output_viz_path=str(html_path),
                        provider="openai",  # 使用OpenAI兼容的provider
                        model=os.getenv("LLM_MODEL", "deepseek-chat"),
                        chunk_size=2000,  # 每次处理2000字符
                        overlap=100  # 重叠100字符确保不遗漏
                    )
                
                # 在线程池中执行同步操作
                await loop.run_in_executor(None, extract_sync)
                
                logger.info(f"langextract扫描完成: {file_id}")
                
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
                full_path = Path(settings.UPLOAD_DIR) / jsonl_path
                if full_path.exists():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        # langextract生成的JSONL格式，每行是一个提取结果
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
        
        # 获取所有文件的扫描结果
        files_result = await db.execute(
            select(ScanFile).where(ScanFile.task_id == task_id)
        )
        files = files_result.scalars().all()
        
        # 统计信息
        completed_files = sum(1 for f in files if f.file_status == 'completed')
        failed_files = sum(1 for f in files if f.file_status == 'failed')
        
        return {
            "task_id": task.task_id,
            "status": task.task_status,
            "summary": {
                "total_files": len(files),
                "completed_files": completed_files,
                "failed_files": failed_files
            },
            "files": [
                {
                    "file_id": f.file_id,
                    "status": f.file_status,
                    "jsonl_path": f.jsonl_path,
                    "html_path": f.html_path,
                    "error": f.file_error,
                    "start_time": f.start_time.isoformat() if f.start_time else None,
                    "end_time": f.end_time.isoformat() if f.end_time else None
                }
                for f in files
            ],
            "completed_time": task.end_time.isoformat() if task.end_time else None
        }
    
    async def list_tasks(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        create_by: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """查询任务列表"""
        # 构建查询条件
        conditions = []
        if create_by:
            conditions.append(ScanTask.create_by == create_by)
        
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
            
            task_list.append({
                "task_id": task.task_id,
                "status": task.task_status,
                "total_files": file_stats['total'],
                "completed_files": file_stats['completed'],
                "failed_files": file_stats['failed'],
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
        full_path = Path(settings.UPLOAD_DIR) / scan_file.jsonl_path
        
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
        full_path = Path(settings.UPLOAD_DIR) / scan_file.html_path
        
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
scan_task_service_langextract = LangExtractScanTaskService()