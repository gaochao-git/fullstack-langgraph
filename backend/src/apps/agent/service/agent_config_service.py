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
        
        if not agent_config or not agent_config.get('llm_config'):
            # Return default configuration if agent not found or no LLM config
            return {
                'model_name': selected_model or 'deepseek-chat',
                'temperature': 0.1,
                'max_tokens': 2000,
                'base_url': 'https://api.deepseek.com',
                'available_models': ['deepseek-chat']
            }
        
        llm_config = agent_config['llm_config']
        
        # Handle case where llm_config might be a JSON string
        if isinstance(llm_config, str):
            try:
                llm_config = json.loads(llm_config)
            except (json.JSONDecodeError, ValueError):
                llm_config = {}
        elif not isinstance(llm_config, dict):
            llm_config = {}
        
        # Extract configuration with fallbacks and type conversion
        temperature = llm_config.get('temperature', 0.1)
        if isinstance(temperature, str):
            try:
                temperature = float(temperature)
            except (ValueError, TypeError):
                temperature = 0.1
        
        max_tokens = llm_config.get('max_tokens', 2000)
        if isinstance(max_tokens, str):
            try:
                max_tokens = int(max_tokens)
            except (ValueError, TypeError):
                max_tokens = 2000
        
        top_p = llm_config.get('top_p', 1.0)
        if isinstance(top_p, str):
            try:
                top_p = float(top_p)
            except (ValueError, TypeError):
                top_p = 1.0
        
        frequency_penalty = llm_config.get('frequency_penalty', 0.0)
        if isinstance(frequency_penalty, str):
            try:
                frequency_penalty = float(frequency_penalty)
            except (ValueError, TypeError):
                frequency_penalty = 0.0
        
        presence_penalty = llm_config.get('presence_penalty', 0.0)
        if isinstance(presence_penalty, str):
            try:
                presence_penalty = float(presence_penalty)
            except (ValueError, TypeError):
                presence_penalty = 0.0
        
        # Use selected_model if provided, otherwise use configured model
        model_name = selected_model or llm_config.get('model_name', 'deepseek-chat')
        
        logger.info(f"模型选择逻辑: selected_model={selected_model}, configured_model={llm_config.get('model_name')}, final_model={model_name}")
        
        # Get model info from database (includes endpoint_url and api_key)
        model_info = AgentConfigService._get_model_info_from_db(model_name, db)
        
        result = {
            'model_name': model_name,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'top_p': top_p,
            'frequency_penalty': frequency_penalty,
            'presence_penalty': presence_penalty,
            'available_models': llm_config.get('available_models', ['deepseek-chat']),
            'base_url': model_info.get('endpoint_url', 'https://api.deepseek.com')
        }
        
        # Add API key if found in database
        if model_info.get('api_key'):
            result['api_key'] = model_info.get('api_key')
            
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