"""
Token使用情况Hook - 用于在流式响应中添加token统计信息
"""
import json
from typing import Dict, Any, AsyncIterator
from langchain_core.messages import BaseMessage, SystemMessage
import tiktoken

from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class TokenUsageHook:
    """Token使用情况监控Hook"""
    
    def __init__(self, llm_config=None):
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.llm_config = llm_config
        self.max_context_length = self._get_max_context_length()
        
    def _get_max_context_length(self) -> int:
        """获取模型的上下文长度"""
        max_context_length = 128000  # 默认值
        
        if self.llm_config:
            try:
                if hasattr(self.llm_config, 'config_data'):
                    # 如果是数据库模型对象
                    import json
                    config_data = json.loads(self.llm_config.config_data) if isinstance(self.llm_config.config_data, str) else self.llm_config.config_data
                    context_length = config_data.get("context_length")
                    if context_length:
                        max_context_length = int(context_length)
                elif isinstance(self.llm_config, dict):
                    # 如果是字典配置
                    context_length = self.llm_config.get("context_length")
                    if context_length:
                        max_context_length = int(context_length)
            except Exception as e:
                logger.debug(f"从llm_config获取上下文长度失败: {e}")
                
        return max_context_length
    
    def count_tokens(self, text: str) -> int:
        """计算文本的token数"""
        try:
            return len(self.encoder.encode(text))
        except Exception:
            # 粗略估算：中文约1.5字符/token，英文约4字符/token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + english_chars / 4)
    
    def count_messages_tokens(self, messages: list) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            if isinstance(msg, BaseMessage):
                # 消息类型
                total += self.count_tokens(msg.__class__.__name__)
                # 消息内容
                total += self.count_tokens(str(msg.content))
                # 消息格式的额外开销
                total += 4
            elif isinstance(msg, dict):
                # 处理字典格式的消息
                total += self.count_tokens(msg.get('type', ''))
                total += self.count_tokens(str(msg.get('content', '')))
                total += 4
        return total
    
    async def add_token_usage_to_stream(self, stream: AsyncIterator[Any], thread_id: str) -> AsyncIterator[Any]:
        """在流式响应中注入token使用情况"""
        messages = []
        
        async for chunk in stream:
            # 先返回原始chunk
            yield chunk
            
            # 收集消息用于计算token
            if isinstance(chunk, dict):
                # 处理values事件中的消息
                if 'values' in chunk and 'messages' in chunk['values']:
                    messages = chunk['values']['messages']
                # 处理updates事件中的消息
                elif 'updates' in chunk:
                    for update in chunk.get('updates', {}).values():
                        if isinstance(update, dict) and 'messages' in update:
                            messages.extend(update['messages'])
        
        # 在流结束时，发送token使用情况
        if messages:
            total_tokens = self.count_messages_tokens(messages)
            usage_ratio = total_tokens / self.max_context_length
            
            # 构造token使用情况的事件
            token_usage_event = {
                "event": "token_usage",
                "data": {
                    "thread_id": thread_id,
                    "token_usage": {
                        "used": total_tokens,
                        "total": self.max_context_length,
                        "percentage": round(usage_ratio * 100, 1),
                        "remaining": self.max_context_length - total_tokens
                    }
                }
            }
            
            logger.debug(f"发送token使用情况: {token_usage_event}")
            yield token_usage_event


def create_token_usage_hook(llm_config=None):
    """创建Token使用情况Hook"""
    return TokenUsageHook(llm_config)