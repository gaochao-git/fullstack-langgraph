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
    """扫描用户输入和文件中的敏感数据"""
    llm = get_llm()
    
    # 构建所有需要扫描的内容
    all_content = []
    
    # 添加用户输入
    user_text = state.get("user_input_text", "")
    if user_text and user_text.strip():
        all_content.append(f"===== 用户输入文本 =====\n{user_text}")
    
    # 添加文件内容
    for file_id, file_info in state.get("file_contents", {}).items():
        if file_info.get("content"):
            file_name = file_info.get("file_name", file_id)
            all_content.append(f"\n===== 文件：{file_name} =====\n{file_info['content'][:2000]}")
    
    if not all_content:
        return {
            "messages": state["messages"] + [AIMessage(content="未找到需要扫描的内容")]
        }
    
    # 让LLM一次性扫描所有内容
    prompt = f"""你是一个敏感数据扫描工具。你的任务是扫描文本中的敏感信息并生成脱敏后的安全报告。

待扫描内容：
{'\n'.join(all_content)}

你的任务：扫描上述内容中的所有敏感数据，并生成脱敏报告。

重要提示：
- 单独的用户名（如：gaochao、admin等）不属于敏感信息，不需要脱敏
- 用户名+密码的组合才是敏感信息（需要对密码脱敏）
- 重点关注：身份证号、手机号、银行卡号、密码、邮箱、IP地址、API密钥等

重要要求：
- 绝对不要在报告中显示敏感信息的原始值
- 对所有敏感信息进行脱敏处理，规则如下：
  * 默认：将敏感信息的后半部分用*替换（如：gaochao → gao****，13812345678 → 138****5678）
  * 身份证号：只显示前6位和后4位（如：110101****1234）
  * 银行卡号：只显示前4位和后4位（如：6222****4321）
  * 邮箱：@前面部分隐藏一半（如：test@163.com → te**@163.com）
  * 密码：显示前2-3位字符，其余用*替换（如：12345678 → 123*****，password123 → pas*****）
  * 短密码（少于6位）：显示第一位（如：12345 → 1****）
- 说明在哪个内容源发现了什么类型的敏感信息
- 如果没有发现敏感数据，请明确说明

注意：这是一个安全扫描任务，不是文档内容总结。你只需要：
1. 找出敏感信息
2. 对其脱敏
3. 生成扫描报告

报告格式要求：
1. 使用与输入相同的分隔符格式
2. 文件名要完整显示，便于区分

示例：
===== 用户输入文本 =====
- 发现手机号：138****5678
- 发现邮箱：te**@163.com

===== 文件：example.txt =====
- 发现密码：555***** (关联用户名：gaochao)

===== 文件：data.docx =====
- 未发现敏感信息

总结：
- 扫描了X个内容源，Y个包含敏感信息
- 主要敏感类型：[列出发现的类型]

记住：这不是文档分析或内容总结，而是敏感数据安全扫描！"""
    
    result = await llm.ainvoke(prompt)
    
    return {
        "messages": state["messages"] + [AIMessage(content=result.content)]
    }