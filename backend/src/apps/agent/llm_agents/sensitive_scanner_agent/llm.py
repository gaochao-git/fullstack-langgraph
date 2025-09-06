"""敏感数据扫描智能体LLM配置"""

from typing import Optional, Dict, Any
from ..agent_utils import get_llm_config_for_agent as _get_llm_config_from_db
from src.shared.core.logging import get_logger
from .configuration import AGENT_DETAIL_CONFIG

logger = get_logger(__name__)

# 默认 LLM 配置
DEFAULT_LLM_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.1,
    "max_tokens": 8000,
    "api_key": "sk-default",
    "base_url": "https://api.openai.com/v1"
}


def get_llm_config(agent_id: str, selected_model: Optional[str] = None) -> Dict[str, Any]:
    """
    获取LLM配置
    
    Args:
        agent_id: 智能体ID
        selected_model: 用户选择的模型（可选）
        
    Returns:
        LLM配置字典
    """
    try:
        # 从数据库获取配置
        llm_config = _get_llm_config_from_db(agent_id, selected_model)
    except Exception as e:
        logger.warning(f"从数据库获取 LLM 配置失败，使用默认配置: {e}")
        # 如果失败，使用默认配置
        llm_config = DEFAULT_LLM_CONFIG.copy()
        if selected_model:
            llm_config["model"] = selected_model
    
    # 设置默认温度（敏感数据扫描需要低温度以确保准确性）
    if "temperature" not in llm_config:
        llm_config["temperature"] = AGENT_DETAIL_CONFIG.get("temperature", 0.1)
    
    # 设置最大token数
    if "max_tokens" not in llm_config:
        llm_config["max_tokens"] = AGENT_DETAIL_CONFIG.get("max_tokens", 8000)
    
    logger.info(f"[{agent_id}] LLM配置: model={llm_config.get('model')}, temperature={llm_config.get('temperature')}")
    
    return llm_config