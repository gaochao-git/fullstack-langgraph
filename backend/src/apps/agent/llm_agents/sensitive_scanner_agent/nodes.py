"""敏感数据扫描节点实现"""
from typing import Dict, Any
import re
from langchain_core.messages import AIMessage
from src.shared.db.config import get_async_db_context
from src.apps.agent.service.document_service import document_service
from src.shared.core.logging import get_logger
from .state import OverallState
from .llm import get_llm
from .prompts import SCAN_PROMPT_TEMPLATE

logger = get_logger(__name__)


async def fetch_files(state: OverallState) -> Dict[str, Any]:
    """获取文件内容和用户输入文本"""
    file_contents = {}
    errors = []
    user_input_text = ""
    
    # 1. 提取用户输入的文本
    for msg in state["messages"]:
        # 找到用户的消息（human message）
        if hasattr(msg, "type") and msg.type == "human":
            user_input_text = msg.content
            logger.info(f"提取到用户输入文本: {user_input_text[:100]}...")
            break
    
    # 2. 从消息中提取 file_ids
    file_ids = []
    for msg in state["messages"]:
        # 检查是否是 human message 且包含 file_ids
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            if "file_ids" in msg.additional_kwargs:
                file_ids.extend(msg.additional_kwargs["file_ids"])
    
    # 如果state中也有file_ids，合并
    if state.get("file_ids"):
        file_ids.extend(state["file_ids"])
    
    # 去重
    file_ids = list(set(file_ids))
    
    # 3. 判断扫描内容
    has_user_text = bool(user_input_text and user_input_text.strip())
    has_files = bool(file_ids)
    
    if not has_user_text and not has_files:
        return {
            "user_input_text": "",
            "file_contents": {},
            "errors": ["未找到需要扫描的内容"],
            "messages": state["messages"] + [AIMessage(content="未找到需要扫描的内容，请提供文本或上传文件")]
        }
    
    # 4. 获取文件内容（如果有）
    if has_files:
        logger.info(f"准备获取文件内容，file_ids: {file_ids}")
        
        async with get_async_db_context() as db:
            for file_id in file_ids:
                try:
                    doc_info = await document_service.get_document_content(db, file_id)
                    if doc_info:
                        # 安全地获取文件信息，避免None值
                        content = doc_info.get("content") or ""
                        file_name = doc_info.get("file_name") or f"未知文件_{file_id[:8]}"
                        file_size = doc_info.get("file_size") or 0
                        
                        # 计算文字数量
                        word_count = len(content)
                        
                        # 统计图片数量
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
                        # 调试：记录获取到的文件信息（不记录内容，避免敏感信息泄露）
                        logger.info(f"文件 {file_id} 信息: file_name={file_name}, file_size={file_size}, words={word_count}, images={image_count}")
                    else:
                        errors.append(f"文件 {file_id} 不存在")
                except Exception as e:
                    logger.error(f"获取文件内容失败 {file_id}: {e}")
                    errors.append(f"获取文件 {file_id} 失败: {str(e)}")
    
    # 5. 生成状态消息
    status_parts = []
    if has_user_text:
        status_parts.append("用户输入文本")
    if len(file_contents) > 0:
        status_parts.append(f"{len(file_contents)} 个文件")
    
    status_message = f"准备扫描: {' 和 '.join(status_parts)}"
    
    return {
        "user_input_text": user_input_text,
        "file_contents": file_contents,
        "errors": state.get("errors", []) + errors,
        "messages": state["messages"] + [AIMessage(content=status_message)]
    }


def prepare_scan_sources(state: OverallState) -> list:
    """准备所有需要扫描的内容源"""
    scan_sources = []
    CHUNK_SIZE = 50000  # 每个块的最大字符数
    
    # 1. 用户输入文本
    user_text = state.get("user_input_text", "")
    if user_text and user_text.strip():
        scan_sources.append({
            "source_name": "用户输入文本",
            "content": user_text,
            "source_type": "user_input",
            "word_count": len(user_text),
            "file_size": 0,
            "image_count": 0,
            "file_name": "用户输入文本",
            "chunk_index": None,
            "total_chunks": 1
        })
    
    # 2. 文件内容（每个文件可能被拆分为多个块）
    for file_id, file_info in state.get("file_contents", {}).items():
        content = file_info.get("content", "")
        if not content:
            continue
            
        content_length = len(content)
        file_name = file_info.get('file_name', file_id)
        
        # 如果内容长度小于等于块大小，作为单个源处理
        if content_length <= CHUNK_SIZE:
            scan_sources.append({
                "source_name": f"文件：{file_name}",
                "content": content,
                "source_type": "file",
                "file_id": file_id,
                "file_size": file_info.get("file_size", 0),
                "word_count": file_info.get("word_count", 0),
                "image_count": file_info.get("image_count", 0),
                "file_name": file_name,
                "chunk_index": None,
                "total_chunks": 1
            })
        else:
            # 需要分块处理
            total_chunks = (content_length + CHUNK_SIZE - 1) // CHUNK_SIZE
            logger.info(f"文件 {file_name} 需要分成 {total_chunks} 个块进行扫描")
            
            for i in range(total_chunks):
                start = i * CHUNK_SIZE
                end = min((i + 1) * CHUNK_SIZE, content_length)
                chunk_content = content[start:end]
                
                # 统计当前块的图片数量
                image_pattern = r'\[图片[^\]]*\]'
                chunk_image_count = len(re.findall(image_pattern, chunk_content))
                
                scan_sources.append({
                    "source_name": f"文件：{file_name} (块 {i+1}/{total_chunks})",
                    "content": chunk_content,
                    "source_type": "file_chunk",
                    "file_id": file_id,
                    "file_size": file_info.get("file_size", 0),
                    "word_count": len(chunk_content),
                    "image_count": chunk_image_count,
                    "file_name": file_name,
                    "chunk_index": i + 1,
                    "total_chunks": total_chunks,
                    "original_word_count": file_info.get("word_count", 0),
                    "original_image_count": file_info.get("image_count", 0)
                })
    
    return scan_sources


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


async def scan_files(state: OverallState) -> Dict[str, Any]:
    """串行扫描用户输入和文件中的敏感数据，每个文件独立调用LLM"""
    
    # 准备所有需要扫描的内容源
    scan_sources = prepare_scan_sources(state)
    
    if not scan_sources:
        return {
            "messages": state["messages"] + [AIMessage(content="未找到需要扫描的内容")]
        }
    
    # 收集所有扫描结果
    all_scan_results = []
    
    # 串行扫描每个内容源
    for i, source in enumerate(scan_sources, 1):
        # 为每个源创建新的LLM实例
        llm = get_llm()
        
        logger.info(f"扫描进度 [{i}/{len(scan_sources)}] - {source['source_name']}")
        
        try:
            # 使用提示词模板
            prompt = SCAN_PROMPT_TEMPLATE.format(
                source_name=source['source_name'],
                content_length=len(source['content']),
                file_name=source['file_name'],
                content=source['content']  # 不限制内容长度
            )
            
            # 调用LLM扫描
            result = await llm.ainvoke(prompt)
            
            # 判断扫描结果类型
            scan_content = result.content
            # 检查是否为解析失败或内容异常（通过LLM返回的文档解析状态判断）
            is_error = ("文件内容异常" in scan_content or 
                       "解析失败" in scan_content or
                       "部分内容" in scan_content)
            has_sensitive = "未发现敏感信息" not in scan_content and not is_error
            
            all_scan_results.append({
                "source": source['source_name'],
                "source_type": source.get('source_type', 'file'),
                "scan_result": scan_content,
                "has_sensitive": has_sensitive,
                "is_content_error": is_error,
                "file_size": source['file_size'],
                "word_count": source['word_count'],
                "image_count": source['image_count'],
                "file_name": source['file_name']
            })
            
        except Exception as e:
            logger.error(f"扫描 {source['source_name']} 时出错: {e}")
            
            # 处理不同类型的错误
            error_message = str(e)
            if "maximum context length" in error_message:
                # 上下文长度超限错误
                scan_result = "文件内容过长|||文件超出模型处理能力范围|||未发现敏感信息"
                is_error = True
            elif "Error code: 400" in error_message:
                # 其他400错误
                scan_result = "文件处理失败|||模型处理请求失败|||未发现敏感信息"
                is_error = True
            else:
                # 其他错误
                scan_result = f"扫描失败|||{error_message[:50]}...|||未发现敏感信息"
                is_error = False
            
            all_scan_results.append({
                "source": source['source_name'],
                "source_type": source.get('source_type', 'file'),
                "scan_result": scan_result,
                "has_sensitive": False,
                "error": True,
                "is_content_error": is_error,
                "file_size": source['file_size'],
                "word_count": source['word_count'],
                "image_count": source['image_count'],
                "file_name": source['file_name']
            })
    
    # 生成扫描报告
    final_report = generate_scan_report(scan_sources, all_scan_results)
    
    # 只返回一个最终的综合报告消息
    return {
        "messages": state["messages"] + [AIMessage(content=final_report)]
    }