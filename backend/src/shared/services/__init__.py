"""
共享服务层
只保留跨模块的通用服务
具体业务服务已迁移到各自的业务模块中
"""

from .user_service import UserService, UserThreadService

# 导入基础服务以保持向后兼容
try:
    from .base_service import BaseService
except ImportError:
    BaseService = None

__all__ = [
    'UserService',
    'UserThreadService', 
    # 向后兼容
    'BaseService'
]

# 注意：以下服务已迁移到各自的业务模块
# - SOPService -> src.apps.sop.service
# - AgentService -> src.apps.agent.service  
# - AgentConfigService -> src.apps.agent.service
# - MCPService -> src.apps.mcp.service