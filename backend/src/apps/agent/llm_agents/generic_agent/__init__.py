"""Generic Agent - 通用可配置化智能体

这是一个通用的Agent模板，支持：
- 可配置化的模型选择和参数
- 灵活的工具集成
- 可定制的提示词
- 支持ReAct和自定义工作流
"""

from .graph import create_generic_agent

__all__ = ["create_generic_agent"]