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
    is_command_safe
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
    """获取系统基本信息。包括：主机名、内核版本、操作系统信息、运行时间、CPU型号、CPU核数、内存使用情况、磁盘使用情况、系统负载、登录用户
    
    Args:
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
    
    Returns:
        包含系统信息的JSON字符串，字段包括：
        - hostname: 主机名
        - kernel_version: 内核版本
        - os_info: 操作系统信息
        - uptime: 系统运行时间
        - cpu_model: CPU型号
        - cpu_cores: CPU核心数
        - memory_info: 内存使用情况（free -h输出）
        - disk_usage: 磁盘使用情况（df -h输出）
        - load_average: 系统负载（1分钟、5分钟、15分钟）
        - logged_users: 当前登录用户
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
async def execute_command(
    command: str = "",
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """在远程服务器上执行不限制参数的安全命令。支持的命令：
    - ls: 列出目录内容
    - ps: 查看进程状态
    - grep: 搜索文本内容
    - pgrep: 按名称查找进程
    - df: 查看磁盘空间使用情况
    - free: 查看内存使用情况
    - uptime: 查看系统运行时间和负载
    - tail: 查看文件末尾内容（注意：必须指定-n参数限制行数，如tail -n 100，避免实时监听导致卡住）
    - ping: 测试网络连通性（注意：必须使用-c参数限制次数，如ping -c 4，避免持续ping导致卡住）
    - uniq: 去除重复行，常用于管道命令中
    - head: 查看文件开头内容（注意：建议使用-n参数限制行数，如head -n 20）
    - wc: 统计行数、字数、字符数
    - sort: 对文本进行排序
    
    Args:
        command: 要在远程服务器上执行的命令
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
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
        client = _create_ssh_client(host)
        
        logger.info(f"执行命令: {command} on host: {host or 'default'}")
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


if __name__ == "__main__":
    # 获取端口
    port = config.get('port', 3002)
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"SSH config: host={config.get('host')}, configs={len(config.get('configs', []))} users")
    
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)