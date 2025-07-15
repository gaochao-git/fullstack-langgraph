"""
故障诊断代理工具定义模块
包含所有可用的诊断工具和工具列表
"""

from typing import List, Set, Dict, Any
import json
import logging

# 导入工具模块
from src.tools import ssh_tool, sop_tool, mysql_tool, elasticsearch_tool, zabbix_tool, general_tool

logger = logging.getLogger(__name__)

# SSH诊断工具列表
ssh_tools = [
    ssh_tool.get_system_info,
    ssh_tool.analyze_processes,
    ssh_tool.check_service_status,
    ssh_tool.analyze_system_logs,
    ssh_tool.execute_system_command
]

# SOP相关工具列表
sop_tools = [
    sop_tool.get_sop_content,
    sop_tool.get_sop_detail,
    sop_tool.list_sops,
    sop_tool.search_sops
]

# MySQL诊断工具列表
mysql_tools = mysql_tool.mysql_tools

# Elasticsearch诊断工具列表
elasticsearch_tools = elasticsearch_tool.elasticsearch_tools

# Zabbix监控工具列表
zabbix_tools = zabbix_tool.zabbix_tools

# 通用工具
general_tools = [
    general_tool.get_current_time
]

# 所有可用工具的完整列表
all_tools = ssh_tools + sop_tools + mysql_tools + elasticsearch_tools + zabbix_tools + general_tools

# 工具名称到工具对象的映射
tool_name_mapping = {}
for tool in all_tools:
    tool_name_mapping[tool.name] = tool

# 工具类别映射
tool_categories = {
    "ssh": ssh_tools,
    "sop": sop_tools,
    "mysql": mysql_tools,
    "elasticsearch": elasticsearch_tools,
    "zabbix": zabbix_tools,
    "all": all_tools
}

def extract_required_tools_from_sop(sop_data: Dict[str, Any]) -> Set[str]:
    """从SOP数据中提取需要的工具名称
    
    Args:
        sop_data: SOP数据字典
    
    Returns:
        需要的工具名称集合
    """
    required_tools = set()
    
    # 1. 从 tools_required 字段获取工具
    if "tools_required" in sop_data:
        required_tools.update(sop_data["tools_required"])
    
    # 2. 从步骤中提取工具，排除 llm 工具
    if "steps" in sop_data:
        for step in sop_data["steps"]:
            if "tool" in step and step["tool"] != "llm":
                required_tools.add(step["tool"])
    
    logger.info(f"从SOP中提取到需要的工具: {required_tools}")
    return required_tools

def get_tools_for_sop(sop_data: Dict[str, Any]) -> List:
    """根据SOP数据动态获取需要的工具列表
    
    Args:
        sop_data: SOP数据字典
    
    Returns:
        SOP需要的工具对象列表
    """
    # 提取SOP需要的工具名称
    required_tool_names = extract_required_tools_from_sop(sop_data)
    
    # 总是包含SOP相关工具
    required_tool_names.update(["get_sop_content", "get_sop_detail", "list_sops", "search_sops"])
    
    # 根据工具名称获取工具对象
    sop_tools_list = []
    missing_tools = []
    
    for tool_name in required_tool_names:
        if tool_name in tool_name_mapping:
            sop_tools_list.append(tool_name_mapping[tool_name])
        else:
            missing_tools.append(tool_name)
    
    if missing_tools:
        logger.warning(f"以下工具未找到: {missing_tools}")
    
    logger.info(f"为SOP选择了 {len(sop_tools_list)} 个工具: {[tool.name for tool in sop_tools_list]}")
    return sop_tools_list

def get_tools_by_category(category: str = "all"):
    """根据类别获取工具列表
    
    Args:
        category: 工具类别，可选值: "ssh", "sop", "mysql", "elasticsearch", "zabbix", "all"
    
    Returns:
        对应类别的工具列表
    """
    return tool_categories.get(category, all_tools)