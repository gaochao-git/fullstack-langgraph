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
    "find",    # 查找文件
    "netstat", # 查看网络连接状态
}

# 限制参数的命令模板
PARAMETERIZED_COMMANDS = {}

# 验证器映射
VALIDATORS = {}


def _check_find_args(tokens: List[str]) -> Tuple[bool, str]:
    """检查find命令的参数是否安全
    
    Args:
        tokens: shlex解析后的命令tokens，tokens[0]是'find'
    
    Returns:
        (是否安全, 错误消息)
    """
    # find命令的安全参数白名单
    FIND_SAFE_PARAMS = {
        '-name',                     # 文件名匹配（最常用）
        '-type',                     # 文件类型 f/d
        '-mtime',                    # 修改时间
        '-atime',                    # 访问时间
        '-ctime',                    # 状态改变时间
        '-size',                     # 文件大小
        '-maxdepth',                 # 搜索深度限制
    }
    
    # 跳过'find'本身，从第二个token开始检查
    i = 1
    while i < len(tokens):
        token = tokens[i]
        
        # 检查是否是参数（以-开头）
        if token.startswith('-'):
            # 只允许白名单中的参数
            if token not in FIND_SAFE_PARAMS:
                return False, f"find命令包含未授权的参数: {token}"
        
        i += 1
    
    return True, "find命令参数检查通过"

def is_command_safe(command: str) -> Tuple[bool, str]:
    """检查命令是否安全 - 使用白名单机制"""
    # 检查基本的危险模式，即使命令在白名单中
    dangerous_patterns = [
        '&&', '||', ';', '\n', '\r',  # 命令链接
        '>', '>>', '<',                # 重定向  
        '`', '$(',                     # 命令替换
        '..',                          # 目录遍历
        '/etc/passwd', '/etc/shadow',  # 敏感文件
        '/root/', '~/',                # 敏感目录
        '2>/dev/null',                 # 错误重定向（常用于探测）
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command:
            return False, f"命令包含危险模式: {pattern}"
    
    try:
        # 使用 shlex 解析整个命令，确保语法正确
        tokens = shlex.split(command, posix=True)
        
        if not tokens:
            return False, "空命令"
        
        # 检查第一个命令是否在白名单中
        first_cmd = tokens[0]
        if first_cmd not in UNRESTRICTED_COMMANDS:
            return False, f"命令 '{first_cmd}' 不在允许列表中"
        
        # 如果是find命令，进行额外的参数检查
        if first_cmd == 'find':
            is_safe, msg = _check_find_args(tokens)
            if not is_safe:
                return False, msg
        
        # 如果包含管道，检查管道中的每个命令
        if '|' in tokens:
            # 找到所有管道符的位置
            pipe_indices = [i for i, token in enumerate(tokens) if token == '|']
            
            if pipe_indices:
                # 添加起始和结束索引
                indices = [0] + pipe_indices + [len(tokens)]
                
                # 检查每个管道段的第一个命令
                for i in range(len(indices) - 1):
                    start = indices[i]
                    if i > 0:
                        start += 1  # 跳过管道符本身
                    end = indices[i + 1]
                    
                    # 获取这个管道段的 tokens
                    segment_tokens = tokens[start:end]
                    
                    if segment_tokens:
                        # 第一个 token 就是命令名
                        cmd_name = segment_tokens[0]
                        
                        if cmd_name not in UNRESTRICTED_COMMANDS:
                            return False, f"管道命令 '{cmd_name}' 不在允许列表中"
                        
                        # 如果管道中的命令是find，也需要检查参数
                        if cmd_name == 'find':
                            is_safe, msg = _check_find_args(segment_tokens)
                            if not is_safe:
                                return False, msg
                            
    except ValueError as e:
        # shlex.split 失败通常是因为引号不匹配
        return False, f"命令语法错误：{str(e)}"
    
    return True, "命令安全检查通过"

