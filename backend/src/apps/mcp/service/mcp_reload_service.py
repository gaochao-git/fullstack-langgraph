"""
MCP Gateway热更新服务
"""

import subprocess
import os
from src.shared.core.config import settings
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def reload_mcp_gateway() -> bool:
    """
    触发MCP Gateway重新加载配置
    
    通过读取PID文件并发送SIGHUP信号来触发重新加载。
    这需要MCP Gateway和后端服务在同一台机器上。
    
    Returns:
        bool: 是否成功触发
    """
    pid_file = settings.MCP_RELOAD_PID
    
    if not pid_file:
        logger.warning("未配置MCP_RELOAD_PID，热更新功能不可用")
        return False
    
    try:
        # 检查PID文件是否存在
        if not os.path.exists(pid_file):
            logger.error(f"PID文件不存在: {pid_file}")
            return False
            
        # 读取PID
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
            
        if not pid or not pid.isdigit():
            logger.error(f"PID文件内容无效: {pid}")
            return False
            
        logger.info(f"从PID文件读取到进程ID: {pid}")
        
        # 检查进程是否存在
        try:
            # 使用kill -0检查进程是否存在（不发送信号）
            subprocess.run(["kill", "-0", pid], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error(f"PID {pid} 对应的进程不存在")
            return False
        
        # 发送SIGHUP信号触发重新加载
        subprocess.run(["kill", "-HUP", pid], check=True)
        logger.info(f"成功向PID {pid} 发送SIGHUP信号，触发MCP Gateway重新加载")
        return True
        
    except FileNotFoundError:
        logger.error(f"PID文件不存在: {pid_file}")
        return False
    except PermissionError:
        logger.error(f"无权限读取PID文件或发送信号: {pid_file}")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"发送信号失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"热更新出错: {str(e)}")
        return False