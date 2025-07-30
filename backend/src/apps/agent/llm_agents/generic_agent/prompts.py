"""通用Agent提示词管理

简化版本，统一从数据库获取系统提示词
"""

from ..prompt_utils import get_system_prompt_from_db


def get_system_prompt(agent_name: str = "generic_agent") -> str:
    """
    获取通用智能体的系统提示词，使用统一的数据库获取方法
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        系统提示词字符串
        
    Raises:
        ValueError: 如果数据库中没有找到有效的系统提示词
    """
    return get_system_prompt_from_db(agent_name)


# 保持向后兼容性
def get_system_prompt_from_config(agent_id: str, **kwargs) -> str:
    """
    从配置服务获取系统提示词（向后兼容方法）
    
    现在直接调用统一的数据库获取方法
    """
    return get_system_prompt_from_db(agent_id)


# 导出函数
__all__ = ["get_system_prompt", "get_system_prompt_from_config"]


