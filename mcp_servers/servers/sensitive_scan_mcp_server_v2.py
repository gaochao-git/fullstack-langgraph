#!/usr/bin/env python3
"""
Sensitive Data Scanner MCP Server V2
敏感数据扫描MCP服务器 V2 版本
使用 LangExtract 进行精确的敏感信息提取和可视化
"""

import json
import logging
import os
import asyncio
import re
import aiofiles
from pathlib import Path
from asyncio import Semaphore
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastmcp import FastMCP
from base_config import MCPServerConfig

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("Sensitive Data Scanner Server V2")

# 加载配置
config = MCPServerConfig('sensitive_scan_server_v2')

# 获取LangExtract配置
LANGEXTRACT_PROVIDER = config.get('langextract_provider', 'gemini')  # gemini, openai, custom
LANGEXTRACT_MODEL = config.get('langextract_model', 'gemini-2.0-flash-exp')
LANGEXTRACT_API_KEY = config.get('langextract_api_key', '')
LANGEXTRACT_BASE_URL = config.get('langextract_base_url', '')  # 用于自定义API地址
VISUALIZATION_OUTPUT_DIR = config.get('visualization_output_dir', '/tmp/scan_visualizations')

# 获取分块大小配置（默认10000字符）
CHUNK_SIZE = config.get('chunk_size', 10000)

# 获取文件并发度配置（默认3个文件同时扫描）
FILE_CONCURRENCY = config.get('file_concurrency', 3)

# 获取文档存储路径配置
DOCUMENT_STORAGE_PATH = config.get('document_storage_path', '/tmp/documents/uploads')

logger.info(f"文档存储路径配置: DOCUMENT_STORAGE_PATH = {DOCUMENT_STORAGE_PATH}")

# 初始化LangExtract扫描器
try:
    from langextract_sensitive_scanner import LangExtractSensitiveScanner
    
    # 准备API密钥
    api_key = LANGEXTRACT_API_KEY
    if not api_key:
        # 根据提供商从环境变量读取
        if LANGEXTRACT_PROVIDER == 'gemini':
            api_key = os.environ.get('GOOGLE_API_KEY')
        elif LANGEXTRACT_PROVIDER == 'openai' or LANGEXTRACT_PROVIDER == 'custom':
            api_key = os.environ.get('OPENAI_API_KEY')
    
    langextract_scanner = LangExtractSensitiveScanner(
        model_id=LANGEXTRACT_MODEL,
        api_key=api_key,
        provider=LANGEXTRACT_PROVIDER,
        base_url=LANGEXTRACT_BASE_URL if LANGEXTRACT_PROVIDER == 'custom' else None,
        enable_visualization=True  # 启用可视化以支持原生报告生成
    )
    logger.info(f"LangExtract 扫描器已初始化 (提供商: {LANGEXTRACT_PROVIDER}, 模型: {LANGEXTRACT_MODEL})")
except ImportError as e:
    logger.error(f"无法导入 LangExtract: {str(e)}")
    logger.error("请确保 langextract_sensitive_scanner.py 在同目录下")
    raise ImportError(f"无法导入 LangExtract 模块: {str(e)}")
except Exception as e:
    logger.error(f"初始化 LangExtract 扫描器失败: {str(e)}")
    raise Exception(f"LangExtract 扫描器初始化失败: {str(e)}")


async def read_content_from_file(file_path: str) -> str:
    """从文件读取内容"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
                logger.info(f"成功使用 {encoding} 编码从文件读取内容: {file_path}")
                return content
        except FileNotFoundError:
            logger.error(f"解析文件不存在: {file_path}")
            return ""
        except UnicodeDecodeError:
            continue
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                logger.error(f"解析文件不存在: {file_path}")
                return ""
            continue
    
    # 如果所有编码都失败，尝试使用错误处理策略
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
            logger.warning(f"使用 utf-8 编码（忽略错误）读取文件: {file_path}")
            return content
    except FileNotFoundError:
        logger.error(f"解析文件不存在: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"读取解析文件失败: {file_path}, 错误: {e}")
        return ""


async def get_file_content_from_filesystem(file_id: str) -> Dict[str, Any]:
    """从文件系统获取文件内容"""
    try:
        # 构建文件路径
        base_path = Path(DOCUMENT_STORAGE_PATH)
        
        # 查找原始文件和解析后的文件
        original_file_pattern = f"{file_id}.*"
        parsed_file_path = base_path / f"{file_id}.parse.txt"
        
        # 获取文件元数据
        file_metadata = {}
        file_name = f"document_{file_id}"
        file_type = "unknown"
        file_size = 0
        
        # 查找原始文件获取文件信息
        if not file_name.startswith("document_"):
            for file_path in base_path.glob(original_file_pattern):
                if not str(file_path).endswith('.parse.txt'):
                    file_name = file_path.name
                    file_type = file_path.suffix[1:] if file_path.suffix else 'unknown'
                    file_size = file_path.stat().st_size
                    break
        
        # 检查解析后的文件是否存在
        if not parsed_file_path.exists():
            # 尝试直接读取原始文本文件
            for file_path in base_path.glob(original_file_pattern):
                if file_path.suffix in ['.txt', '.md']:
                    content = await read_content_from_file(str(file_path))
                    if content:
                        break
            else:
                logger.error(f"找不到文件: {file_id}")
                return {
                    'success': False,
                    'content': '',
                    'error': f'找不到文件: {file_id}'
                }
        else:
            # 读取解析后的内容
            content = await read_content_from_file(str(parsed_file_path))
            if not content:
                return {
                    'success': False,
                    'content': '',
                    'error': f'无法读取解析文件: {parsed_file_path}'
                }
        
        # 统计图片数量（匹配 [图片 数字] 格式）
        image_count = len(re.findall(r'\[图片\s*\d*\]', content))
        
        # 获取字符数
        char_count = file_metadata.get('char_count', len(content))
        
        return {
            'success': True,
            'content': content,
            'file_name': file_name,
            'file_type': file_type,
            'file_size': file_size,
            'doc_metadata': file_metadata,
            'image_count': image_count,
            'char_count': char_count
        }
            
    except Exception as e:
        logger.error(f"从文件系统读取文件失败: {str(e)}")
        return {
            'success': False,
            'content': '',
            'error': f'从文件系统读取文件失败: {str(e)}'
        }


async def scan_content_with_langextract(content: str, file_name: str = "未知文件") -> Dict[str, Any]:
    """使用LangExtract扫描内容中的敏感信息"""
    try:
        # 使用同步方法（因为langextract目前是同步的）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            langextract_scanner.scan_text,
            content,
            file_name
        )
        
        # 直接返回Scanner的结果
        return result
            
    except Exception as e:
        logger.error(f"LangExtract扫描失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'document_name': file_name
        }


async def scan_single_file(file_id: str) -> Dict[str, Any]:
    """扫描单个文件并返回结果字典"""
    file_data = await get_file_content_from_filesystem(file_id)
    
    if not file_data['success']:
        return {
            'file_id': file_id,
            'success': False,
            'error': file_data['error']
        }
    
    # 使用LangExtract扫描
    scan_result = await scan_content_with_langextract(
        file_data['content'], 
        file_data['file_name']
    )
    
    if not scan_result['success']:
        return {
            'file_id': file_id,
            'file_name': file_data['file_name'],
            'success': False,
            'error': scan_result.get('error', '未知错误')
        }
    
    # 合并文件信息和扫描结果
    return {
        **scan_result,  # 直接使用Scanner返回的所有字段
        'file_id': file_id,
        'file_name': file_data['file_name'],  # 添加file_name以保持兼容性
        'file_type': file_data['file_type'],
        'file_size': file_data['file_size'],
        'image_count': file_data.get('image_count', 0),
        'char_count': file_data.get('char_count', 0)
    }


@mcp.tool()
async def scan_document_v2(file_ids: List[str]) -> str:
    """
    扫描文档中的敏感信息
    
    Args:
        file_ids: 文件ID列表（文件系统中的file_id列表）
    
    Returns:
        扫描结果报告（包含可视化报告链接）
    """
    try:
        logger.info(f"开始扫描 {len(file_ids)} 个文件")
        
        if not file_ids:
            return "错误: 未提供文件ID"
        
        # 统一使用批量处理逻辑（无论是1个还是多个文件）
        output = ""
        
        # 显示扫描报告头部
        output = f"扫描报告\n"
        output += f"{'='*50}\n"
        output += f"扫描文件数: {len(file_ids)}\n"
        output += f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"扫描引擎: LangExtract ({LANGEXTRACT_PROVIDER})\n"
        output += f"使用模型: {LANGEXTRACT_MODEL}\n"
        output += f"{'='*50}\n\n"
        
        # 使用信号量控制并发度
        semaphore = Semaphore(FILE_CONCURRENCY)
        
        async def scan_with_semaphore(file_id: str):
            async with semaphore:
                return await scan_single_file(file_id)
        
        # 并发扫描所有文件
        scan_tasks = [scan_with_semaphore(file_id) for file_id in file_ids]
        scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # 处理扫描结果
        total_sensitive_count = 0
        files_with_sensitive = 0
        langextract_results = []  # 用于可视化
        
        for idx, scan_data in enumerate(scan_results, 1):
            # 处理异常情况
            if isinstance(scan_data, Exception):
                output += f"\n内容源{idx}: {file_ids[idx-1]}\n"
                output += f"扫描失败: 处理过程中发生异常 - {str(scan_data)}\n"
                output += "="*50 + "\n"
                continue
                
            if not scan_data.get('success', False):
                output += f"\n内容源{idx}: {scan_data.get('file_id', file_ids[idx-1])}\n"
                output += f"扫描失败: {scan_data.get('error', '未知错误')}\n"
                output += "="*50 + "\n"
                continue
            
            # 收集LangExtract结果用于可视化（如果启用了可视化）
            if scan_data.get('langextract_result'):
                langextract_results.append(scan_data['langextract_result'])
            
            # 格式化文件大小
            file_size_kb = scan_data.get('file_size', 0) / 1024
            
            # 判断解析状态
            parse_status = "内容完整"
            
            # 输出文件结果
            output += f"\n内容源{idx}: {scan_data.get('document_name', scan_data.get('file_name', '未知文件'))}\n"
            output += f"1.文档信息：{file_size_kb:.1f}KB、文字{scan_data.get('char_count', 0)}"
            if scan_data.get('image_count', 0) > 0:
                output += f"(包含图片{scan_data['image_count']}张的解析内容)"
            output += "\n"
            output += f"2.文档解析状态：{parse_status}\n"
            # 显示文档摘要
            document_summary = scan_data.get('document_summary', '')
            if document_summary:
                output += f"3.文档摘要：{document_summary}\n"
            else:
                output += f"3.文档摘要：无摘要\n"
            output += f"4.敏感信息扫描结果："
            
            if scan_data.get('has_sensitive', False):
                files_with_sensitive += 1
                total_sensitive_count += scan_data.get('sensitive_count', 0)
                output += f"发现{scan_data.get('sensitive_count', 0)}个敏感信息\n"
                # 最多展示3个
                sensitive_items = scan_data.get('sensitive_items', [])
                for i, item in enumerate(sensitive_items[:3], 1):
                    output += f"  {i}) {item.get('type', '未知类型')}: {item.get('masked_value', '***')}\n"
                if len(sensitive_items) > 3:
                    output += f"  ...还有{len(sensitive_items)-3}个敏感信息未展示\n"
            else:
                output += "未发现敏感信息\n"
            
            output += "="*50 + "\n"
        
        # 显示汇总统计
        output += f"\n{'='*50}\n"
        output += f"扫描汇总:\n"
        output += f"   - 扫描文件总数: {len(file_ids)}\n"
        output += f"   - 包含敏感信息的文件: {files_with_sensitive}\n"
        output += f"   - 敏感信息总数: {total_sensitive_count}\n"
        
        # 准备报告数据
        report_data = {
            "scan_time": datetime.now().isoformat(),
            "total_files": len(file_ids),
            "total_sensitive": total_sensitive_count,
            "files_with_sensitive": files_with_sensitive,
            "engine": "LangExtract",
            "model": LANGEXTRACT_MODEL,
            "items": [],
            "statistics": {}
        }
        
        # 收集所有敏感信息项
        for scan_data in scan_results:
            if isinstance(scan_data, dict) and scan_data.get('success') and scan_data.get('has_sensitive'):
                file_name = scan_data.get('document_name', scan_data.get('file_name', '未知文件'))
                
                # 直接使用Scanner返回的sensitive_items
                for item in scan_data.get('sensitive_items', []):
                    report_item = {
                        "type": item.get('type', '未知类型'),
                        "masked_value": item.get('masked_value', '***'),
                        "context": item.get('context', ''),
                        "file": file_name,
                        "file_id": scan_data.get('file_id', '')  # 添加file_id
                    }
                    report_data["items"].append(report_item)
                
                # 直接使用Scanner返回的sensitive_stats统计
                if scan_data.get('sensitive_stats'):
                    for item_type, count in scan_data['sensitive_stats'].items():
                        if item_type not in report_data["statistics"]:
                            report_data["statistics"][item_type] = 0
                        report_data["statistics"][item_type] += count
        
        # 保存报告数据为JSON
        if total_sensitive_count > 0:
            try:
                os.makedirs(VISUALIZATION_OUTPUT_DIR, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_filename = f"scan_report_{timestamp}.json"
                report_path = os.path.join(VISUALIZATION_OUTPUT_DIR, report_filename)
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                
                # 生成报告标识符
                report_id = f"[REPORT:SENSITIVE_SCAN:{report_filename}:查看完整扫描报告]"
                output += f"\n{'='*50}\n"
                output += f"📊 扫描报告:\n"
                output += f"   {report_id}\n"
                logger.info(f"扫描报告已生成: {report_path}")
                
                # 生成LangExtract HTML可视化报告
                if langextract_results:
                    try:
                        viz_filename = f"scan_viz_{timestamp}.html"
                        viz_path = os.path.join(VISUALIZATION_OUTPUT_DIR, viz_filename)
                        
                        loop = asyncio.get_event_loop()
                        html_path = await loop.run_in_executor(
                            None,
                            langextract_scanner.generate_visualization,
                            langextract_results,
                            viz_path
                        )
                        
                        if html_path:
                            logger.info(f"LangExtract可视化报告已生成: {html_path}")
                    except Exception as e:
                        logger.error(f"生成LangExtract可视化报告失败: {str(e)}")
            except Exception as e:
                logger.error(f"保存报告数据失败: {str(e)}")
                output += f"\n保存报告失败: {str(e)}\n"
        
        return output.rstrip()  # 去掉末尾换行
        
    except Exception as e:
        logger.error(f"扫描文档过程中发生异常: {str(e)}", exc_info=True)
        return f"错误: 扫描过程中发生异常 - {str(e)}"


if __name__ == "__main__":
    # 启动服务器
    port = config.get('port', 3008)
    logger.info(f"Starting Sensitive Data Scanner MCP Server V2 on port {port}")
    
    # 显示引擎配置信息
    logger.info(f"扫描引擎: LangExtract")
    logger.info(f"模型: {LANGEXTRACT_MODEL}")
    logger.info(f"提供商: {LANGEXTRACT_PROVIDER}")
    if LANGEXTRACT_PROVIDER == 'custom':
        logger.info(f"API地址: {LANGEXTRACT_BASE_URL}")
    logger.info(f"可视化: 已启用 (输出目录: {VISUALIZATION_OUTPUT_DIR})")
    logger.info(f"分块大小: {CHUNK_SIZE} 字符")
    logger.info(f"文件并发度: {FILE_CONCURRENCY}")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)