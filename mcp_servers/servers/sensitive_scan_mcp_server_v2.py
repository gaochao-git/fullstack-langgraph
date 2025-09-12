#!/usr/bin/env python3
"""
Sensitive Data Scanner MCP Server V2
敏感数据扫描MCP服务器 V2 版本
集成 LangExtract 进行更精确的敏感信息提取和可视化
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

# 获取配置
USE_LANGEXTRACT = config.get('use_langextract', False)
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
logger.info(f"使用 LangExtract: {USE_LANGEXTRACT}")

# 根据配置选择扫描器
if USE_LANGEXTRACT:
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
        logger.info(f"已启用 LangExtract 扫描器 (提供商: {LANGEXTRACT_PROVIDER}, 模型: {LANGEXTRACT_MODEL})")
    except ImportError as e:
        logger.error(f"无法导入 LangExtract: {str(e)}")
        logger.error("请确保 langextract_sensitive_scanner.py 在同目录下")
        # 强制使用 LangExtract，不回退
        raise ImportError(f"必须使用 LangExtract 但导入失败: {str(e)}")
    except Exception as e:
        logger.error(f"初始化 LangExtract 扫描器失败: {str(e)}")
        # 强制使用 LangExtract，不回退
        raise Exception(f"必须使用 LangExtract 但初始化失败: {str(e)}")
else:
    langextract_scanner = None

# 如果不使用 LangExtract，则使用原有的 LangChain 实现
if not USE_LANGEXTRACT:
    # LangChain imports
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    
    # 获取LLM配置
    LLM_API_BASE = config.get('llm_api_base') or os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    LLM_API_KEY = config.get('llm_api_key') or os.environ.get('DEEPSEEK_API_KEY', '')
    LLM_MODEL = config.get('llm_model') or os.environ.get('LLM_MODEL', 'deepseek-chat')
    
    # 初始化LangChain LLM
    llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_base=LLM_API_BASE,
        openai_api_key=LLM_API_KEY,
        temperature=0.1,
        timeout=60.0,
        max_tokens=1000
    )
    
    # JSON输出解析器
    json_parser = JsonOutputParser()
    
    # 默认扫描提示词
    SYSTEM_PROMPT = """你是一个专业的敏感数据扫描助手。你的任务是扫描文本中的敏感信息并生成脱敏后的安全报告。

需要识别的敏感信息类型：
1. 个人身份信息：身份证号、护照号、驾驶证号
2. 联系方式：手机号、座机号、邮箱地址
3. 金融信息：银行卡号、信用卡号、账号信息
4. 账户凭据：用户名密码组合、API密钥、Token、证书密钥
5. 网络信息：内网IP地址、服务器地址、数据库连接串
6. 医疗信息：病历号、医保号、诊断信息
7. 其他敏感：社保号、车牌号、家庭住址

重要提示：
- 单独的用户名（如：admin、root、gaochao等）不属于敏感信息
- 只有用户名+密码的组合才是敏感信息
- 公开的域名（如：baidu.com）不属于敏感信息
- 需要重点关注上下文，判断信息是否真的敏感

脱敏规则：
- 手机号：只显示前3位和后4位（如：138****5678）
- 身份证号：只显示前6位和后4位（如：110101****1234）
- 银行卡号：只显示前4位和后4位（如：6222****4321）
- 邮箱：@前面部分隐藏一半（如：te**@163.com）
- IP地址：隐藏中间两段（如：192.***.***234）
- 密码/密钥：全部替换为星号
- 其他敏感信息：保留首尾，中间用星号替换

输出要求：
你必须以JSON格式输出，包含以下字段：
{
    "has_sensitive": true/false,  // 是否包含敏感信息
    "sensitive_count": 0,         // 敏感信息数量
    "sensitive_items": [          // 敏感信息列表
        {
            "type": "身份证号",
            "masked_value": "110101****1234",
            "context": "出现的上下文"
        }
    ],
    "summary": "文档摘要"         // 50字以内的文档内容摘要
}

注意：绝对不要在输出中包含敏感信息的原始值！"""


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


async def scan_content_with_llm(content: str, file_name: str = "未知文件") -> Dict[str, Any]:
    """使用LLM扫描内容中的敏感信息（原有LangChain实现）"""
    try:
        max_chunk_size = CHUNK_SIZE
        
        # 如果内容较短，直接扫描
        if len(content) <= max_chunk_size:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"请扫描以下文档内容：\n\n文件名：{file_name}\n\n内容：\n{content}")
            ]
            
            response = await llm.ainvoke(messages)
            result = json_parser.parse(response.content)
            
            return {
                'success': True,
                'result': result
            }
        
        # 对大文件进行分片处理
        chunks = []
        for i in range(0, len(content), max_chunk_size):
            chunks.append(content[i:i + max_chunk_size])
        
        logger.info(f"大文件 {file_name} 被分成 {len(chunks)} 个分片（每片最大 {max_chunk_size} 字符）")
        
        # 串行扫描所有分片，保持文本顺序
        responses = []
        for idx, chunk in enumerate(chunks):
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"请扫描以下文档内容：\n\n文件名：{file_name}（第{idx+1}/{len(chunks)}部分）\n\n内容：\n{chunk}")
            ]
            response = await llm.ainvoke(messages)
            responses.append(response)
            logger.debug(f"完成扫描 {file_name} 的第 {idx+1}/{len(chunks)} 部分")
        
        # 合并分片结果
        merged_result = {
            'has_sensitive': False,
            'sensitive_count': 0,
            'sensitive_items': [],
            'summary': f'大文件分{len(chunks)}部分扫描'
        }
        
        all_summaries = []
        for idx, response in enumerate(responses):
            try:
                chunk_result = json_parser.parse(response.content)
                
                if chunk_result.get('has_sensitive'):
                    merged_result['has_sensitive'] = True
                    merged_result['sensitive_count'] += chunk_result.get('sensitive_count', 0)
                    
                    # 添加敏感项，标注来源分片
                    for item in chunk_result.get('sensitive_items', []):
                        item['chunk'] = idx + 1
                        merged_result['sensitive_items'].append(item)
                
                if chunk_result.get('summary'):
                    all_summaries.append(f"第{idx+1}部分: {chunk_result['summary']}")
                    
            except Exception as e:
                logger.error(f"解析第{idx+1}部分结果失败: {e}")
        
        # 限制敏感信息项数量
        if len(merged_result['sensitive_items']) > 10:
            merged_result['sensitive_items'] = merged_result['sensitive_items'][:10]
            merged_result['summary'] += f"（仅显示前10个敏感信息）"
        
        # 合并摘要
        if all_summaries:
            merged_result['summary'] = " | ".join(all_summaries[:3])
            if len(all_summaries) > 3:
                merged_result['summary'] += f" 等{len(all_summaries)}部分"
        
        return {
            'success': True,
            'result': merged_result
        }
        
    except Exception as e:
        logger.error(f"LLM扫描失败: {str(e)}")
        return {
            'success': False,
            'error': f'扫描失败: {str(e)}'
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
        
        if result["success"]:
            # 转换为原有格式
            llm_format_result = {
                'has_sensitive': result['has_sensitive'],
                'sensitive_count': result['sensitive_count'],
                'sensitive_items': [
                    {
                        'type': item['type'],
                        'masked_value': item['masked_value'],
                        'context': item['context']
                    }
                    for item in result.get('sensitive_items', [])
                ],
                'summary': f"LangExtract扫描，发现{result['sensitive_count']}个敏感信息"
            }
            
            return {
                'success': True,
                'result': llm_format_result,
                'langextract_result': result  # 保留原始结果用于可视化
            }
        else:
            return {
                'success': False,
                'error': result.get('error', '未知错误')
            }
            
    except Exception as e:
        logger.error(f"LangExtract扫描失败: {str(e)}")
        return {
            'success': False,
            'error': f'扫描失败: {str(e)}'
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
    
    # 根据配置选择扫描方法
    if USE_LANGEXTRACT and langextract_scanner:
        scan_result = await scan_content_with_langextract(
            file_data['content'], 
            file_data['file_name']
        )
    else:
        scan_result = await scan_content_with_llm(
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
    
    return {
        'file_id': file_id,
        'file_name': file_data['file_name'],
        'file_type': file_data['file_type'],
        'file_size': file_data['file_size'],
        'image_count': file_data.get('image_count', 0),
        'char_count': file_data.get('char_count', 0),
        'success': True,
        'result': scan_result['result'],
        'langextract_result': scan_result.get('langextract_result')  # 如果使用LangExtract
    }


@mcp.tool()
async def scan_document_v2(file_ids: List[str], enable_visualization: bool = True) -> str:
    """
    扫描文档中的敏感信息
    
    Args:
        file_ids: 文件ID列表（文件系统中的file_id列表）
        enable_visualization: 是否生成可视化报告（仅在使用LangExtract时有效，默认为True）
    
    Returns:
        扫描结果报告
    """
    try:
        logger.info(f"开始扫描 {len(file_ids)} 个文件，可视化: {enable_visualization}")
        
        if not file_ids:
            return "错误: 未提供文件ID"
        
        # 统一使用批量处理逻辑（无论是1个还是多个文件）
        output = ""
        
        # 获取引擎信息
        engine_info = get_scan_engine_info()
        
        # 显示扫描报告头部
        output = f"扫描报告\n"
        output += f"{'='*50}\n"
        output += f"扫描文件数: {len(file_ids)}\n"
        output += f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"扫描引擎: {engine_info['engine']}"
        if engine_info['langextract_enabled']:
            output += f" ({engine_info['langextract_provider']})"
        output += "\n"
        output += f"使用模型: {engine_info.get('langextract_model') or engine_info.get('langchain_model')}\n"
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
            
            result = scan_data.get('result', {})
            
            # 收集LangExtract结果用于可视化
            if scan_data.get('langextract_result'):
                langextract_results.append(scan_data['langextract_result'])
            
            # 格式化文件大小
            file_size_kb = scan_data.get('file_size', 0) / 1024
            
            # 判断解析状态
            parse_status = "内容完整"
            if result.get('summary', '').find('解析失败') >= 0:
                parse_status = "内容解析异常"
            
            # 输出文件结果
            output += f"\n内容源{idx}: {scan_data.get('file_name', '未知文件')}\n"
            output += f"1.文档信息：{file_size_kb:.1f}KB、文字{scan_data.get('char_count', 0)}"
            if scan_data.get('image_count', 0) > 0:
                output += f"(包含图片{scan_data['image_count']}张的解析内容)"
            output += "\n"
            output += f"2.文档解析状态：{parse_status}\n"
            output += f"3.文档摘要：{result.get('summary', '无摘要')[:100]}\n"
            output += f"4.敏感信息扫描结果："
            
            if result.get('has_sensitive', False):
                files_with_sensitive += 1
                total_sensitive_count += result.get('sensitive_count', 0)
                output += f"发现{result.get('sensitive_count', 0)}个敏感信息\n"
                # 最多展示3个
                sensitive_items = result.get('sensitive_items', [])
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
            "engine": engine_info['engine'],
            "model": engine_info.get('langextract_model') or engine_info.get('langchain_model'),
            "items": [],
            "statistics": {}
        }
        
        # 收集所有敏感信息项
        for scan_data in scan_results:
            if isinstance(scan_data, dict) and scan_data.get('success'):
                result = scan_data.get('result', {})
                file_name = scan_data.get('file_name', '未知文件')
                
                for item in result.get('sensitive_items', []):
                    report_item = {
                        "type": item.get('type', '未知类型'),
                        "masked_value": item.get('masked_value', '***'),
                        "context": item.get('context', ''),
                        "file": file_name
                    }
                    report_data["items"].append(report_item)
                    
                    # 统计
                    item_type = item.get('type', '未知类型')
                    if item_type not in report_data["statistics"]:
                        report_data["statistics"][item_type] = 0
                    report_data["statistics"][item_type] += 1
        
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
                
                # 如果使用LangExtract，仍然可以生成HTML可视化
                if enable_visualization and USE_LANGEXTRACT and langextract_results:
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


def get_scan_engine_info() -> Dict[str, Any]:
    """
    获取当前扫描引擎信息（内部方法）
    
    Returns:
        扫描引擎配置信息字典
    """
    return {
        "engine": "LangExtract" if USE_LANGEXTRACT else "LangChain",
        "langextract_enabled": USE_LANGEXTRACT,
        "langextract_provider": LANGEXTRACT_PROVIDER if USE_LANGEXTRACT else None,
        "langextract_model": LANGEXTRACT_MODEL if USE_LANGEXTRACT else None,
        "langextract_base_url": LANGEXTRACT_BASE_URL if USE_LANGEXTRACT and LANGEXTRACT_PROVIDER == 'custom' else None,
        "langchain_model": LLM_MODEL if not USE_LANGEXTRACT else None,
        "chunk_size": CHUNK_SIZE,
        "file_concurrency": FILE_CONCURRENCY,
        "visualization_enabled": USE_LANGEXTRACT,
        "visualization_output_dir": VISUALIZATION_OUTPUT_DIR if USE_LANGEXTRACT else None
    }


if __name__ == "__main__":
    # 启动服务器
    port = config.get('port', 3008)
    logger.info(f"Starting Sensitive Data Scanner MCP Server V2 on port {port}")
    
    # 显示引擎配置信息
    engine_info = get_scan_engine_info()
    logger.info(f"扫描引擎: {engine_info['engine']}")
    logger.info(f"模型: {engine_info.get('langextract_model') or engine_info.get('langchain_model')}")
    if engine_info['langextract_enabled']:
        logger.info(f"提供商: {engine_info['langextract_provider']}")
        logger.info(f"可视化: 已启用 (输出目录: {engine_info['visualization_output_dir']})")
    logger.info(f"分块大小: {engine_info['chunk_size']} 字符")
    logger.info(f"文件并发度: {engine_info['file_concurrency']}")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)