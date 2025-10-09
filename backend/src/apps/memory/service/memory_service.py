"""
记忆管理服务（简化版 - 仅使用 Mem0）
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.core.logging import get_logger
from src.shared.core.config import settings
from src.shared.core.exceptions import BusinessException, ResponseCode
from src.apps.memory.schema import (
    MemoryCreate, MemoryUpdate, MemorySearch,
    SystemArchitectureCreate, IncidentCreate, UserPreferenceCreate
)
from src.apps.agent.memory_factory import get_enterprise_memory

logger = get_logger(__name__)


class MemoryService:
    """记忆管理服务类（简化版）"""
    
    def __init__(self):
        self._memory_instance = None
    
    async def _get_memory(self):
        """获取记忆实例（懒加载）"""
        if not settings.MEM0_ENABLE:
            raise BusinessException("Mem0记忆系统未启用", ResponseCode.SERVICE_UNAVAILABLE)

        if not self._memory_instance:
            self._memory_instance = await get_enterprise_memory()
        return self._memory_instance
    
    async def add_memory(self, db: AsyncSession, data: MemoryCreate) -> Dict[str, Any]:
        """添加记忆"""
        try:
            memory = await self._get_memory()
            memory_id = await memory.add_memory(
                namespace=data.namespace,
                content=data.content,
                metadata=data.metadata,
                **data.namespace_params
            )
            
            logger.info(f"成功添加记忆: {memory_id}")
            return {"memory_id": memory_id}
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise BusinessException(f"添加记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def search_memories(self, db: AsyncSession, data: MemorySearch) -> List[Dict[str, Any]]:
        """搜索记忆"""
        try:
            memory = await self._get_memory()
            memories = await memory.search_memories(
                namespace=data.namespace,
                query=data.query,
                limit=data.limit,
                **data.namespace_params
            )
            
            logger.info(f"搜索记忆: namespace={data.namespace}, query={data.query}, 结果数量={len(memories)}")
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise BusinessException(f"搜索记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def update_memory(self, db: AsyncSession, data: MemoryUpdate, current_user: dict = None) -> None:
        """更新记忆"""
        try:
            memory = await self._get_memory()
            
            # 获取当前用户信息用于审计
            user_name = "system"
            if current_user:
                user_name = current_user.get("username", "system")
            
            # 添加用户信息到namespace_params
            update_params = dict(data.namespace_params)
            update_params["user_name"] = user_name
            
            await memory.update_memory(
                namespace=data.namespace,
                memory_id=data.memory_id,
                content=data.content,
                **update_params
            )
            
            logger.info(f"成功更新记忆: {data.memory_id}, updated_by={user_name}")
            
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
            raise BusinessException(f"更新记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def delete_memory(self, db: AsyncSession, namespace: str, memory_id: str) -> None:
        """删除记忆"""
        try:
            memory = await self._get_memory()
            await memory.delete_memory(namespace=namespace, memory_id=memory_id)
            
            logger.info(f"成功删除记忆: {memory_id}")
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            raise BusinessException(f"删除记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def store_system_architecture(self, db: AsyncSession, data: SystemArchitectureCreate) -> None:
        """存储系统架构信息"""
        try:
            memory = await self._get_memory()
            await memory.store_system_architecture(
                system_id=data.system_id,
                architecture_info=data.architecture_info
            )
            
            logger.info(f"成功存储系统架构信息: {data.system_id}")
            
        except Exception as e:
            logger.error(f"存储系统架构失败: {e}")
            raise BusinessException(f"存储系统架构失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def store_incident(self, db: AsyncSession, data: IncidentCreate) -> None:
        """存储故障案例"""
        try:
            memory = await self._get_memory()
            await memory.store_incident(
                system_id=data.system_id,
                incident=data.incident
            )
            
            logger.info(f"成功存储故障案例: {data.system_id}")
            
        except Exception as e:
            logger.error(f"存储故障案例失败: {e}")
            raise BusinessException(f"存储故障案例失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def store_user_preference(self, db: AsyncSession, data: UserPreferenceCreate) -> None:
        """存储用户偏好"""
        try:
            memory = await self._get_memory()
            await memory.store_user_preference(
                user_id=data.user_id,
                preference=data.preference
            )
            
            logger.info(f"成功存储用户偏好: {data.user_id}")
            
        except Exception as e:
            logger.error(f"存储用户偏好失败: {e}")
            raise BusinessException(f"存储用户偏好失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def get_diagnosis_context(self, db: AsyncSession, issue: str, system_id: str, user_id: str) -> Dict[str, Any]:
        """获取诊断上下文"""
        try:
            memory = await self._get_memory()
            context = await memory.get_diagnosis_context(
                issue=issue,
                system_id=system_id,
                user_id=user_id
            )
            
            logger.info(f"获取诊断上下文: system_id={system_id}, user_id={user_id}")
            return context
            
        except Exception as e:
            logger.error(f"获取诊断上下文失败: {e}")
            raise BusinessException(f"获取诊断上下文失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def list_memories_by_namespace(self, db: AsyncSession, namespace_type: str, **params) -> List[Dict[str, Any]]:
        """按命名空间列出记忆"""
        try:
            memory = await self._get_memory()
            
            # 检查memory对象是否初始化成功
            if not memory:
                raise BusinessException("记忆系统未初始化", ResponseCode.INTERNAL_ERROR)
            
            # 检查命名空间类型是否支持
            if hasattr(memory, 'NAMESPACES'):
                namespace_template = memory.NAMESPACES.get(namespace_type)
                if not namespace_template:
                    raise BusinessException(f"不支持的命名空间类型: {namespace_type}", ResponseCode.BAD_REQUEST)
            
            memories = await memory.get_all_memories(
                namespace=namespace_type,  # 传递namespace_type而不是模板
                **params
            )
            
            return memories
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            raise BusinessException(f"列出记忆失败: {str(e)}", ResponseCode.INTERNAL_ERROR)
    
    async def get_memory_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """获取记忆统计信息（简化版）"""
        # 简化版本：直接返回基本信息
        return {
            "message": "统计功能需要通过 Mem0 API 获取",
            "status": "not_implemented"
        }


# 创建单例服务实例
memory_service = MemoryService()