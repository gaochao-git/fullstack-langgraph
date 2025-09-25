"""IDC Research package routers exports"""

from .reports_endpoints import router as reports_router
from .analysis_endpoints import router as analysis_router

__all__ = ["reports_router", "analysis_router"]

