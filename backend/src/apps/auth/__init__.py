"""
认证模块
提供JWT和CAS两种认证方式
"""

from src.apps.auth.endpoints import router
from src.apps.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_optional,
    require_auth,
    require_roles,
    require_permissions,
    CurrentUser,
    CurrentActiveUser,
    OptionalUser,
    is_admin,
    is_user
)
from src.apps.auth.models import (
    AuthUser,
    AuthToken,
    AuthSession,
    AuthLoginHistory,
    AuthApiKey
)
from src.apps.auth.service import AuthService
from src.apps.auth.utils import (
    PasswordUtils,
    JWTUtils,
    MFAUtils,
    APIKeyUtils,
    TokenBlacklist
)

__all__ = [
    # Router
    "router",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_user_optional",
    "require_auth",
    "require_roles",
    "require_permissions",
    "CurrentUser",
    "CurrentActiveUser",
    "OptionalUser",
    "is_admin",
    "is_user",
    
    # Models
    "AuthUser",
    "AuthToken",
    "AuthSession",
    "AuthLoginHistory",
    "AuthApiKey",
    
    # Services
    "AuthService",
    
    # Utils
    "PasswordUtils",
    "JWTUtils",
    "MFAUtils",
    "APIKeyUtils",
    "TokenBlacklist",
]