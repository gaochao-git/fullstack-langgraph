"""
MCP Gateway热更新服务
"""

import os
import httpx
import subprocess
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def reload_mcp_gateway() -> bool:
    """
    触发MCP Gateway重新加载配置
    
    支持两种方式：
    1. HTTP API方式（需要MCP Gateway配置NOTIFIER_TYPE=api）
    2. Signal方式（默认，通过SIGHUP信号）
    
    Returns:
        bool: 是否成功触发
    """
    # 检查是否配置了HTTP方式
    reload_url = os.getenv("MCP_RELOAD_URL") or os.getenv("APISERVER_NOTIFIER_API_TARGET_URL")
    
    # 如果配置了URL，尝试HTTP方式
    if reload_url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(reload_url, timeout=5.0)
                
                if response.status_code == 200:
                    logger.info(f"成功触发MCP Gateway热更新（HTTP）: {reload_url}")
                    return True
                else:
                    logger.warning(f"HTTP热更新失败: {response.status_code}，尝试使用信号方式")
                    
        except httpx.ConnectError:
            logger.warning(f"无法连接到 {reload_url}，尝试使用信号方式")
        except Exception as e:
            logger.warning(f"HTTP热更新出错: {str(e)}，尝试使用信号方式")
    
    # 尝试信号方式（默认方式）
    try:
        # 获取MCP Gateway的PID文件路径
        pid_file = os.getenv("MCP_GATEWAY_PID_FILE", "/var/run/mcp-gateway.pid")
        
        # 如果PID文件不存在，尝试通过进程名查找
        if not os.path.exists(pid_file):
            logger.info("PID文件不存在，尝试通过进程名查找")
            result = subprocess.run(
                ["pgrep", "-f", "mcp-gateway"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split()[0]
                logger.info(f"找到MCP Gateway进程，PID: {pid}")
                # 发送SIGHUP信号
                subprocess.run(["kill", "-HUP", pid], check=True)
                logger.info("成功发送SIGHUP信号触发热更新")
                return True
            else:
                logger.warning("未找到MCP Gateway进程")
                return False
        
        # 从PID文件读取PID
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        
        # 发送SIGHUP信号
        subprocess.run(["kill", "-HUP", pid], check=True)
        logger.info(f"成功向PID {pid} 发送SIGHUP信号触发热更新")
        return True
        
    except FileNotFoundError:
        logger.warning("未找到PID文件或kill命令")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"发送信号失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Signal热更新出错: {str(e)}")
        return False