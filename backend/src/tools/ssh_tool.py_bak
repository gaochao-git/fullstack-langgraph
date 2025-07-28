"""
SSH工具 - 使用LangChain工具框架
"""

import paramiko
import json
import time
from typing import Dict, Any, List, Optional
import logging
from langchain.tools import tool
from pydantic import BaseModel, Field
from io import StringIO

logger = logging.getLogger(__name__)

def _create_ssh_client():
    """创建新的SSH连接，每次调用都重新连接"""
    # 默认连接参数，按优先级排序
    default_configs = [
        {"hostname": "82.156.146.51", "username": "root", "password": "123456"},
        {"hostname": "82.156.146.51", "username": "gaochao", "password": "fffjjj"},
        {"hostname": "82.156.146.51", "username": "admin", "password": "admin"}
    ]
    
    for config in default_configs:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=config["hostname"],
                port=22,
                username=config["username"],
                password=config["password"],
                timeout=10
            )
            
            logger.info(f"SSH连接成功，用户: {config['username']}")
            return client
            
        except Exception as e:
            logger.debug(f"尝试用户 {config['username']} 失败: {e}")
            continue
    
    raise Exception("无法建立SSH连接，请检查网络和服务器状态")

class SystemInfoInput(BaseModel):
    """系统信息查询输入参数"""
    connection_name: str = Field(default="default", description="SSH连接名称")

@tool("get_system_info", args_schema=SystemInfoInput)
def get_system_info(connection_name: str = "default") -> str:
    """获取系统基本信息。用于了解服务器的硬件配置和运行状态。
    
    Args:
        connection_name: SSH连接名称（此参数保留兼容性，实际会创建新连接）
    
    Returns:
        包含系统信息的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client()
        
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
        
        return json.dumps(parsed_info, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return json.dumps({"error": f"Failed to get system info: {str(e)}"})
    finally:
        if client:
            client.close()

class ProcessAnalysisInput(BaseModel):
    """进程分析输入参数"""
    connection_name: str = Field(default="default", description="SSH连接名称")
    process_name: Optional[str] = Field(default=None, description="进程名称筛选")
    sort_by: str = Field(default="cpu", description="排序方式：cpu, memory, pid")

@tool("analyze_processes", args_schema=ProcessAnalysisInput)
def analyze_processes(
    connection_name: str = "default",
    process_name: Optional[str] = None,
    sort_by: str = "cpu"
) -> str:
    """分析系统进程。用于查看系统中运行的进程和资源使用情况。
    
    Args:
        connection_name: SSH连接名称（此参数保留兼容性，实际会创建新连接）
        process_name: 进程名称筛选
        sort_by: 排序方式(cpu, memory, pid)
    
    Returns:
        包含进程分析结果的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client()
        
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
        
        client.close()
        
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
        
        return json.dumps({
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
        return json.dumps({"error": f"Failed to analyze processes: {str(e)}"})
    finally:
        if client:
            client.close()

class ServiceStatusInput(BaseModel):
    """服务状态查询输入参数"""
    connection_name: str = Field(default="default", description="SSH连接名称")
    service_names: Optional[List[str]] = Field(default=None, description="服务名称列表")

@tool("check_service_status", args_schema=ServiceStatusInput)
def check_service_status(
    connection_name: str = "default",
    service_names: Optional[List[str]] = None
) -> str:
    """检查系统服务状态。用于查看关键服务的运行状态。
    
    Args:
        connection_name: SSH连接名称
        service_names: 要检查的服务名称列表
    
    Returns:
        包含服务状态的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client()
        
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
        
        return json.dumps(service_status, indent=2)
        
    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return json.dumps({"error": f"Failed to check service status: {str(e)}"})
    finally:
        if client:
            client.close()

class LogAnalysisInput(BaseModel):
    """日志分析输入参数"""
    connection_name: str = Field(default="default", description="SSH连接名称")
    log_file: str = Field(description="日志文件路径")
    lines: int = Field(default=100, description="读取行数")
    pattern: Optional[str] = Field(default=None, description="搜索模式")

@tool("analyze_system_logs", args_schema=LogAnalysisInput)
def analyze_system_logs(
    connection_name: str = "default",
    log_file: str = "/var/log/syslog",
    lines: int = 100,
    pattern: Optional[str] = None
) -> str:
    """分析系统日志。用于查看系统日志中的错误和异常信息。
    
    Args:
        connection_name: SSH连接名称
        log_file: 日志文件路径
        lines: 读取的行数
        pattern: 搜索模式（grep模式）
    
    Returns:
        包含日志分析结果的JSON字符串
    """
    client = None
    try:
        client = _create_ssh_client()
        
        # 检查日志文件是否存在
        stdin, stdout, stderr = client.exec_command(f"test -f {log_file} && echo 'exists' || echo 'not found'")
        file_check = stdout.read().decode().strip()
        
        if file_check != 'exists':
            return json.dumps({"error": f"Log file {log_file} not found"})
        
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
        
        return json.dumps({
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
        return json.dumps({"error": f"Failed to analyze system logs: {str(e)}"})
    finally:
        if client:
            client.close()

class CommandExecutionInput(BaseModel):
    """命令执行输入参数"""
    connection_name: str = Field(default="default", description="SSH连接名称")
    command: str = Field(description="要执行的命令")
    timeout: int = Field(default=300, description="超时时间(秒)")

@tool("execute_system_command", args_schema=CommandExecutionInput)
def execute_system_command(
    connection_name: str = "default",
    command: str = "",
    timeout: int = 300
) -> str:
    """执行系统命令。用于执行系统诊断和维护命令。
    
    Args:
        connection_name: SSH连接名称
        command: 要执行的命令
        timeout: 超时时间(秒，默认5分钟)
    
    Returns:
        包含命令执行结果的JSON字符串
    """
    
    # 安全检查：限制危险命令
    dangerous_commands = [
        'rm -rf', 'mkfs', 'dd if=', 'fdisk', 'parted',
        'shutdown', 'reboot', 'init 0', 'init 6',
        'passwd', 'userdel', 'groupdel',
        '>', '>>', 'format', 'del /f'
    ]
    
    command_lower = command.lower()
    for dangerous in dangerous_commands:
        if dangerous in command_lower:
            return json.dumps({
                "error": f"Command contains dangerous operation: {dangerous}. Command blocked for security."
            })
    
    client = None
    try:
        client = _create_ssh_client()
        
        logger.info(f"开始执行命令: {command} (超时: {timeout}秒)")
        start_time = time.time()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        
        # 读取输出
        output = stdout.read().decode()
        error_output = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        execution_time = time.time() - start_time
        
        # 记录执行结果
        if exit_code == 0:
            logger.info(f"命令执行成功: {command} (耗时: {execution_time:.2f}秒)")
        else:
            logger.warning(f"命令执行失败: {command}, 退出码: {exit_code}, 耗时: {execution_time:.2f}秒")
            if error_output:
                logger.warning(f"错误输出: {error_output[:200]}...")  # 只记录前200字符
        
        return json.dumps({
            "command": command,
            "exit_code": exit_code,
            "execution_time_seconds": round(execution_time, 2),
            "timeout_used": timeout,
            "stdout": output,
            "stderr": error_output,
            "success": exit_code == 0,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, indent=2)
        
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"执行命令 '{command}' 时发生 {error_type}: {str(e)}")
        return json.dumps({
            "error": f"Failed to execute command: {str(e)}",
            "error_type": error_type,
            "command": command,
            "timeout_used": timeout
        })
    finally:
        if client:
            try:
                client.close()
                logger.debug("SSH连接已关闭")
            except Exception as e:
                logger.warning(f"关闭SSH连接时出错: {e}")

# 导出所有工具
ssh_tools = [
    get_system_info,
    analyze_processes,
    check_service_status,
    analyze_system_logs,
    execute_system_command
]
