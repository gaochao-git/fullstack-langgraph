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


@mcp.tool()
async def list_directory(
    path: str = "/tmp",
    show_hidden: bool = False,
    sort_by: str = "name",
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """列出目录内容（替代 ls 命令）

    Args:
        path: 目录路径，默认 /tmp
        show_hidden: 是否显示隐藏文件，默认 False
        sort_by: 排序方式，name=按名称, size=按大小, time=按修改时间，默认 name
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的目录内容列表
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if '..' in path or path.startswith('~'):
            return json_dumps({"error": "路径包含非法字符"})

        if sort_by not in ['name', 'size', 'time']:
            return json_dumps({"error": "sort_by 必须是 name, size 或 time"})

        # 构建安全的 ls 命令
        ls_cmd = "ls -l"
        if show_hidden:
            ls_cmd += "a"

        if sort_by == "size":
            ls_cmd += "S"
        elif sort_by == "time":
            ls_cmd += "t"

        # 添加路径（用引号包裹）
        safe_path = path.replace("'", "'\\''")
        ls_cmd += f" '{safe_path}'"

        logger.info(f"执行命令: {ls_cmd}")
        stdin, stdout, stderr = client.exec_command(ls_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        if error_output:
            return json_dumps({
                "success": False,
                "error": error_output,
                "path": path
            })

        return json_dumps({
            "success": True,
            "path": path,
            "output": output
        }, indent=2)

    except Exception as e:
        logger.error(f"列出目录失败: {str(e)}")
        return json_dumps({"error": f"列出目录失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def list_processes(
    filter_user: Optional[str] = None,
    filter_name: Optional[str] = None,
    show_all: bool = True,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """列出系统进程（替代 ps 命令）

    Args:
        filter_user: 按用户名过滤，可选
        filter_name: 按进程名过滤（支持部分匹配），可选
        show_all: 是否显示所有进程，默认 True
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的进程列表
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 构建安全的 ps 命令
        ps_cmd = "ps aux" if show_all else "ps -u $(whoami)"

        # 添加过滤
        if filter_user:
            # 验证用户名（只允许字母数字下划线）
            if not filter_user.replace('_', '').replace('-', '').isalnum():
                return json_dumps({"error": "用户名包含非法字符"})
            ps_cmd += f" | grep '^{filter_user}'"

        if filter_name:
            # 转义特殊字符
            safe_name = filter_name.replace("'", "'\\''")
            ps_cmd += f" | grep '{safe_name}'"

        logger.info(f"执行命令: {ps_cmd}")
        stdin, stdout, stderr = client.exec_command(ps_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        return json_dumps({
            "success": True,
            "filter_user": filter_user,
            "filter_name": filter_name,
            "output": output
        }, indent=2)

    except Exception as e:
        logger.error(f"列出进程失败: {str(e)}")
        return json_dumps({"error": f"列出进程失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def read_file_tail(
    file_path: str,
    lines: int = 100,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """读取文件末尾内容（替代 tail 命令）

    Args:
        file_path: 文件路径
        lines: 显示行数，默认100行，最大1000行
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的文件内容
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if '..' in file_path or file_path.startswith('~'):
            return json_dumps({"error": "文件路径包含非法字符"})

        if not isinstance(lines, int) or lines < 1 or lines > 1000:
            return json_dumps({"error": "lines 必须是 1-1000 之间的整数"})

        # 构建安全的 tail 命令
        safe_path = file_path.replace("'", "'\\''")
        tail_cmd = f"tail -n {lines} '{safe_path}'"

        logger.info(f"执行命令: {tail_cmd}")
        stdin, stdout, stderr = client.exec_command(tail_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        if error_output:
            return json_dumps({
                "success": False,
                "error": error_output,
                "file_path": file_path
            })

        return json_dumps({
            "success": True,
            "file_path": file_path,
            "lines_requested": lines,
            "content": output
        }, indent=2)

    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        return json_dumps({"error": f"读取文件失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def read_file_head(
    file_path: str,
    lines: int = 100,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """读取文件开头内容（替代 head 命令）

    Args:
        file_path: 文件路径
        lines: 显示行数，默认100行，最大1000行
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的文件内容
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if '..' in file_path or file_path.startswith('~'):
            return json_dumps({"error": "文件路径包含非法字符"})

        if not isinstance(lines, int) or lines < 1 or lines > 1000:
            return json_dumps({"error": "lines 必须是 1-1000 之间的整数"})

        # 构建安全的 head 命令
        safe_path = file_path.replace("'", "'\\''")
        head_cmd = f"head -n {lines} '{safe_path}'"

        logger.info(f"执行命令: {head_cmd}")
        stdin, stdout, stderr = client.exec_command(head_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        if error_output:
            return json_dumps({
                "success": False,
                "error": error_output,
                "file_path": file_path
            })

        return json_dumps({
            "success": True,
            "file_path": file_path,
            "lines_requested": lines,
            "content": output
        }, indent=2)

    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        return json_dumps({"error": f"读取文件失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def search_file_content(
    file_path: str,
    pattern: str,
    max_lines: int = 100,
    context_lines: int = 0,
    case_sensitive: bool = True,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """在文件中搜索内容（替代 grep 命令）

    Args:
        file_path: 文件路径
        pattern: 搜索模式（支持正则表达式）
        max_lines: 最大返回行数，默认100行
        context_lines: 上下文行数，0=不显示上下文，默认0
        case_sensitive: 是否区分大小写，默认 True
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的搜索结果
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if '..' in file_path or file_path.startswith('~'):
            return json_dumps({"error": "文件路径包含非法字符"})

        if not isinstance(max_lines, int) or max_lines < 1 or max_lines > 1000:
            return json_dumps({"error": "max_lines 必须是 1-1000 之间的整数"})

        if not isinstance(context_lines, int) or context_lines < 0 or context_lines > 10:
            return json_dumps({"error": "context_lines 必须是 0-10 之间的整数"})

        # 构建安全的 grep 命令
        safe_path = file_path.replace("'", "'\\''")
        safe_pattern = pattern.replace("'", "'\\''")

        grep_cmd = "grep"
        if not case_sensitive:
            grep_cmd += " -i"
        if context_lines > 0:
            grep_cmd += f" -C {context_lines}"

        grep_cmd += f" '{safe_pattern}' '{safe_path}' | head -n {max_lines}"

        logger.info(f"执行命令: {grep_cmd}")
        stdin, stdout, stderr = client.exec_command(grep_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        # grep 未找到匹配时 exit_code 是 1，不算错误
        return json_dumps({
            "success": True,
            "file_path": file_path,
            "pattern": pattern,
            "matches": output,
            "match_count": len(output.strip().split('\n')) if output.strip() else 0
        }, indent=2)

    except Exception as e:
        logger.error(f"搜索文件失败: {str(e)}")
        return json_dumps({"error": f"搜索文件失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def get_disk_usage(
    mount_point: Optional[str] = None,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """获取磁盘使用情况（替代 df 命令）

    Args:
        mount_point: 挂载点路径，可选。不指定则显示所有挂载点
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的磁盘使用情况
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 构建安全的 df 命令
        df_cmd = "df -h"

        if mount_point:
            # 参数验证
            if '..' in mount_point or mount_point.startswith('~'):
                return json_dumps({"error": "挂载点路径包含非法字符"})
            safe_path = mount_point.replace("'", "'\\''")
            df_cmd += f" '{safe_path}'"

        logger.info(f"执行命令: {df_cmd}")
        stdin, stdout, stderr = client.exec_command(df_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        if error_output:
            return json_dumps({
                "success": False,
                "error": error_output
            })

        return json_dumps({
            "success": True,
            "mount_point": mount_point,
            "output": output
        }, indent=2)

    except Exception as e:
        logger.error(f"获取磁盘使用情况失败: {str(e)}")
        return json_dumps({"error": f"获取磁盘使用情况失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def list_network_connections(
    protocol: Optional[str] = None,
    state: Optional[str] = None,
    listening_only: bool = False,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """列出网络连接（替代 netstat 命令）

    Args:
        protocol: 协议过滤，tcp/udp，可选
        state: 连接状态过滤，如 ESTABLISHED/LISTEN/TIME_WAIT，可选
        listening_only: 是否仅显示监听端口，默认 False
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的网络连接列表
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if protocol and protocol not in ['tcp', 'udp', 'tcp4', 'tcp6', 'udp4', 'udp6']:
            return json_dumps({"error": "protocol 必须是 tcp, udp, tcp4, tcp6, udp4 或 udp6"})

        valid_states = ['ESTABLISHED', 'LISTEN', 'TIME_WAIT', 'CLOSE_WAIT', 'SYN_SENT', 'SYN_RECV']
        if state and state not in valid_states:
            return json_dumps({"error": f"state 必须是以下之一: {', '.join(valid_states)}"})

        # 构建安全的 netstat 命令
        netstat_cmd = "netstat -an"

        if protocol:
            if protocol == 'tcp':
                netstat_cmd += " | grep tcp"
            elif protocol == 'udp':
                netstat_cmd += " | grep udp"
            else:
                netstat_cmd += f" | grep {protocol}"

        if listening_only:
            netstat_cmd += " | grep LISTEN"
        elif state:
            netstat_cmd += f" | grep {state}"

        logger.info(f"执行命令: {netstat_cmd}")
        stdin, stdout, stderr = client.exec_command(netstat_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        return json_dumps({
            "success": True,
            "protocol": protocol,
            "state": state,
            "listening_only": listening_only,
            "output": output
        }, indent=2)

    except Exception as e:
        logger.error(f"列出网络连接失败: {str(e)}")
        return json_dumps({"error": f"列出网络连接失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def ping_host(
    target: str,
    count: int = 4,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """测试网络连通性（替代 ping 命令）

    Args:
        target: 目标主机IP或域名
        count: ping次数，默认4次，最大10次
        host: 执行ping的源主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的ping结果
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if not isinstance(count, int) or count < 1 or count > 10:
            return json_dumps({"error": "count 必须是 1-10 之间的整数"})

        # 简单验证目标主机格式（防止命令注入）
        if any(c in target for c in [';', '&', '|', '`', '$', '>', '<', '\n']):
            return json_dumps({"error": "目标主机包含非法字符"})

        # 构建安全的 ping 命令
        safe_target = target.replace("'", "'\\''")
        ping_cmd = f"ping -c {count} '{safe_target}'"

        logger.info(f"执行命令: {ping_cmd}")
        stdin, stdout, stderr = client.exec_command(ping_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        return json_dumps({
            "success": True,
            "target": target,
            "count": count,
            "output": output,
            "error": error_output if error_output else None
        }, indent=2)

    except Exception as e:
        logger.error(f"Ping失败: {str(e)}")
        return json_dumps({"error": f"Ping失败: {str(e)}"})
    finally:
        if client:
            client.close()


@mcp.tool()
async def resource_top_n(
    resource_type: str = "cpu",
    top_n: int = 10,
    host: Optional[str] = None,
    timeout: int = 30
) -> str:
    """查看资源占用 TOP N

    Args:
        resource_type: 资源类型
            - cpu: CPU占用
            - mem: 内存占用
            - net: 网络流量（所有网卡）
        top_n: 返回前N个结果，默认10，范围1-100
        host: 目标主机IP或域名
        timeout: 超时时间（秒），默认30秒

    Returns:
        JSON格式的 TOP N 列表，包含详细的资源占用信息
    """
    client = None
    try:
        client = _create_ssh_client(host)

        # 参数验证
        if resource_type not in ['cpu', 'mem', 'net']:
            return json_dumps({
                "error": "resource_type 必须是 cpu, mem 或 net"
            })

        if not isinstance(top_n, int) or top_n < 1 or top_n > 100:
            return json_dumps({
                "error": "top_n 必须是 1-100 之间的整数"
            })

        # 构建命令
        if resource_type == "cpu":
            # 按CPU排序
            ps_cmd = f"ps aux | head -1 && ps aux | sort -k3 -rn | head -n {top_n}"
            sort_column = "CPU"
            return_type = "processes"

        elif resource_type == "mem":
            # 按内存排序
            ps_cmd = f"ps aux | head -1 && ps aux | sort -k4 -rn | head -n {top_n}"
            sort_column = "MEM"
            return_type = "processes"

        else:  # net
            # 网络流量统计（所有网卡）
            # 方案：采样两次 /proc/net/dev，计算差值得到流量速率
            net_cmd = """
# 第一次采样
cat /proc/net/dev > /tmp/net_stat1_$$
sleep 2
# 第二次采样
cat /proc/net/dev > /tmp/net_stat2_$$

# 计算差值并统计
awk '
BEGIN { FS="[: ]+" }
NR==FNR {
    if (NF >= 10 && $1 != "Inter" && $1 != "face") {
        iface = $2;
        rx1[iface] = $3;  # 接收字节
        tx1[iface] = $11; # 发送字节
    }
    next;
}
{
    if (NF >= 10 && $1 != "Inter" && $1 != "face") {
        iface = $2;
        rx2 = $3;
        tx2 = $11;
        if (iface in rx1) {
            rx_rate = (rx2 - rx1[iface]) / 2;  # 除以2秒
            tx_rate = (tx2 - tx1[iface]) / 2;
            total_rate = rx_rate + tx_rate;

            # 转换为人类可读格式
            if (total_rate > 1024*1024*1024) {
                rate_str = sprintf("%.2f GB/s", total_rate/1024/1024/1024);
            } else if (total_rate > 1024*1024) {
                rate_str = sprintf("%.2f MB/s", total_rate/1024/1024);
            } else if (total_rate > 1024) {
                rate_str = sprintf("%.2f KB/s", total_rate/1024);
            } else {
                rate_str = sprintf("%.0f B/s", total_rate);
            }

            if (rx_rate > 1024*1024) {
                rx_str = sprintf("%.2f MB/s", rx_rate/1024/1024);
            } else if (rx_rate > 1024) {
                rx_str = sprintf("%.2f KB/s", rx_rate/1024);
            } else {
                rx_str = sprintf("%.0f B/s", rx_rate);
            }

            if (tx_rate > 1024*1024) {
                tx_str = sprintf("%.2f MB/s", tx_rate/1024/1024);
            } else if (tx_rate > 1024) {
                tx_str = sprintf("%.2f KB/s", tx_rate/1024);
            } else {
                tx_str = sprintf("%.0f B/s", tx_rate);
            }

            if (total_rate > 0) {
                print iface "|" rx_str "|" tx_str "|" rate_str "|" total_rate;
            }
        }
    }
}
' /tmp/net_stat1_$$ /tmp/net_stat2_$$ | sort -t'|' -k5 -rn | head -n {top_n}

# 清理临时文件
rm -f /tmp/net_stat1_$$ /tmp/net_stat2_$$
"""
            ps_cmd = net_cmd.strip()
            sort_column = "Network Traffic"
            return_type = "network"

        logger.info(f"执行命令: {ps_cmd}")
        stdin, stdout, stderr = client.exec_command(ps_cmd, timeout=timeout)
        output = stdout.read().decode()
        error_output = stderr.read().decode()

        if error_output and resource_type != "net":
            return json_dumps({
                "success": False,
                "error": error_output
            })

        # 根据类型解析输出
        if return_type == "processes":
            # 解析 ps aux 输出
            lines = output.strip().split('\n')
            if len(lines) < 2:
                return json_dumps({
                    "success": False,
                    "error": "无法获取进程信息"
                })

            header = lines[0]
            processes = []

            for line in lines[1:]:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    processes.append({
                        "user": parts[0],
                        "pid": parts[1],
                        "cpu_percent": parts[2],
                        "mem_percent": parts[3],
                        "vsz_kb": parts[4],
                        "rss_kb": parts[5],
                        "tty": parts[6],
                        "stat": parts[7],
                        "start": parts[8],
                        "time": parts[9],
                        "command": parts[10]
                    })

            return json_dumps({
                "success": True,
                "resource_type": resource_type,
                "sort_by": sort_column,
                "top_n": top_n,
                "total_processes": len(processes),
                "header": header,
                "processes": processes
            }, indent=2)

        else:  # network
            # 解析网络流量输出（格式：interface|rx_rate|tx_rate|total_rate|total_bytes）
            lines = output.strip().split('\n')
            traffic_data = []

            for line in lines:
                if not line.strip():
                    continue
                parts = line.split('|')
                if len(parts) == 5:
                    traffic_data.append({
                        "interface": parts[0],       # 网卡名称
                        "rx_rate": parts[1],         # 接收速率（下载）
                        "tx_rate": parts[2],         # 发送速率（上传）
                        "total_rate": parts[3],      # 总速率
                        "total_bytes_per_sec": float(parts[4])  # 用于排序
                    })

            # 如果没有流量数据
            if not traffic_data:
                return json_dumps({
                    "success": True,
                    "resource_type": resource_type,
                    "top_n": top_n,
                    "message": "当前所有网卡流量为0或无活跃网卡",
                    "traffic": []
                }, indent=2)

            return json_dumps({
                "success": True,
                "resource_type": resource_type,
                "sort_by": "Network Traffic (All Interfaces)",
                "top_n": top_n,
                "total_interfaces": len(traffic_data),
                "description": "所有网卡流量统计（2秒采样）",
                "note": "rx=接收(下载), tx=发送(上传), total=总流量",
                "traffic": [
                    {
                        "interface": item["interface"],
                        "rx_rate": item["rx_rate"],
                        "tx_rate": item["tx_rate"],
                        "total_rate": item["total_rate"]
                    } for item in traffic_data
                ]
            }, indent=2)

    except Exception as e:
        logger.error(f"获取资源TOP N失败: {str(e)}")
        return json_dumps({
            "error": f"获取资源TOP N失败: {str(e)}"
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