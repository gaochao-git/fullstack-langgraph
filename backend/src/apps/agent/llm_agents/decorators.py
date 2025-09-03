"""
Agent 装饰器
提供自动注册功能
"""

from typing import Callable, Dict, Any
from functools import wraps
import inspect

# 全局注册表
_agent_registry: Dict[str, Dict[str, Any]] = {}


def agent(
    agent_id: str, 
    description: str = "", 
    agent_type: str = "内置",
    capabilities: list = None,
    version: str = "1.0.0",
    icon: str = "Bot",
    owner: str = "system"
):
    """Agent 注册装饰器 - 所有使用此装饰器的都是内置 Agent
    
    注意：
    - 使用 @agent 装饰器的都是内置 Agent，会被注册到系统
    - 前端创建的 Agent 不使用装饰器，通过 generic_agent 模板运行
    
    使用示例：
    ```python
    # 在 configuration.py 中定义
    INIT_AGENT_CONFIG = {
        "agent_id": "my_agent",
        "description": "我的智能助手",
        "agent_type": "内置",
        "capabilities": ["能力1", "能力2"],
        "version": "1.0.0",
        "icon": "Bot",
        "owner": "system"
    }
    
    # 在 graph.py 中使用
    @agent(**INIT_AGENT_CONFIG)
    async def create_my_agent(config, checkpointer=None):
        # Agent 创建逻辑
        pass
    ```
    """
    def decorator(func: Callable) -> Callable:
        # 获取模块信息
        module = inspect.getmodule(func)
        module_parts = module.__name__.split('.')
        
        # 提取 Agent 模块名（从 llm_agents.xxx.graph 中提取 xxx）
        agent_module = None
        for i, part in enumerate(module_parts):
            if part == "llm_agents" and i + 1 < len(module_parts):
                agent_module = module_parts[i + 1]
                break
        
        if not agent_module:
            raise ValueError(f"无法从模块 {module.__name__} 中提取 Agent 模块名")
        
        # 注册到全局注册表 - 所有使用装饰器的都是内置 Agent
        _agent_registry[agent_id] = {
            "module": agent_module,
            "creator": func.__name__,
            "description": description,
            "builtin": True,  # 所有使用装饰器的都是内置 Agent
            "agent_type": agent_type,
            "capabilities": capabilities or [],
            "version": version,
            "icon": icon,
            "owner": owner,
            "func": func  # 直接保存函数引用，避免重复导入
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get_registered_agents() -> Dict[str, Dict[str, Any]]:
    """获取所有通过装饰器注册的 Agent"""
    return _agent_registry.copy()