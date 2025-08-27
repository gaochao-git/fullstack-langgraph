"""
LLM Agent Hooks - 用于扩展和定制 Agent 行为
"""

from .message_monitor_hook import monitor_hook, create_monitor_hook

__all__ = [
    'monitor_hook',
    'create_monitor_hook'
]