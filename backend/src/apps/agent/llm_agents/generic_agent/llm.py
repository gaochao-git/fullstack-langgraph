"""
LLM 配置管理模块
"""
from typing import Dict, Any, Optional
from ..agent_utils import get_llm_config_for_agent as _get_llm_config_from_db
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 默认 LLM 配置
DEFAULT_LLM_CONFIG = {
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2000,
    "api_key": "sk-default",  # 需要在环境变量中设置
    "base_url": "https://api.openai.com/v1"
}


def get_llm_config(agent_id: str, selected_model: Optional[str] = None) -> Dict[str, Any]:
    """获取 LLM 配置，如果数据库获取失败则返回默认配置"""
    try:
        config = _get_llm_config_from_db(agent_id, selected_model)
        return config
    except Exception as e:
        logger.warning(f"从数据库获取 LLM 配置失败，使用默认配置: {e}")
        # 如果指定了模型，更新默认配置
        default_config = DEFAULT_LLM_CONFIG.copy()
        if selected_model:
            default_config["model"] = selected_model
        return default_config