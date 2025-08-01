"""
统一的工具管理工具
用于所有智能体从数据库获取工具配置
"""

import json
from typing import Dict, List, Any, Optional
from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.db.config import get_sync_db


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
            
        tools_config = agent_config.get('tools_config', {})
        
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
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)