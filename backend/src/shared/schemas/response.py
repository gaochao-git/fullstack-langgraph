"""全局统一响应格式"""

from typing import Optional, Any, Generic, TypeVar, Union, List, Dict
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
    INVALID_API_KEY = 461  # 自定义错误码：API密钥无效
    
    # 服务器错误
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


class UnifiedResponse(BaseModel, Generic[T]):
    """统一响应格式 - data 只能是字典或字典列表"""
    status: ResponseStatus
    msg: str
    data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    code: int
    
    class Config:
        use_enum_values = True


# PaginatedData 类已移除，直接使用字典格式


def success_response(
    data: Optional[Any] = None,
    msg: str = "操作成功",
    code: int = ResponseCode.SUCCESS
) -> UnifiedResponse:
    """成功响应 - 自动序列化模型对象和查询结果"""
    # 自动序列化模型对象
    if data is not None and hasattr(data, 'to_dict'):
        data = data.to_dict()
    # 处理SQLAlchemy查询结果
    if data is not None and hasattr(data, 'mappings'):
        data = [dict(row) for row in data.mappings()]
    
    return UnifiedResponse(
        status=ResponseStatus.OK,
        msg=msg,
        data=data,
        code=code
    )


def error_response(
    msg: str = "操作失败",
    code: int = ResponseCode.INTERNAL_ERROR
) -> UnifiedResponse:
    """错误响应 - data 固定为 None"""
    return UnifiedResponse(
        status=ResponseStatus.ERROR,
        msg=msg,
        data=None,  # 错误响应不返回业务数据
        code=code
    )


def paginated_response(
    items: list,
    total: int,
    page: int,
    size: int,
    msg: str = "查询成功"
) -> UnifiedResponse:
    """分页响应 - 自动序列化模型对象列表"""
    # 自动序列化模型对象列表
    if items and hasattr(items[0], 'to_dict'):
        items = [item.to_dict() for item in items]
    
    # 直接构造字典格式，符合 UnifiedResponse 的校验要求
    pagination_dict = {
        "items": items,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size,
            "has_next": page * size < total,
            "has_prev": page > 1
        }
    }
    
    return UnifiedResponse(
        status=ResponseStatus.OK,
        msg=msg,
        data=pagination_dict,
        code=ResponseCode.SUCCESS
    )