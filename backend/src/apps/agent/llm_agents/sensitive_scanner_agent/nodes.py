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
            "file_name": "用户输入文本"
        })
    
    # 2. 文件内容（每个文件作为独立的扫描源）
    for file_id, file_info in state.get("file_contents", {}).items():
        if file_info.get("content"):
            scan_sources.append({
                "source_name": f"文件：{file_info.get('file_name', file_id)}",
                "content": file_info["content"],
                "source_type": "file",
                "file_id": file_id,
                "file_size": file_info.get("file_size", 0),
                "word_count": file_info.get("word_count", 0),
                "image_count": file_info.get("image_count", 0),
                "file_name": file_info.get("file_name", "")
            })
    
    return scan_sources


def generate_scan_report(scan_sources: list, all_scan_results: list) -> str:
    """生成扫描报告"""
    # 统计总图片数量（直接使用预计算的值）
    total_image_count = sum(result.get('image_count', 0) for result in all_scan_results)
    
    # 构建报告内容
    report_parts = []
    
    # 扫描概览
    report_parts.append("【扫描概览】")
    report_parts.append("")  # 添加空行
    report_parts.append(f"扫描范围：{len(scan_sources)} 个内容源")
    if total_image_count > 0:
        report_parts.append(f"包含图片：{total_image_count} 张（已解析为文字）")
    report_parts.append("")
    
    # 扫描详情
    report_parts.append("【扫描详情】")
    for i, result in enumerate(all_scan_results, 1):
        # 构建内容源标题
        if result.get('source_type') == 'user_input':
            display_source = "用户输入文本"
        else:
            display_source = f"用户上传文件{result['file_name']}"
        report_parts.append(f"\n内容源{i}:{display_source}")
        
        # 准备默认状态（仅在LLM没有返回状态时使用）
        if result.get("error") or result.get("is_content_error"):
            status = "内容解析异常"
        else:
            status = "内容已解析"
        
        # 从LLM返回的内容中提取信息
        scan_content = result['scan_result']
        
        # 解析LLM的输出（现在有3行）并按顺序组装报告
        lines = scan_content.strip().split('\n')
        
        # 临时存储各部分内容
        doc_parse_status = ""
        doc_summary = ""
        scan_result = ""
        
        for line in lines:
            if line.startswith('1. '):
                # 文档解析状态
                doc_parse_status = '1. ' + line[3:]
            elif line.startswith('2. '):
                # 文档摘要
                doc_summary = '2. ' + line[3:]
            elif line.startswith('3. '):
                # 敏感信息扫描结果
                scan_result = '4. ' + line[3:]
        
        # 按正确的顺序添加到报告中
        # 1. 文件状态（使用LLM返回的解析状态，而不是系统判断的状态）
        if doc_parse_status:
            report_parts.append(doc_parse_status)
        else:
            # 如果LLM没有返回状态，使用默认状态
            report_parts.append(f"1. 文件状态：{status}")
            
        if doc_summary:
            report_parts.append(doc_summary)
        
        # 添加文档信息行（第3行）
        file_size = result.get('file_size', 0)
        word_count = result.get('word_count', 0)
        image_count = result.get('image_count', 0)
        
        # 将字节转换为KB，保留1位小数
        file_size_kb = round(file_size / 1024, 1) if file_size > 0 else 0
        
        # 构建文档信息
        doc_info = f"3. 文档信息：文件大小: {file_size_kb}KB • 文字数量: {word_count}字"
        if image_count > 0:
            doc_info += f"（含{image_count}张图片解析内容）"
        report_parts.append(doc_info)
        
        # 添加敏感信息扫描结果（第4行）
        if scan_result:
            report_parts.append(scan_result)
    
    # 扫描总结
    report_parts.append("\n【扫描总结】")
    report_parts.append("")  # 添加一个空行
    
    # 收集异常文件和敏感信息文件的名称
    error_files = []
    sensitive_files = []
    
    for result in all_scan_results:
        # 直接使用预存的文件名
        file_name = result.get('file_name') or result['source']
        
        # 收集异常文件
        if result.get("error") or result.get("is_content_error"):
            error_files.append(file_name)
            
        # 收集包含敏感信息的文件
        if result.get("has_sensitive"):
            sensitive_files.append(file_name)
    
    # 构建总结内容
    report_parts.append(f"1. 总计扫描：{len(scan_sources)} 个内容源")
    
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
                content=source['content'][:500000]  # 限制内容长度
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
            all_scan_results.append({
                "source": source['source_name'],
                "source_type": source.get('source_type', 'file'),
                "scan_result": f"扫描失败: {str(e)}",
                "has_sensitive": False,
                "error": True,
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