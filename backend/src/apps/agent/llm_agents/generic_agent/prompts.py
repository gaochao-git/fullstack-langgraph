"""
提示词管理模块
"""
from ..agent_utils import get_system_prompt_from_db_async
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 通用智能体的默认提示词
DEFAULT_SYSTEM_PROMPT = """你是一个通用的AI助手。

## 你的核心原则：
1. 准确理解用户的需求
2. 提供有帮助的回答
3. 使用可用的工具完成任务
4. 保持友好和专业的交流

请根据用户的需求，使用合适的工具来帮助他们完成任务。"""


async def get_system_prompt_async(agent_id: str) -> str:
    """获取系统提示词，如果数据库获取失败则返回默认值"""
    try:
        prompt = await get_system_prompt_from_db_async(agent_id)
        return prompt
    except Exception as e:
        logger.warning(f"从数据库获取提示词失败，使用默认提示词: {e}")
        return DEFAULT_SYSTEM_PROMPT


