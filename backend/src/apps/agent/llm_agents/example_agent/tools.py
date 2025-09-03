"""
Example Agent 工具模块
定义 Agent 特有的自定义工具
"""

from typing import List, Any
from langchain_core.tools import tool
from ..agent_utils import get_tools_config_from_db
from src.apps.agent.tools import general_tool
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


# ========== 内置工具定义 ==========
@tool
def example_tool(text: str) -> str:
    """示例工具 - 文本转大写"""
    return f"处理结果: {text.upper()}"


@tool
def word_counter(text: str) -> str:
    """字数统计工具"""
    word_count = len(text.split())
    char_count = len(text)
    return f"字数: {word_count}, 字符数: {char_count}"


@tool
def text_reverser(text: str) -> str:
    """文本反转工具"""
    return text[::-1]


@tool
def text_analyzer(text: str) -> str:
    """文本分析工具 - 综合分析文本特征"""
    analysis = {
        "长度": len(text),
        "单词数": len(text.split()),
        "包含数字": any(char.isdigit() for char in text),
        "包含大写": any(char.isupper() for char in text),
        "包含小写": any(char.islower() for char in text),
        "行数": len(text.splitlines())
    }
    
    result = "文本分析结果：\n"
    for key, value in analysis.items():
        result += f"- {key}: {value}\n"
    
    return result


# ========== 工具获取函数 ==========
async def get_example_agent_tools(agent_id: str) -> List[Any]:
    """获取 Example Agent 的完整工具列表
    
    包括：
    1. 数据库配置的系统工具
    2. Agent 特有的内置工具
    """
    all_tools = []
    
    try:
        # 1. 获取数据库配置的工具
        tools_config = get_tools_config_from_db(agent_id)
        
        # 处理系统工具配置
        system_tools_config = tools_config.get('system_tools', [])
        system_tools_map = {
            'get_current_time': general_tool.get_current_time,
            # 可以在这里添加更多系统工具
        }
        
        for tool_name in system_tools_config:
            if tool_name in system_tools_map:
                all_tools.append(system_tools_map[tool_name])
                logger.debug(f"添加系统工具: {tool_name}")
        
    except Exception as e:
        logger.warning(f"加载数据库工具配置失败: {e}")
    
    # 2. 添加 Agent 特有的内置工具（这些工具始终可用）
    builtin_tools = [example_tool, word_counter, text_reverser, text_analyzer]
    all_tools.extend(builtin_tools)
    logger.debug(f"添加内置工具: {[t.name for t in builtin_tools]}")
    
    logger.info(f"Agent {agent_id} 工具加载完成，共 {len(all_tools)} 个工具")
    return all_tools