"""全局统一响应格式"""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel
from enum import Enum

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """响应状态枚举"""
    OK = "ok"
    ERROR = "error"


class ResponseCode(int, Enum):
    """响应状态码枚举"""
    # 成功状态码
    SUCCESS = 200
    CREATED = 201
    
    # 客户端错误
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    VALIDATION_ERROR = 422
    
    # 服务器错误
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class UnifiedResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    status: ResponseStatus
    msg: str
    data: Optional[T] = None
    code: int
    
    class Config:
        use_enum_values = True


class PaginatedData(BaseModel, Generic[T]):
    """分页数据格式"""
    items: list[T]
    pagination: dict[str, Any]


def success_response(
    data: Optional[Any] = None,
    msg: str = "操作成功",
    code: int = ResponseCode.SUCCESS
) -> UnifiedResponse:
    """成功响应"""
    return UnifiedResponse(
        status=ResponseStatus.OK,
        msg=msg,
        data=data,
        code=code
    )


def error_response(
    msg: str = "操作失败",
    code: int = ResponseCode.INTERNAL_ERROR,
    data: Optional[Any] = None
) -> UnifiedResponse:
    """错误响应"""
    return UnifiedResponse(
        status=ResponseStatus.ERROR,
        msg=msg,
        data=data,
        code=code
    )


def paginated_response(
    items: list,
    total: int,
    page: int,
    size: int,
    msg: str = "查询成功"
) -> UnifiedResponse[PaginatedData]:
    """分页响应"""
    pagination_data = PaginatedData(
        items=items,
        pagination={
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size,
            "has_next": page * size < total,
            "has_prev": page > 1
        }
    )
    
    return UnifiedResponse(
        status=ResponseStatus.OK,
        msg=msg,
        data=pagination_data,
        code=ResponseCode.SUCCESS
    )