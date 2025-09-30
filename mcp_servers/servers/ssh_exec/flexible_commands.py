"""
灵活的SSH命令执行机制
分为两类：不限制参数的命令和限制参数的命令
"""

from typing import Dict, List, Optional, Tuple, Any
import shlex

# 不限制参数的命令（只包含真正安全的只读命令）
UNRESTRICTED_COMMANDS = {
    "ls",      # 列出目录
    "ps",      # 查看进程
    "grep",    # 搜索文本（虽然可以读文件，但是必需的功能）
    "pgrep",   # 进程查找
    "df",      # 磁盘空间
    "free",    # 内存使用
    "uptime",  # 系统运行时间
    "ssh",     # SSH到其他服务器
    "tail",    # 查看文件末尾
    "ping",    # 网络连通性测试
}

# 限制参数的命令模板
PARAMETERIZED_COMMANDS = {
    
    "check_port": {
        "template": "timeout 5 nc -zv {host} {port}",
        "description": "检查端口连通性",
        "parameters": {
            "host": {
                "type": "str",
                "description": "目标主机",
                "validator": "hostname_or_ip"
            },
            "port": {
                "type": "int",
                "min": 1,
                "max": 65535,
                "description": "端口号"
            }
        }
    },
    
    "disk_usage": {
        "template": "timeout 10 du -h --max-depth={depth} {directory} 2>/dev/null | sort -h | tail -n {lines}",
        "description": "查看目录占用空间",
        "parameters": {
            "directory": {
                "type": "str",
                "description": "目录路径",
                "validator": "directory_path",
                "default": "/tmp"
            },
            "depth": {
                "type": "int",
                "min": 1,
                "max": 2,
                "default": 1,
                "description": "目录深度"
            },
            "lines": {
                "type": "int",
                "min": 10,
                "max": 20,
                "default": 10,
                "description": "显示行数"
            }
        }
    },
    
    
    "netstat_filter": {
        "template": "netstat -an | grep {pattern}",
        "description": "过滤网络连接",
        "parameters": {
            "pattern": {
                "type": "str",
                "description": "端口或IP模式",
                "validator": "safe_pattern"
            }
        }
    },
    
    "system_info": {
        "template": "{command}",
        "description": "获取系统信息",
        "parameters": {
            "command": {
                "type": "str",
                "description": "系统信息命令",
                "validator": "system_info_command"
            }
        }
    },
    
    "netstat_info": {
        "template": "netstat -{options}",
        "description": "查看网络连接信息",
        "parameters": {
            "options": {
                "type": "str",
                "description": "netstat选项",
                "validator": "netstat_options"
            }
        }
    },
    
    "basic_info": {
        "template": "{command}",
        "description": "基础系统信息",
        "parameters": {
            "command": {
                "type": "str",
                "description": "基础命令",
                "validator": "basic_command"
            }
        }
    }
}

# 参数验证器
def validate_file_path(path: str) -> bool:
    """验证文件路径是否安全"""
    # 不允许路径遍历
    if '..' in path or path.startswith('~'):
        return False
    
    # 不允许的路径模式（更严格的限制）
    dangerous_patterns = [
        '/etc/shadow',
        '/etc/passwd',
        '/etc/security',
        '.ssh/',
        'id_rsa',
        'id_dsa',
        'id_ecdsa',
        'id_ed25519',
        '.history',
        '.bash_history',
        '.zsh_history',
        '/root/',
        '/home/',  # 限制访问用户家目录
        '.pem',
        '.key',
        '.crt',
        'private',
        'secret',
    ]
    
    path_lower = path.lower()
    for danger in dangerous_patterns:
        if danger in path_lower:
            return False
    
    # 只允许特定目录
    allowed_prefixes = [
        '/var/log/',
        '/tmp/',
        '/opt/',
        '/usr/local/',
        '/proc/self/',
    ]
    
    # 必须以允许的前缀开始
    if not any(path.startswith(prefix) for prefix in allowed_prefixes):
        return False
        
    return True

def validate_directory_path(path: str) -> bool:
    """验证目录路径是否安全"""
    if not validate_file_path(path):
        return False
    
    # 额外的目录检查
    if path.startswith('/proc/') and not path.startswith('/proc/self/'):
        return False
        
    return True

def validate_hostname_or_ip(host: str) -> bool:
    """验证主机名或IP是否合法"""
    import re
    
    # IP地址正则
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # 域名正则（简化版）
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if re.match(ip_pattern, host):
        # 验证IP地址范围
        parts = host.split('.')
        for part in parts:
            if int(part) > 255:
                return False
        return True
    
    return bool(re.match(domain_pattern, host))

def validate_safe_pattern(pattern: str) -> bool:
    """验证搜索模式是否安全"""
    # 长度限制
    if len(pattern) > 100:
        return False
        
    # 不允许的字符（更严格）
    dangerous_chars = ['`', '$', '\\', '\n', '\r', ';', '&', '|', '>', '<', '"', "'", '(', ')', '{', '}', '[', ']', '*', '?', '~', '!', '#', '%', '^']
    
    for char in dangerous_chars:
        if char in pattern:
            return False
            
    # 只允许字母、数字、点、横线、下划线、空格
    import re
    if not re.match(r'^[\w\s\.\-]+$', pattern):
        return False
            
    return True

def validate_system_info_command(command: str) -> bool:
    """验证系统信息命令是否安全"""
    # 只允许特定的系统信息命令
    allowed_commands = [
        "top -b -n 2 -d 1 | head -100",  # 2次采样，1秒间隔，限制100行输出
        "iostat",
        "iostat -x 1 5",
        "vmstat",
        "vmstat 1 5",
    ]
    return command in allowed_commands

def validate_netstat_options(options: str) -> bool:
    """验证netstat选项是否安全"""
    allowed_options = ["an", "tlnp", "s", "rn", "i"]
    return options in allowed_options

def validate_basic_command(command: str) -> bool:
    """验证基础命令是否安全"""
    allowed_commands = [
        "date",
        "hostname", 
        "uname -a",
        "w",
        "who"
    ]
    return command in allowed_commands

# 验证器映射
VALIDATORS = {
    "file_path": validate_file_path,
    "directory_path": validate_directory_path,
    "hostname_or_ip": validate_hostname_or_ip,
    "safe_pattern": validate_safe_pattern,
    "system_info_command": validate_system_info_command,
    "netstat_options": validate_netstat_options,
    "basic_command": validate_basic_command,
}

def validate_parameter(param_name: str, param_value: Any, param_config: Dict) -> Tuple[bool, str, Any]:
    """验证单个参数"""
    param_type = param_config.get("type", "str")
    
    # 类型转换
    try:
        if param_type == "int":
            param_value = int(param_value)
        elif param_type == "str":
            param_value = str(param_value)
    except (ValueError, TypeError):
        return False, f"参数 {param_name} 类型错误，期望 {param_type}", None
    
    # 范围检查（对于整数）
    if param_type == "int":
        min_val = param_config.get("min")
        max_val = param_config.get("max")
        
        if min_val is not None and param_value < min_val:
            return False, f"参数 {param_name} 小于最小值 {min_val}", None
        if max_val is not None and param_value > max_val:
            return False, f"参数 {param_name} 大于最大值 {max_val}", None
    
    # 自定义验证器
    validator_name = param_config.get("validator")
    if validator_name and validator_name in VALIDATORS:
        validator = VALIDATORS[validator_name]
        if not validator(param_value):
            return False, f"参数 {param_name} 验证失败: {param_value}", None
    
    return True, "验证通过", param_value

def build_parameterized_command(command_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
    """构建参数化命令"""
    if command_name not in PARAMETERIZED_COMMANDS:
        return False, f"未知的命令模板: {command_name}", None
    
    cmd_config = PARAMETERIZED_COMMANDS[command_name]
    template = cmd_config["template"]
    param_configs = cmd_config["parameters"]
    
    # 验证并处理参数
    validated_params = {}
    for param_name, param_config in param_configs.items():
        if param_name in parameters:
            # 用户提供的参数
            param_value = parameters[param_name]
        elif "default" in param_config:
            # 使用默认值
            param_value = param_config["default"]
        else:
            # 必需参数缺失
            return False, f"缺少必需参数: {param_name}", None
        
        # 验证参数
        is_valid, message, validated_value = validate_parameter(param_name, param_value, param_config)
        if not is_valid:
            return False, message, None
            
        validated_params[param_name] = validated_value
    
    # 构建命令
    try:
        command = template.format(**validated_params)
        return True, cmd_config["description"], command
    except KeyError as e:
        return False, f"模板参数错误: {e}", None

def is_command_safe(command: str) -> Tuple[bool, str]:
    """检查命令是否安全"""
    # 危险字符和模式（不包括管道符，因为管道在安全的命令间是允许的）
    dangerous_patterns = [
        '&&', '||', ';', '\n', '\r',  # 命令链接
        '>', '>>', '<',                # 重定向
        '`', '$(',                     # 命令替换
        'rm ', 'dd ', 'mkfs',          # 危险命令
        'shutdown', 'reboot', 'init',  # 系统命令
        'kill', 'pkill',               # 进程终止
        'chmod', 'chown',              # 权限修改
        'passwd', 'useradd', 'userdel', # 用户管理
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command:
            return False, f"命令包含危险模式: {pattern}"
    
    # 如果包含管道，检查管道两边的命令是否都安全
    if '|' in command:
        pipe_parts = command.split('|')
        for part in pipe_parts:
            part = part.strip()
            if part:
                # 获取每个部分的命令名
                cmd_parts = part.split()
                if cmd_parts:
                    cmd_name = cmd_parts[0]
                    # 检查是否是白名单命令或常见的文本处理命令
                    # 只允许安全命令和几个必需的文本处理命令
                    allowed_pipe_commands = UNRESTRICTED_COMMANDS.union({
                        'wc', 'sort', 'head', 'tail'
                    })
                    if cmd_name not in allowed_pipe_commands:
                        return False, f"管道命令 '{cmd_name}' 不在允许列表中"
    
    return True, "命令安全检查通过"

def get_available_commands() -> Dict[str, Any]:
    """获取所有可用命令的信息"""
    return {
        "unrestricted_commands": list(UNRESTRICTED_COMMANDS),
        "parameterized_commands": {
            name: {
                "description": config["description"],
                "parameters": {
                    param_name: {
                        "type": param_config["type"],
                        "description": param_config["description"],
                        "min": param_config.get("min"),
                        "max": param_config.get("max"),
                        "default": param_config.get("default")
                    }
                    for param_name, param_config in config["parameters"].items()
                }
            }
            for name, config in PARAMETERIZED_COMMANDS.items()
        }
    }