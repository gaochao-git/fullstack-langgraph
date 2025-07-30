"""
提示词管理模块
专门管理智能运维助手的提示词
"""

from ..prompt_utils import get_system_prompt_from_db

def get_system_prompt(agent_name: str = "diagnostic_agent") -> str:
    """
    获取智能体的系统提示词，使用统一的数据库获取方法
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        系统提示词字符串
        
    Raises:
        ValueError: 如果数据库中没有找到有效的系统提示词
    """
    return get_system_prompt_from_db(agent_name)

# 导出提示词函数和向后兼容的SYSTEM_PROMPT变量
# 注意: SYSTEM_PROMPT现在动态从数据库获取，不再是静态常量
def _get_default_system_prompt():
    """获取默认系统提示词，用于向后兼容"""
    try:
        return get_system_prompt()
    except Exception as e:
        print(f"Warning: 无法获取系统提示词，使用空字符串: {e}")
        return ""

# 保持向后兼容性 - 但现在从数据库动态获取
SYSTEM_PROMPT = _get_default_system_prompt()

# 导出提示词
__all__ = ["get_system_prompt", "SYSTEM_PROMPT"]