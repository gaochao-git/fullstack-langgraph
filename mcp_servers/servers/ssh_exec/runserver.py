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
        host: 目标主机IP或域名，必须提供
    """
    if host is None:
        raise Exception("必须指定目标主机host参数")

    port = config.get('ssh_port', 22)
    username = config.get('ssh_username')
    key_file = config.get('ssh_key_file')

    if not username:
        raise Exception("配置中缺少ssh_username")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 使用密钥认证
        if key_file:
            key_path = os.path.expanduser(key_file)
            if not os.path.exists(key_path):
                raise Exception(f"私钥文件不存在: {key_path}")

            key = paramiko.RSAKey.from_private_key_file(key_path)
            client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=key,
                timeout=10
            )
            logger.info(f"SSH密钥连接成功，主机: {host}, 用户: {username}, 密钥: {key_path}")
        else:
            raise Exception("配置中缺少ssh_key_file")

        return client

    except Exception as e:
        logger.error(f"SSH连接失败: {e}")
        raise Exception(f"无法建立SSH连接: {str(e)}")

@mcp.tool()
async def get_system_info(host: Optional[str] = None, timeout: int = 30) -> str:
    """获取系统基本信息。包括：主机名、内核版本、操作系统信息、运行时间、CPU型号、CPU核数、内存使用情况、磁盘使用情况、系统负载、登录用户

    Args:
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
        timeout: 命令执行超时时间（秒），默认30秒

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
    - netstat: 查看网络连接状态（可使用所有参数，如：-an, -tlnp, -s等）

    注意：查找文件请使用专门的 find_file 工具，该工具提供更安全的参数验证
    
    Args:
        command: 要在远程服务器上执行的命令
        host: 目标主机IP或域名（可选）。如果不提供，使用配置中的默认主机
        timeout: 超时时间(秒，默认30秒)
    
    Returns:
        包含命令执行结果的JSON字符串
    """
    
    if not command:
        return json_dumps({"error": "命令不能为空"})
    
    # 使用统一的安全检查（包含白名单和语法检查）
    is_safe, safety_msg = is_command_safe(command.strip())
    if not is_safe:
        return json_dumps({
            "error": safety_msg,
            "allowed_commands": list(UNRESTRICTED_COMMANDS)
        })
    
    
    # 额外的安全检查：命令长度限制
    if len(command) > 500:
        return json_dumps({"error": "命令过长，最多允许500个字符"})
    
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


@mcp.tool()
async def find_file(
    path: str = "/",
    name: Optional[str] = None,
    file_type: Optional[str] = None,
    size_mb: Optional[int] = None,
    size_operator: str = "+",
    mtime_days: Optional[int] = None,
    ctime_days: Optional[int] = None,
    limit: int = 100,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """安全的文件查找工具

    Args:
        path: 搜索路径，默认为根目录 /
        name: 文件名匹配模式（支持通配符，如 "*.log"）
        file_type: 文件类型，f=普通文件，d=目录
        size_mb: 文件大小（MB）
        size_operator: 大小运算符，+ 表示大于，- 表示小于，默认为 +
        mtime_days: 修改时间（天数），正数表示N天前，负数表示N天内
        ctime_days: 状态改变时间（天数）
        limit: 返回结果数量限制，默认100
        host: 目标主机IP或域名
        timeout: 命令执行超时时间（秒），默认30秒

    Returns:
        JSON格式的查找结果，包含文件路径、大小、修改时间等信息
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 构建安全的find命令
        find_parts = ["find", path]

        # 添加文件类型
        if file_type:
            if file_type not in ['f', 'd', 'l']:
                return json_dumps({
                    "error": "file_type必须是 f(文件)、d(目录) 或 l(链接) 之一"
                })
            find_parts.extend(["-type", file_type])

        # 添加文件名匹配
        if name:
            # 转义特殊字符，防止命令注入
            safe_name = name.replace("'", "'\\''")
            find_parts.extend(["-name", f"'{safe_name}'"])

        # 添加文件大小
        if size_mb is not None:
            if not isinstance(size_mb, int) or size_mb < 1:
                return json_dumps({
                    "error": "size_mb必须是大于0的整数"
                })
            if size_operator not in ['+', '-', '']:
                return json_dumps({
                    "error": "size_operator必须是 +（大于）、-（小于）或空（等于）"
                })
            find_parts.extend(["-size", f"{size_operator}{size_mb}M"])

        # 添加修改时间
        if mtime_days is not None:
            if not isinstance(mtime_days, int):
                return json_dumps({
                    "error": "mtime_days必须是整数"
                })
            find_parts.extend(["-mtime", str(mtime_days)])

        # 添加状态改变时间
        if ctime_days is not None:
            if not isinstance(ctime_days, int):
                return json_dumps({
                    "error": "ctime_days必须是整数"
                })
            find_parts.extend(["-ctime", str(ctime_days)])

        # 添加结果限制和详细信息显示
        find_parts.append("-printf")
        find_parts.append("'%p|%s|%TY-%Tm-%Td %TH:%TM|%u|%g\\n'")

        # 限制结果数量
        find_cmd = " ".join(find_parts) + f" 2>/dev/null | head -n {limit}"

        logger.info(f"执行查找命令: {find_cmd}")

        # 执行命令
        stdin, stdout, stderr = client.exec_command(find_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        # 解析结果
        files = []
        for line in output.strip().split('\n'):
            if not line:
                continue

            parts = line.split('|')
            if len(parts) == 5:
                file_path, size_bytes, mtime, owner, group = parts

                # 转换大小为人类可读格式
                size_bytes_int = int(size_bytes) if size_bytes.isdigit() else 0
                if size_bytes_int >= 1024 * 1024 * 1024:
                    size_human = f"{size_bytes_int / (1024**3):.2f}G"
                elif size_bytes_int >= 1024 * 1024:
                    size_human = f"{size_bytes_int / (1024**2):.2f}M"
                elif size_bytes_int >= 1024:
                    size_human = f"{size_bytes_int / 1024:.2f}K"
                else:
                    size_human = f"{size_bytes_int}B"

                files.append({
                    "path": file_path,
                    "size_bytes": size_bytes_int,
                    "size_human": size_human,
                    "modified_time": mtime,
                    "owner": owner,
                    "group": group
                })

        return json_dumps({
            "success": True,
            "search_path": path,
            "total_found": len(files),
            "limit": limit,
            "files": files
        }, indent=2)

    except Exception as e:
        logger.error(f"文件查找失败: {str(e)}")
        return json_dumps({
            "error": f"文件查找失败: {str(e)}"
        })
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    # 获取端口
    port = config.get('port', 3002)

    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"SSH config: username={config.get('ssh_username')}, key_file={config.get('ssh_key_file')}")

    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)