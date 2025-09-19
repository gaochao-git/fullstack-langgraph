"""
消息监控 Hook - 用于 create_react_agent 的 pre_model_hook
监控上下文使用情况，在接近限制时注入提醒消息
"""

import os
from pathlib import Path
import tiktoken
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, RemoveMessage

from src.shared.core.logging import get_logger
from src.shared.core.config import settings

logger = get_logger(__name__)

# 设置 tiktoken 缓存目录为 hooks/tiktoken 子目录
# 所有 tiktoken 编码器文件都放在这个目录下
tiktoken_cache_dir = Path(__file__).parent / "tiktoken"
if tiktoken_cache_dir.exists():
    os.environ["TIKTOKEN_CACHE_DIR"] = str(tiktoken_cache_dir)
    logger.info(f"使用内置 tiktoken 缓存: {tiktoken_cache_dir}")

# 特殊标记，用于删除所有消息
REMOVE_ALL_MESSAGES = "__all__"


class MessageMonitorHook:
    """消息监控 Hook - 符合 create_react_agent 的 pre_model_hook 接口"""
    
    def __init__(self, llm_config=None):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.warning_threshold = settings.MULTI_TURN_CONTEXT_THRESHOLD  # 警告阈值（如0.8）
        self.critical_threshold = 0.95  # 严重警告阈值
        self.llm_config = llm_config  # 存储LLM配置
        
    def count_tokens(self, text: str) -> int:
        """计算文本的token数"""
        try:
            return len(self.encoder.encode(text))
        except Exception:
            # 粗略估算：中文约1.5字符/token，英文约4字符/token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + english_chars / 4)
    
    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            # 消息类型
            total += self.count_tokens(msg.__class__.__name__)
            # 消息内容
            total += self.count_tokens(str(msg.content))
            # 消息格式的额外开销
            total += 4
        return total
    
    def get_max_context_length(self) -> int:
        """获取模型的上下文长度"""
        max_context_length = 128000  # 默认值
        
        # 如果初始化时传入了llm_config，直接使用
        if self.llm_config:
            try:
                if hasattr(self.llm_config, 'config_data'):
                    # 如果是数据库模型对象
                    import json
                    config_data = json.loads(self.llm_config.config_data) if isinstance(self.llm_config.config_data, str) else self.llm_config.config_data
                    context_length = config_data.get("context_length")
                    if context_length:
                        max_context_length = int(context_length)
                        logger.debug(f"使用配置的上下文长度: {max_context_length}")
                elif isinstance(self.llm_config, dict):
                    # 如果是字典配置
                    context_length = self.llm_config.get("context_length")
                    if context_length:
                        max_context_length = int(context_length)
                        logger.debug(f"使用配置的上下文长度: {max_context_length}")
            except Exception as e:
                logger.debug(f"从llm_config获取上下文长度失败: {e}")
            
        return max_context_length
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理状态并返回更新
        
        Args:
            state: 包含 messages 的图状态
            
        Returns:
            状态更新字典，包含 llm_input_messages
        """
        logger.info("🔍 [MessageMonitorHook] 进入消息监控钩子")
        
        messages = state.get("messages", [])
        if not messages:
            logger.debug("[MessageMonitorHook] 没有消息，退出钩子")
            return {}
            
        # 获取模型上下文限制
        max_context_length = self.get_max_context_length()
        logger.debug(f"[MessageMonitorHook] 模型上下文长度: {max_context_length:,} tokens")
        
        # 计算总token数
        total_tokens = self.count_messages_tokens(messages)
        usage_ratio = total_tokens / max_context_length
        logger.info(
            f"📊 [MessageMonitorHook] 上下文使用情况: "
            f"{total_tokens:,}/{max_context_length:,} tokens ({usage_ratio*100:.1f}%)"
        )
        
        # 将token统计信息存储到状态中，供后续使用
        state["token_usage"] = {
            "used": total_tokens,
            "total": max_context_length,
            "percentage": usage_ratio * 100
        }
        
        # 检查最后一条消息是否是用户消息且过大
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                last_msg_tokens = self.count_tokens(str(last_msg.content))
                if last_msg_tokens > max_context_length * 0.9:  # 单条消息超过90%上下文
                    logger.error(
                        f"❌ 用户输入过长，无法处理:\n"
                        f"  - 消息长度: {last_msg_tokens:,} tokens\n"
                        f"  - 模型限制: {max_context_length:,} tokens\n"
                        f"  - 占用比例: {(last_msg_tokens / max_context_length * 100):.1f}%"
                    )
                    # 抛出异常，让上层处理
                    raise ValueError(
                        f"用户输入过长（{last_msg_tokens:,} tokens），"
                        f"超过模型上下文限制（{max_context_length:,} tokens）的90%。"
                        f"请缩短输入内容。"
                    )
        
        # 根据使用率决定是否注入警告
        if usage_ratio < self.warning_threshold:
            # 未达到警告阈值，不需要注入消息
            logger.info(f"✅ [MessageMonitorHook] 上下文使用率正常，退出钩子")
            return {}
            
        # 检查是否已经有警告消息（避免重复警告）
        has_warning = False
        for msg in messages[-5:]:  # 检查最近5条消息
            if isinstance(msg, SystemMessage) and "[上下文警告]" in str(msg.content):
                has_warning = True
                break
        
        if has_warning:
            logger.debug("[MessageMonitorHook] 已存在警告消息，跳过注入")
            return {}
            
        # 构建警告消息
        remaining_tokens = max_context_length - total_tokens
        remaining_percentage = (1 - usage_ratio) * 100
        
        if usage_ratio >= self.critical_threshold:
            # 严重警告
            warning_msg = SystemMessage(
                content=f"""[上下文警告] ⚠️ 对话即将达到模型上下文限制！
                
当前使用：{total_tokens:,} / {max_context_length:,} tokens ({usage_ratio*100:.1f}%)
剩余空间：{remaining_tokens:,} tokens ({remaining_percentage:.1f}%)

建议：
1. 立即开启新的对话，避免后续消息被截断
2. 保存当前对话的重要信息
3. 新对话中可以引用本次对话的关键结论"""
            )
        else:
            # 普通警告
            warning_msg = SystemMessage(
                content=f"""[上下文警告] 📊 对话上下文使用率较高
                
当前使用：{total_tokens:,} / {max_context_length:,} tokens ({usage_ratio*100:.1f}%)
剩余空间：约{remaining_percentage:.0f}%

温馨提示：如需进行长时间对话，建议适时开启新会话。"""
            )
        
        # 构建新的消息列表，在最后一条用户消息之前插入警告
        new_messages = messages.copy()
        if messages and isinstance(messages[-1], HumanMessage):
            # 在最后一条用户消息前插入警告
            new_messages = messages[:-1] + [warning_msg] + [messages[-1]]
        else:
            # 直接添加到末尾
            new_messages.append(warning_msg)
            
        logger.info(
            f"💡 [MessageMonitorHook] 注入上下文警告:\n"
            f"  - 当前使用: {usage_ratio*100:.1f}%\n"
            f"  - 警告级别: {'严重' if usage_ratio >= self.critical_threshold else '普通'}"
        )
        
        # 返回更新，使用 llm_input_messages
        logger.info("🔚 [MessageMonitorHook] 完成处理，退出钩子（已注入警告）")
        return {
            "llm_input_messages": new_messages
        }


# 工厂函数，用于创建带配置的监控器
def create_monitor_hook(llm_config=None):
    """
    创建消息监控 Hook
    
    Args:
        llm_config: LLM配置，可以是数据库模型对象或字典
                   - 数据库对象: 应包含 config_data 属性，其中有 context_length
                   - 字典: 应直接包含 context_length 键
    
    Returns:
        MessageMonitorHook 实例
        
    Example:
        # 使用数据库配置
        llm_config = await get_llm_config(model_id)
        hook = create_monitor_hook(llm_config)
        
        # 使用字典配置
        hook = create_monitor_hook({"context_length": 128000})
        
        # 在create_react_agent中使用
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_prompt,
            pre_model_hook=hook
        )
    """
    return MessageMonitorHook(llm_config)


# 创建默认实例（无配置，使用默认上下文长度）
monitor_hook = MessageMonitorHook()