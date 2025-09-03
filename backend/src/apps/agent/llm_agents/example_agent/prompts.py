"""
提示词管理模块
"""
from ..agent_utils import get_system_prompt_from_db_async
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 默认提示词（数据库没有配置时的备用）
DEFAULT_SYSTEM_PROMPT = """你是一个示例助手，具有文本处理能力。

## 你的能力
1. **文本处理** - 将文本转换为大写
2. **字数统计** - 统计文本的字数和字符数  
3. **文本反转** - 反转文本内容
4. **文本分析** - 对文本进行综合分析

## 工作原则
1. 准确理解用户需求，选择合适的工具
2. 处理结果要清晰明了
3. 遇到错误时给出友好的提示
4. 保持专业和友好的交流方式

请根据用户的需求选择合适的工具来帮助他们。"""


async def get_system_prompt_async(agent_id: str) -> str:
    """获取系统提示词，如果数据库获取失败则返回默认值"""
    try:
        prompt = await get_system_prompt_from_db_async(agent_id)
        return prompt
    except Exception as e:
        logger.warning(f"从数据库获取提示词失败，使用默认提示词: {e}")
        return DEFAULT_SYSTEM_PROMPT