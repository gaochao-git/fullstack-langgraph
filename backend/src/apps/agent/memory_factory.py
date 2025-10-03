"""
Mem0 长期记忆管理模块 - 标准三层架构

完全遵循Mem0官方标准的三层记忆架构：
1. 用户记忆 - 使用 user_id
2. 智能体记忆 - 使用 agent_id
3. 会话记忆 - 使用 run_id

支持组合使用：
- user_id + agent_id: 用户与特定智能体的交互记忆
- user_id + run_id: 用户的特定会话记忆
"""
import os
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import json
from datetime import datetime
from mem0 import Memory
from langchain_openai import OpenAIEmbeddings
import asyncio

from src.shared.core.config import settings
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

# 全局单例
_memory_store: Optional[Memory] = None
_initialized: bool = False


class EnterpriseMemory:
    """企业级记忆管理 - Mem0标准三层架构"""

    # 记忆类型标签（使用metadata存储）
    MEMORY_TYPES = {
        # 用户相关
        "user_profile": "用户档案",
        "user_expertise": "专业技能",
        "user_preferences": "偏好设置",

        # 系统知识
        "system_architecture": "系统架构",
        "service_dependencies": "服务依赖",
        "deployment_info": "部署信息",

        # 运维知识
        "incident_history": "故障历史",
        "solution_patterns": "解决方案",
        "runbooks": "操作手册",
        "best_practices": "最佳实践",
    }

    def __init__(self):
        self.memory = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化 Mem0 记忆存储"""
        global _memory_store, _initialized

        # 检查是否启用 Mem0
        if not settings.MEM0_ENABLE:
            logger.info("Mem0 长期记忆系统未启用")
            return

        if _initialized and _memory_store:
            self.memory = _memory_store
            return

        async with self._lock:
            if _initialized and _memory_store:
                self.memory = _memory_store
                return

            try:
                logger.info("初始化 Mem0 记忆系统...")

                # 构建配置
                config = self._build_config()

                # 创建 Memory 实例
                _memory_store = Memory.from_config(config)
                self.memory = _memory_store
                _initialized = True

                logger.info("✅ Mem0 记忆系统初始化成功")

            except Exception as e:
                logger.error(f"❌ Mem0 初始化失败: {e}")
                raise

    def _build_config(self) -> Dict[str, Any]:
        """构建 Mem0 配置"""
        # 嵌入模型配置
        embedder_config = {
            "provider": "openai",
            "config": {
                "model": settings.MEM0_EMBEDDING_MODEL,
                "api_key": settings.LLM_API_KEY,
                "openai_base_url": settings.LLM_BASE_URL,
                "embedding_dims": settings.MEM0_EMBEDDING_DIM
            }
        }

        # LLM配置
        llm_config = {
            "provider": "openai",
            "config": {
                "model": settings.LLM_MODEL,
                "api_key": settings.LLM_API_KEY,
                "openai_base_url": settings.LLM_BASE_URL,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }

        # 向量存储配置
        vector_store_config = {
            "provider": settings.MEM0_VECTOR_DB_TYPE,
            "config": {
                "host": settings.MEM0_VECTOR_DB_HOST,
                "port": settings.MEM0_VECTOR_DB_PORT,
                "dbname": settings.MEM0_VECTOR_DB_NAME,
                "user": settings.MEM0_VECTOR_DB_USER,
                "password": settings.MEM0_VECTOR_DB_PASSWORD,
                "collection_name": settings.MEM0_VECTOR_DB_TABLE,
                "embedding_model_dims": settings.MEM0_EMBEDDING_DIM
            }
        }

        return {
            "llm": llm_config,
            "embedder": embedder_config,
            "vector_store": vector_store_config,
            "version": settings.MEM0_MEMORY_VERSION
        }

    # ==================== 核心方法：标准三层记忆 ====================

    async def add_user_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        memory_type: str = "general",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加用户级记忆

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            memory_type: 记忆类型
            metadata: 额外元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            result = self.memory.add(
                messages,
                user_id=user_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加用户记忆: user_id={user_id}, memory_id={memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加用户记忆失败: {e}")
            raise

    async def add_agent_memory(
        self,
        messages: List[Dict[str, str]],
        agent_id: str,
        memory_type: str = "general",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加智能体级记忆

        Args:
            messages: 对话消息列表
            agent_id: 智能体ID
            memory_type: 记忆类型
            metadata: 额外元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            result = self.memory.add(
                messages,
                agent_id=agent_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加智能体记忆: agent_id={agent_id}, memory_id={memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加智能体记忆失败: {e}")
            raise

    async def add_session_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        run_id: str,
        memory_type: str = "conversation",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加会话级记忆

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            run_id: 会话ID
            memory_type: 记忆类型
            metadata: 额外元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            result = self.memory.add(
                messages,
                user_id=user_id,
                run_id=run_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加会话记忆: user_id={user_id}, run_id={run_id}, memory_id={memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加会话记忆失败: {e}")
            raise

    async def add_user_agent_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        agent_id: str,
        memory_type: str = "interaction",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加用户-智能体交互记忆

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            agent_id: 智能体ID
            memory_type: 记忆类型
            metadata: 额外元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            result = self.memory.add(
                messages,
                user_id=user_id,
                agent_id=agent_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加用户-智能体记忆: user_id={user_id}, agent_id={agent_id}, memory_id={memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加用户-智能体记忆失败: {e}")
            raise

    # ==================== Mem0 原生方法封装 ====================

    async def add_conversation_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """从对话中学习记忆（Mem0原生方法）"""
        if not self.memory:
            await self.initialize()

        try:
            result = self.memory.add(
                messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加对话记忆: user_id={user_id}, agent_id={agent_id}, run_id={run_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加对话记忆失败: {e}")
            raise

    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索记忆（Mem0原生方法）"""
        if not self.memory:
            await self.initialize()

        try:
            results = self.memory.search(
                query,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                limit=limit
            )

            logger.info(f"搜索记忆: query='{query[:50]}...', 返回 {len(results)} 条结果")
            return results

        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise

    async def list_all_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出所有记忆（Mem0原生方法）"""
        if not self.memory:
            await self.initialize()

        try:
            memories = self.memory.get_all(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )

            logger.info(f"列出记忆: user_id={user_id}, agent_id={agent_id}, 返回 {len(memories)} 条")
            return memories

        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            raise

    async def delete_all_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> bool:
        """删除所有记忆（Mem0原生方法）"""
        if not self.memory:
            await self.initialize()

        try:
            self.memory.delete_all(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )

            logger.info(f"✅ 删除记忆: user_id={user_id}, agent_id={agent_id}, run_id={run_id}")
            return True

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False

    # ==================== 工具方法 ====================

    def _extract_memory_id(self, result: Any) -> str:
        """从Mem0返回结果中提取memory_id"""
        if isinstance(result, dict):
            return result.get('id', 'unknown')
        elif isinstance(result, list) and result:
            return result[0].get('id', 'unknown')
        return 'unknown'

    async def reset(self):
        """重置所有记忆（危险操作，仅用于测试）"""
        if not self.memory:
            await self.initialize()

        try:
            logger.warning("⚠️ 正在重置所有记忆...")
            self.memory.reset()
            logger.info("✅ 记忆重置完成")
            return True
        except Exception as e:
            logger.error(f"重置记忆失败: {e}")
            return False

    @asynccontextmanager
    async def get_memory(self):
        """获取Memory实例的上下文管理器"""
        if not self.memory:
            await self.initialize()

        try:
            yield self.memory
        except Exception as e:
            logger.error(f"Memory操作失败: {e}")
            raise


# 单例实例
enterprise_memory = EnterpriseMemory()


async def get_enterprise_memory() -> EnterpriseMemory:
    """获取企业级记忆管理器实例"""
    if not enterprise_memory.memory:
        await enterprise_memory.initialize()
    return enterprise_memory