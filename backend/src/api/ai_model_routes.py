"""AI Model Configuration management routes."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json
import uuid
import logging
import aiohttp
import asyncio
from pydantic import BaseModel

from ..database.config import get_db
from ..database.models import AIModelConfig

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class AIModelCreateRequest(BaseModel):
    model_name: str
    model_provider: str
    model_type: str
    endpoint_url: str
    api_key_value: Optional[str] = None
    model_description: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None


class AIModelUpdateRequest(BaseModel):
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    model_type: Optional[str] = None
    endpoint_url: Optional[str] = None
    api_key_value: Optional[str] = None
    model_description: Optional[str] = None
    model_status: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None


class AIModelTestRequest(BaseModel):
    model_provider: str
    model_type: str
    endpoint_url: str
    api_key_value: Optional[str] = None


class AIModelTestResponse(BaseModel):
    status: str
    latency_ms: Optional[int] = None
    message: str
    error_details: Optional[str] = None


class OllamaDiscoverRequest(BaseModel):
    endpoint_url: str


async def _test_model_connection(
    provider: str, 
    model_type: str, 
    endpoint_url: str, 
    api_key: Optional[str] = None,
    timeout: int = 15
) -> Dict[str, Any]:
    """测试AI模型连接"""
    try:
        start_time = datetime.now()
        
        if provider == "ollama":
            # Ollama API测试
            test_url = f"{endpoint_url.rstrip('/')}/api/generate"
            payload = {
                "model": model_type,
                "prompt": "Hello, world!",
                "stream": False
            }
            headers = {"Content-Type": "application/json"}
            
        elif provider in ["openai-compatible", "deepseek", "qwen"]:
            # OpenAI兼容API测试（包括DeepSeek、Qwen等）
            test_url = f"{endpoint_url.rstrip('/')}/chat/completions"
            payload = {
                "model": model_type,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            headers = {
                "Content-Type": "application/json"
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
        else:
            return {
                "status": "error",
                "message": f"不支持的服务商: {provider}",
                "latency_ms": 0
            }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                test_url, 
                json=payload, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                end_time = datetime.now()
                latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                if response.status == 200:
                    return {
                        "status": "success",
                        "message": "连接测试成功",
                        "latency_ms": latency_ms
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"连接测试失败: HTTP {response.status}",
                        "latency_ms": latency_ms,
                        "error_details": error_text
                    }
                    
    except asyncio.TimeoutError:
        return {
            "status": "error",
            "message": "连接超时",
            "latency_ms": timeout * 1000
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"连接错误: {str(e)}",
            "latency_ms": 0,
            "error_details": str(e)
        }


async def _discover_ollama_models(endpoint_url: str, timeout: int = 15) -> List[str]:
    """发现Ollama服务器上的模型"""
    try:
        # 确保端点URL格式正确
        base_url = endpoint_url.rstrip('/')
        discover_url = f"{base_url}/api/tags"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                discover_url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'models' in data and isinstance(data['models'], list):
                        return [model.get('name', '') for model in data['models'] if model.get('name')]
                    return []
                else:
                    error_text = await response.text()
                    logger.error(f"Ollama发现失败 HTTP {response.status}: {error_text}")
                    return []
                    
    except asyncio.TimeoutError:
        logger.error(f"Ollama发现超时: {endpoint_url}")
        return []
    except Exception as e:
        logger.error(f"Ollama发现错误: {str(e)}")
        return []


@router.get("/ai-models", response_model=Dict[str, Any])
async def get_ai_models(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    provider: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    team_name: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取AI模型列表"""
    try:
        # 构建查询条件
        conditions = []
        if provider:
            conditions.append(AIModelConfig.model_provider == provider)
        if status:
            conditions.append(AIModelConfig.model_status == status)
        if team_name:
            # 如果有团队字段，可以添加团队过滤条件
            pass
            
        # 构建查询
        query = db.query(AIModelConfig)
        if conditions:
            query = query.filter(and_(*conditions))
            
        # 获取总数
        total = query.count()
        
        # 分页查询
        models = query.order_by(AIModelConfig.create_time.desc()).offset((page - 1) * size).limit(size).all()
        
        # 转换为字典
        model_list = [model.to_dict() for model in models]
        
        return {
            "code": 200,
            "data": {
                "total": total,
                "items": model_list,
                "page": page,
                "size": size
            },
            "message": "获取模型列表成功"
        }
        
    except Exception as e:
        logger.error(f"获取AI模型列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.post("/ai-models", response_model=Dict[str, Any])
async def create_ai_model(
    model_data: AIModelCreateRequest,
    db: Session = Depends(get_db)
):
    """创建AI模型配置"""
    try:
        # 生成唯一ID
        model_id = f"model-{uuid.uuid4().hex[:12]}"
        
        # 检查模型ID是否已存在
        existing_model = db.query(AIModelConfig).filter(AIModelConfig.model_id == model_id).first()
        while existing_model:
            model_id = f"model-{uuid.uuid4().hex[:12]}"
            existing_model = db.query(AIModelConfig).filter(AIModelConfig.model_id == model_id).first()
        
        # 创建模型配置
        ai_model = AIModelConfig(
            model_id=model_id,
            model_name=model_data.model_name,
            model_provider=model_data.model_provider,
            model_type=model_data.model_type,
            endpoint_url=model_data.endpoint_url,
            api_key_value=model_data.api_key_value,
            model_description=model_data.model_description,
            model_status='inactive',  # 默认为非激活状态
            config_data=json.dumps(model_data.config_data) if model_data.config_data else None,
            create_by='frontend_user',
            create_time=datetime.utcnow(),
            update_time=datetime.utcnow()
        )
        
        db.add(ai_model)
        db.commit()
        db.refresh(ai_model)
        
        return {
            "code": 200,
            "data": ai_model.to_dict(),
            "message": "模型创建成功"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建AI模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建模型失败: {str(e)}")


@router.put("/ai-models/{model_id}", response_model=Dict[str, Any])
async def update_ai_model(
    model_id: str,
    model_data: AIModelUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新AI模型配置"""
    try:
        # 查找模型
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.model_id == model_id).first()
        if not ai_model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        # 更新字段
        update_data = model_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'config_data' and value is not None:
                setattr(ai_model, field, json.dumps(value))
            else:
                setattr(ai_model, field, value)
        
        ai_model.update_by = 'frontend_user'
        ai_model.update_time = datetime.utcnow()
        
        db.commit()
        db.refresh(ai_model)
        
        return {
            "code": 200,
            "data": ai_model.to_dict(),
            "message": "模型更新成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新AI模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新模型失败: {str(e)}")


@router.delete("/ai-models/{model_id}", response_model=Dict[str, Any])
async def delete_ai_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """删除AI模型配置"""
    try:
        # 查找模型
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.model_id == model_id).first()
        if not ai_model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        db.delete(ai_model)
        db.commit()
        
        return {
            "code": 200,
            "data": None,
            "message": "模型删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除AI模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除模型失败: {str(e)}")


@router.get("/ai-models/{model_id}", response_model=Dict[str, Any])
async def get_ai_model(
    model_id: str,
    db: Session = Depends(get_db)
):
    """获取单个AI模型配置"""
    try:
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.model_id == model_id).first()
        if not ai_model:
            raise HTTPException(status_code=404, detail="模型不存在")
        
        return {
            "code": 200,
            "data": ai_model.to_dict(),
            "message": "获取模型成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI模型失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模型失败: {str(e)}")


@router.post("/ai-models/test-connection", response_model=Dict[str, Any])
async def test_ai_model_connection(
    test_data: AIModelTestRequest
):
    """测试AI模型连接"""
    try:
        result = await _test_model_connection(
            provider=test_data.model_provider,
            model_type=test_data.model_type,
            endpoint_url=test_data.endpoint_url,
            api_key=test_data.api_key_value
        )
        
        return {
            "code": 200,
            "data": result,
            "message": "连接测试完成"
        }
        
    except Exception as e:
        logger.error(f"测试AI模型连接失败: {str(e)}")
        return {
            "code": 500,
            "data": {
                "status": "error",
                "message": f"测试失败: {str(e)}",
                "latency_ms": 0
            },
            "message": "连接测试失败"
        }


@router.post("/ai-models/discover-ollama", response_model=Dict[str, Any])
async def discover_ollama_models(
    discover_data: OllamaDiscoverRequest
):
    """发现Ollama服务器上的模型"""
    try:
        models = await _discover_ollama_models(discover_data.endpoint_url)
        
        return {
            "code": 200,
            "data": {
                "models": models,
                "count": len(models)
            },
            "message": f"发现 {len(models)} 个模型"
        }
        
    except Exception as e:
        logger.error(f"发现Ollama模型失败: {str(e)}")
        return {
            "code": 500,
            "data": {
                "models": [],
                "count": 0
            },
            "message": f"发现失败: {str(e)}"
        }