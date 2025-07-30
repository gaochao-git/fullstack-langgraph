"""
统一的提示词管理工具
用于所有智能体从数据库获取系统提示词
"""

from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.db.config import get_sync_db


def get_system_prompt_from_db(agent_name: str) -> str:
    """
    统一从数据库获取智能体的系统提示词
    
    Args:
        agent_name: 智能体名称（agent_id）
        
    Returns:
        系统提示词字符串
        
    Raises:
        ValueError: 如果数据库中没有找到有效的系统提示词
    """
    if not agent_name: raise ValueError("智能体名称不能为空")
    
    try:
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            prompt_config = AgentConfigService.get_prompt_config_from_agent(agent_name, db)
        finally:
            db.close()
            
        system_prompt = prompt_config.get('system_prompt', '').strip()
        # 必须从数据库中获取有效的系统提示词
        if system_prompt:
            return system_prompt
        else:
            raise ValueError(f"数据库中没有找到智能体 '{agent_name}' 的系统提示词配置")
    except Exception as e:
        error_msg = f"获取智能体 '{agent_name}' 的系统提示词失败: {e}"
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)


def validate_system_prompt(system_prompt: str, agent_name: str = "unknown") -> None:
    """
    验证系统提示词的有效性
    
    Args:
        system_prompt: 系统提示词内容
        agent_name: 智能体名称（用于错误提示）
        
    Raises:
        ValueError: 如果系统提示词无效
    """
    if not system_prompt or not system_prompt.strip():
        raise ValueError(f"智能体 '{agent_name}' 的系统提示词不能为空")
    
    if len(system_prompt.strip()) < 10:
        raise ValueError(f"智能体 '{agent_name}' 的系统提示词过短，可能配置错误")
    
    print(f"✅ 智能体 '{agent_name}' 的系统提示词验证通过")


# 导出函数
__all__ = ["get_system_prompt_from_db", "validate_system_prompt"]