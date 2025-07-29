"""AI Model管理路由 - 使用统一响应格式"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.apps.ai_model.schema.ai_model import (
    AIModelCreate, AIModelUpdate, AIModelQueryParams,
    AIModelTestRequest, AIModelTestResponse, AIModelStatusUpdate,
    OllamaDiscoverRequest, OllamaDiscoverResponse
)
from src.apps.ai_model.service.ai_model_service import ai_model_service
from src.shared.schemas.response import (
    UnifiedResponse, success_response, paginated_response, ResponseCode
)
from src.shared.core.exceptions import BusinessException
from src.shared.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["AI Model Management"])


@router.post("/v1/ai-models", response_model=UnifiedResponse)
async def create_ai_model(
    model_data: AIModelCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建AI模型"""
    model = await ai_model_service.create_model(db, model_data.dict())
    return success_response(
        data=model,
        msg="AI模型创建成功",
        code=ResponseCode.CREATED
    )


@router.get("/v1/ai-models/{model_id}", response_model=UnifiedResponse)
async def get_ai_model(
    model_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定AI模型"""
    model = await ai_model_service.get_model_by_id(db, model_id)
    if not model:
        raise BusinessException(f"AI模型 {model_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=model,
        msg="获取AI模型成功"
    )


@router.get("/v1/ai-models", response_model=UnifiedResponse)
async def list_ai_models(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, max_length=200, description="搜索关键词"),
    provider: Optional[str] = Query(None, max_length=100, description="提供商过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    model_type: Optional[str] = Query(None, max_length=100, description="模型类型过滤"),
    db: AsyncSession = Depends(get_async_db)
):
    """查询AI模型列表"""
    models, total = await ai_model_service.list_models(
        db, 
        page=page,
        size=size,
        provider=provider,
        status=status,
        search=search
    )
    return paginated_response(
        items=models,
        total=total,
        page=page,
        size=size,
        msg="查询AI模型列表成功"
    )


@router.put("/v1/ai-models/{model_id}", response_model=UnifiedResponse)
async def update_ai_model(
    model_id: str,
    model_data: AIModelUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新AI模型"""
    updated_model = await ai_model_service.update_model(db, model_id, model_data.dict(exclude_unset=True))
    if not updated_model:
        raise BusinessException(f"AI模型 {model_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_model,
        msg="AI模型更新成功"
    )


@router.delete("/v1/ai-models/{model_id}", response_model=UnifiedResponse)
async def delete_ai_model(
    model_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """删除AI模型"""
    success = await ai_model_service.delete_model(db, model_id)
    if not success:
        raise BusinessException(f"AI模型 {model_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data={"deleted_id": model_id},
        msg="AI模型删除成功"
    )


@router.post("/v1/ai-models/test-connection", response_model=UnifiedResponse)
async def test_ai_model_connection(
    test_request: AIModelTestRequest
):
    """测试AI模型连接"""
    try:
        result = await ai_model_service.test_model_connection(
            provider=test_request.model_provider,
            model_type=test_request.model_type,
            endpoint_url=test_request.endpoint_url,
            api_key=test_request.api_key_value,
            timeout=test_request.timeout
        )
        
        return success_response(
            data=result,
            msg="AI模型连接测试完成"
        )
    except Exception as e:
        logger.error(f"AI模型连接测试失败: {e}")
        return success_response(
            data={
                "status": "error",
                "message": f"测试失败: {str(e)}",
                "latency_ms": 0
            },
            msg="AI模型连接测试失败"
        )


@router.post("/v1/ai-models/discover-ollama", response_model=UnifiedResponse)
async def discover_ollama_models(
    discover_request: OllamaDiscoverRequest
):
    """发现Ollama服务器上的模型"""
    try:
        models = await ai_model_service.discover_ollama_models(
            endpoint_url=discover_request.endpoint_url,
            timeout=discover_request.timeout
        )
        
        return success_response(
            data={
                "models": models,
                "count": len(models)
            },
            msg=f"发现 {len(models)} 个Ollama模型"
        )
    except Exception as e:
        logger.error(f"发现Ollama模型失败: {e}")
        return success_response(
            data={
                "models": [],
                "count": 0
            },
            msg=f"发现失败: {str(e)}"
        )


@router.patch("/v1/ai-models/{model_id}/status", response_model=UnifiedResponse)
async def update_model_status(
    model_id: str,
    status_data: AIModelStatusUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新AI模型状态"""
    updated_model = await ai_model_service.update_model_status(db, model_id, status_data.status)
    if not updated_model:
        raise BusinessException(f"AI模型 {model_id} 不存在", ResponseCode.NOT_FOUND)
    
    return success_response(
        data=updated_model,
        msg=f"模型状态已更新为 {status_data.status}"
    )


@router.get("/v1/ai-models/meta/providers", response_model=UnifiedResponse)
async def get_ai_model_providers(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有AI模型提供商"""
    providers = await ai_model_service.get_providers(db)
    return success_response(
        data=providers,
        msg="获取AI模型提供商成功"
    )


@router.get("/v1/ai-models/meta/types", response_model=UnifiedResponse)
async def get_ai_model_types(
    db: AsyncSession = Depends(get_async_db)
):
    """获取所有AI模型类型"""
    types = await ai_model_service.get_model_types(db)
    return success_response(
        data=types,
        msg="获取AI模型类型成功"
    )


@router.get("/v1/ai-models/meta/statistics", response_model=UnifiedResponse)
async def get_ai_model_statistics(
    db: AsyncSession = Depends(get_async_db)
):
    """获取AI模型统计信息"""
    status_stats = await ai_model_service.get_status_statistics(db)
    provider_stats = await ai_model_service.get_provider_statistics(db)
    
    return success_response(
        data={
            "status_statistics": status_stats,
            "provider_statistics": provider_stats
        },
        msg="获取AI模型统计信息成功"
    )