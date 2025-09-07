"""敏感数据扫描节点实现"""
from typing import Dict, Any
from langchain_core.messages import AIMessage
from src.shared.db.config import get_async_db_context
from src.apps.agent.service.document_service import document_service
from src.shared.core.logging import get_logger
from .state import OverallState
from .llm import get_llm

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
                        file_contents[file_id] = {
                            "content": doc_info.get("content", ""),
                            "file_name": doc_info.get("file_name", ""),
                            "file_size": doc_info.get("file_size", 0)
                        }
                        # 调试：记录获取到的文件信息
                        logger.info(f"文件 {file_id} 信息: file_name={doc_info.get('file_name')}, file_size={doc_info.get('file_size')}")
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


async def scan_files(state: OverallState) -> Dict[str, Any]:
    """串行扫描用户输入和文件中的敏感数据，每个文件独立调用LLM"""
    
    # 准备所有需要扫描的内容源
    scan_sources = []
    
    # 1. 用户输入文本
    user_text = state.get("user_input_text", "")
    if user_text and user_text.strip():
        scan_sources.append({
            "source_name": "用户输入文本",
            "content": user_text,
            "source_type": "user_input"
        })
    
    # 2. 文件内容（每个文件作为独立的扫描源）
    for file_id, file_info in state.get("file_contents", {}).items():
        if file_info.get("content"):
            scan_sources.append({
                "source_name": f"文件：{file_info.get('file_name', file_id)}",
                "content": file_info["content"],  # 不再截断
                "source_type": "file",
                "file_id": file_id,
                "file_size": file_info.get("file_size", len(file_info["content"]))
            })
    
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
            # 为每个源构建专门的提示词
            prompt = f"""你是一个敏感数据扫描工具。你的任务是扫描文本中的敏感信息并生成脱敏后的安全报告。

待扫描内容来源：{source['source_name']}
内容长度：{len(source['content'])} 字符

待扫描内容：
{source['content']}

你的任务：扫描上述内容中的所有敏感数据，并生成脱敏报告。

特别注意：
- 如果内容看起来像是文件解析失败的错误信息（如"解析失败"、"无法读取"、"文件损坏"等），请输出：
  • 文件内容异常：[简要说明异常情况]
- 如果内容是乱码或无法理解的格式，请输出：
  • 文件内容异常：文件可能已损坏或格式不支持

重要提示：
- 单独的用户名（如：gaochao、admin等）不属于敏感信息，不需要脱敏
- 用户名+密码的组合才是敏感信息（需要对密码脱敏）
- 重点关注：身份证号、手机号、银行卡号、密码、邮箱、IP地址、API密钥等

重要要求：
- 绝对不要在报告中显示敏感信息的原始值
- 对所有敏感信息进行脱敏处理，规则如下：
  * 默认：将敏感信息的后半部分用*替换（如：13812345678 → 138****5678）
  * 身份证号：只显示前6位和后4位（如：110101****1234）
  * 银行卡号：只显示前4位和后4位（如：6222****4321）
  * 邮箱：@前面部分隐藏一半（如：test@163.com → te**@163.com）
  * 密码：显示前2-3位字符，其余用*替换（如：12345678 → 123*****）
  * 短密码（少于6位）：显示第一位（如：12345 → 1****）

输出要求：
请严格按以下格式输出（每行紧凑，不要空行）：

1. 文档解析状态：[内容完整/部分内容/解析失败]
2. 文档摘要：[简要描述文档内容，不超过50字]
3. 敏感信息扫描结果：• 发现[类型]：[脱敏后的值] (关联信息) 或 • 未发现敏感信息

文档解析状态说明：
- 内容完整：文档成功解析，内容完整
- 部分内容：文档包含"内容过长，只获取部分信息"等提示
- 解析失败：文档包含"解析失败"、"无法读取"、"需要安装"等错误信息

重要：
- 只需要输出这3行
- 每行内容紧凑，不要换行
- 多个敏感信息用 • 分隔，都在第3行内"""
            
            # 调用LLM扫描
            result = await llm.ainvoke(prompt)
            
            # 判断扫描结果类型
            scan_content = result.content
            # 检查是否为解析失败或内容异常（通过LLM返回的文档解析状态判断）
            is_error = ("文件内容异常" in scan_content or 
                       "解析失败" in scan_content or
                       "部分内容" in scan_content)
            has_sensitive = "未发现敏感信息" not in scan_content and not is_error
            
            # 计算文字数量（包括全部内容）
            word_count = len(source['content'])
            
            all_scan_results.append({
                "source": source['source_name'],
                "scan_result": scan_content,
                "has_sensitive": has_sensitive,
                "is_content_error": is_error,
                "file_size": source.get('file_size', 0),  # 保存文件大小
                "word_count": word_count,  # 保存文字数量
                "content": source['content']  # 保存内容用于后续图片检测
            })
            
        except Exception as e:
            logger.error(f"扫描 {source['source_name']} 时出错: {e}")
            all_scan_results.append({
                "source": source['source_name'],
                "scan_result": f"扫描失败: {str(e)}",
                "has_sensitive": False,
                "error": True,
                "file_size": source.get('file_size', 0),  # 保存文件大小
                "word_count": 0,  # 错误时文字数量为0
                "content": source.get('content', '')  # 保存内容用于后续图片检测
            })
    
    # 构建最终的综合报告
    sensitive_count = sum(1 for r in all_scan_results if r.get("has_sensitive", False))
    error_count = sum(1 for r in all_scan_results if r.get("error", False))
    content_error_count = sum(1 for r in all_scan_results if r.get("is_content_error", False))
    
    # 统计总图片数量
    import re
    total_image_count = 0
    image_pattern = r'\[图片[^\]]*\]'
    for result in all_scan_results:
        content = result.get('content', '')
        if content:
            image_matches = re.findall(image_pattern, content)
            total_image_count += len(image_matches)
    
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
        source_type = "用户输入文本" if i == 1 and "用户输入" in result['source'] else f"用户上传文件{result['source'].replace('文件：', '')}"
        report_parts.append(f"\n内容源{i}:{source_type}")
        
        # 准备默认状态（仅在LLM没有返回状态时使用）
        if result.get("error"):
            status = "内容解析异常"
        elif result.get("is_content_error"):
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
        # 将字节转换为KB，保留1位小数
        file_size_kb = round(file_size / 1024, 1) if file_size > 0 else 0
        
        # 检查内容中是否包含图片标记
        content = result.get('content', '')
        # 匹配各种图片标记格式：[图片文件: xxx]、[图片 1]、[图片1]等
        image_pattern = r'\[图片[^\]]*\]'
        image_matches = re.findall(image_pattern, content)
        image_count = len(image_matches)
        
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
        # 提取文件名（去掉"文件："前缀）
        source_name = result['source']
        if source_name.startswith("文件："):
            file_name = source_name[3:]
        else:
            file_name = source_name
            
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
    
    final_report = "\n".join(report_parts)
    
    # 只返回一个最终的综合报告消息
    return {
        "messages": state["messages"] + [AIMessage(content=final_report)]
    }