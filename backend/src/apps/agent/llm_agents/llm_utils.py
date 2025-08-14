"""
LLM配置和创建的公共工具方法
"""

import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session
from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.core.logging import get_logger
import httpx

logger = get_logger(__name__)


def get_model_config(
    agent_id: str, 
    db: Session, 
    selected_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取Agent的模型配置
    
    Args:
        agent_id: Agent的ID
        db: 数据库会话
        selected_model: 可选的指定模型名称，会覆盖Agent默认配置的模型
        
    Returns:
        包含模型配置的字典，包括:
        - model_name: 模型名称
        - temperature: 温度参数
        - max_tokens: 最大token数
        - base_url: API端点URL
        - api_key: API密钥（如果在数据库中配置了）
    """
    return AgentConfigService.get_model_config_from_agent(agent_id, db, selected_model)


def get_prompt_config(agent_id: str, db: Session) -> Dict[str, str]:
    """
    获取Agent的提示词配置
    
    Args:
        agent_id: Agent的ID
        db: 数据库会话
        
    Returns:
        包含提示词配置的字典，包括:
        - system_prompt: 系统提示词
        - user_prompt_template: 用户提示词模板
        - assistant_prompt_template: 助手提示词模板
    """
    return AgentConfigService.get_prompt_config_from_agent(agent_id, db)


def get_api_key(base_url: str, api_key_from_db: Optional[str] = None) -> str:
    """
    获取API密钥，优先使用数据库配置，其次使用环境变量
    
    Args:
        base_url: API端点URL，用于判断使用哪个环境变量
        api_key_from_db: 数据库中配置的API密钥
        
    Returns:
        API密钥字符串
        
    Raises:
        ValueError: 当无法找到API密钥时
    """
    # 优先使用数据库中的API key
    if api_key_from_db:
        return api_key_from_db
    
    # 根据base_url判断使用哪个环境变量
    api_key = None
    
    if "deepseek.com" in base_url:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    elif "openai.com" in base_url or "api.openai.com" in base_url:
        api_key = os.environ.get("OPENAI_API_KEY")
    elif "anthropic.com" in base_url:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    elif "zhipuai.cn" in base_url:
        api_key = os.environ.get("ZHIPUAI_API_KEY")
    elif "moonshot.cn" in base_url:
        api_key = os.environ.get("MOONSHOT_API_KEY")
    elif "dashscope.aliyuncs.com" in base_url:
        api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIBABA_CLOUD_API_KEY")
    else:
        # 默认回退选项
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            f"未找到API密钥。请为 {base_url} 设置相应的环境变量或在数据库中配置API密钥。"
        )
    
    return api_key


def create_llm(
    model_name: str,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    base_url: str = "https://api.deepseek.com",
    api_key: Optional[str] = None,
    max_retries: int = 2
) -> ChatOpenAI:
    """
    创建ChatOpenAI实例
    
    Args:
        model_name: 模型名称
        temperature: 温度参数，控制输出随机性
        max_tokens: 最大输出token数
        base_url: API端点URL
        api_key: API密钥，如果不提供则从环境变量获取
        max_retries: 最大重试次数
        
    Returns:
        配置好的ChatOpenAI实例
    """
    # 获取API密钥
    actual_api_key = api_key or get_api_key(base_url)
    
    # 记录配置信息
    logger.info(f"创建LLM实例:")
    logger.info(f"  模型: {model_name}")
    logger.info(f"  温度: {temperature}")
    logger.info(f"  API端点: {base_url}")
    if max_tokens:
        logger.info(f"  最大Token: {max_tokens}")
    
    # 创建自定义 httpx 客户端，忽略 SSL 验证
    http_client = httpx.Client(verify=False)
    
    # 创建LLM实例
    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        api_key=actual_api_key,
        base_url=base_url,
        http_client=http_client,
    )


def create_llm_from_config(
    agent_id: str,
    db: Session,
    selected_model: Optional[str] = None,
    temperature_override: Optional[float] = None,
    max_retries: int = 2
) -> ChatOpenAI:
    """
    根据Agent配置创建LLM实例的便捷方法
    
    Args:
        agent_id: Agent的ID
        db: 数据库会话
        selected_model: 可选的指定模型名称
        temperature_override: 可选的温度覆盖值
        max_retries: 最大重试次数
        
    Returns:
        配置好的ChatOpenAI实例
    """
    # 获取模型配置
    model_config = get_model_config(agent_id, db, selected_model)
    
    # 使用配置创建LLM
    return create_llm(
        model_name=model_config.get("model_name", "deepseek-chat"),
        temperature=temperature_override if temperature_override is not None else model_config.get("temperature", 0.1),
        max_tokens=model_config.get("max_tokens"),
        base_url=model_config.get("base_url", "https://api.deepseek.com"),
        api_key=model_config.get("api_key"),
        max_retries=max_retries
    )