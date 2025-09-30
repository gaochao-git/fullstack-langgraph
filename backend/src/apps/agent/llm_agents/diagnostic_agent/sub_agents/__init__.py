"""诊断子智能体模块"""

from typing import TypedDict, NotRequired, Union, Any, Dict
from langchain_core.language_models import LanguageModelLike

class SubAgent(TypedDict):
    """子智能体配置"""
    name: str
    description: str
    prompt: str
    tools: NotRequired[list[str]]
    model: NotRequired[Union[LanguageModelLike, Dict[str, Any]]]

# 导出所有子智能体配置
from .log_analyzer import LOG_ANALYZER_CONFIG
from .alert_correlator import ALERT_CORRELATOR_CONFIG
from .monitor_analyzer import MONITOR_ANALYZER_CONFIG
from .change_analyzer import CHANGE_ANALYZER_CONFIG
from .simplified_task_tool import create_simplified_diagnostic_task_tool, SIMPLIFIED_SUBAGENTS

__all__ = [
    'SubAgent',
    'LOG_ANALYZER_CONFIG',
    'ALERT_CORRELATOR_CONFIG', 
    'MONITOR_ANALYZER_CONFIG',
    'CHANGE_ANALYZER_CONFIG',
    'create_simplified_diagnostic_task_tool',
    'SIMPLIFIED_SUBAGENTS'
]