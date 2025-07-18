"""
普通问答工具权限控制模块
定义哪些工具需要用户确认，哪些命令在白名单中可以免确认
"""

from typing import Dict, List, Set
import re
import logging

logger = logging.getLogger(__name__)

# 工具权限配置
TOOL_PERMISSIONS = {
    # 1. 免审批工具 - 安全的查询工具，可以直接调用
    "no_approval_required": {
        "get_current_time",  # 获取当前时间
        "get_sop_content",   # 查询SOP内容（只读）
        "get_sop_detail",    # 查询SOP详情（只读）
        "list_sops",         # 列出SOP（只读）
        "search_sops",       # 搜索SOP（只读）
        "get_es_data",       # ES数据查询（只读）
        "get_es_indices",    # ES索引查询（只读）
        "get_es_trends_data", # ES趋势数据查询（只读）
    },
    
    # 2. 需要审批工具 - 涉及系统操作的工具
    "approval_required": {
        "get_system_info",
        "analyze_processes", 
        "check_service_status",
        "analyze_system_logs",
        "execute_system_command",
        # MySQL工具
        "execute_mysql_query",
        "check_mysql_status",
        "analyze_mysql_performance",
        # Elasticsearch工具
        "search_elasticsearch",
        "get_elasticsearch_cluster_health",
        "get_elasticsearch_indices",
        # Zabbix工具
        "get_zabbix_alerts",
        "get_zabbix_host_info",
        "get_zabbix_metrics",
        "get_zabbix_metric_data",
    }
}

# 需要审批工具的白名单命令配置
# 这些是安全的查询命令，即使在需要审批的工具中也可以免审批
WHITELIST_COMMANDS = {
    "execute_system_command": {
        # 系统信息查询命令（只读） - 精确匹配
        "date", "uptime", "whoami", "pwd", "hostname",
        "uname -a", "cat /etc/os-release", "df -h", "free -m",
        "ps aux", "top -n 1", "htop -n 1", "vmstat", "iostat",
        "netstat -tuln", "ss -tuln", "lsof -i", "who", "w",
        
        # 日志查看命令（只读，限制行数）
        "tail -n 50", "head -n 50",
        
        # 网络诊断命令
        "ping -c 4", "nslookup", "dig", "traceroute",
        
        # 文件系统查看（只读） - 常用参数组合
        "ls", "ls -l", "ls -la", "ls -al", "ls -a", "ll",
        "find", "locate", "which", "whereis", "stat", "file", "du -sh",
        
        # 进程和服务查看
        "systemctl status", "service status", "jobs", "pgrep", "pkill -l",
    },
    
    "execute_mysql_query": {
        # 安全的MySQL查询命令
        "SHOW DATABASES", "SHOW TABLES", "SHOW PROCESSLIST", 
        "SHOW STATUS", "SHOW VARIABLES", "SHOW ENGINE INNODB STATUS",
        "SELECT", "DESCRIBE", "EXPLAIN", "SHOW CREATE TABLE",
        "SHOW GRANTS", "SHOW MASTER STATUS", "SHOW SLAVE STATUS",
    },
    
    "get_system_info": set(),  # get_system_info 本身就是只读的，全部允许
    "analyze_processes": set(),  # analyze_processes 本身就是只读的，全部允许
    "check_service_status": set(),  # check_service_status 本身就是只读的，全部允许
    "analyze_system_logs": set(),  # analyze_system_logs 本身就是只读的，全部允许
}

def is_tool_approval_required(tool_name: str) -> bool:
    """
    检查工具是否需要用户审批
    
    Args:
        tool_name: 工具名称
        
    Returns:
        True表示需要审批，False表示可直接执行
    """
    if tool_name in TOOL_PERMISSIONS["no_approval_required"]:
        return False
    elif tool_name in TOOL_PERMISSIONS["approval_required"]:
        return True
    else:
        # 未知工具默认需要审批
        logger.warning(f"未知工具 {tool_name}，默认需要审批")
        return True

def is_command_whitelisted(tool_name: str, command_args: Dict) -> bool:
    """
    检查命令是否在白名单中，可以免审批
    
    Args:
        tool_name: 工具名称
        command_args: 工具调用参数
        
    Returns:
        True表示在白名单中可免审批，False表示需要审批
    """
    if tool_name not in WHITELIST_COMMANDS:
        return False
    
    whitelist = WHITELIST_COMMANDS[tool_name]
    
    # 如果白名单为空集合，表示该工具本身就是安全的
    if not whitelist:
        return True
    
    # 检查具体命令
    if tool_name == "execute_system_command":
        command = command_args.get("command", "")
        return _is_system_command_safe(command, whitelist)
    
    elif tool_name == "execute_mysql_query":
        query = command_args.get("query", "").upper().strip()
        return _is_mysql_query_safe(query, whitelist)
    
    return False

def _is_system_command_safe(command: str, whitelist: Set[str]) -> bool:
    """检查系统命令是否安全 - 精确匹配白名单"""
    command = command.strip()
    
    # 精确匹配白名单命令
    return command in whitelist

def _is_mysql_query_safe(query: str, whitelist: Set[str]) -> bool:
    """检查MySQL查询是否安全 - 精确匹配白名单"""
    # 标准化查询：移除多余空格和分号，转大写
    query = re.sub(r'\s+', ' ', query.strip().rstrip(';')).upper()
    
    # 精确匹配白名单查询
    return query in whitelist

# 已移除危险操作符检查函数，改用精确白名单匹配

def check_tool_permission(tool_name: str, tool_args: Dict) -> Dict[str, any]:
    """
    检查工具调用权限
    
    Args:
        tool_name: 工具名称
        tool_args: 工具参数
        
    Returns:
        权限检查结果字典:
        {
            "approved": bool,  # 是否已获得批准（可直接执行）
            "requires_approval": bool,  # 是否需要用户确认
            "reason": str,  # 原因说明
            "risk_level": str,  # 风险等级: "low", "medium", "high"
        }
    """
    # 1. 检查工具是否需要审批
    requires_approval = is_tool_approval_required(tool_name)
    
    if not requires_approval:
        return {
            "approved": True,
            "requires_approval": False,
            "reason": f"工具 {tool_name} 为安全查询工具，可直接执行",
            "risk_level": "low"
        }
    
    # 2. 检查是否在白名单中
    is_whitelisted = is_command_whitelisted(tool_name, tool_args)
    
    if is_whitelisted:
        return {
            "approved": True,
            "requires_approval": False,
            "reason": f"命令在白名单中，评估为安全操作",
            "risk_level": "low"
        }
    
    # 3. 需要用户确认
    risk_level = _assess_risk_level(tool_name, tool_args)
    
    return {
        "approved": False,
        "requires_approval": True,
        "reason": f"工具 {tool_name} 涉及系统操作，需要用户确认",
        "risk_level": risk_level
    }

def _assess_risk_level(tool_name: str, tool_args: Dict) -> str:
    """评估操作风险等级"""
    high_risk_tools = {"execute_system_command"}
    medium_risk_tools = {"execute_mysql_query", "analyze_system_logs"}
    
    if tool_name in high_risk_tools:
        command = tool_args.get("command", "")
        if any(dangerous in command.lower() for dangerous in ["rm", "kill", "chmod", "sudo"]):
            return "high"
        return "medium"
    elif tool_name in medium_risk_tools:
        return "medium"
    else:
        return "low"

def get_approval_message(tool_name: str, tool_args: Dict, risk_level: str) -> str:
    """生成用户确认消息"""
    risk_emoji = {"low": "🟡", "medium": "🟠", "high": "🔴"}
    emoji = risk_emoji.get(risk_level, "🟡")
    
    message = f"{emoji} **需要确认工具调用**\n\n"
    message += f"**工具**: {tool_name}\n"
    message += f"**风险等级**: {risk_level.upper()}\n"
    message += f"**参数**: {tool_args}\n\n"
    
    if risk_level == "high":
        message += "⚠️ **高风险操作**：此操作可能对系统造成重大影响，请仔细确认！\n"
    elif risk_level == "medium":
        message += "⚠️ **中等风险操作**：此操作会访问系统资源，请确认是否继续。\n"
    else:
        message += "ℹ️ **低风险操作**：此操作相对安全，但仍需确认。\n"
    
    message += "\n**请回复**：\n"
    message += "- `确认` 或 `y` - 同意执行\n"
    message += "- `拒绝` 或 `n` - 拒绝执行\n"
    message += "- `详情` - 查看详细说明"
    
    return message

# 导出主要函数
__all__ = [
    "check_tool_permission",
    "get_approval_message",
    "is_tool_approval_required",
    "is_command_whitelisted"
]