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
    "tail",    # 查看文件末尾
    "ping",    # 网络连通性测试
    "uniq",    # 去除重复行
    "head",    # 查看文件开头
    "wc",      # 统计行数、字数等
    "sort",    # 排序文本
    "netstat", # 查看网络连接状态
}


def is_command_safe(command: str) -> Tuple[bool, str]:
    """检查命令是否安全 - 使用白名单机制"""
    # 先移除允许的安全重定向，避免误判
    safe_redirects = ['2>/dev/null']
    cleaned_command = command
    for safe_redirect in safe_redirects:
        cleaned_command = cleaned_command.replace(safe_redirect, '')

    # 检查基本的危险模式，即使命令在白名单中
    dangerous_patterns = [
        '&&', '||', ';', '\n', '\r',  # 命令链接
        '>', '>>', '<',                # 重定向（注意：安全的>/dev/null已被移除）
        '`', '$(',                     # 命令替换
        '..',                          # 目录遍历
        '/etc/passwd', '/etc/shadow',  # 敏感文件
    ]

    for pattern in dangerous_patterns:
        if pattern in cleaned_command:
            return False, f"命令包含危险模式: {pattern}"

    try:
        # 先按管道符分割原始命令
        pipe_segments = command.split('|')

        # 对每个管道段独立解析和检查
        for segment in pipe_segments:
            segment = segment.strip()
            if not segment:
                continue

            # 使用 shlex 解析这个管道段
            tokens = shlex.split(segment, posix=True)

            if not tokens:
                continue

            # 检查命令是否在白名单中
            cmd_name = tokens[0]
            if cmd_name not in UNRESTRICTED_COMMANDS:
                return False, f"命令 '{cmd_name}' 不在允许列表中"

    except ValueError as e:
        # shlex.split 失败通常是因为引号不匹配
        return False, f"命令语法错误：{str(e)}"

    return True, "命令安全检查通过"

