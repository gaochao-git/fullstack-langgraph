"""通用Agent工具管理系统

支持多种工具类别的动态加载和配置化管理
"""

import os
import json
import math
import requests
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

# 基础工具类别定义

# === 搜索工具 ===
def web_search(query: str, max_results: int = 5) -> str:
    """网络搜索工具
    
    Args:
        query: 搜索查询
        max_results: 最大结果数量
        
    Returns:
        搜索结果摘要
    """
    try:
        # 这里应该接入真实的搜索API
        # 示例使用简单的模拟搜索
        return f"搜索 '{query}' 的结果：\n- 相关信息1\n- 相关信息2\n- 相关信息3"
    except Exception as e:
        return f"搜索失败: {str(e)}"


def knowledge_search(query: str, domain: str = "general") -> str:
    """知识库搜索工具
    
    Args:
        query: 查询内容
        domain: 领域范围
        
    Returns:
        知识库搜索结果
    """
    # 模拟知识库搜索
    return f"在{domain}领域搜索'{query}'的结果：相关知识条目"


# === 计算工具 ===
def calculator(expression: str) -> str:
    """数学计算器
    
    Args:
        expression: 数学表达式
        
    Returns:
        计算结果
    """
    try:
        # 安全的数学表达式计算
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round})
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


def unit_converter(value: float, from_unit: str, to_unit: str) -> str:
    """单位转换工具
    
    Args:
        value: 数值
        from_unit: 源单位
        to_unit: 目标单位
        
    Returns:
        转换结果
    """
    # 简单的长度单位转换示例
    length_units = {
        "m": 1.0,
        "cm": 0.01,
        "mm": 0.001,
        "km": 1000.0,
        "ft": 0.3048,
        "in": 0.0254
    }
    
    try:
        if from_unit in length_units and to_unit in length_units:
            meters = value * length_units[from_unit]
            result = meters / length_units[to_unit]
            return f"{value} {from_unit} = {result} {to_unit}"
        else:
            return f"不支持的单位转换: {from_unit} -> {to_unit}"
    except Exception as e:
        return f"转换错误: {str(e)}"


# === 文本处理工具 ===
def text_analyzer(text: str) -> str:
    """文本分析工具
    
    Args:
        text: 待分析文本
        
    Returns:
        分析结果
    """
    try:
        word_count = len(text.split())
        char_count = len(text)
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        
        return f"""文本分析结果:
- 字符数: {char_count}
- 词数: {word_count}  
- 句子数: {sentence_count}
- 平均句长: {word_count/max(sentence_count, 1):.1f} 词/句"""
    except Exception as e:
        return f"文本分析错误: {str(e)}"


def text_summarizer(text: str, max_length: int = 200) -> str:
    """文本摘要工具
    
    Args:
        text: 源文本
        max_length: 最大摘要长度
        
    Returns:
        文本摘要
    """
    try:
        # 简单的摘要算法：取前几句
        sentences = text.split('.')
        summary = ""
        for sentence in sentences:
            if len(summary + sentence) < max_length:
                summary += sentence + ". "
            else:
                break
        
        return f"文本摘要: {summary.strip()}"
    except Exception as e:
        return f"摘要生成错误: {str(e)}"


# === 时间工具 ===
def get_current_time() -> str:
    """获取当前时间"""
    return f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def time_calculator(start_time: str, end_time: str) -> str:
    """时间计算工具
    
    Args:
        start_time: 开始时间 (YYYY-MM-DD HH:MM:SS)
        end_time: 结束时间 (YYYY-MM-DD HH:MM:SS)
        
    Returns:
        时间差计算结果
    """
    try:
        from datetime import datetime
        start = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        diff = end - start
        
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"时间差: {days}天 {hours}小时 {minutes}分钟 {seconds}秒"
    except Exception as e:
        return f"时间计算错误: {str(e)}"


# === 数据处理工具 ===
def json_processor(json_text: str, action: str = "format") -> str:
    """JSON处理工具
    
    Args:
        json_text: JSON文本
        action: 操作类型 (format, validate, minify)
        
    Returns:
        处理结果
    """
    try:
        data = json.loads(json_text)
        
        if action == "format":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif action == "validate":
            return "JSON格式有效"
        elif action == "minify":
            return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        else:
            return f"不支持的操作: {action}"
    except json.JSONDecodeError as e:
        return f"JSON格式错误: {str(e)}"
    except Exception as e:
        return f"JSON处理错误: {str(e)}"


# === 系统工具 ===
def system_info() -> str:
    """获取系统信息"""
    try:
        import platform
        return f"""系统信息:
- 操作系统: {platform.system()}
- 版本: {platform.version()}
- 架构: {platform.machine()}
- Python版本: {platform.python_version()}"""
    except Exception as e:
        return f"获取系统信息失败: {str(e)}"


# === 工具类别映射 ===
TOOL_CATEGORIES = {
    "search": {
        "web_search": {
            "function": web_search,
            "description": "网络搜索工具，可以搜索互联网上的信息",
            "parameters": {
                "query": {"type": "string", "description": "搜索查询"},
                "max_results": {"type": "integer", "description": "最大结果数量", "default": 5}
            },
            "risk_level": "low"
        },
        "knowledge_search": {
            "function": knowledge_search,
            "description": "知识库搜索工具",
            "parameters": {
                "query": {"type": "string", "description": "查询内容"},
                "domain": {"type": "string", "description": "领域范围", "default": "general"}
            },
            "risk_level": "low"
        }
    },
    
    "calculation": {
        "calculator": {
            "function": calculator,
            "description": "数学计算器，支持基本数学运算和函数",
            "parameters": {
                "expression": {"type": "string", "description": "数学表达式"}
            },
            "risk_level": "low"
        },
        "unit_converter": {
            "function": unit_converter,
            "description": "单位转换工具",
            "parameters": {
                "value": {"type": "number", "description": "数值"},
                "from_unit": {"type": "string", "description": "源单位"},
                "to_unit": {"type": "string", "description": "目标单位"}
            },
            "risk_level": "low"
        }
    },
    
    "text_processing": {
        "text_analyzer": {
            "function": text_analyzer,
            "description": "文本分析工具，统计字符、词数等信息",
            "parameters": {
                "text": {"type": "string", "description": "待分析文本"}
            },
            "risk_level": "low"
        },
        "text_summarizer": {
            "function": text_summarizer,
            "description": "文本摘要工具",
            "parameters": {
                "text": {"type": "string", "description": "源文本"},
                "max_length": {"type": "integer", "description": "最大摘要长度", "default": 200}
            },
            "risk_level": "low"
        }
    },
    
    "time": {
        "get_current_time": {
            "function": get_current_time,
            "description": "获取当前时间",
            "parameters": {},
            "risk_level": "low"
        },
        "time_calculator": {
            "function": time_calculator,
            "description": "时间计算工具",
            "parameters": {
                "start_time": {"type": "string", "description": "开始时间 (YYYY-MM-DD HH:MM:SS)"},
                "end_time": {"type": "string", "description": "结束时间 (YYYY-MM-DD HH:MM:SS)"}
            },
            "risk_level": "low"
        }
    },
    
    "data_processing": {
        "json_processor": {
            "function": json_processor,
            "description": "JSON处理工具",
            "parameters": {
                "json_text": {"type": "string", "description": "JSON文本"},
                "action": {"type": "string", "description": "操作类型", "default": "format"}
            },
            "risk_level": "low"
        }
    },
    
    "system": {
        "system_info": {
            "function": system_info,
            "description": "获取系统信息",
            "parameters": {},
            "risk_level": "medium"
        }
    }
}


def get_tools_by_categories(categories: List[str]) -> Dict[str, Any]:
    """根据类别获取工具
    
    Args:
        categories: 工具类别列表
        
    Returns:
        符合类别的工具字典
    """
    selected_tools = {}
    
    for category in categories:
        if category in TOOL_CATEGORIES:
            selected_tools.update(TOOL_CATEGORIES[category])
    
    return selected_tools


def get_all_tools() -> Dict[str, Any]:
    """获取所有可用工具"""
    all_tools = {}
    for category_tools in TOOL_CATEGORIES.values():
        all_tools.update(category_tools)
    return all_tools


def get_high_risk_tools() -> List[str]:
    """获取高风险工具列表"""
    high_risk_tools = []
    
    for category_tools in TOOL_CATEGORIES.values():
        for tool_name, tool_info in category_tools.items():
            if tool_info.get("risk_level") in ["high", "critical"]:
                high_risk_tools.append(tool_name)
    
    return high_risk_tools


def validate_tool_call(tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, str]:
    """验证工具调用参数
    
    Args:
        tool_name: 工具名称
        parameters: 调用参数
        
    Returns:
        (是否有效, 错误信息)
    """
    # 查找工具定义
    tool_info = None
    for category_tools in TOOL_CATEGORIES.values():
        if tool_name in category_tools:
            tool_info = category_tools[tool_name]
            break
    
    if not tool_info:
        return False, f"工具 '{tool_name}' 不存在"
    
    # 验证必需参数
    required_params = tool_info.get("parameters", {})
    for param_name, param_info in required_params.items():
        if param_info.get("required", True) and param_name not in parameters:
            return False, f"缺少必需参数: {param_name}"
    
    return True, ""


def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
    """执行工具调用
    
    Args:
        tool_name: 工具名称
        parameters: 调用参数
        
    Returns:
        执行结果
    """
    # 验证工具调用
    is_valid, error_msg = validate_tool_call(tool_name, parameters)
    if not is_valid:
        return f"工具调用错误: {error_msg}"
    
    # 查找并执行工具
    for category_tools in TOOL_CATEGORIES.values():
        if tool_name in category_tools:
            tool_function = category_tools[tool_name]["function"]
            try:
                return tool_function(**parameters)
            except Exception as e:
                return f"工具执行错误: {str(e)}"
    
    return f"工具 '{tool_name}' 未找到"


def get_langchain_tools_by_categories(categories: List[str]) -> List[Any]:
    """获取LangChain格式的工具列表，用于create_react_agent
    
    Args:
        categories: 工具类别列表
        
    Returns:
        LangChain工具列表
    """
    from langchain_core.tools import tool
    
    selected_tools = get_tools_by_categories(categories)
    langchain_tools = []
    
    for tool_name, tool_info in selected_tools.items():
        # 获取参数信息
        params = tool_info.get("parameters", {})
        
        # 创建工具函数
        func = tool_info["function"]
        description = tool_info["description"]
        
        # 使用闭包避免变量绑定问题
        def make_tool(func_ref, tool_name, desc):
            @tool(description=desc)
            def tool_wrapper(**kwargs):
                return func_ref(**kwargs)
            # 手动设置工具名称
            tool_wrapper.name = tool_name
            return tool_wrapper
        
        langchain_tools.append(make_tool(func, tool_name, description))
    
    return langchain_tools