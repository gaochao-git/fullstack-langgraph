"""通用Agent工具函数

提供模型实例化、图编译、配置管理等通用功能
"""

import os
import io
import base64
from typing import Dict, Any, Optional, Union
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langgraph.graph import StateGraph

# 根据项目结构导入模型类
try:
    from langchain_deepseek import ChatDeepSeek
except ImportError:
    ChatDeepSeek = None

try:
    from langchain_community.chat_models.tongyi import ChatTongyi
except ImportError:
    ChatTongyi = None


def get_model_instance(model_config: Dict[str, Any]) -> BaseLanguageModel:
    """根据配置创建模型实例
    
    Args:
        model_config: 模型配置字典
        
    Returns:
        模型实例
        
    Raises:
        ValueError: 当模型提供商不支持时
    """
    
    provider = model_config.get("provider", "deepseek").lower()
    model_name = model_config.get("model", "deepseek-chat")
    temperature = model_config.get("temperature", 0.1)
    max_tokens = model_config.get("max_tokens", 4000)
    max_retries = model_config.get("max_retries", 3)
    
    # DeepSeek模型
    if provider == "deepseek":
        if not ChatDeepSeek:
            raise ValueError("ChatDeepSeek not available. Please install langchain-deepseek.")
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required for DeepSeek models.")
        
        return ChatDeepSeek(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            api_key=api_key
        )
    
    # OpenAI及兼容模型
    elif provider in ["openai", "openai-compatible"]:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = model_config.get("base_url")
        
        if provider == "openai-compatible" and not base_url:
            raise ValueError("base_url is required for OpenAI-compatible models.")
        
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            api_key=api_key,
            base_url=base_url
        )
    
    # Ollama模型
    elif provider == "ollama":
        base_url = model_config.get("base_url", "http://localhost:11434")
        
        return ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url,
            num_predict=max_tokens
        )
    
    # 通义千问模型
    elif provider == "qwen":
        if not ChatTongyi:
            raise ValueError("ChatTongyi not available. Please install the required package.")
        
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable is required for Qwen models.")
        
        return ChatTongyi(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            dashscope_api_key=api_key
        )
    
    else:
        raise ValueError(f"Unsupported model provider: {provider}")


def validate_model_config(model_config: Dict[str, Any]) -> tuple[bool, str]:
    """验证模型配置
    
    Args:
        model_config: 模型配置
        
    Returns:
        (是否有效, 错误信息)
    """
    
    required_fields = ["provider", "model"]
    for field in required_fields:
        if field not in model_config:
            return False, f"Missing required field: {field}"
    
    provider = model_config["provider"].lower()
    
    # 验证提供商特定的配置
    if provider == "deepseek":
        if not os.getenv("DEEPSEEK_API_KEY"):
            return False, "DEEPSEEK_API_KEY environment variable is required"
    
    elif provider in ["openai", "openai-compatible"]:
        if not os.getenv("OPENAI_API_KEY"):
            return False, "OPENAI_API_KEY environment variable is required"
        
        if provider == "openai-compatible" and not model_config.get("base_url"):
            return False, "base_url is required for OpenAI-compatible models"
    
    elif provider == "qwen":
        if not os.getenv("DASHSCOPE_API_KEY"):
            return False, "DASHSCOPE_API_KEY environment variable is required"
    
    # 验证数值参数
    numeric_fields = {
        "temperature": (0.0, 2.0),
        "max_tokens": (1, 100000),
        "max_retries": (0, 10)
    }
    
    for field, (min_val, max_val) in numeric_fields.items():
        if field in model_config:
            value = model_config[field]
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                return False, f"{field} must be between {min_val} and {max_val}"
    
    return True, ""


def compile_graph_with_checkpointer(workflow: StateGraph) -> Any:
    """编译状态图并设置检查点，参考diagnostic_agent实现
    
    Args:
        workflow: 状态图工作流
        
    Returns:
        编译后的图
    """
    
    try:
        # 参考diagnostic_agent的检查点设置
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        
        return workflow.compile(checkpointer=checkpointer)
    except Exception as e:
        print(f"Warning: Failed to compile graph with checkpointer: {str(e)}")
        return workflow.compile()


def save_graph_image(graph: Any, filename: str, output_dir: str = "graphs") -> str:
    """保存图结构为图片
    
    Args:
        graph: 图实例
        filename: 文件名（不含扩展名）
        output_dir: 输出目录
        
    Returns:
        保存的文件路径
    """
    
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成图片
        img_data = graph.get_graph().draw_mermaid_png()
        
        # 保存文件
        filepath = os.path.join(output_dir, f"{filename}.png")
        with open(filepath, "wb") as f:
            f.write(img_data)
        
        return filepath
        
    except Exception as e:
        print(f"Warning: Failed to save graph image: {str(e)}")
        return ""


def get_graph_mermaid(graph: Any) -> str:
    """获取图的Mermaid格式定义
    
    Args:
        graph: 图实例
        
    Returns:
        Mermaid格式的图定义
    """
    
    try:
        return graph.get_graph().draw_mermaid()
    except Exception as e:
        return f"Error generating mermaid: {str(e)}"


def format_execution_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """格式化执行结果
    
    Args:
        result: 原始执行结果
        
    Returns:
        格式化后的结果
    """
    
    formatted = {
        "success": True,
        "data": {},
        "metadata": {},
        "errors": [],
        "warnings": []
    }
    
    if isinstance(result, dict):
        # 提取主要数据
        if "messages" in result:
            formatted["data"]["messages"] = result["messages"]
            if result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    formatted["data"]["final_answer"] = last_message.content
        
        # 提取元数据
        metadata_fields = [
            "iteration_count", "tool_calls_count", "used_tools", 
            "execution_summary", "agent_config"
        ]
        for field in metadata_fields:
            if field in result:
                formatted["metadata"][field] = result[field]
        
        # 提取错误和警告
        if "errors" in result:
            formatted["errors"] = result["errors"]
            if result["errors"]:
                formatted["success"] = False
        
        if "warnings" in result:
            formatted["warnings"] = result["warnings"]
    
    return formatted


def create_agent_config_template(agent_type: str = "generic") -> Dict[str, Any]:
    """创建Agent配置模板
    
    Args:
        agent_type: Agent类型
        
    Returns:
        配置模板
    """
    
    template = {
        "agent_id": f"{agent_type}_agent",
        "agent_name": f"{agent_type.capitalize()} Agent",
        "agent_description": f"A configurable {agent_type} agent",
        
        # 模型配置
        "model_provider": "deepseek",
        "model_name": "deepseek-chat",
        "model_temperature": 0.1,
        "model_max_tokens": 4000,
        "model_max_retries": 3,
        
        # 工作流配置
        "workflow_type": "react",
        "max_iterations": 10,
        "enable_memory": True,
        "enable_streaming": True,
        
        # 工具配置
        "enabled_tool_categories": ["search", "calculation", "text_processing"],
        "custom_tools": [],
        "enable_mcp_tools": True,
        "require_approval_tools": [],
        
        # 提示词配置
        "system_prompt_template": None,
        "role_description": "你是一个有用的AI助手",
        "personality_traits": ["helpful", "professional", "accurate"],
        
        # 安全配置
        "enable_content_filter": True,
        "max_tool_calls_per_turn": 5,
        "timeout_seconds": 300,
        
        # 实验性功能
        "enable_self_reflection": False,
        "enable_parallel_execution": False
    }
    
    return template


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """合并配置字典
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
        
    Returns:
        合并后的配置
    """
    
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            merged[key] = merge_configs(merged[key], value)
        else:
            # 直接覆盖
            merged[key] = value
    
    return merged


def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """清理和验证配置
    
    Args:
        config: 原始配置
        
    Returns:
        清理后的配置
    """
    
    sanitized = {}
    
    # 定义允许的配置键和类型
    allowed_fields = {
        "agent_id": str,
        "agent_name": str,
        "agent_description": str,
        "model_provider": str,
        "model_name": str,
        "model_temperature": (int, float),
        "model_max_tokens": int,
        "model_max_retries": int,
        "workflow_type": str,
        "max_iterations": int,
        "enable_memory": bool,
        "enable_streaming": bool,
        "enabled_tool_categories": list,
        "custom_tools": list,
        "enable_mcp_tools": bool,
        "require_approval_tools": list,
        "system_prompt_template": (str, type(None)),
        "role_description": str,
        "personality_traits": list,
        "enable_content_filter": bool,
        "max_tool_calls_per_turn": int,
        "timeout_seconds": int,
        "enable_self_reflection": bool,
        "enable_parallel_execution": bool
    }
    
    for key, expected_type in allowed_fields.items():
        if key in config:
            value = config[key]
            if isinstance(value, expected_type):
                sanitized[key] = value
            else:
                print(f"Warning: Invalid type for {key}, expected {expected_type}, got {type(value)}")
    
    return sanitized