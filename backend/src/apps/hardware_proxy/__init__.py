"""
硬件资源管理API代理端点
通过主项目后端转发到独立的硬件资源管理服务
"""

import asyncio
import json
import os
import time
from typing import Dict, Optional

from fastapi import APIRouter, Request, Response, Depends, HTTPException
from httpx import AsyncClient, ConnectError, TimeoutException
from src.apps.auth.dependencies import get_current_user
from src.shared.core.logging import get_logger

logger = get_logger(__name__)
# All routers included in `api_router` are mounted under `/api` globally
# (see `backend/src/main.py#L114`). Using a prefix that already contains
# `/api` would therefore create paths like `/api/api/...` and break routing.
router = APIRouter(prefix="/v1/hardware-proxy", tags=["Hardware Resource Proxy"])

# 配置目标服务地址
HARDWARE_SERVICE_BASE_URL = os.getenv("HARDWARE_SERVICE_BASE_URL", "http://127.0.0.1:8888")
TIMEOUT = 30.0  # 请求超时时间

# 硬件服务的认证令牌（实际应该从配置文件或环境变量读取）
# 可通过环境变量配置静态令牌或用户名密码，实现自动登录
HARDWARE_SERVICE_TOKEN = os.getenv("HARDWARE_SERVICE_TOKEN", "").strip()
HARDWARE_SERVICE_USERNAME = os.getenv("HARDWARE_SERVICE_USERNAME", "").strip()
HARDWARE_SERVICE_PASSWORD = os.getenv("HARDWARE_SERVICE_PASSWORD", "").strip()
HARDWARE_SERVICE_LOGIN_ENDPOINT = os.getenv("HARDWARE_SERVICE_LOGIN_ENDPOINT", "/api/auth/login")
TOKEN_REFRESH_MARGIN = int(os.getenv("HARDWARE_SERVICE_TOKEN_REFRESH_MARGIN", "120"))

# 如果既没有配置令牌，也没有配置自动登录凭证，则回退到默认测试令牌（仅限本地测试）
if not HARDWARE_SERVICE_TOKEN and not (HARDWARE_SERVICE_USERNAME and HARDWARE_SERVICE_PASSWORD):
    HARDWARE_SERVICE_TOKEN = (
        #"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZGlzcGxheV9uYW1lIjoi57O757uf566h55CG5ZGYIiwiaXNfYWRtaW4iOnRydWUsImxvZ2luX3NvdXJjZSI6ImxvY2FsIiwiZXhwIjoxNzU5MjI0NjYwLCJuYmYiOjE3NTkxMzgyNjAsImlhdCI6MTc1OTEzODI2MH0.imZFjC0a7G6UBh6r3Pybv2OF1aK-HUWuhIC35odt2zw"
    )
    logger.warning("使用默认的硬件服务令牌，请设置 HARDWARE_SERVICE_TOKEN 或自动登录凭证")

# 创建共享的 HTTP 客户端
client = AsyncClient(base_url=HARDWARE_SERVICE_BASE_URL, timeout=TIMEOUT)

# 缓存自动登录获取的令牌，避免重复登录
_token_state: Dict[str, Optional[int]] = {
    "token": HARDWARE_SERVICE_TOKEN or None,
    "expires_at": None,
}
_token_lock = asyncio.Lock()


def _token_is_valid() -> bool:
    token = _token_state.get("token")
    if not token or TOKEN_REFRESH_MARGIN < 0:
        return bool(token)

    expires_at = _token_state.get("expires_at")
    if not expires_at:
        return True

    current_ts = int(time.time())
    return current_ts < (expires_at - TOKEN_REFRESH_MARGIN)


async def _login_hardware_service(force_refresh: bool = False) -> Optional[str]:
    """通过用户名密码登录硬件服务并缓存令牌。"""
    if HARDWARE_SERVICE_TOKEN and not force_refresh:
        return HARDWARE_SERVICE_TOKEN

    if not (HARDWARE_SERVICE_USERNAME and HARDWARE_SERVICE_PASSWORD):
        logger.error(
            "未配置硬件服务认证信息，请设置 HARDWARE_SERVICE_TOKEN 或 HARDWARE_SERVICE_USERNAME/HARDWARE_SERVICE_PASSWORD"
        )
        raise HTTPException(
            status_code=500,
            detail="Hardware service credentials are not configured",
        )

    if _token_is_valid() and not force_refresh:
        return _token_state.get("token")

    async with _token_lock:
        # 双重检查，避免并发重复登录
        if _token_is_valid() and not force_refresh:
            return _token_state.get("token")

        logger.info("尝试登录硬件服务以获取令牌")
        login_payload = {
            "username": HARDWARE_SERVICE_USERNAME,
            "password": HARDWARE_SERVICE_PASSWORD,
        }

        login_response = await client.post(
            HARDWARE_SERVICE_LOGIN_ENDPOINT,
            json=login_payload,
        )

        if login_response.status_code != 200:
            logger.error(
                "硬件服务登录失败，状态码 %s，响应：%s",
                login_response.status_code,
                await login_response.aread(),
            )
            raise HTTPException(
                status_code=502,
                detail="Failed to authenticate with hardware service",
            )

        try:
            payload = login_response.json()
        except ValueError as exc:
            logger.error("解析硬件服务登录响应失败: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="Hardware service login response is invalid",
            ) from exc

        token_info = payload.get("data") or {}
        token = token_info.get("token")
        if not token:
            logger.error("硬件服务登录响应缺少 token 字段: %s", payload)
            raise HTTPException(
                status_code=502,
                detail="Hardware service login did not return a token",
            )

        expires_at_raw = token_info.get("expires_at")
        expires_at: Optional[int]
        if isinstance(expires_at_raw, (int, float)):
            expires_at = int(expires_at_raw)
        elif isinstance(expires_at_raw, str) and expires_at_raw.isdigit():
            expires_at = int(expires_at_raw)
        else:
            expires_at = None

        _token_state["token"] = token
        _token_state["expires_at"] = expires_at

        logger.info("硬件服务登录成功，令牌已缓存%s", f"，有效期至 {expires_at}" if expires_at else "")
        return token


async def _get_authorization_header(force_refresh: bool = False) -> Optional[str]:
    token = await _login_hardware_service(force_refresh=force_refresh)
    if not token:
        return None
    return f"Bearer {token}"


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_hardware_api(
    path: str,
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    """
    代理转发硬件资源管理API请求

    1. 验证用户身份（通过主项目认证）
    2. 转发请求到硬件资源管理服务
    3. 可选：添加内部认证令牌
    """
    try:
        # 记录请求信息
        logger.info(f"Proxying request: {request.method} /{path}")
        logger.debug(f"Query params: {dict(request.query_params)}")

        # 获取原始请求数据
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    body = json.loads(body_bytes)
                except json.JSONDecodeError:
                    body = body_bytes.decode('utf-8')

        # 构建请求头，可以添加内部认证
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)
        headers.pop("authorization", None)

        # 添加硬件服务的认证令牌（支持自动登录）
        auth_header = await _get_authorization_header()
        if auth_header:
            headers["Authorization"] = auth_header

        # 传递用户信息给下游服务（可选）
        headers["X-User-Id"] = str(current_user.get("user_id", ""))
        headers["X-User-Name"] = current_user.get("username", "")
        headers["X-User-Roles"] = json.dumps(current_user.get("roles", []))

        # 转发请求到硬件服务
        # 添加 /api 前缀，因为硬件服务的API都在 /api 路径下
        target_path = f"/api/{path}" if not path.startswith("api/") else f"/{path}"

        logger.info(f"Forwarding to hardware service: {HARDWARE_SERVICE_BASE_URL}{target_path}")

        async def forward_request():
            return await client.request(
                method=request.method,
                url=target_path,
                params=dict(request.query_params),
                json=body if isinstance(body, dict) else None,
                content=body if isinstance(body, (str, bytes)) else None,
                headers=headers,
            )

        hardware_response = await forward_request()

        # 如果令牌失效，尝试刷新后重试一次
        if (
            hardware_response.status_code == 401
            and not HARDWARE_SERVICE_TOKEN
            and HARDWARE_SERVICE_USERNAME
            and HARDWARE_SERVICE_PASSWORD
        ):
            logger.info("硬件服务返回401，尝试刷新令牌并重试一次")
            refreshed_header = await _get_authorization_header(force_refresh=True)
            if refreshed_header:
                headers["Authorization"] = refreshed_header
                hardware_response = await forward_request()

        # 复制响应状态码
        response.status_code = hardware_response.status_code

        # 复制响应头
        for key, value in hardware_response.headers.items():
            if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]:
                response.headers[key] = value

        # 返回响应内容
        try:
            return hardware_response.json()
        except:
            return hardware_response.text

    except ConnectError:
        logger.error(f"Failed to connect to hardware service at {HARDWARE_SERVICE_BASE_URL}")
        raise HTTPException(
            status_code=503,
            detail="Hardware resource service is unavailable"
        )
    except TimeoutException:
        logger.error(f"Request to hardware service timed out")
        raise HTTPException(
            status_code=504,
            detail="Hardware resource service request timeout"
        )
    except Exception as e:
        logger.error(f"Error proxying hardware API request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.on_event("shutdown")
async def shutdown_event():
    """关闭HTTP客户端"""
    await client.aclose()
