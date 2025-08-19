"""
Agent configuration service for dynamic loading from database.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from src.shared.core.dependencies import get_sync_db
from src.apps.agent.models import AgentConfig
from src.shared.core.logging import get_logger

logger = get_logger(__name__)
from src.apps.ai_model.models import AIModelConfig


class AgentConfigService:
    """Service to manage agent configurations from database."""
    
    @staticmethod
    def get_agent_config(agent_name: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get agent configuration from database.
        
        Args:
            agent_name: Name of the agent to get configuration for
            db: Database session
            
        Returns:
            Dictionary containing agent configuration or None if not found
        """
        try:
            # Query agent by agent_id (which corresponds to agent name)
            agent = db.query(AgentConfig).filter(AgentConfig.agent_id == agent_name).first()
            
            if not agent:
                return None
                
            # 使用to_dict方法来确保正确的JSON解析
            agent_dict = agent.to_dict()
            
            # 提取需要的字段
            config = {
                'agent_name': agent_dict.get('agent_name', ''),
                'description': agent_dict.get('description', ''),
                'capabilities': agent_dict.get('capabilities', []),
                'llm_config': agent_dict.get('llm_info', {}),
                'prompt_config': agent_dict.get('prompt_info', {}),
                'tools_config': agent_dict.get('tools_info', {}),
                'enabled': agent_dict.get('enabled', True),
                'status': agent_dict.get('status', 'stopped'),
                'is_builtin': agent_dict.get('is_builtin', 'no')  # 添加is_builtin字段
            }
            
            return config
            
        except Exception as e:
            print(f"Error loading agent config for {agent_name}: {e}")
            return None
    
    @staticmethod 
    def get_model_config_from_agent(agent_name: str, db: Session, selected_model: str = None) -> Dict[str, Any]:
        """
        Extract model configuration from agent settings.
        
        Args:
            agent_name: Name of the agent
            db: Database session
            selected_model: Optional model to override the default configured model
            
        Returns:
            Dictionary containing model configuration with fallback defaults
        """
        agent_config = AgentConfigService.get_agent_config(agent_name, db)
        
        if not agent_config:
            logger.warning(f"Agent configuration not found for agent: {agent_name}")
            return {}
            
        if not agent_config.get('llm_config'):
            logger.warning(f"LLM configuration not found for agent: {agent_name}")
            return {}
        
        llm_config = agent_config['llm_config']
        
        # Handle case where llm_config might be a JSON string
        if isinstance(llm_config, str):
            try:
                llm_config = json.loads(llm_config)
            except (json.JSONDecodeError, ValueError):
                llm_config = []
        
        # 只支持新的数据结构：llm_config必须是列表
        if not isinstance(llm_config, list):
            logger.error(f"Invalid LLM configuration format for agent: {agent_name}. Expected list, got {type(llm_config)}. Please update configuration to new format.")
            return {}
            
        if not llm_config:
            logger.error(f"Empty LLM configuration for agent: {agent_name}")
            return {}
            
        # 如果指定了模型，查找对应的配置
        if selected_model:
            for config in llm_config:
                if config.get('model_name') == selected_model:
                    model_args = config.get('model_args', {})
                    # Get model info from database
                    model_info = AgentConfigService._get_model_info_from_db(selected_model, db)
                    if not model_info.get('endpoint_url'):
                        logger.error(f"No endpoint_url found for model: {selected_model}")
                        return {}
                        
                    result = {
                        'model_name': selected_model,
                        'temperature': model_args.get('temperature', 0.7),
                        'max_tokens': model_args.get('max_tokens', 2000),
                        'top_p': model_args.get('top_p', 1.0),
                        'base_url': model_info['endpoint_url'],
                        'available_models': [cfg.get('model_name') for cfg in llm_config if cfg.get('model_name')]
                    }
                    if model_info.get('api_key'):
                        result['api_key'] = model_info['api_key']
                    return result
        
        # 如果没有指定模型或没找到，使用第一个配置
        first_config = llm_config[0]
        model_name = first_config.get('model_name')
        if not model_name:
            logger.error(f"No model_name in first config for agent: {agent_name}")
            return {}
            
        model_args = first_config.get('model_args', {})
        model_info = AgentConfigService._get_model_info_from_db(model_name, db)
        if not model_info.get('endpoint_url'):
            logger.error(f"No endpoint_url found for model: {model_name}")
            return {}
            
        result = {
            'model_name': model_name,
            'temperature': model_args.get('temperature', 0.7),
            'max_tokens': model_args.get('max_tokens', 2000),
            'top_p': model_args.get('top_p', 1.0),
            'base_url': model_info['endpoint_url'],
            'available_models': [cfg.get('model_name') for cfg in llm_config if cfg.get('model_name')]
        }
        if model_info.get('api_key'):
            result['api_key'] = model_info['api_key']
        return result
    
    @staticmethod
    def get_prompt_config_from_agent(agent_name: str, db: Session) -> Dict[str, str]:
        """
        Extract prompt configuration from agent settings.
        
        Args:
            agent_name: Name of the agent
            db: Database session
            
        Returns:
            Dictionary containing prompt configuration
        """
        agent_config = AgentConfigService.get_agent_config(agent_name, db)
        
        if not agent_config or not agent_config.get('prompt_config'):
            # Return default system prompt if not configured
            return {
                'system_prompt': f'你是一个专业的智能运维助手，名为{agent_name}。请根据用户需求提供专业的帮助。',
                'user_prompt_template': '',
                'assistant_prompt_template': ''
            }
        
        prompt_config = agent_config['prompt_config']
        
        # Handle case where prompt_config might be a JSON string
        if isinstance(prompt_config, str):
            try:
                # Try to parse as JSON first
                parsed_config = json.loads(prompt_config)
                if isinstance(parsed_config, dict):
                    prompt_config = parsed_config
                else:
                    # If parsed but not a dict, treat original string as system_prompt
                    prompt_config = {'system_prompt': prompt_config}
            except (json.JSONDecodeError, ValueError):
                # If not valid JSON, treat as plain system prompt
                prompt_config = {'system_prompt': prompt_config}
        
        # Handle case where prompt_config might be other types
        if isinstance(prompt_config, str):
            return {
                'system_prompt': prompt_config,
                'user_prompt_template': '',
                'assistant_prompt_template': ''
            }
        elif isinstance(prompt_config, dict):
            return {
                'system_prompt': prompt_config.get('system_prompt', f'你是一个专业的智能运维助手，名为{agent_name}。'),
                'user_prompt_template': prompt_config.get('user_prompt_template', ''),
                'assistant_prompt_template': prompt_config.get('assistant_prompt_template', '')
            }
        else:
            # Fallback for unexpected types
            return {
                'system_prompt': f'你是一个专业的智能运维助手，名为{agent_name}。请根据用户需求提供专业的帮助。',
                'user_prompt_template': '',
                'assistant_prompt_template': ''
            }
    
    
    @staticmethod
    def _get_model_info_from_db(model_name: str, db: Session) -> Dict[str, str]:
        """
        Get complete model information from database.
        
        Args:
            model_name: Name of the model
            db: Database session
            
        Returns:
            Dictionary containing model info (endpoint_url, api_key, etc.)
        """
        try:
            # Query model by model_type (which matches model_name)
            model = db.query(AIModelConfig).filter(
                AIModelConfig.model_type == model_name,
                AIModelConfig.model_status == 'active'
            ).first()
            
            if model:
                return {
                    'endpoint_url': model.endpoint_url,
                    'api_key': model.api_key_value,
                    'provider': model.model_provider,
                    'model_name': model.model_name
                }
            
            return {}
            
        except Exception as e:
            print(f"Error getting model info for {model_name}: {e}")
            return {}
    
    @staticmethod
    def get_agent_available_models(agent_name: str, db: Session) -> List[Dict[str, Any]]:
        """
        Get available models configured for a specific agent.
        
        Args:
            agent_name: Name of the agent
            db: Database session
            
        Returns:
            List of available models with their details
        """
        agent_config = AgentConfigService.get_agent_config(agent_name, db)
        
        if not agent_config or not agent_config.get('llm_config'):
            return []
            
        # get_agent_config返回的llm_config可能还是字符串，需要再次解析
        llm_config = agent_config['llm_config']
        
        # 如果是字符串，尝试解析JSON
        if isinstance(llm_config, str):
            try:
                llm_config = json.loads(llm_config)
            except (json.JSONDecodeError, ValueError):
                return []
        
        if not isinstance(llm_config, dict):
            return []
            
        # Get available models list from agent configuration
        available_model_types = llm_config.get('available_models', [])
        
        if not available_model_types:
            return []
            
        # Get model details from database for each available model
        try:
            models = []
            for model_type in available_model_types:
                model = db.query(AIModelConfig).filter(
                    AIModelConfig.model_type == model_type,
                    AIModelConfig.model_status == 'active'
                ).first()
                
                if model:
                    models.append({
                        'id': model.model_id,
                        'name': model.model_name,
                        'provider': model.model_provider,
                        'type': model.model_type,
                        'endpoint': model.endpoint_url
                    })
            
            return models
            
        except Exception as e:
            print(f"Error getting agent available models for {agent_name}: {e}")
            return []
    
    @staticmethod
    def get_available_models_from_db(db: Session) -> Dict[str, Any]:
        """
        Get available active models from database.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary mapping model names to their configurations
        """
        try:
            # Query active models
            models = db.query(AIModelConfig).filter(
                AIModelConfig.model_status == 'active'
            ).all()
            
            model_map = {}
            for model in models:
                model_map[model.model_type] = {
                    'name': model.model_name,
                    'provider': model.model_provider,
                    'endpoint': model.endpoint_url,
                    'api_key': model.api_key_value,
                    'model_type': model.model_type
                }
            
            return model_map
            
        except Exception as e:
            print(f"Error loading available models: {e}")
            return {}