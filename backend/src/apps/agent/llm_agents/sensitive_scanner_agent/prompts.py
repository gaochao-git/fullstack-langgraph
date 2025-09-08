"""
提示词管理模块
"""
from ..agent_utils import get_system_prompt_from_db_async
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 核心提示词框架（不可被覆盖的部分）
CORE_PROMPT_TEMPLATE = """你是一个敏感数据扫描工具。你的任务是扫描文本中的敏感信息并生成脱敏后的安全报告。

待扫描内容来源：{source_name}
内容长度：{content_length} 字符
文件名：{file_name}

待扫描内容：
{content}

你的任务：扫描上述内容中的所有敏感数据，并生成脱敏报告。

特别注意：
- 如果内容看起来像是文件解析失败的错误信息（如"解析失败"、"无法读取"、"文件损坏"等），请输出：
  • 文件内容异常：[简要说明异常情况]
- 如果内容是乱码或无法理解的格式，请输出：
  • 文件内容异常：文件可能已损坏或格式不支持

{custom_rules}

输出要求(请严格按以下格式输出)：
内容完整/部分内容/解析失败|||简要描述文档内容，不超过50字|||发现敏感信息(脱敏后的值)/未发现敏感信息

文档解析状态说明：
- 内容完整：文档成功解析，内容完整
- 部分内容：文档包含"内容过长，只获取部分信息"等提示
- 解析失败：文档包含"解析失败"、"无法读取"、"需要安装"等错误信息

重要：
- 只输出一行，用|||分隔三部分内容
- 不要添加任何额外的换行符或空格
- 如果发现多个敏感信息，用分号分隔：发现敏感信息(身份证:110****1234; 手机号:138****5678)
- 如果敏感信息超过3个，只输出前3个，并在末尾加上"等"字

重要要求：
- 绝对不要在报告中显示敏感信息的原始值
- 对所有敏感信息进行脱敏处理，将敏感信息一半内容用*号替换
"""

# 默认敏感信息识别规则（可被数据库配置覆盖）
DEFAULT_SCAN_RULES = """敏感信息识别规则：
- 单独的用户名（如：gaochao、admin等）不属于敏感信息，不需要脱敏
- 用户名+密码的组合才是敏感信息（需要对密码脱敏）
- 重点关注：身份证号、手机号、银行卡号、密码、邮箱、IP地址、API密钥等"""

async def get_system_prompt_async(agent_id: str) -> str:
    """获取系统提示词，组合核心框架和自定义规则"""
    try:
        # 从数据库获取自定义规则
        custom_rules = await get_system_prompt_from_db_async(agent_id)
        # 将自定义规则嵌入核心框架
        return CORE_PROMPT_TEMPLATE.replace("{custom_rules}", custom_rules)
    except Exception as e:
        logger.warning(f"从数据库获取自定义规则失败，使用默认规则: {e}")
        # 使用默认规则
        return CORE_PROMPT_TEMPLATE.replace("{custom_rules}", DEFAULT_SCAN_RULES)