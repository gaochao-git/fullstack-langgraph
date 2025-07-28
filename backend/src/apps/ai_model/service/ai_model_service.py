"""AI Model服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json
import asyncio
import aiohttp
import logging
from datetime import datetime

from src.apps.ai_model.dao.ai_model_dao import AIModelDAO
from src.apps.ai_model.models import AIModelConfig
from src.shared.db.transaction import transactional
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class AIModelService:
    """AI模型服务 - 清晰的单一职责实现"""
    
    def __init__(self):
        self._dao = AIModelDAO()
    
    @transactional()
    async def create_model(
        self, 
        session: AsyncSession, 
        model_data: Dict[str, Any]
    ) -> AIModelConfig:
        """创建AI模型"""
        # 生成唯一ID
        model_id = f"model-{uuid.uuid4().hex[:12]}"
        
        # 检查模型ID是否已存在
        existing = await self._dao.get_by_model_id(session, model_id)
        while existing:
            model_id = f"model-{uuid.uuid4().hex[:12]}"
            existing = await self._dao.get_by_model_id(session, model_id)
        
        # 转换数据
        data = model_data.copy()
        data.update({
            'model_id': model_id,
            'model_status': 'inactive',  # 默认为非激活状态
            'create_by': 'system',
            'update_by': 'system'
        })
        
        # 处理JSON字段
        if 'config_data' in data and data['config_data'] is not None:
            data['config_data'] = json.dumps(data['config_data'])
        
        logger.info(f"Creating AI model: {model_data.get('model_name')}")
        return await self._dao.create(session, data)
    
    async def get_model_by_id(
        self, 
        session: AsyncSession, 
        model_id: str
    ) -> Optional[AIModelConfig]:
        """根据ID获取AI模型"""
        return await self._dao.get_by_model_id(session, model_id)
    
    async def list_models(
        self, 
        session: AsyncSession, 
        page: int = 1,
        size: int = 10,
        provider: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[AIModelConfig], int]:
        """列出AI模型"""
        # 构建过滤条件
        filters = {}
        if provider:
            filters['model_provider'] = provider
        if status:
            filters['model_status'] = status
        
        # 搜索功能
        if search:
            models = await self._dao.search_by_name(
                session,
                search,
                provider=provider,
                status=status,
                limit=size,
                offset=(page - 1) * size
            )
            # 获取搜索总数
            all_results = await self._dao.search_by_name(
                session, 
                search,
                provider=provider,
                status=status
            )
            total = len(all_results)
        else:
            # 普通查询
            models = await self._dao.get_list(
                session,
                filters=filters if filters else None,
                limit=size,
                offset=(page - 1) * size,
                order_by='create_time'
            )
            total = await self._dao.count(session, filters=filters if filters else None)
        
        return models, total
    
    @transactional()
    async def update_model(
        self, 
        session: AsyncSession, 
        model_id: str, 
        model_data: Dict[str, Any]
    ) -> Optional[AIModelConfig]:
        """更新AI模型"""
        # 检查是否存在
        existing = await self._dao.get_by_model_id(session, model_id)
        if not existing:
            raise ValueError(f"AI model with ID {model_id} not found")
        
        # 转换数据
        data = model_data.copy()
        
        # 移除不可更新字段
        data.pop('model_id', None)
        data.pop('create_time', None)
        data.pop('create_by', None)
        data['update_by'] = 'system'
        
        # 处理JSON字段
        if 'config_data' in data and data['config_data'] is not None:
            data['config_data'] = json.dumps(data['config_data'])
        
        logger.info(f"Updating AI model: {model_id}")
        return await self._dao.update_by_field(session, 'model_id', model_id, data)
    
    @transactional()
    async def delete_model(
        self, 
        session: AsyncSession, 
        model_id: str
    ) -> bool:
        """删除AI模型"""
        existing = await self._dao.get_by_model_id(session, model_id)
        if not existing:
            return False
        
        logger.info(f"Deleting AI model: {model_id}")
        return await self._dao.delete_by_field(session, 'model_id', model_id) > 0
    
    async def get_providers(self, session: AsyncSession) -> List[str]:
        """获取所有提供商"""
        return await self._dao.get_all_providers(session)
    
    async def get_model_types(self, session: AsyncSession) -> List[str]:
        """获取所有模型类型"""
        return await self._dao.get_all_types(session)
    
    async def get_status_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取状态统计"""
        return await self._dao.get_status_statistics(session)
    
    async def get_provider_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取提供商统计"""
        return await self._dao.get_provider_statistics(session)
    
    async def get_active_models(self, session: AsyncSession) -> List[AIModelConfig]:
        """获取激活的模型（兼容性方法）"""
        return await self._dao.get_active_models(session)
    
    async def get_models_by_provider(
        self, 
        session: AsyncSession, 
        provider: str
    ) -> List[AIModelConfig]:
        """获取指定提供商的模型（兼容性方法）"""
        return await self._dao.get_models_by_provider(session, provider)
    
    @transactional()
    async def update_model_status(
        self,
        session: AsyncSession,
        model_id: str,
        status: str
    ) -> Optional[AIModelConfig]:
        """更新模型状态"""
        return await self._dao.update_model_status(session, model_id, status)
    
    async def test_model_connection(
        self,
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
    
    async def discover_ollama_models(
        self,
        endpoint_url: str,
        timeout: int = 15
    ) -> List[str]:
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


# 全局实例
ai_model_service = AIModelService()