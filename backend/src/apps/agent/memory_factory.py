"""
Mem0 长期记忆管理模块 V2 - 三层记忆架构

改进内容：
1. 移除自定义 NAMESPACES，使用 Mem0 的三层记忆隔离机制
2. 实现用户全局记忆（user_id）
3. 实现智能体全局记忆（agent_id）
4. 实现组织全局记忆（user_id="organization"）
5. 支持分层记忆检索和组合
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
    """企业级三层记忆管理类"""

    # 记忆层级定义
    MEMORY_LEVELS = {
        "ORGANIZATION": "organization",  # 组织级记忆（全局知识库）
        "USER_GLOBAL": "user_global",     # 用户级记忆（跨智能体）
        "AGENT_GLOBAL": "agent_global",   # 智能体级记忆（跨用户）
        "USER_AGENT": "user_agent",       # 用户-智能体交互记忆
        "SESSION": "session"              # 会话级临时记忆
    }

    # 记忆类型标签（使用 metadata 而不是 namespace）
    MEMORY_TYPES = {
        # 用户相关
        "user_profile": "用户个人档案",
        "user_expertise": "用户专业技能",
        "user_preferences": "用户偏好设置",

        # 组织相关
        "system_architecture": "系统架构",
        "service_dependencies": "服务依赖",
        "deployment_info": "部署信息",

        # 运维知识
        "incident_history": "故障历史",
        "solution_patterns": "解决方案模式",
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
                logger.info("初始化 Mem0 三层记忆系统...")

                # 构建配置
                config = self._build_config()

                logger.info(f"Mem0配置: {config}")

                # 创建 Memory 实例
                _memory_store = Memory.from_config(config)
                self.memory = _memory_store
                _initialized = True

                logger.info("✅ Mem0 三层记忆系统初始化成功")

            except Exception as e:
                logger.error(f"初始化 Mem0 失败: {e}")
                raise

    def _build_config(self) -> Dict[str, Any]:
        """构建 Mem0 配置"""

        # 嵌入模型配置
        embedder_config = {
            "provider": "openai",
            "config": {
                "model": settings.EMBEDDING_MODEL_NAME,
                "api_key": settings.EMBEDDING_API_KEY,
                "openai_base_url": settings.EMBEDDING_API_BASE_URL,
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

    # ==================== 核心方法：三层记忆添加 ====================

    async def add_organization_memory(
        self,
        messages: List[Dict[str, str]],
        memory_type: str = "general",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加组织级全局记忆（所有用户和智能体共享）

        Args:
            messages: 对话消息列表
            memory_type: 记忆类型标签
            metadata: 额外的元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "level": self.MEMORY_LEVELS["ORGANIZATION"],
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            result = self.memory.add(
                messages,
                user_id="organization",  # 特殊的组织用户ID
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加组织记忆成功: memory_id={memory_id}, type={memory_type}")
            return memory_id

        except Exception as e:
            logger.error(f"添加组织记忆失败: {e}")
            raise

    async def add_user_global_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        memory_type: str = "profile",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加用户全局记忆（该用户在所有智能体间共享）

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            memory_type: 记忆类型（profile/expertise/preferences）
            metadata: 额外的元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "level": self.MEMORY_LEVELS["USER_GLOBAL"],
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 仅使用 user_id，不指定 agent_id
            result = self.memory.add(
                messages,
                user_id=user_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加用户全局记忆成功: user_id={user_id}, memory_id={memory_id}, type={memory_type}")
            return memory_id

        except Exception as e:
            logger.error(f"添加用户全局记忆失败: {e}")
            raise

    async def add_agent_global_memory(
        self,
        messages: List[Dict[str, str]],
        agent_id: str,
        memory_type: str = "knowledge",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加智能体全局记忆（该智能体在所有用户间共享）

        Args:
            messages: 对话消息列表
            agent_id: 智能体ID
            memory_type: 记忆类型（knowledge/experience/pattern）
            metadata: 额外的元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "level": self.MEMORY_LEVELS["AGENT_GLOBAL"],
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 仅使用 agent_id，不指定 user_id（使用特殊值）
            result = self.memory.add(
                messages,
                user_id=f"agent_{agent_id}",  # 特殊的智能体用户ID
                agent_id=agent_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加智能体全局记忆成功: agent_id={agent_id}, memory_id={memory_id}, type={memory_type}")
            return memory_id

        except Exception as e:
            logger.error(f"添加智能体全局记忆失败: {e}")
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
        添加用户-智能体交互记忆（特定用户与特定智能体的记忆）

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            agent_id: 智能体ID
            memory_type: 记忆类型
            metadata: 额外的元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "level": self.MEMORY_LEVELS["USER_AGENT"],
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 同时使用 user_id 和 agent_id
            result = self.memory.add(
                messages,
                user_id=user_id,
                agent_id=agent_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加用户-智能体交互记忆成功: user_id={user_id}, agent_id={agent_id}, memory_id={memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加用户-智能体交互记忆失败: {e}")
            raise

    async def add_session_memory(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        agent_id: str,
        run_id: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加会话临时记忆（会话结束后可清除）

        Args:
            messages: 对话消息列表
            user_id: 用户ID
            agent_id: 智能体ID
            run_id: 会话ID
            metadata: 额外的元数据

        Returns:
            memory_id: 记忆ID
        """
        if not self.memory:
            await self.initialize()

        try:
            combined_metadata = {
                "level": self.MEMORY_LEVELS["SESSION"],
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }

            # 使用 user_id + agent_id + run_id
            result = self.memory.add(
                messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=combined_metadata,
                infer=True
            )

            memory_id = self._extract_memory_id(result)
            logger.info(f"✅ 添加会话记忆成功: run_id={run_id}, memory_id={memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"添加会话记忆失败: {e}")
            raise

    # ==================== 核心方法：分层记忆检索 ====================

    async def search_organization_memory(
        self,
        query: str,
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict]:
        """检索组织级全局记忆"""
        if not self.memory:
            await self.initialize()

        search_params = {
            "query": query,
            "user_id": "organization",
            "limit": limit or settings.MEM0_SEARCH_LIMIT
        }

        if threshold is not None:
            search_params["threshold"] = threshold

        logger.info(f"🔍 检索组织记忆: query='{query[:50]}...'")

        memories = self.memory.search(**search_params)
        return self._process_search_results(memories, "organization")

    async def search_user_global_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict]:
        """检索用户全局记忆（跨智能体）"""
        if not self.memory:
            await self.initialize()

        search_params = {
            "query": query,
            "user_id": user_id,
            "limit": limit or settings.MEM0_SEARCH_LIMIT
        }

        if threshold is not None:
            search_params["threshold"] = threshold

        logger.info(f"🔍 检索用户全局记忆: user_id={user_id}, query='{query[:50]}...'")

        memories = self.memory.search(**search_params)
        return self._process_search_results(memories, user_id)

    async def search_agent_global_memory(
        self,
        query: str,
        agent_id: str,
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict]:
        """检索智能体全局记忆（跨用户）"""
        if not self.memory:
            await self.initialize()

        search_params = {
            "query": query,
            "user_id": f"agent_{agent_id}",
            "agent_id": agent_id,
            "limit": limit or settings.MEM0_SEARCH_LIMIT
        }

        if threshold is not None:
            search_params["threshold"] = threshold

        logger.info(f"🔍 检索智能体全局记忆: agent_id={agent_id}, query='{query[:50]}...'")

        memories = self.memory.search(**search_params)
        return self._process_search_results(memories, f"agent_{agent_id}")

    async def search_user_agent_memory(
        self,
        query: str,
        user_id: str,
        agent_id: str,
        limit: int = 5,
        threshold: float = None
    ) -> List[Dict]:
        """检索用户-智能体交互记忆"""
        if not self.memory:
            await self.initialize()

        search_params = {
            "query": query,
            "user_id": user_id,
            "agent_id": agent_id,
            "limit": limit or settings.MEM0_SEARCH_LIMIT
        }

        if threshold is not None:
            search_params["threshold"] = threshold

        logger.info(f"🔍 检索用户-智能体交互记忆: user_id={user_id}, agent_id={agent_id}")

        memories = self.memory.search(**search_params)
        return self._process_search_results(memories, user_id)

    async def search_combined_memory(
        self,
        query: str,
        user_id: str,
        agent_id: str,
        limit_per_level: int = 3,
        threshold: float = None
    ) -> Dict[str, List[Dict]]:
        """
        组合检索多层记忆（推荐使用）

        Returns:
            {
                "organization": [...],  # 组织记忆
                "user_global": [...],   # 用户全局记忆
                "agent_global": [...],  # 智能体全局记忆
                "user_agent": [...]     # 用户-智能体记忆
            }
        """
        logger.info(f"🔍 组合检索记忆: user_id={user_id}, agent_id={agent_id}, query='{query[:50]}...'")

        # 并发检索各层记忆
        org_task = self.search_organization_memory(query, limit_per_level, threshold)
        user_task = self.search_user_global_memory(query, user_id, limit_per_level, threshold)
        agent_task = self.search_agent_global_memory(query, agent_id, limit_per_level, threshold)
        user_agent_task = self.search_user_agent_memory(query, user_id, agent_id, limit_per_level, threshold)

        org_memories, user_memories, agent_memories, user_agent_memories = await asyncio.gather(
            org_task, user_task, agent_task, user_agent_task
        )

        result = {
            "organization": org_memories,
            "user_global": user_memories,
            "agent_global": agent_memories,
            "user_agent": user_agent_memories
        }

        total_count = sum(len(v) for v in result.values())
        logger.info(f"✅ 组合检索完成: 共找到 {total_count} 条记忆")

        return result

    # ==================== 辅助方法 ====================

    def _extract_memory_id(self, result) -> str:
        """从 Mem0 返回结果中提取 memory_id"""
        if isinstance(result, dict):
            if result.get("results") == []:
                logger.warning("Mem0返回空结果")
                import uuid
                return str(uuid.uuid4())
            elif result.get("results") and len(result["results"]) > 0:
                first_result = result["results"][0]
                return first_result.get("id", str(result))
            else:
                return result.get("memory_id") or result.get("id") or str(result)
        else:
            return str(result)

    def _process_search_results(self, memories, user_id: str) -> List[Dict]:
        """处理搜索结果，统一格式"""
        if isinstance(memories, dict) and 'results' in memories:
            memory_list = memories['results']
        elif isinstance(memories, list):
            memory_list = memories
        else:
            logger.warning(f"未知的搜索结果格式: {type(memories)}")
            return []

        processed = []
        for memory in memory_list:
            if isinstance(memory, dict):
                processed.append({
                    "id": memory.get('id'),
                    "content": memory.get('memory') or memory.get('text') or memory.get('content'),
                    "score": memory.get('score', 1.0),
                    "metadata": memory.get('metadata', {}),
                    "user_id": user_id
                })
            else:
                processed.append({
                    "id": getattr(memory, 'id', None),
                    "content": getattr(memory, 'memory', None) or getattr(memory, 'text', None),
                    "score": getattr(memory, 'score', 1.0),
                    "metadata": getattr(memory, 'metadata', {}),
                    "user_id": user_id
                })

        return processed

    # ==================== 列表和删除方法 ====================

    async def list_all_memories(
        self,
        user_id: str,
        agent_id: str = None,
        run_id: str = None
    ) -> List[Dict]:
        """获取所有记忆（使用 Mem0 原生 get_all 方法）"""
        if not self.memory:
            await self.initialize()

        try:
            raw_result = self.memory.get_all(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )
            logger.info(f"Mem0 get_all原始返回: {raw_result}, 类型: {type(raw_result)}")

            if isinstance(raw_result, dict) and 'results' in raw_result:
                memories = raw_result['results']
            elif isinstance(raw_result, list):
                memories = raw_result
            else:
                logger.warning(f"未知的get_all返回格式: {type(raw_result)}")
                memories = []

            formatted_memories = []
            for memory in memories:
                if memory is not None:
                    if isinstance(memory, dict):
                        memory_item = {
                            "id": memory.get('id'),
                            "content": memory.get('memory') or memory.get('text') or memory.get('content'),
                            "metadata": memory.get('metadata', {}),
                            "user_id": memory.get('user_id', user_id)
                        }
                    else:
                        memory_item = {
                            "id": getattr(memory, 'id', None),
                            "content": getattr(memory, 'memory', None) or getattr(memory, 'text', None),
                            "metadata": getattr(memory, 'metadata', {}),
                            "user_id": getattr(memory, 'user_id', user_id)
                        }
                    formatted_memories.append(memory_item)

            logger.info(f"list_all_memories: 返回 {len(formatted_memories)} 条记忆 (user_id={user_id}, agent_id={agent_id})")
            return formatted_memories

        except Exception as e:
            logger.error(f"Mem0 get_all调用失败: {e}")
            return []

    async def delete_all_memories(
        self,
        user_id: str,
        agent_id: str = None,
        run_id: str = None
    ) -> bool:
        """删除所有记忆"""
        if not self.memory:
            await self.initialize()

        try:
            self.memory.delete_all(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )
            logger.info(f"✅ 成功删除记忆: user_id={user_id}, agent_id={agent_id}, run_id={run_id}")
            return True

        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False


# 单例实例
_enterprise_memory: Optional[EnterpriseMemory] = None


async def get_enterprise_memory() -> EnterpriseMemory:
    """获取企业记忆管理实例"""
    global _enterprise_memory

    if not _enterprise_memory:
        _enterprise_memory = EnterpriseMemory()
        await _enterprise_memory.initialize()

    return _enterprise_memory


async def cleanup_memory():
    """清理资源"""
    global _memory_store, _initialized, _enterprise_memory

    _memory_store = None
    _initialized = False
    _enterprise_memory = None
    logger.info("✅ 三层记忆系统已清理")
