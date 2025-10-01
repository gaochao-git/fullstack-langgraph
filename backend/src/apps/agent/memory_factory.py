"""
Mem0 长期记忆管理模块

用于管理企业知识、用户偏好、系统架构等长期记忆
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
    """企业级长期记忆管理类"""
    
    # 记忆命名空间定义
    NAMESPACES = {
        # 用户维度
        "user_profile": "user:{user_id}:profile",
        "user_expertise": "user:{user_id}:expertise",
        "user_preferences": "user:{user_id}:preferences",
        
        # 系统架构维度
        "system_topology": "org:architecture:topology",
        "service_dependencies": "org:architecture:dependencies:{service_id}",
        "deployment_info": "org:architecture:deployment:{system_id}",
        
        # 业务维度
        "business_flows": "org:business:flows:{process_id}",
        "sla_requirements": "org:business:sla:{service_id}",
        "critical_services": "org:business:critical",
        
        # 运维知识维度
        "incident_history": "org:ops:incidents:{system_id}",
        "solution_patterns": "org:ops:solutions:{problem_type}",
        "runbooks": "org:ops:runbooks:{scenario}",
        "best_practices": "org:ops:practices:{domain}",
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
                logger.info("初始化 Mem0 长期记忆系统...")
                
                # 构建配置
                config = self._build_config()
                
                logger.info(f"Mem0配置: {config}")
                
                # 创建 Memory 实例
                _memory_store = Memory.from_config(config)
                self.memory = _memory_store
                _initialized = True
                
                logger.info("✅ Mem0 长期记忆系统初始化成功")
                
            except Exception as e:
                logger.error(f"初始化 Mem0 失败: {e}")
                raise
    
    def _build_config(self) -> Dict[str, Any]:
        """构建 Mem0 配置"""
        
        # 设置embedder所需的环境变量
        os.environ["OPENAI_API_KEY"] = settings.EMBEDDING_API_KEY or settings.LLM_API_KEY
        
        # 嵌入模型配置 (使用兼容OpenAI的API)
        embedder_config = {
            "provider": "openai",
            "config": {
                "model": settings.EMBEDDING_MODEL_NAME,
                "openai_base_url": settings.EMBEDDING_API_BASE_URL,
                "embedding_dims": settings.MEM0_EMBEDDING_DIM
            }
        }
        
        # LLM配置 (用于记忆推理)
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
        
        # 向量存储配置 (PostgreSQL + pgvector)
        vector_store_config = {
            "provider": settings.MEM0_VECTOR_DB_TYPE,
            "config": {
                "host": settings.MEM0_VECTOR_DB_HOST,
                "port": settings.MEM0_VECTOR_DB_PORT,
                "dbname": settings.MEM0_VECTOR_DB_NAME,
                "user": settings.MEM0_VECTOR_DB_USER,
                "password": settings.MEM0_VECTOR_DB_PASSWORD,
                "collection_name": settings.MEM0_VECTOR_DB_TABLE
            }
        }
        
        return {
            "llm": llm_config,
            "embedder": embedder_config,
            "vector_store": vector_store_config,
            "version": settings.MEM0_MEMORY_VERSION
        }
    
    async def add_memory(self, namespace: str, content: str, metadata: Dict[str, Any] = None, **kwargs) -> str:
        """添加记忆"""
        if not self.memory:
            await self.initialize()
        
        # 获取并格式化命名空间模板
        namespace_template = self.NAMESPACES.get(namespace, namespace)
        formatted_namespace = namespace_template.format(**kwargs)
        
        # 构建消息（使用正确的格式）
        messages = [{"role": "user", "content": content}]
        
        # 添加元数据
        if metadata is None:
            metadata = {}
        metadata.update({
            "namespace": formatted_namespace,
            "timestamp": datetime.now().isoformat(),
            "version": settings.MEM0_MEMORY_VERSION
        })
        
        # 添加记忆（使用正确的API调用方式）
        result = self.memory.add(
            messages,  # 直接传递messages作为位置参数
            user_id=formatted_namespace,
            metadata=metadata,
            infer=True  # 启用记忆推理
        )
        
        logger.info(f"添加记忆到 {formatted_namespace}: {result}")
        return result
    
    async def search_memories(self, namespace: str, query: str, limit: int = None, **kwargs) -> List[Dict]:
        """搜索记忆"""
        if not self.memory:
            await self.initialize()
        
        # 获取并格式化命名空间模板
        namespace_template = self.NAMESPACES.get(namespace, namespace)
        formatted_namespace = namespace_template.format(**kwargs)
        
        # 搜索记忆
        memories = self.memory.search(
            query=query,
            user_id=formatted_namespace,
            limit=limit or settings.MEM0_SEARCH_LIMIT
        )
        
        # 处理搜索结果，支持不同的返回格式
        if isinstance(memories, dict) and 'results' in memories:
            memory_list = memories['results']
        elif isinstance(memories, list):
            memory_list = memories
        else:
            logger.warning(f"未知的搜索结果格式: {type(memories)}")
            memory_list = []
        
        # 解析和过滤记忆
        filtered_memories = []
        for memory in memory_list:
            # 解析记忆数据
            if isinstance(memory, dict):
                memory_id = memory.get('id')
                content = memory.get('memory') or memory.get('text') or memory.get('content')
                score = memory.get('score', 1.0)
                metadata = memory.get('metadata', {})
            else:
                # 处理对象格式
                memory_id = getattr(memory, 'id', None)
                content = getattr(memory, 'memory', None) or getattr(memory, 'text', None) or getattr(memory, 'content', None)
                score = getattr(memory, 'score', 1.0)
                metadata = getattr(memory, 'metadata', {})
            
            # 过滤有效内容和相关性 (score越小越相关，使用<=判断)
            if content and score <= settings.MEM0_RELEVANCE_THRESHOLD:
                filtered_memories.append({
                    "id": memory_id,
                    "content": content,
                    "score": score,
                    "metadata": metadata
                })
        
        logger.info(f"从 {formatted_namespace} 搜索到 {len(filtered_memories)} 条相关记忆")
        return filtered_memories
    
    async def get_all_memories(self, namespace: str, **kwargs) -> List[Dict]:
        """获取命名空间下的所有记忆"""
        if not self.memory:
            await self.initialize()
        
        # 获取并格式化命名空间模板
        namespace_template = self.NAMESPACES.get(namespace, namespace)
        formatted_namespace = namespace_template.format(**kwargs)
        
        # 获取所有记忆
        memories = self.memory.get_all(user_id=formatted_namespace)
        
        return [
            {
                "id": m.id if hasattr(m, 'id') else None,
                "content": m.memory if hasattr(m, 'memory') else str(m),
                "metadata": m.metadata if hasattr(m, 'metadata') else {}
            }
            for m in memories
        ]
    
    async def update_memory(self, namespace: str, memory_id: str, content: str, **kwargs):
        """更新记忆"""
        if not self.memory:
            await self.initialize()
        
        # 获取并格式化命名空间模板
        namespace_template = self.NAMESPACES.get(namespace, namespace)
        formatted_namespace = namespace_template.format(**kwargs)
        
        # 更新记忆
        self.memory.update(memory_id, content, user_id=formatted_namespace)
        logger.info(f"更新记忆 {memory_id} 在 {formatted_namespace}")
    
    async def delete_memory(self, namespace: str, memory_id: str, **kwargs):
        """删除记忆"""
        if not self.memory:
            await self.initialize()
        
        # 获取并格式化命名空间模板
        namespace_template = self.NAMESPACES.get(namespace, namespace)
        formatted_namespace = namespace_template.format(**kwargs)
        
        # 删除记忆
        self.memory.delete(memory_id, user_id=formatted_namespace)
        logger.info(f"删除记忆 {memory_id} 从 {formatted_namespace}")
    
    async def store_system_architecture(self, system_id: str, architecture_info: Dict[str, Any]):
        """存储系统架构信息"""
        content = f"""
系统ID: {system_id}
架构信息: {json.dumps(architecture_info, ensure_ascii=False, indent=2)}
"""
        await self.add_memory(
            namespace=self.NAMESPACES["deployment_info"],
            content=content,
            metadata={
                "type": "system_architecture",
                "system_id": system_id,
                **architecture_info
            },
            system_id=system_id
        )
    
    async def store_incident(self, system_id: str, incident: Dict[str, Any]):
        """存储故障案例"""
        content = f"""
故障时间: {incident.get('timestamp', datetime.now().isoformat())}
故障现象: {incident.get('symptoms', '')}
根因分析: {incident.get('root_cause', '')}
解决方案: {incident.get('solution', '')}
影响范围: {incident.get('impact', '')}
"""
        await self.add_memory(
            namespace=self.NAMESPACES["incident_history"],
            content=content,
            metadata={
                "type": "incident",
                "system_id": system_id,
                **incident
            },
            system_id=system_id
        )
    
    async def store_user_preference(self, user_id: str, preference: Dict[str, Any]):
        """存储用户偏好"""
        content = f"""
用户偏好设置: {json.dumps(preference, ensure_ascii=False, indent=2)}
"""
        await self.add_memory(
            namespace=self.NAMESPACES["user_preferences"],
            content=content,
            metadata={
                "type": "preference",
                "user_id": user_id,
                **preference
            },
            user_id=user_id
        )
    
    async def get_diagnosis_context(self, issue: str, system_id: str, user_id: str) -> Dict[str, Any]:
        """获取诊断上下文"""
        # 1. 搜索系统架构信息
        system_memories = await self.search_memories(
            namespace=self.NAMESPACES["deployment_info"],
            query=f"{system_id} {issue}",
            system_id=system_id
        )
        
        # 2. 搜索相似故障案例
        incident_memories = await self.search_memories(
            namespace=self.NAMESPACES["incident_history"],
            query=issue,
            system_id=system_id
        )
        
        # 3. 搜索解决方案模式
        solution_memories = await self.search_memories(
            namespace=self.NAMESPACES["solution_patterns"],
            query=issue,
            problem_type="general"
        )
        
        # 4. 获取用户偏好
        user_preferences = await self.get_all_memories(
            namespace=self.NAMESPACES["user_preferences"],
            user_id=user_id
        )
        
        return {
            "system_context": system_memories,
            "similar_incidents": incident_memories,
            "solution_patterns": solution_memories,
            "user_preferences": user_preferences,
            "current_issue": issue,
            "timestamp": datetime.now().isoformat()
        }


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
    logger.info("✅ 长期记忆系统已清理")