"""
敏感数据扫描的 Celery 任务
"""
import json
from typing import List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy import update, and_, select
from src.celery.celery import app
from src.celery.db_utils import get_db_session
from src.shared.core.logging import get_logger
from src.shared.core.config import settings
from src.shared.db.models import now_shanghai
from .models import ScanTask, ScanFile, ScanConfig
from .langextract_scanner import LangExtractSensitiveScanner
from src.apps.agent.models import AgentDocumentUpload

logger = get_logger(__name__)


class ScanTaskProcessor:
    """扫描任务处理器 - 专门用于Celery Worker环境"""

    def __init__(self):
        # 确保扫描结果目录存在
        self.scan_results_dir = Path(settings.DOCUMENT_DIR) / "scan_results"
        self.scan_results_dir.mkdir(parents=True, exist_ok=True)

        # 检查LLM配置
        if not settings.LLM_MODEL or not settings.LLM_API_KEY or not settings.LLM_BASE_URL:
            raise ValueError("必须在配置文件中设置 LLM_MODEL, LLM_API_KEY 和 LLM_BASE_URL")

    def _get_scanner_with_config(
        self,
        config_id: str = None,
        max_workers: int = 10,
        batch_length: int = 10,
        extraction_passes: int = 1,
        max_char_buffer: int = 2000
    ) -> LangExtractSensitiveScanner:
        """
        根据配置ID获取对应的扫描器配置

        Args:
            config_id: 配置ID（可选）
            max_workers: 最大并行工作线程数
            batch_length: 批处理长度
            extraction_passes: 提取遍数
            max_char_buffer: 最大字符缓冲区大小

        Returns:
            配置好的扫描器实例
        """
        # 从数据库获取配置
        try:
            with get_db_session() as db:
                from .models import ScanConfig

                # 如果指定了config_id，使用指定的配置
                if config_id:
                    result = db.execute(
                        select(ScanConfig).where(
                            and_(ScanConfig.config_id == config_id, ScanConfig.status == 'active')
                        )
                    )
                else:
                    # 否则使用默认配置
                    result = db.execute(
                        select(ScanConfig).where(
                            and_(ScanConfig.is_default == 1, ScanConfig.status == 'active')
                        )
                    )

                config = result.scalar_one_or_none()

                if config:
                    # 解析examples
                    import langextract as lx
                    examples = None
                    if config.examples_config:
                        try:
                            examples_data = json.loads(config.examples_config)
                            examples = []
                            for ex in examples_data:
                                extractions = [
                                    lx.data.Extraction(
                                        extraction_class=ext['extraction_class'],
                                        extraction_text=ext['extraction_text']
                                    )
                                    for ext in ex.get('extractions', [])
                                ]
                                examples.append(lx.data.ExampleData(
                                    text=ex['text'],
                                    extractions=extractions
                                ))
                        except Exception as e:
                            logger.warning(f"解析配置examples失败: {e}")

                    logger.info(f"使用自定义扫描配置: {config.config_name}")
                    return LangExtractSensitiveScanner(
                        custom_prompt=config.prompt_description,
                        custom_examples=examples,
                        max_workers=max_workers,
                        batch_length=batch_length,
                        extraction_passes=extraction_passes,
                        max_char_buffer=max_char_buffer
                    )
        except Exception as e:
            logger.warning(f"获取扫描配置失败，使用默认配置: {e}")

        # 没有配置或获取失败，使用默认配置
        logger.info("使用默认扫描配置")
        return LangExtractSensitiveScanner(
            max_workers=max_workers,
            batch_length=batch_length,
            extraction_passes=extraction_passes,
            max_char_buffer=max_char_buffer
        )
    
    def process_scan_task(
        self,
        task_id: str,
        file_ids: List[str],
        config_id: str = None,
        max_workers: int = 10,
        batch_length: int = 10,
        extraction_passes: int = 1,
        max_char_buffer: int = 2000
    ):
        """处理扫描任务"""
        logger.info(f"开始处理扫描任务: {task_id}")

        try:
            with get_db_session() as db:
                # 更新任务状态为处理中
                db.execute(
                    update(ScanTask)
                    .where(ScanTask.task_id == task_id)
                    .values(
                        task_status='processing',
                        start_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                )
                db.commit()

            # 处理每个文件
            for file_id in file_ids:
                self._scan_file_with_langextract(
                    task_id,
                    file_id,
                    config_id,
                    max_workers,
                    batch_length,
                    extraction_passes,
                    max_char_buffer
                )
            
            # 更新任务状态为完成
            with get_db_session() as db:
                db.execute(
                    update(ScanTask)
                    .where(ScanTask.task_id == task_id)
                    .values(
                        task_status='completed',
                        end_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                )
                db.commit()
                
        except Exception as e:
            logger.error(f"扫描任务失败 {task_id}: {str(e)}")
            with get_db_session() as db:
                db.execute(
                    update(ScanTask)
                    .where(ScanTask.task_id == task_id)
                    .values(
                        task_status='failed',
                        task_errors=str(e),
                        end_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                )
                db.commit()
            raise
    
    def _scan_file_with_langextract(
        self,
        task_id: str,
        file_id: str,
        config_id: str = None,
        max_workers: int = 10,
        batch_length: int = 10,
        extraction_passes: int = 1,
        max_char_buffer: int = 2000
    ):
        """使用langextract扫描单个文件"""
        try:
            with get_db_session() as db:
                # 更新文件状态为读取中
                db.execute(
                    update(ScanFile)
                    .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                    .values(
                        file_status='reading',
                        start_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                )
                db.commit()
            
            # 从数据库获取文件路径
            with get_db_session() as db:
                from sqlalchemy import select
                result = db.execute(
                    select(AgentDocumentUpload.file_path).where(
                        AgentDocumentUpload.file_id == file_id
                    )
                )
                db_file_path = result.scalar_one_or_none()

                if not db_file_path:
                    raise Exception(f"文件记录不存在: {file_id}")

            # 解析路径（相对路径 -> 绝对路径）
            file_path = Path(settings.UPLOAD_DIR) / db_file_path

            if not file_path.exists() or not file_path.is_file():
                # 尝试解析后的文件（.parse.txt）
                parse_path = file_path.parent / f"{file_path.stem}.parse.txt"
                if parse_path.exists() and parse_path.is_file():
                    file_path = parse_path
                else:
                    raise Exception(f"文件不存在: {file_path}")
            
            # 获取文件名
            original_filename = file_path.name
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 更新文件状态为扫描中
            with get_db_session() as db:
                db.execute(
                    update(ScanFile)
                    .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                    .values(
                        file_status='scanning',
                        update_time=now_shanghai()
                    )
                )
                db.commit()
            
            # 使用langextract进行扫描
            logger.info(f"开始使用langextract扫描文件: {file_id}")

            # 获取配置并创建scanner
            scanner = self._get_scanner_with_config(
                config_id=config_id,
                max_workers=max_workers,
                batch_length=batch_length,
                extraction_passes=extraction_passes,
                max_char_buffer=max_char_buffer
            )

            # 使用scanner进行扫描（同步操作）
            result = scanner.scan_document(file_id, content)
            
            if not result["success"]:
                raise Exception(f"扫描失败: {result.get('error', '未知错误')}")
            
            logger.info(f"langextract扫描完成: {file_id}, 发现 {result['extractions']} 个敏感信息")
            
            # 创建任务目录
            task_dir = self.scan_results_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成输出文件路径
            base_name = f"{file_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            jsonl_path = task_dir / f"{base_name}.jsonl"
            html_path = task_dir / f"{base_name}.html"
            
            # 保存JSONL结果
            if result["document"]:
                # 保存langextract格式的JSONL
                scanner.save_results([result["document"]], str(jsonl_path))
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
            self._fix_jsonl_char_intervals(str(jsonl_path), content)

            # 生成可视化HTML
            scanner.generate_visualization(str(jsonl_path), str(html_path))
            
            # 返回相对路径
            jsonl_relative = f"scan_results/{task_id}/{base_name}.jsonl"
            html_relative = f"scan_results/{task_id}/{base_name}.html"
            
            # 更新文件状态为完成
            with get_db_session() as db:
                db.execute(
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
                db.commit()
                
        except Exception as e:
            logger.error(f"扫描文件失败 {file_id}: {str(e)}")
            with get_db_session() as db:
                db.execute(
                    update(ScanFile)
                    .where(and_(ScanFile.task_id == task_id, ScanFile.file_id == file_id))
                    .values(
                        file_status='failed',
                        file_error=str(e),
                        end_time=now_shanghai(),
                        update_time=now_shanghai()
                    )
                )
                db.commit()
    
    def _fix_jsonl_char_intervals(self, jsonl_path: str, original_text: str) -> None:
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


@app.task(bind=True, time_limit=3600, soft_time_limit=3300, queue='priority_low')
def scan_files_task(
    self,
    task_id: str,
    file_ids: List[str],
    config_id: str = None,
    max_workers: int = 10,
    batch_length: int = 10,
    extraction_passes: int = 1,
    max_char_buffer: int = 2000
):
    """
    扫描文件任务（Celery版本）

    Args:
        task_id: 扫描任务ID
        file_ids: 文件ID列表
        config_id: 配置ID（可选）
        max_workers: 最大并行工作线程数
        batch_length: 批处理长度
        extraction_passes: 提取遍数
        max_char_buffer: 最大字符缓冲区大小
    """
    logger.info(f"开始执行扫描任务: {task_id}, 文件数: {len(file_ids)}, 配置ID: {config_id}")

    try:
        # 创建处理器实例
        processor = ScanTaskProcessor()

        # 处理扫描任务
        processor.process_scan_task(
            task_id,
            file_ids,
            config_id,
            max_workers,
            batch_length,
            extraction_passes,
            max_char_buffer
        )

        logger.info(f"扫描任务完成: {task_id}")
        return {
            "status": "success",
            "task_id": task_id,
            "total_files": len(file_ids)
        }

    except Exception as e:
        logger.error(f"扫描任务失败 {task_id}: {str(e)}")
        # 支持重试，每次重试间隔5分钟，最多重试3次
        raise self.retry(exc=e, countdown=300, max_retries=3)