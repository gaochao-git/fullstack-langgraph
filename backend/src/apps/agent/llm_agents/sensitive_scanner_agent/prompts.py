"""
提示词管理模块
"""
from ..agent_utils import get_system_prompt_from_db_async
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 默认提示词（数据库没有配置时的备用）
DEFAULT_SYSTEM_PROMPT = """你是一个敏感数据扫描助手，具有文本处理能力。
你的任务是扫描文本中的敏感数据，例如个人身份信息、密码、信用卡号等。
敏感数据的定义：
1. 个人身份信息：姓名、手机号、邮箱、身份证号等
2. 密码：任何包含字母、数字和特殊字符的字符串
3. 信用卡号：16位数字，以4开头
4. 银行账号：10位数字
5. 手机号：11位数字，以1开头
6. 邮箱：包含@符号的字符串

## 你的能力


## 工作原则


请根据用户的需求选择合适的工具来帮助他们。"""


async def get_system_prompt_async(agent_id: str) -> str:
    """获取系统提示词，如果数据库获取失败则返回默认值"""
    try:
        prompt = await get_system_prompt_from_db_async(agent_id)
        return prompt
    except Exception as e:
        logger.warning(f"从数据库获取提示词失败，使用默认提示词: {e}")
        return DEFAULT_SYSTEM_PROMPT