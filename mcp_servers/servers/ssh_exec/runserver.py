#!/usr/bin/env python3
"""
SSH Tools MCP Server
基于现有SSH工具实现的MCP服务器
"""

import paramiko
import json
import time
from typing import Dict, Any, List, Optional
import logging
from io import StringIO
import os
from fastmcp import FastMCP
from ..common.base_config import MCPServerConfig

# 定义一个辅助函数来输出中文友好的JSON
def json_dumps(obj, **kwargs):
    """输出不转义中文的JSON"""
    return json.dumps(obj, ensure_ascii=False, **kwargs)
from .flexible_commands import (
    UNRESTRICTED_COMMANDS,
    PARAMETERIZED_COMMANDS,
    build_parameterized_command,
    is_command_safe,
    get_available_commands
)

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("SSH Tools Server")

# 加载配置
config = MCPServerConfig('ssh_exec')

def _create_ssh_client(host=None):
    """创建新的SSH连接，每次调用都重新连接
    
    Args:
        host: 目标主机IP或域名，如果不提供则使用配置中的默认主机
    """
    ssh_configs = config.get('configs', [])
    if host is None:
        host = config.get('host')
    port = config.get('ssh_port', 22)  # 使用ssh_port而不是port
    
    for ssh_config in ssh_configs:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 判断是密钥认证还是密码认证
            if 'key_file' in ssh_config:
                # 密钥认证
                key_path = os.path.expanduser(ssh_config['key_file'])
                if not os.path.exists(key_path):
                    logger.debug(f"私钥文件不存在: {key_path}")
                    continue
                
                try:
                    key = paramiko.RSAKey.from_private_key_file(key_path)
                    client.connect(
                        hostname=host,
                        port=port,
                        username=ssh_config["username"],
                        pkey=key,
                        timeout=10
                    )
                    logger.info(f"SSH密钥连接成功，主机: {host}, 用户: {ssh_config['username']}, 密钥: {key_path}")
                except Exception as key_error:
                    logger.debug(f"密钥认证失败: {key_error}")
                    continue
            else:
                # 密码认证
                client.connect(
                    hostname=host,
                    port=port,
                    username=ssh_config["username"],
                    password=ssh_config.get("password", ""),
                    timeout=10
                )
                logger.info(f"SSH密码连接成功，主机: {host}, 用户: {ssh_config['username']}")
            
            return client
            
        except Exception as e:
            logger.debug(f"尝试用户 {ssh_config['username']} 失败: {e}")
            continue
    
    raise Exception("无法建立SSH连接，请检查网络和服务器状态")

@mcp.tool()
async def get_system_info(host: Optional[str] = None) -> str:
    """获取系统基本信息。用于了解服务器的硬件配置和运行状态。
    
    Args:
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
    
    Returns:
        包含系统信息的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client(host)
        
        commands = {
            'hostname': 'hostname',
            'kernel': 'uname -r',
            'os_info': 'cat /etc/os-release | head -5',
            'uptime': 'uptime',
            'cpu_info': 'cat /proc/cpuinfo | grep "model name" | head -1',
            'cpu_count': 'nproc',
            'memory_info': 'free -h',
            'disk_usage': 'df -h',
            'load_average': 'cat /proc/loadavg',
            'who': 'who'
        }
        
        system_info = {}
        
        for key, command in commands.items():
            try:
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()
                
                if error:
                    system_info[key] = {"error": error}
                else:
                    system_info[key] = output
                    
            except Exception as e:
                system_info[key] = {"error": str(e)}
        
        # 解析一些关键信息
        parsed_info = {
            "hostname": system_info.get('hostname', 'Unknown'),
            "kernel_version": system_info.get('kernel', 'Unknown'),
            "os_info": system_info.get('os_info', 'Unknown'),
            "uptime": system_info.get('uptime', 'Unknown'),
            "cpu_model": system_info.get('cpu_info', 'Unknown').replace('model name\t:', '').strip(),
            "cpu_cores": system_info.get('cpu_count', 'Unknown'),
            "memory_info": system_info.get('memory_info', 'Unknown'),
            "disk_usage": system_info.get('disk_usage', 'Unknown'),
            "load_average": system_info.get('load_average', 'Unknown'),
            "logged_users": system_info.get('who', 'Unknown'),
            "raw_data": system_info
        }
        
        return json_dumps(parsed_info, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return json_dumps({"error": f"Failed to get system info: {str(e)}"})
    finally:
        if client:
            client.close()

@mcp.tool()
async def analyze_processes(
    host: Optional[str] = None,
    process_name: Optional[str] = None,
    sort_by: str = "cpu"
) -> str:
    """分析系统进程。用于查看系统中运行的进程和资源使用情况。
    
    Args:
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
        process_name: 进程名称筛选
        sort_by: 排序方式(cpu, memory, pid)
    
    Returns:
        包含进程分析结果的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client(host)
        
        # 构建ps命令
        if process_name:
            ps_command = f"ps aux | grep '{process_name}' | grep -v grep"
        else:
            ps_command = "ps aux --sort=-%cpu | head -20"  # 默认按CPU排序取前20
        
        if sort_by == "memory":
            ps_command = ps_command.replace("--sort=-%cpu", "--sort=-%mem")
        elif sort_by == "pid":
            ps_command = ps_command.replace("--sort=-%cpu", "--sort=-pid")
        
        stdin, stdout, stderr = client.exec_command(ps_command)
        ps_output = stdout.read().decode().strip()
        
        # 获取进程统计信息
        stdin, stdout, stderr = client.exec_command("ps aux | wc -l")
        total_processes = int(stdout.read().decode().strip()) - 1  # 减去标题行
        
        # 获取僵尸进程
        stdin, stdout, stderr = client.exec_command("ps aux | awk '$8 ~ /^Z/ { print $0 }'")
        zombie_processes = stdout.read().decode().strip()
        
        # 获取高CPU使用率进程
        stdin, stdout, stderr = client.exec_command("ps aux --sort=-%cpu | head -5 | tail -n +2")
        high_cpu_processes = stdout.read().decode().strip()
        
        # 获取高内存使用率进程
        stdin, stdout, stderr = client.exec_command("ps aux --sort=-%mem | head -5 | tail -n +2")
        high_mem_processes = stdout.read().decode().strip()
        
        # 解析进程信息
        processes = []
        if ps_output:
            lines = ps_output.split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu_percent": parts[2],
                            "memory_percent": parts[3],
                            "vsz": parts[4],
                            "rss": parts[5],
                            "tty": parts[6],
                            "stat": parts[7],
                            "start": parts[8],
                            "time": parts[9],
                            "command": parts[10]
                        })
        
        return json_dumps({
            "total_processes": total_processes,
            "filtered_processes": processes,
            "zombie_processes": zombie_processes.split('\n') if zombie_processes else [],
            "high_cpu_processes": high_cpu_processes.split('\n') if high_cpu_processes else [],
            "high_memory_processes": high_mem_processes.split('\n') if high_mem_processes else [],
            "filter_applied": process_name,
            "sort_by": sort_by
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing processes: {e}")
        return json_dumps({"error": f"Failed to analyze processes: {str(e)}"})
    finally:
        if client:
            client.close()

@mcp.tool()
async def check_service_status(
    host: Optional[str] = None,
    service_names: Optional[List[str]] = None
) -> str:
    """检查系统服务状态。用于查看关键服务的运行状态。
    
    Args:
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
        service_names: 要检查的服务名称列表
    
    Returns:
        包含服务状态的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client(host)
        
        service_status = {}
        
        if not service_names:
            # 获取所有运行中的服务
            stdin, stdout, stderr = client.exec_command("systemctl list-units --type=service --state=running --no-pager")
            running_services = stdout.read().decode()
            
            # 获取失败的服务
            stdin, stdout, stderr = client.exec_command("systemctl list-units --type=service --state=failed --no-pager")
            failed_services = stdout.read().decode()
            
            service_status = {
                "running_services": running_services,
                "failed_services": failed_services
            }
        else:
            # 检查指定服务
            for service_name in service_names:
                try:
                    # 检查服务状态
                    stdin, stdout, stderr = client.exec_command(f"systemctl is-active {service_name}")
                    is_active = stdout.read().decode().strip()
                    
                    stdin, stdout, stderr = client.exec_command(f"systemctl is-enabled {service_name}")
                    is_enabled = stdout.read().decode().strip()
                    
                    # 获取服务详细状态
                    stdin, stdout, stderr = client.exec_command(f"systemctl status {service_name} --no-pager -l")
                    status_detail = stdout.read().decode()
                    
                    service_status[service_name] = {
                        "active": is_active,
                        "enabled": is_enabled,
                        "status_detail": status_detail,
                        "healthy": is_active.lower() == "active"
                    }
                    
                except Exception as e:
                    service_status[service_name] = {
                        "error": str(e),
                        "healthy": False
                    }
        
        return json_dumps(service_status, indent=2)
        
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return json_dumps({"error": f"Failed to check service status: {str(e)}"})
    finally:
        if client:
            client.close()

@mcp.tool()
async def analyze_system_logs(
    host: Optional[str] = None,
    log_file: str = "/var/log/syslog",
    lines: int = 100,
    pattern: Optional[str] = None
) -> str:
    """分析系统日志。用于查看系统日志中的错误和异常信息。
    
    Args:
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
        log_file: 日志文件路径
        lines: 读取的行数
        pattern: 搜索模式（grep模式）
    
    Returns:
        包含日志分析结果的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client(host)
        
        # 检查日志文件是否存在
        stdin, stdout, stderr = client.exec_command(f"test -f {log_file} && echo 'exists' || echo 'not found'")
        file_check = stdout.read().decode().strip()
        
        if file_check != 'exists':
            return json_dumps({"error": f"Log file {log_file} not found"})
        
        # 构建命令
        if pattern:
            command = f"tail -n {lines} {log_file} | grep -i '{pattern}'"
        else:
            command = f"tail -n {lines} {log_file}"
        
        stdin, stdout, stderr = client.exec_command(command)
        log_content = stdout.read().decode()
        
        # 分析错误级别
        error_commands = {
            'errors': f"tail -n {lines} {log_file} | grep -i 'error' | wc -l",
            'warnings': f"tail -n {lines} {log_file} | grep -i 'warning\\|warn' | wc -l",
            'critical': f"tail -n {lines} {log_file} | grep -i 'critical\\|crit' | wc -l",
            'failed': f"tail -n {lines} {log_file} | grep -i 'failed\\|fail' | wc -l"
        }
        
        log_stats = {}
        for key, cmd in error_commands.items():
            stdin, stdout, stderr = client.exec_command(cmd)
            count = stdout.read().decode().strip()
            log_stats[key] = int(count) if count.isdigit() else 0
        
        # 获取最近的错误行
        stdin, stdout, stderr = client.exec_command(f"tail -n {lines} {log_file} | grep -i 'error\\|critical\\|failed' | tail -10")
        recent_errors = stdout.read().decode().strip()
        
        return json_dumps({
            "log_file": log_file,
            "lines_analyzed": lines,
            "pattern_filter": pattern,
            "log_statistics": log_stats,
            "recent_errors": recent_errors.split('\n') if recent_errors else [],
            "log_content": log_content.split('\n')[-50:] if log_content else [],  # 最后50行
            "summary": {
                "total_issues": sum(log_stats.values()),
                "severity": "high" if log_stats.get('critical', 0) > 0 or log_stats.get('errors', 0) > 10 else "medium" if log_stats.get('errors', 0) > 0 else "low"
            }
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing system logs: {e}")
        return json_dumps({"error": f"Failed to analyze system logs: {str(e)}"})
    finally:
        if client:
            client.close()

@mcp.tool()
async def execute_command(
    command: str = "",
    timeout: int = 30
) -> str:
    """执行不限制参数的安全命令。支持 ls、ps、grep、pgrep、df、free、uptime 等常用运维命令。
    
    Args:
        command: 要执行的命令
        timeout: 超时时间(秒，默认30秒)
    
    Returns:
        包含命令执行结果的JSON字符串
    """
    
    if not command:
        return json_dumps({"error": "命令不能为空"})
    
    # 解析命令
    parts = command.strip().split()
    if not parts:
        return json_dumps({"error": "无效的命令"})
    
    cmd_name = parts[0]
    
    # 检查是否是允许的命令
    if cmd_name not in UNRESTRICTED_COMMANDS:
        return json_dumps({
            "error": f"命令 '{cmd_name}' 不在允许列表中",
            "allowed_commands": list(UNRESTRICTED_COMMANDS)
        })
    
    # 安全检查
    is_safe, safety_msg = is_command_safe(command)
    if not is_safe:
        return json_dumps({"error": safety_msg})
    
    # 额外的安全检查：命令长度限制
    if len(command) > 500:
        return json_dumps({"error": "命令过长，最多允许500个字符"})
    
    # 防止命令参数过多
    if len(parts) > 20:
        return json_dumps({"error": "命令参数过多，最多允许20个参数"})
    
    client = None
    try:
        client = _create_ssh_client()
        
        logger.info(f"执行命令: {command}")
        start_time = time.time()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        
        # 读取输出
        output = stdout.read().decode()
        error_output = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        execution_time = time.time() - start_time
        
        return json_dumps({
            "command": command,
            "exit_code": exit_code,
            "execution_time_seconds": round(execution_time, 2),
            "stdout": output,
            "stderr": error_output,
            "success": exit_code == 0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, indent=2)
        
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")
        return json_dumps({
            "error": f"执行命令失败: {str(e)}",
            "command": command
        })
    finally:
        if client:
            client.close()

@mcp.tool()
async def execute_parameterized_command(
    command_name: str,
    parameters: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> str:
    """执行参数化的安全命令。如 tail_file、ping_host 等。
    
    Args:
        command_name: 命令模板名称
        parameters: 命令参数字典
        timeout: 超时时间(秒)
    
    Returns:
        包含命令执行结果的JSON字符串
    """
    
    if parameters is None:
        parameters = {}
    
    # 构建命令
    is_valid, message, command = build_parameterized_command(command_name, parameters)
    
    if not is_valid:
        return json_dumps({
            "error": message,
            "available_commands": list(PARAMETERIZED_COMMANDS.keys())
        })
    
    client = None
    try:
        client = _create_ssh_client()
        
        logger.info(f"执行参数化命令: {command} ({message})")
        start_time = time.time()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        
        # 读取输出
        output = stdout.read().decode()
        error_output = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        execution_time = time.time() - start_time
        
        return json_dumps({
            "command_name": command_name,
            "command": command,
            "description": message,
            "parameters": parameters,
            "exit_code": exit_code,
            "execution_time_seconds": round(execution_time, 2),
            "stdout": output,
            "stderr": error_output,
            "success": exit_code == 0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, indent=2)
        
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")
        return json_dumps({
            "error": f"执行命令失败: {str(e)}",
            "command_name": command_name,
            "parameters": parameters
        })
    finally:
        if client:
            client.close()

@mcp.tool()
async def list_available_commands() -> str:
    """列出所有可用的SSH命令。
    
    Returns:
        可用命令的详细信息
    """
    
    return json_dumps(get_available_commands(), indent=2)

@mcp.tool()
async def execute_system_command(
    connection_name: str = "default",
    command: str = "",
    timeout: int = 300
) -> str:
    """[已废弃] 请使用 execute_command 或 execute_parameterized_command。
    
    - execute_command: 执行不限制参数的命令（ls、grep、ps等）
    - execute_parameterized_command: 执行参数化命令（tail_file、ping_host等）
    """
    
    return json_dumps({
        "error": "此函数已废弃",
        "suggestion": "请使用 execute_command 或 execute_parameterized_command",
        "help": "使用 list_available_commands 查看所有可用命令"
    })

if __name__ == "__main__":
    # 获取端口
    port = config.get('port', 3002)
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"SSH config: host={config.get('host')}, configs={len(config.get('configs', []))} users")
    
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)