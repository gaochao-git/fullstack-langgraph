"""
业务服务层
处理业务逻辑，协调多个DAO操作
"""

from .sop_service import SOPService
from .agent_service import AgentService
from .agent_config_service import AgentConfigService

# 导入其他服务以保持向后兼容
try:
    from .base_service import BaseService
    from .mcp_service import MCPService
    from .user_service import UserService
except ImportError:
    # 如果旧服务不存在，定义空类以避免导入错误
    BaseService = None
    MCPService = None
    UserService = None

__all__ = [
    'SOPService',
    'AgentService',
    'AgentConfigService',
    # 向后兼容
    'BaseService',
    'MCPService', 
    'UserService'
]