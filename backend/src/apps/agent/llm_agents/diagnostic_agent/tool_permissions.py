"""
工具权限配置 - 定义哪些工具需要用户审批
"""

from typing import Dict, Any

# 工具权限配置 - 统一的配置结构
TOOL_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    # SSH工具 - 系统操作类
    "get_system_info": {
        "requires_approval": True,
        "category": "ssh",
        "risk_level": "medium",
        "description": "获取系统信息"
    },
    "analyze_processes": {
        "requires_approval": True,
        "category": "ssh", 
        "risk_level": "medium",
        "description": "分析系统进程"
    },
    "check_service_status": {
        "requires_approval": True,
        "category": "ssh",
        "risk_level": "medium", 
        "description": "检查服务状态"
    },
    "analyze_system_logs": {
        "requires_approval": True,
        "category": "ssh",
        "risk_level": "medium",
        "description": "分析系统日志"
    },
    "execute_system_command": {
        "requires_approval": True,
        "category": "ssh",
        "risk_level": "high",
        "description": "执行系统命令"
    },
    
    # MySQL工具 - 数据库操作类
    "execute_mysql_query": {
        "requires_approval": True,
        "category": "mysql",
        "risk_level": "high",
        "description": "执行MySQL查询"
    },
    
    # Elasticsearch工具 - 搜索引擎操作类
    "get_es_data": {
        "requires_approval": True,
        "category": "elasticsearch",
        "risk_level": "medium",
        "description": "获取ES数据"
    },
    "get_es_indices": {
        "requires_approval": True,
        "category": "elasticsearch", 
        "risk_level": "low",
        "description": "获取ES索引列表"
    },
    "get_es_trends_data": {
        "requires_approval": True,
        "category": "elasticsearch",
        "risk_level": "medium",
        "description": "获取ES趋势数据"
    },
    
    # Zabbix工具 - 监控系统操作类
    "get_zabbix_metrics": {
        "requires_approval": True,
        "category": "zabbix",
        "risk_level": "low",
        "description": "获取Zabbix指标列表"
    },
    "get_zabbix_metric_data": {
        "requires_approval": True,
        "category": "zabbix",
        "risk_level": "medium",
        "description": "获取Zabbix指标数据"
    },
    
    # SOP工具 - 只读查询，安全
    "get_sop_content": {
        "requires_approval": False,
        "category": "sop",
        "risk_level": "low",
        "description": "获取SOP内容"
    },
    "get_sop_detail": {
        "requires_approval": False,
        "category": "sop",
        "risk_level": "low", 
        "description": "获取SOP详情"
    },
    "list_sops": {
        "requires_approval": False,
        "category": "sop",
        "risk_level": "low",
        "description": "列出SOP列表"
    },
    "search_sops": {
        "requires_approval": False,
        "category": "sop",
        "risk_level": "low",
        "description": "搜索SOP"
    },
    
    # 通用工具 - 基础功能，安全
    "get_current_time": {
        "requires_approval": False,
        "category": "general",
        "risk_level": "low",
        "description": "获取当前时间"
    },
}

def is_tool_requiring_approval(tool_name: str) -> bool:
    """
    检查工具是否需要用户审批
    
    Args:
        tool_name: 工具名称
        
    Returns:
        True表示需要审批，False表示可直接执行
    """
    tool_config = TOOL_PERMISSIONS.get(tool_name, {})
    return tool_config.get("requires_approval", True)  # 默认需要审批（安全优先）

def get_tool_config(tool_name: str) -> Dict[str, Any]:
    """
    获取工具配置信息
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具配置字典
    """
    return TOOL_PERMISSIONS.get(tool_name, {
        "requires_approval": True,  # 默认需要审批
        "category": "unknown",
        "risk_level": "medium",
        "description": "未知工具"
    })

def get_tools_by_approval_status(requires_approval: bool) -> Dict[str, Dict[str, Any]]:
    """
    根据审批要求筛选工具
    
    Args:
        requires_approval: True获取需要审批的工具，False获取安全工具
        
    Returns:
        符合条件的工具字典
    """
    return {
        tool_name: config 
        for tool_name, config in TOOL_PERMISSIONS.items()
        if config.get("requires_approval") == requires_approval
    }

def get_tools_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """
    根据类别筛选工具
    
    Args:
        category: 工具类别
        
    Returns:
        指定类别的工具字典
    """
    return {
        tool_name: config
        for tool_name, config in TOOL_PERMISSIONS.items()
        if config.get("category") == category
    }