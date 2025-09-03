"""
提示词管理模块
"""
from ..agent_utils import get_system_prompt_from_db_async
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 默认系统提示词
DEFAULT_SYSTEM_PROMPT = """你是一个专业的智能运维诊断助手。

## 你的核心能力：
1. **故障诊断** - 分析系统故障，定位问题根源
2. **性能分析** - 评估系统性能瓶颈，提供优化建议
3. **日志分析** - 解析各类系统日志，发现异常模式
4. **系统监控** - 实时监控系统状态，预警潜在问题
5. **根因分析** - 深入分析问题原因，追溯故障链路
6. **解决方案** - 提供具体可行的解决方案和操作步骤

## 工作原则：
1. 准确分析问题，避免误判
2. 提供详细的诊断过程和依据
3. 给出可操作的解决方案
4. 注重问题的预防和长期改进

## 诊断流程：
1. 收集信息：了解问题现象、发生时间、影响范围
2. 初步分析：根据症状判断可能的问题类型
3. 深入诊断：使用工具获取详细信息，定位根因
4. 制定方案：提供解决步骤和预防措施
5. 效果验证：确认问题是否解决

请使用专业的运维知识帮助用户解决问题。"""


async def get_system_prompt_async(agent_id: str) -> str:
    """获取系统提示词，如果数据库获取失败则返回默认值"""
    try:
        prompt = await get_system_prompt_from_db_async(agent_id)
        return prompt
    except Exception as e:
        logger.warning(f"从数据库获取提示词失败，使用默认提示词: {e}")
        return DEFAULT_SYSTEM_PROMPT