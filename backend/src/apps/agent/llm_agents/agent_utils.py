"""
统一的智能体配置工具
用于获取智能体的模型配置、提示词和工具配置
"""

import os
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.db.config import get_sync_db, get_async_db_context
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
        # 未知的API端点，不做默认假设
        logger.warning(f"Unknown API endpoint: {base_url}, cannot determine which API key to use")
    
    if not api_key:
        raise ValueError(
            f"未找到API密钥。请为 {base_url} 设置相应的环境变量或在数据库中配置API密钥。"
        )
    
    return api_key


def get_llm_config_for_agent(
    agent_id: str,
    selected_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取Agent的LLM配置 - 自动处理数据库连接
    
    Args:
        agent_id: Agent的ID
        selected_model: 可选的指定模型名称
        
    Returns:
        LLM配置字典，包含所有创建ChatOpenAI所需的参数
    """
    db_gen = get_sync_db()
    db = next(db_gen)
    try:
        model_config = get_model_config(agent_id, db, selected_model)
        
        # 检查必要的配置
        if not model_config:
            logger.error(f"No model configuration found for agent: {agent_id}")
            raise ValueError(f"No model configuration found for agent: {agent_id}")
            
        if not model_config.get("model_name"):
            logger.error(f"No model_name in configuration for agent: {agent_id}")
            raise ValueError(f"No model_name in configuration for agent: {agent_id}")
            
        if not model_config.get("base_url"):
            logger.error(f"No base_url in configuration for agent: {agent_id}")
            raise ValueError(f"No base_url in configuration for agent: {agent_id}")
        
        # 返回可以直接传给ChatOpenAI的配置
        return {
            "model": model_config["model_name"],
            "temperature": model_config.get("temperature", 0.7),
            "max_tokens": model_config.get("max_tokens", 2000),
            "max_retries": 2,
            "api_key": get_api_key(
                model_config["base_url"],
                model_config.get("api_key")
            ),
            "base_url": model_config["base_url"],
            "http_client": httpx.Client(verify=False)
        }
    finally:
        db.close()




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
    
    logger.info(f"智能体 '{agent_name}' 的系统提示词验证通过")


def get_tools_config_from_db(agent_id: str) -> Dict[str, Any]:
    """
    统一从数据库获取智能体的工具配置
    
    Args:
        agent_id: 智能体名称（agent_id）
        
    Returns:
        工具配置字典，包含 mcp_tools 和 system_tools
        
    Raises:
        ValueError: 如果数据库中没有找到有效的工具配置
    """
    if not agent_id:
        raise ValueError("智能体名称不能为空")
    
    try:
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            agent_config = AgentConfigService.get_agent_config(agent_id, db)
        finally:
            db.close()
            
        if not agent_config:
            raise ValueError(f"数据库中没有找到智能体 '{agent_id}' 的配置")
            
        tools_config = agent_config.get('tools_info', {})
        
        # Handle case where tools_config might be a JSON string
        if isinstance(tools_config, str):
            try:
                tools_config = json.loads(tools_config)
            except (json.JSONDecodeError, ValueError):
                tools_config = {}
        
        if not isinstance(tools_config, dict):
            tools_config = {}
            
        return tools_config
        
    except Exception as e:
        error_msg = f"获取智能体 '{agent_id}' 的工具配置失败: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)




def get_system_tools_map():
    """
    动态获取所有系统工具的映射
    
    Returns:
        Dict[str, Any]: 工具名称到工具实例的映射
    """
    import os
    import importlib
    import inspect
    
    tools_map = {}
    tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
    
    # 扫描tools目录下的所有Python文件
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # 移除.py后缀
            
            try:
                # 动态导入模块
                module_path = f'src.apps.agent.tools.{module_name}'
                module = importlib.import_module(module_path)
                
                # 扫描模块中的所有工具
                for name, obj in inspect.getmembers(module):
                    # 检查是否是LangChain工具对象
                    if (hasattr(obj, 'name') and 
                        hasattr(obj, 'description') and
                        hasattr(obj, 'run')):  # LangChain工具都有run方法
                        
                        tools_map[obj.name] = obj
                        logger.debug(f"注册系统工具: {obj.name} from {module_name}")
                        
            except Exception as e:
                logger.warning(f"加载工具模块 {module_name} 失败: {e}")
                
    return tools_map


async def get_system_prompt_from_db_async(agent_name: str) -> str:
    """
    统一从数据库获取智能体的系统提示词（异步版本）
    
    Args:
        agent_name: 智能体名称（agent_id）
        
    Returns:
        系统提示词字符串
        
    Raises:
        ValueError: 如果数据库中没有找到有效的系统提示词
    """
    if not agent_name: 
        raise ValueError("智能体名称不能为空")
    
    try:
        async with get_async_db_context() as db:
            # 由于 AgentConfigService.get_prompt_config_from_agent 是同步的，
            # 我们需要直接查询数据库
            from sqlalchemy import select
            from src.apps.agent.models import AgentConfig
            
            result = await db.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_name)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                raise ValueError(f"未找到智能体 '{agent_name}'")
            
            # 获取提示词配置
            # prompt_info 字段已经是 JSON 类型，不需要 json.loads
            prompt_config = agent.prompt_info if agent.prompt_info else {}
            system_prompt = prompt_config.get('system_prompt', '').strip()
            
            if system_prompt:
                return system_prompt
            else:
                raise ValueError(f"数据库中没有找到智能体 '{agent_name}' 的系统提示词配置")
                
    except Exception as e:
        error_msg = f"获取智能体 '{agent_name}' 的系统提示词失败: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)


async def get_llm_config_from_db(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    异步获取智能体的LLM配置信息，包括context_length等参数
    
    Args:
        agent_id: 智能体ID
        
    Returns:
        包含LLM配置的字典，如果获取失败返回None
    """
    try:
        async with get_async_db_context() as db:
            from sqlalchemy import select
            from src.apps.agent.models import AgentConfig
            from src.apps.ai_model.models import AIModelConfig
            
            # 获取智能体配置
            result = await db.execute(
                select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if not agent:
                logger.warning(f"未找到智能体 '{agent_id}'")
                return None
            
            # 获取LLM配置
            llm_info = agent.llm_info if agent.llm_info else []
            
            # 处理 llm_info 可能是字符串的情况
            if isinstance(llm_info, str):
                try:
                    llm_info = json.loads(llm_info)
                except (json.JSONDecodeError, ValueError):
                    llm_info = []
            
            # llm_info 应该是一个列表
            if not isinstance(llm_info, list):
                logger.warning(f"智能体 '{agent_id}' 的llm_info格式错误，期望列表，实际类型: {type(llm_info)}")
                llm_info = []
            
            # 检查是否有配置的模型
            if not llm_info:
                logger.warning(f"智能体 '{agent_id}' 没有配置模型")
                return None
                
            # 获取第一个模型的配置
            first_model_config = llm_info[0]
            if not isinstance(first_model_config, dict):
                logger.warning(f"智能体 '{agent_id}' 的模型配置格式错误")
                return None
                
            first_model = first_model_config.get('model_name')
            if not first_model:
                logger.warning(f"智能体 '{agent_id}' 的第一个模型配置缺少model_name")
                return None
            
            # 从AI模型表查询详细信息
            # 注意：在llm_info中存储的model_name实际对应数据库中的model_type字段
            model_result = await db.execute(
                select(AIModelConfig).where(
                    AIModelConfig.model_type == first_model,
                    AIModelConfig.model_status == 'active'
                )
            )
            model_config = model_result.scalar_one_or_none()
            
            if not model_config:
                logger.warning(f"未找到模型 '{first_model}' 的配置")
                return None
            
            # 构建返回的配置
            llm_config = {
                'model_name': first_model,
                'endpoint_url': model_config.endpoint_url,
                'provider': model_config.model_provider
            }
            
            # 添加API密钥（如果有）
            if model_config.api_key_value:
                llm_config['api_key'] = model_config.api_key_value
            
            # 解析config_data获取context_length等参数
            if model_config.config_data:
                try:
                    config_data = model_config.config_data if isinstance(model_config.config_data, dict) else json.loads(model_config.config_data)
                    if 'context_length' in config_data:
                        llm_config['context_length'] = config_data['context_length']
                    # 添加其他可能的配置参数
                    for key in ['max_tokens', 'temperature', 'top_p']:
                        if key in config_data:
                            llm_config[key] = config_data[key]
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"解析模型config_data失败: {e}")
            
            return llm_config
            
    except Exception as e:
        logger.error(f"获取智能体 '{agent_id}' 的LLM配置失败: {e}")
        return None


# 导出函数
__all__ = [
    "get_llm_config_for_agent",
    "get_system_prompt_from_db_async",
    "get_tools_config_from_db",
    "get_system_tools_map",
    "validate_system_prompt",
    "get_llm_config_from_db"
]