"""
公共端点
"""
from fastapi import APIRouter
from src.shared.core.config import settings
from src.shared.schemas.response import success_response, UnifiedResponse
from src.shared.schemas.config import SystemConfig, UploadConfig, FeatureFlags, UIConfig

router = APIRouter(tags=["Common"])


@router.get("/v1/config/system", response_model=UnifiedResponse)
async def get_system_config():
    """获取系统配置（公开接口）"""
    config = SystemConfig(
        upload=UploadConfig(
            max_upload_size_mb=settings.MAX_UPLOAD_SIZE_MB,
            allowed_extensions=settings.UPLOAD_ALLOWED_EXTENSIONS
        ),
        features=FeatureFlags(
            enable_sso=True,
            enable_cas=getattr(settings, 'CAS_SERVER_URL', None) is not None,
            enable_mcp=True,
            enable_scheduled_tasks=True
        ),
        ui=UIConfig(
            theme="light",
            app_title=settings.APP_NAME
        )
    )
    return success_response(data=config.model_dump(), msg="获取系统配置成功")