"""敏感数据扫描任务服务层 - 完整实现"""

import os
import re
import json
import asyncio
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.config import settings
from .models import ScanTask, ScanFile

logger = get_logger(__name__)


class SensitiveDataScanner:
    """敏感数据扫描器"""
    
    # 敏感数据正则表达式
    PATTERNS = {
        "身份证号": r'\b[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b',
        "手机号": r'\b1[3-9]\d{9}\b',
        "银行卡号": r'\b[1-9]\d{15,18}\b',
        "邮箱地址": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "统一社会信用代码": r'\b[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}\b',
        "车牌号": r'\b[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-HJ-NP-Z0-9]{4}[A-HJ-NP-Z0-9挂学警港澳]\b',
        "护照号": r'\b[GgEe]\d{8}\b',
        "IPv4地址": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        "密码": r'(?i)(password|passwd|pwd|密码)\s*[:=]\s*[^\s]+',
        "API密钥": r'(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?key)\s*[:=]\s*[\'"]?[\w-]{16,}[\'"]?'
    }
    
    def scan_text(self, text: str) -> List[Dict[str, Any]]:
        """扫描文本中的敏感数据"""
        results = []
        
        for data_type, pattern in self.PATTERNS.items():
            matches = re.finditer(pattern, text, re.IGNORECASE if data_type in ["邮箱地址", "密码", "API密钥"] else 0)
            for match in matches:
                # 获取匹配位置的上下文
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                context = text[start:end]
                
                # 脱敏处理
                sensitive_value = match.group()
                if len(sensitive_value) > 4:
                    masked_value = sensitive_value[:3] + '*' * (len(sensitive_value) - 6) + sensitive_value[-3:]
                else:
                    masked_value = '*' * len(sensitive_value)
                
                results.append({
                    "type": data_type,
                    "value": masked_value,
                    "original_value": sensitive_value,  # 实际应用中不应返回原始值
                    "position": {
                        "start": match.start(),
                        "end": match.end()
                    },
                    "context": context,
                    "line_number": text[:match.start()].count('\n') + 1
                })
        
        return results


class FullScanTaskService:
    """扫描任务服务层 - 完整实现"""
    
    def __init__(self):
        self.scanner = SensitiveDataScanner()
        # 确保扫描结果目录存在
        self.scan_results_dir = Path(settings.UPLOAD_DIR) / "scan_results"
        self.scan_results_dir.mkdir(parents=True, exist_ok=True)
    
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
        from src.apps.agent.service.document_service import document_service
        
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
                    await self._scan_file(task_id, file_id)
                
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
    
    async def _scan_file(self, task_id: str, file_id: str):
        """扫描单个文件"""
        from src.apps.agent.service.document_service import document_service
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
                
                # 直接读取文件内容，不查询数据库
                # 直接使用file_id构建文件路径
                file_path = Path(settings.UPLOAD_DIR) / f"{file_id}.txt"
                
                if not file_path.exists() or not file_path.is_file():
                    # 尝试解析后的文件
                    file_path = Path(settings.UPLOAD_DIR) / f"{file_id}.parse.txt"
                    
                if not file_path.exists() or not file_path.is_file():
                    raise Exception(f"文件不存在: {file_path}")
                
                # 获取文件名
                original_filename = file_path.name
                
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
                
                # 执行扫描
                scan_results = self.scanner.scan_text(content)
                
                # 生成结果文件
                jsonl_path, html_path = await self._save_scan_results(
                    task_id, file_id, original_filename, 
                    content, scan_results
                )
                
                # 更新文件状态为完成
                async with scan_db.begin():
                    await scan_db.execute(
                        update(ScanFile)
                        .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                        .values(
                            file_status='completed',
                            jsonl_path=jsonl_path,
                            html_path=html_path,
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
    
    async def _save_scan_results(
        self, 
        task_id: str, 
        file_id: str, 
        filename: str,
        content: str,
        scan_results: List[Dict[str, Any]]
    ) -> tuple[str, str]:
        """保存扫描结果为JSONL和HTML格式"""
        # 创建任务目录
        task_dir = self.scan_results_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        base_name = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        jsonl_filename = f"{base_name}.jsonl"
        html_filename = f"{base_name}.html"
        
        # 保存JSONL文件
        jsonl_path = task_dir / jsonl_filename
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            # 写入文档信息
            doc_info = {
                "document_id": file_id,
                "filename": filename,
                "scan_time": datetime.now().isoformat(),
                "total_findings": len(scan_results)
            }
            f.write(json.dumps(doc_info, ensure_ascii=False) + '\n')
            
            # 写入每个发现
            for result in scan_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # 生成HTML报告
        html_path = task_dir / html_filename
        html_content = self._generate_html_report(
            filename, content, scan_results, task_id, file_id
        )
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 返回相对路径
        return (
            f"scan_results/{task_id}/{jsonl_filename}",
            f"scan_results/{task_id}/{html_filename}"
        )
    
    def _generate_html_report(
        self, 
        filename: str, 
        content: str,
        scan_results: List[Dict[str, Any]], 
        task_id: str,
        file_id: str
    ) -> str:
        """生成HTML报告"""
        # 按类型分组统计
        stats = {}
        for result in scan_results:
            data_type = result['type']
            if data_type not in stats:
                stats[data_type] = 0
            stats[data_type] += 1
        
        # 生成高亮的文本内容
        highlighted_content = content
        # 从后往前替换，避免位置偏移
        for result in sorted(scan_results, key=lambda x: x['position']['start'], reverse=True):
            start = result['position']['start']
            end = result['position']['end']
            original = result['original_value']
            highlighted = f'<mark class="{result["type"].replace(" ", "-")}" title="{result["type"]}">{original}</mark>'
            highlighted_content = highlighted_content[:start] + highlighted + highlighted_content[end:]
        
        # 转义HTML特殊字符
        highlighted_content = highlighted_content.replace('\n', '<br>')
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>敏感数据扫描报告 - {filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h1 {{
            color: #2c3e50;
            margin: 0 0 10px 0;
        }}
        .meta {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .summary {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .stat-card h3 {{
            margin: 0 0 5px 0;
            font-size: 16px;
            color: #2c3e50;
        }}
        .stat-card .count {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        .findings {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .finding {{
            background: #f8f9fa;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid #e74c3c;
        }}
        .finding-type {{
            font-weight: bold;
            color: #e74c3c;
            margin-bottom: 5px;
        }}
        .finding-details {{
            font-size: 14px;
            color: #555;
        }}
        .content {{
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-family: monospace;
            font-size: 14px;
            line-height: 1.8;
            overflow-x: auto;
        }}
        mark {{
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: bold;
        }}
        mark.身份证号 {{ background-color: #ffeb3b; }}
        mark.手机号 {{ background-color: #ff9800; }}
        mark.银行卡号 {{ background-color: #f44336; color: white; }}
        mark.邮箱地址 {{ background-color: #2196f3; color: white; }}
        mark.统一社会信用代码 {{ background-color: #9c27b0; color: white; }}
        mark.车牌号 {{ background-color: #4caf50; color: white; }}
        mark.护照号 {{ background-color: #00bcd4; }}
        mark.IPv4地址 {{ background-color: #795548; color: white; }}
        mark.密码 {{ background-color: #e91e63; color: white; }}
        mark.API密钥 {{ background-color: #607d8b; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>敏感数据扫描报告</h1>
        <div class="meta">
            <p>文件名：{filename}</p>
            <p>任务ID：{task_id}</p>
            <p>文件ID：{file_id}</p>
            <p>扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <div class="summary">
        <h2>扫描概要</h2>
        <p>共发现 <strong>{len(scan_results)}</strong> 个敏感数据</p>
        <div class="stats">
"""
        
        for data_type, count in stats.items():
            html += f"""
            <div class="stat-card">
                <h3>{data_type}</h3>
                <div class="count">{count}</div>
            </div>
"""
        
        html += """
        </div>
    </div>
    
    <div class="findings">
        <h2>详细发现</h2>
"""
        
        for i, result in enumerate(scan_results, 1):
            html += f"""
        <div class="finding">
            <div class="finding-type">{i}. {result['type']}</div>
            <div class="finding-details">
                <p>位置：第 {result['line_number']} 行，字符 {result['position']['start']}-{result['position']['end']}</p>
                <p>脱敏值：<code>{result['value']}</code></p>
                <p>上下文：<code>{result['context']}</code></p>
            </div>
        </div>
"""
        
        html += f"""
    </div>
    
    <div class="content">
        <h2>文件内容（高亮显示）</h2>
        <div>{highlighted_content}</div>
    </div>
</body>
</html>
"""
        return html
    
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
                        lines = f.readlines()
                        # 第一行是文档信息，其余是敏感数据项
                        total_items += len(lines) - 1
        
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


# 创建服务实例
scan_task_service = FullScanTaskService()