"""
故障诊断代理工具定义模块
包含所有可用的诊断工具和工具列表
"""

# 导入工具模块
from src.tools import ssh_tool, sop_tool

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

# 所有可用工具的完整列表
all_tools = ssh_tools + sop_tools

# 工具类别映射
tool_categories = {
    "ssh": ssh_tools,
    "sop": sop_tools,
    "all": all_tools
}

def get_tools_by_category(category: str = "all"):
    """根据类别获取工具列表
    
    Args:
        category: 工具类别，可选值: "ssh", "sop", "all"
    
    Returns:
        对应类别的工具列表
    """
    return tool_categories.get(category, all_tools)