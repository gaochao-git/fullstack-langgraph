"""敏感数据扫描节点实现"""
from typing import Dict, Any, Literal
import re
from datetime import datetime
from langchain_core.messages import AIMessage
from src.shared.db.config import get_async_db_context
from src.apps.agent.service.document_service import document_service
from src.shared.core.logging import get_logger
from .state import OverallState
from .llm import get_llm
from .prompts import get_system_prompt_async
from .configuration import INIT_AGENT_CONFIG

logger = get_logger(__name__)


async def prepare_scan(state: OverallState) -> Dict[str, Any]:
    """准备扫描：获取文件内容并创建扫描队列"""
    file_contents = {}
    errors = []
    user_input_text = ""
    scan_queue = []
    
    # 1. 提取用户输入的文本
    for msg in state["messages"]:
        if hasattr(msg, "type") and msg.type == "human":
            user_input_text = msg.content
            logger.info(f"提取到用户输入文本: {user_input_text[:100]}...")
            break
    
    # 2. 从消息中提取文件信息
    file_ids = []
    file_info_map = {}
    
    for msg in state["messages"]:
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            if "files" in msg.additional_kwargs and isinstance(msg.additional_kwargs["files"], list):
                for file_info in msg.additional_kwargs["files"]:
                    if isinstance(file_info, dict) and "file_id" in file_info:
                        file_id = file_info["file_id"]
                        file_ids.append(file_id)
                        file_info_map[file_id] = {
                            "file_name": file_info.get("file_name", f"未知文件_{file_id[:8]}"),
                            "file_size": file_info.get("file_size", 0)
                        }
    
    # 合并state中的file_ids
    if state.get("file_ids"):
        file_ids.extend(state["file_ids"])
    file_ids = list(set(file_ids))
    
    # 3. 判断扫描内容
    has_user_text = bool(user_input_text and user_input_text.strip())
    has_files = bool(file_ids)
    
    if not has_user_text and not has_files:
        return {
            "user_input_text": "",
            "file_contents": {},
            "errors": ["未找到需要扫描的内容"],
            "messages": [AIMessage(content="未找到需要扫描的内容，请提供文本或上传文件")],
            "scan_queue": [],
            "current_scan_index": 0
        }
    
    # 4. 获取文件内容
    if has_files:
        logger.info(f"准备获取文件内容，file_ids: {file_ids}")
        
        async with get_async_db_context() as db:
            for file_id in file_ids:
                try:
                    doc_info = await document_service.get_document_content(db, file_id)
                    if doc_info:
                        content = doc_info.get("content") or ""
                        
                        if file_id in file_info_map:
                            file_name = file_info_map[file_id]["file_name"]
                            file_size = file_info_map[file_id]["file_size"]
                        else:
                            file_name = doc_info.get("file_name") or f"未知文件_{file_id[:8]}"
                            file_size = doc_info.get("file_size") or 0
                        
                        word_count = len(content)
                        image_pattern = r'\[图片[^\]]*\]'
                        image_matches = re.findall(image_pattern, content)
                        image_count = len(image_matches)
                        
                        file_contents[file_id] = {
                            "content": content,
                            "file_name": file_name,
                            "file_size": file_size,
                            "word_count": word_count,
                            "image_count": image_count
                        }
                        logger.info(f"成功获取文件 {file_name} 的内容，字数: {word_count}, 图片数: {image_count}")
                    else:
                        error_msg = f"无法获取文件 {file_id} 的内容"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                except Exception as e:
                    error_msg = f"获取文件 {file_id} 时出错: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
    
    # 5. 构建扫描队列
    # 添加用户输入文本到队列
    if has_user_text:
        scan_queue.append({
            "source_type": "user_input",
            "source_name": "用户输入文本",
            "content": user_input_text,
            "file_name": "user_input",
            "file_size": len(user_input_text.encode('utf-8')),
            "word_count": len(user_input_text),
            "image_count": 0
        })
    
    # 添加文件到队列
    for file_id, file_info in file_contents.items():
        # 检查是否需要分块处理
        content = file_info["content"]
        file_name = file_info["file_name"]
        
        # 简单的分块策略：如果内容超过50000字符，则分块
        max_chunk_size = 50000
        if len(content) > max_chunk_size:
            # 分块处理
            chunks = []
            chunk_size = max_chunk_size
            for i in range(0, len(content), chunk_size):
                chunks.append(content[i:i + chunk_size])
            
            for idx, chunk in enumerate(chunks):
                scan_queue.append({
                    "source_type": "file_chunk",
                    "source_name": f"文件：{file_name} (块 {idx + 1}/{len(chunks)})",
                    "content": chunk,
                    "file_name": file_name,
                    "file_size": file_info["file_size"],
                    "word_count": len(chunk),
                    "image_count": len(re.findall(r'\[图片[^\]]*\]', chunk)),
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                    "original_word_count": file_info["word_count"],
                    "original_image_count": file_info["image_count"]
                })
        else:
            # 不需要分块
            scan_queue.append({
                "source_type": "file",
                "source_name": f"文件：{file_name}",
                "content": content,
                "file_name": file_name,
                "file_size": file_info["file_size"],
                "word_count": file_info["word_count"],
                "image_count": file_info["image_count"]
            })
    
    # 6. 生成状态消息
    status_parts = []
    if has_user_text:
        status_parts.append("用户输入文本")
    if file_contents:
        status_parts.append(f"{len(file_contents)} 个文件")
    
    status_message = f"准备扫描: {' 和 '.join(status_parts)}"
    
    return {
        "user_input_text": user_input_text,
        "file_contents": file_contents,
        "errors": state.get("errors", []) + errors,
        "scan_queue": scan_queue,
        "current_scan_index": 0,
        "all_scan_results": [],
        "messages": [AIMessage(content=status_message)]
    }


async def emit_scan_progress(state: OverallState) -> Dict[str, Any]:
    """发送扫描进度消息"""
    scan_queue = state.get("scan_queue", [])
    current_index = state.get("current_scan_index", 0)
    
    if current_index >= len(scan_queue):
        return {}
    
    source = scan_queue[current_index]
    total = len(scan_queue)
    
    logger.info(f"发送扫描进度 [{current_index + 1}/{total}] - {source['source_name']}")
    
    # 只发送进度消息
    progress_message = AIMessage(
        content=f"[{current_index + 1}/{total}] 正在扫描: {source['source_name']}",
        additional_kwargs={
            "scan_phase": "progress",
            "scan_step": current_index + 1,
            "total_steps": total,
            "source_name": source['source_name'],
            "timestamp": datetime.now().isoformat()
        }
    )
    
    return {
        "messages": [progress_message]
    }


async def perform_scan(state: OverallState) -> Dict[str, Any]:
    """执行扫描并返回结果"""
    scan_queue = state.get("scan_queue", [])
    current_index = state.get("current_scan_index", 0)
    all_scan_results = state.get("all_scan_results", [])
    
    if current_index >= len(scan_queue):
        return {}
    
    source = scan_queue[current_index]
    
    # 创建LLM实例
    llm = get_llm()
    
    try:
        # 获取提示词模板（优先使用数据库配置）
        agent_id = INIT_AGENT_CONFIG["agent_id"]
        prompt_template = await get_system_prompt_async(agent_id)
        
        # 使用提示词模板
        prompt = prompt_template.format(
            source_name=source['source_name'],
            content_length=len(source['content']),
            file_name=source['file_name'],
            content=source['content']
        )
        
        # 调用LLM扫描
        result = await llm.ainvoke(prompt)
        
        # 解析扫描结果
        scan_content = result.content
        is_error = ("文件内容异常" in scan_content or 
                   "解析失败" in scan_content or
                   "部分内容" in scan_content)
        has_sensitive = "未发现敏感信息" not in scan_content and not is_error
        
        # 创建结果消息
        result_message = AIMessage(
            content=f"{source['source_name']} 扫描结果：\n{scan_content}",
            additional_kwargs={
                "scan_phase": "result",
                "scan_step": current_index + 1,
                "source_name": source['source_name'],
                "source_type": source.get('source_type', 'file'),
                "has_sensitive": has_sensitive,
                "is_error": is_error,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 添加到结果列表
        scan_result = {
            "source": source['source_name'],
            "source_type": source.get('source_type', 'file'),
            "scan_result": scan_content,
            "has_sensitive": has_sensitive,
            "error": False,
            "is_content_error": is_error,
            "file_size": source['file_size'],
            "word_count": source['word_count'],
            "image_count": source['image_count'],
            "file_name": source['file_name']
        }
        
        if source.get('chunk_index') is not None:
            scan_result['chunk_index'] = source['chunk_index']
            scan_result['total_chunks'] = source['total_chunks']
        
        all_scan_results.append(scan_result)
        
        # 更新状态，移动到下一个
        return {
            "messages": [result_message],
            "current_scan_index": current_index + 1,
            "all_scan_results": all_scan_results
        }
        
    except Exception as e:
        logger.error(f"扫描 {source['source_name']} 时出错: {e}")
        
        # 处理错误
        error_message = str(e)
        if "maximum context length" in error_message:
            scan_result_text = "文件内容过长|||文件超出模型处理能力范围|||未发现敏感信息"
            is_error = True
        elif "Error code: 400" in error_message:
            scan_result_text = "文件处理失败|||模型处理请求失败|||未发现敏感信息"
            is_error = True
        else:
            scan_result_text = f"扫描失败|||{error_message[:50]}...|||未发现敏感信息"
            is_error = False
        
        error_msg = AIMessage(
            content=f"{source['source_name']} 扫描出错：\n{scan_result_text}",
            additional_kwargs={
                "scan_phase": "error",
                "scan_step": current_index + 1,
                "source_name": source['source_name'],
                "error_message": error_message,
                "is_error": is_error,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        all_scan_results.append({
            "source": source['source_name'],
            "source_type": source.get('source_type', 'file'),
            "scan_result": scan_result_text,
            "has_sensitive": False,
            "error": True,
            "is_content_error": is_error,
            "file_size": source['file_size'],
            "word_count": source['word_count'],
            "image_count": source['image_count'],
            "file_name": source['file_name']
        })
        
        return {
            "messages": [error_msg],
            "current_scan_index": current_index + 1,
            "all_scan_results": all_scan_results
        }


async def generate_final_report(state: OverallState) -> Dict[str, Any]:
    """生成最终扫描报告"""
    scan_queue = state.get("scan_queue", [])
    all_scan_results = state.get("all_scan_results", [])
    
    # 生成扫描报告
    final_report = generate_scan_report(scan_queue, all_scan_results)
    
    # 添加最终报告消息
    return {
        "messages": [AIMessage(
            content=final_report,
            additional_kwargs={
                "scan_phase": "complete",
                "total_sources": len(scan_queue),
                "total_results": len(all_scan_results),
                "timestamp": datetime.now().isoformat()
            }
        )]
    }


def check_scan_progress(state: OverallState) -> Literal["progress", "scan", "report"]:
    """检查扫描进度，决定下一步"""
    scan_queue = state.get("scan_queue", [])
    current_index = state.get("current_scan_index", 0)
    
    if current_index < len(scan_queue):
        return "progress"  # 先显示进度
    else:
        return "report"   # 生成报告


def generate_scan_report(scan_sources: list, all_scan_results: list) -> str:
    """生成扫描报告"""
    # 聚合分块文件的结果
    file_results = {}  # 用于存储每个文件的聚合结果
    user_input_results = []  # 用户输入的结果
    
    for i, result in enumerate(all_scan_results):
        source = scan_sources[i]
        
        if source['source_type'] == 'user_input':
            user_input_results.append(result)
        else:
            # 文件或文件块
            file_name = source['file_name']
            if file_name not in file_results:
                file_results[file_name] = {
                    'chunks': [],
                    'file_size': source['file_size'],
                    'total_word_count': source.get('original_word_count', source['word_count']),
                    'total_image_count': source.get('original_image_count', source['image_count']),
                    'has_sensitive': False,
                    'has_error': False,
                    'is_content_error': False,
                    'all_chunks_complete': True
                }
            
            file_results[file_name]['chunks'].append({
                'chunk_index': source.get('chunk_index'),
                'result': result,
                'source': source
            })
            
            # 更新聚合状态
            if result.get('has_sensitive'):
                file_results[file_name]['has_sensitive'] = True
            if result.get('error'):
                file_results[file_name]['has_error'] = True
            if result.get('is_content_error'):
                file_results[file_name]['is_content_error'] = True
    
    # 计算扫描概览数据
    total_files = len(file_results) + (1 if user_input_results else 0)
    total_image_count = sum(fr['total_image_count'] for fr in file_results.values())
    
    # 构建报告内容
    report_parts = []
    
    # 扫描概览
    report_parts.append("【扫描概览】")
    report_parts.append("")  # 添加空行
    report_parts.append(f"扫描范围：{total_files} 个内容源")
    if total_image_count > 0:
        report_parts.append(f"包含图片：{total_image_count} 张（已解析为文字）")
    report_parts.append("")
    
    # 扫描详情
    report_parts.append("【扫描详情】")
    
    content_index = 1
    
    # 1. 先处理用户输入（如果有）
    if user_input_results:
        for result in user_input_results:
            report_parts.append(f"\n内容源{content_index}:用户输入文本")
            _add_scan_result_to_report(report_parts, result, None)
            content_index += 1
    
    # 2. 处理文件（聚合分块结果）
    for file_name, file_data in file_results.items():
        # 文件名加粗（如果有错误或敏感信息）
        if file_data['has_error'] or file_data['is_content_error'] or file_data['has_sensitive']:
            display_source = f"用户上传文件**{file_name}**"
        else:
            display_source = f"用户上传文件{file_name}"
        
        report_parts.append(f"\n内容源{content_index}:{display_source}")
        
        # 如果文件被分块，需要聚合结果
        chunks = sorted(file_data['chunks'], key=lambda x: x['chunk_index'] or 0)
        if len(chunks) > 1:
            # 聚合多个块的结果
            _add_aggregated_chunk_results_to_report(report_parts, file_data, chunks)
        else:
            # 单个文件，直接添加结果
            _add_scan_result_to_report(report_parts, chunks[0]['result'], file_data)
        
        content_index += 1
    
    # 继续原来的扫描总结部分（需要修改以使用聚合后的数据）
    report_parts.append("\n【扫描总结】")
    report_parts.append("")  # 添加一个空行
    
    # 收集异常文件和敏感信息文件的名称
    error_files = []
    sensitive_files = []
    
    # 处理用户输入
    for result in user_input_results:
        if result.get("error") or result.get("is_content_error"):
            error_files.append("用户输入文本")
        if result.get("has_sensitive"):
            sensitive_files.append("用户输入文本")
    
    # 处理文件
    for file_name, file_data in file_results.items():
        if file_data['has_error'] or file_data['is_content_error']:
            error_files.append(file_name)
        if file_data['has_sensitive']:
            sensitive_files.append(file_name)
    
    # 构建总结内容
    report_parts.append(f"1. 总计扫描：{total_files} 个内容源")
    
    # 文档异常
    if error_files:
        error_names = "、".join(error_files)
        report_parts.append(f"2. 文档异常：{len(error_files)} 个内容源（{error_names}）")
    else:
        report_parts.append(f"2. 文档异常：0 个内容源")
    
    # 敏感信息
    if sensitive_files:
        sensitive_names = "、".join(sensitive_files)
        report_parts.append(f"3. 敏感信息：{len(sensitive_files)} 个内容源（{sensitive_names}）")
    else:
        report_parts.append(f"3. 敏感信息：0 个内容源")
    
    return "\n".join(report_parts)


def _add_scan_result_to_report(report_parts, result, file_data=None):
    """添加单个扫描结果到报告"""
    # 初始化默认值
    doc_parse_status = "内容已解析"
    doc_summary = "无摘要"
    scan_result = "未发现敏感信息"
    
    # 从结果中提取信息
    scan_content = result['scan_result'].strip()
    
    # 解析|||分隔的格式
    parts = scan_content.split('|||')
    if len(parts) >= 3:
        doc_parse_status = parts[0].strip()
        doc_summary = parts[1].strip()
        scan_result = parts[2].strip()
    
    # 生成文档信息
    if file_data:
        file_size = file_data['file_size']
        word_count = file_data['total_word_count']
        image_count = file_data['total_image_count']
    else:
        file_size = result.get('file_size', 0)
        word_count = result.get('word_count', 0)
        image_count = result.get('image_count', 0)
    
    # 将字节转换为KB
    file_size_kb = round(file_size / 1024, 1) if file_size > 0 else 0
    
    # 构建文档信息
    doc_info = f"文件大小: {file_size_kb}KB • 文字数量: {word_count}字"
    if image_count > 0:
        doc_info += f"（含{image_count}张图片解析内容）"
    
    # 按固定格式输出四个标签
    report_parts.append(f"1. 文档解析状态：{doc_parse_status}")
    report_parts.append(f"2. 文档摘要：{doc_summary}")
    report_parts.append(f"3. 文档信息：{doc_info}")
    report_parts.append(f"4. 敏感信息扫描结果：{scan_result}")


def _add_aggregated_chunk_results_to_report(report_parts, file_data, chunks):
    """聚合分块文件的结果并添加到报告"""
    # 收集所有块的信息
    all_summaries = []
    all_sensitive_info = []
    parse_statuses = set()
    
    for chunk_data in chunks:
        result = chunk_data['result']
        scan_content = result['scan_result'].strip()
        
        parts = scan_content.split('|||')
        if len(parts) >= 3:
            parse_status = parts[0].strip()
            summary = parts[1].strip()
            sensitive_info = parts[2].strip()
            
            parse_statuses.add(parse_status)
            if summary and summary != "无摘要":
                all_summaries.append(f"块{chunk_data['chunk_index']}: {summary}")
            if "发现敏感信息" in sensitive_info:
                # 提取敏感信息的具体内容（括号中的部分）
                import re
                match = re.search(r'\((.*?)\)', sensitive_info)
                if match:
                    sensitive_details = match.group(1)
                    # 如果有多个敏感信息，只取第一个
                    if ';' in sensitive_details:
                        first_sensitive = sensitive_details.split(';')[0].strip()
                    else:
                        first_sensitive = sensitive_details
                    all_sensitive_info.append(f"块{chunk_data['chunk_index']}: {first_sensitive}")
                else:
                    all_sensitive_info.append(f"块{chunk_data['chunk_index']}: {sensitive_info}")
    
    # 确定整体解析状态
    if "解析失败" in parse_statuses:
        overall_parse_status = "部分内容解析失败"
    elif "文件内容过长" in parse_statuses:
        overall_parse_status = "部分内容过长"
    elif "部分内容" in parse_statuses:
        overall_parse_status = "部分内容"
    else:
        overall_parse_status = "内容完整"
    
    # 构建整体摘要
    if all_summaries:
        if len(all_summaries) > 3:
            overall_summary = f"大型文件，分{len(chunks)}块扫描"
        else:
            overall_summary = "; ".join(all_summaries[:2]) + ("..." if len(all_summaries) > 2 else "")
    else:
        overall_summary = f"大型文件，分{len(chunks)}块扫描"
    
    # 构建敏感信息结果
    if all_sensitive_info:
        if len(all_sensitive_info) > 3:
            # 显示前3个块的敏感信息，并标注总数
            selected_info = all_sensitive_info[:3]
            overall_sensitive = f"发现敏感信息({'; '.join(selected_info)}等，共{len(all_sensitive_info)}处)"
        else:
            overall_sensitive = f"发现敏感信息({'; '.join(all_sensitive_info)})"
    else:
        overall_sensitive = "未发现敏感信息"
    
    # 生成文档信息
    file_size_kb = round(file_data['file_size'] / 1024, 1) if file_data['file_size'] > 0 else 0
    doc_info = f"文件大小: {file_size_kb}KB • 文字数量: {file_data['total_word_count']}字"
    if file_data['total_image_count'] > 0:
        doc_info += f"（含{file_data['total_image_count']}张图片解析内容）"
    doc_info += f" • 分{len(chunks)}块扫描"
    
    # 输出结果
    report_parts.append(f"1. 文档解析状态：{overall_parse_status}")
    report_parts.append(f"2. 文档摘要：{overall_summary}")
    report_parts.append(f"3. 文档信息：{doc_info}")
    report_parts.append(f"4. 敏感信息扫描结果：{overall_sensitive}")