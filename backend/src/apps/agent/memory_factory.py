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
        "user_profile": "user:{user_name}:profile",
        "user_expertise": "user:{user_name}:expertise", 
        "user_preferences": "user:{user_name}:preferences",
        
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
        
        # 嵌入模型配置 (使用兼容OpenAI的API)
        embedder_config = {
            "provider": "openai",
            "config": {
                "model": settings.EMBEDDING_MODEL_NAME,
                "api_key": settings.EMBEDDING_API_KEY,
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
        
        # 向量存储配置 (PostgreSQL + pgvector) - 官方标准格式
        vector_store_config = {
            "provider": settings.MEM0_VECTOR_DB_TYPE,
            "config": {
                "host": settings.MEM0_VECTOR_DB_HOST,
                "port": settings.MEM0_VECTOR_DB_PORT,
                "dbname": settings.MEM0_VECTOR_DB_NAME,
                "user": settings.MEM0_VECTOR_DB_USER,
                "password": settings.MEM0_VECTOR_DB_PASSWORD,
                "collection_name": settings.MEM0_VECTOR_DB_TABLE,
                "embedding_model_dims": settings.MEM0_EMBEDDING_DIM  # 官方要求的参数
            }
        }
        
        return {
            "llm": llm_config,
            "embedder": embedder_config,
            "vector_store": vector_store_config,
            "version": settings.MEM0_MEMORY_VERSION
        }
    
    def _prepare_call_params(self, namespace: str, metadata: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """准备符合官方标准的调用参数"""
        
        # 提取真实的用户ID（必需），兼容user_name和user_id
        user_id = kwargs.get("user_id") or kwargs.get("user_name")
        if not user_id:
            raise ValueError("user_id or user_name is required for Mem0 API calls")
        
        # 提取可选的智能体ID和会话ID
        agent_id = kwargs.get("agent_id", "diagnostic_agent")  # 默认诊断智能体
        run_id = kwargs.get("run_id")  # 会话级记忆，可选
        
        # 构建namespace和业务元数据
        namespace_template = self.NAMESPACES.get(namespace, namespace)
        # 确保kwargs中包含user_name字段用于格式化
        format_kwargs = dict(kwargs)
        format_kwargs["user_name"] = user_id  # 将获取到的用户标识作为user_name
        formatted_namespace = namespace_template.format(**format_kwargs)
        
        # 获取当前时间戳
        current_time = datetime.now().isoformat()
        
        # 合并元数据，将我们的namespace概念放到metadata中
        combined_metadata = {
            "business_namespace": formatted_namespace,  # 我们的业务命名空间
            "namespace_type": namespace,  # 命名空间类型
            "timestamp": current_time,
            "version": settings.MEM0_MEMORY_VERSION,
            # 审计字段
            "created_by": user_id,
            "create_time": current_time
        }
        
        if metadata:
            combined_metadata.update(metadata)
        
        logger.info(f"准备调用参数: user_id={user_id}, business_namespace={formatted_namespace}, namespace_type={namespace}")
        
        return {
            "user_id": user_id,
            "agent_id": agent_id,
            "run_id": run_id,
            "metadata": combined_metadata
        }
    
    async def add_conversation_memory(self, messages: List[Dict[str, str]], user_id: str, agent_id: str = "diagnostic_agent", run_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """从对话中添加记忆（Mem0 正确用法）"""
        if not self.memory:
            await self.initialize()
        
        try:
            # 使用 Mem0 的正确方式：从对话消息中智能提取记忆
            result = self.memory.add(
                messages,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata or {},
                infer=True  # 开启推理，让 Mem0 智能提取记忆
            )
            
            logger.info(f"Mem0 add原始返回结果: {result}, 类型: {type(result)}")
            
            # 处理返回值格式
            if isinstance(result, dict):
                # 检查是否是空结果
                if result.get("results") == []:
                    logger.warning("Mem0返回空结果，可能添加失败")
                    # 尝试生成一个唯一ID
                    import uuid
                    memory_id = str(uuid.uuid4())
                    logger.warning(f"使用生成的ID: {memory_id}")
                elif result.get("results") and len(result["results"]) > 0:
                    # 从results中提取第一个记忆的ID
                    first_result = result["results"][0]
                    memory_id = first_result.get("id", str(result))
                    logger.info(f"从results中提取到memory_id: {memory_id}")
                else:
                    # 如果返回是字典，尝试提取memory_id或id
                    memory_id = result.get("memory_id") or result.get("id") or str(result)
            else:
                # 如果返回是字符串或其他类型，直接转换
                memory_id = str(result)
            
            logger.info(f"添加记忆完成: user_id={user_id}, memory_id={memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Mem0 add调用失败: {e}")
            raise
    
    async def search_memories(self, namespace: str, query: str, limit: int = None, **kwargs) -> List[Dict]:
        """搜索记忆（简化版：只基于user_id和agent_id过滤）"""
        if not self.memory:
            await self.initialize()
        
        # 直接提取参数，不使用复杂的命名空间逻辑
        user_id = kwargs.get("user_id") or kwargs.get("user_name")
        if not user_id:
            raise ValueError("user_id or user_name is required")
        
        agent_id = kwargs.get("agent_id")
        
        # 提取元数据参数（用于业务层过滤）
        metadata = kwargs.get("metadata", {})
        
        # 提取距离阈值（如果有传递）
        distance_threshold = kwargs.get("threshold") or kwargs.get("distance_threshold")
        
        # 直接使用距离阈值，不需要转换
        threshold = None
        if distance_threshold is not None:
            threshold = float(distance_threshold)
        
        # 构建搜索参数
        search_params = {
            "query": query,
            "user_id": user_id,
            "agent_id": agent_id,
            "limit": limit or settings.MEM0_SEARCH_LIMIT
        }
        
        # 如果指定了阈值，添加到参数中
        if threshold is not None:
            search_params["threshold"] = threshold
        
        # 添加详细的调试日志
        logger.info(f"Mem0搜索参数: {search_params}")
        logger.info(f"传入的distance_threshold={distance_threshold}, 使用的threshold={threshold}")
        
        # 使用官方标准API搜索
        memories = self.memory.search(**search_params)
        
        # 详细记录原始搜索结果
        logger.info(f"Mem0原始搜索结果: type={type(memories)}, content={memories}")
        
        # 处理搜索结果，支持不同的返回格式
        if isinstance(memories, dict) and 'results' in memories:
            memory_list = memories['results']
        elif isinstance(memories, list):
            memory_list = memories
        else:
            logger.warning(f"未知的搜索结果格式: {type(memories)}")
            memory_list = []
        
        logger.info(f"提取到的记忆列表长度: {len(memory_list)}")
        
        # 修复过滤逻辑：如果用户指定了threshold，则使用用户的；否则使用默认的
        effective_threshold = threshold if threshold is not None else settings.MEM0_RELEVANCE_THRESHOLD
        logger.info(f"使用的有效阈值: {effective_threshold} (用户指定: {threshold is not None})")
        
        filtered_memories = []
        
        for i, memory in enumerate(memory_list):
            # 解析记忆数据
            if isinstance(memory, dict):
                memory_id = memory.get('id')
                content = memory.get('memory') or memory.get('text') or memory.get('content')
                score = memory.get('score', 1.0)
                memory_metadata = memory.get('metadata', {})
            else:
                # 处理对象格式
                memory_id = getattr(memory, 'id', None)
                content = getattr(memory, 'memory', None) or getattr(memory, 'text', None) or getattr(memory, 'content', None)
                score = getattr(memory, 'score', 1.0)
                memory_metadata = getattr(memory, 'metadata', {})
            
            logger.info(f"处理记忆{i}: id={memory_id}, score={score}, content_preview={content[:50] if content else 'None'}...")
            
            # 简化过滤逻辑：Mem0已经返回了相关的结果，直接接受
            should_include = False
            if content:
                # Mem0返回的结果已经是相关的，直接接受
                should_include = True
                logger.info(f"记忆{i}: 接受Mem0返回的结果 (score={score})")
            else:
                logger.info(f"记忆{i}: 内容为空，跳过")
            
            if should_include:
                filtered_memories.append({
                    "id": memory_id,
                    "content": content,
                    "score": score,
                    "metadata": memory_metadata,
                    "user_id": user_id  # 添加 user_id 字段
                })
        
        logger.info(f"搜索记忆: user_id={user_id}, agent_id={agent_id}, query={query}, 原始结果数量={len(memory_list)}, 过滤后结果数量={len(filtered_memories)}")
        return filtered_memories
    
    async def list_all_memories(self, user_id: str, agent_id: str = None, run_id: str = None) -> List[Dict]:
        """获取所有记忆（使用 Mem0 原生 get_all 方法）"""
        if not self.memory:
            await self.initialize()
        
        try:
            # 使用 Mem0 原生 get_all 方法
            raw_result = self.memory.get_all(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )
            logger.info(f"Mem0 get_all原始返回: {raw_result}, 类型: {type(raw_result)}")
            
            # 处理不同的返回格式
            if isinstance(raw_result, dict) and 'results' in raw_result:
                memories = raw_result['results']
            elif isinstance(raw_result, list):
                memories = raw_result
            else:
                logger.warning(f"未知的get_all返回格式: {type(raw_result)}")
                memories = []
            
            logger.info(f"提取到的记忆数组: {len(memories)} 条记忆")
            
            # 转换为统一格式
            formatted_memories = []
            for memory in memories:
                if memory is not None:
                    # 处理不同的记忆对象格式
                    if isinstance(memory, dict):
                        memory_item = {
                            "id": memory.get('id'),
                            "content": memory.get('memory') or memory.get('text') or memory.get('content'),
                            "metadata": memory.get('metadata', {}),
                            "user_id": memory.get('user_id', user_id)
                        }
                    else:
                        # 如果是对象格式
                        memory_item = {
                            "id": getattr(memory, 'id', None),
                            "content": getattr(memory, 'memory', None) or getattr(memory, 'text', None) or str(memory),
                            "metadata": getattr(memory, 'metadata', {}),
                            "user_id": getattr(memory, 'user_id', user_id)
                        }
                    
                    formatted_memories.append(memory_item)
            
            logger.info(f"list_all_memories: 返回 {len(formatted_memories)} 条记忆 (user_id={user_id}, agent_id={agent_id})")
            return formatted_memories
            
        except Exception as e:
            logger.error(f"Mem0 get_all调用失败: {e}")
            return []
    
    async def delete_all_memories(self, user_id: str, agent_id: str = None, run_id: str = None) -> bool:
        """删除所有记忆（使用 Mem0 原生 delete_all 方法）"""
        if not self.memory:
            await self.initialize()
        
        try:
            # 使用 Mem0 原生 delete_all 方法，至少需要一个过滤条件
            self.memory.delete_all(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )
            logger.info(f"成功删除记忆: user_id={user_id}, agent_id={agent_id}, run_id={run_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False
    
    async def update_memory(self, namespace: str, memory_id: str, content: str, **kwargs):
        """更新记忆（使用官方标准API）"""
        if not self.memory:
            await self.initialize()
        
        # 获取用户ID和当前时间
        user_id = kwargs.get("user_id") or kwargs.get("user_name")
        current_time = datetime.now().isoformat()
        
        # 构建更新的元数据，包含审计字段
        update_metadata = {
            "updated_by": user_id,
            "update_time": current_time
        }
        
        # 准备标准化的调用参数
        call_params = self._prepare_call_params(namespace, update_metadata, **kwargs)
        
        # 使用官方标准API更新记忆
        self.memory.update(
            memory_id, 
            content, 
            user_id=call_params["user_id"],
            agent_id=call_params.get("agent_id"),
            run_id=call_params.get("run_id")
        )
        logger.info(f"更新记忆: memory_id={memory_id}, user_id={call_params['user_id']}, updated_by={user_id}")
    
    async def delete_memory(self, namespace: str, memory_id: str, **kwargs):
        """删除记忆（使用官方标准API）"""
        if not self.memory:
            await self.initialize()
        
        # 准备标准化的调用参数  
        call_params = self._prepare_call_params(namespace, None, **kwargs)
        
        # 使用官方标准API删除记忆
        self.memory.delete(
            memory_id, 
            user_id=call_params["user_id"],
            agent_id=call_params.get("agent_id"),
            run_id=call_params.get("run_id")
        )
        logger.info(f"删除记忆: memory_id={memory_id}, user_id={call_params['user_id']}")
    
    async def store_system_architecture(self, system_id: str, architecture_info: Dict[str, Any], user_id: str):
        """存储系统架构信息"""
        content = f"""
系统ID: {system_id}
架构信息: {json.dumps(architecture_info, ensure_ascii=False, indent=2)}
"""
        await self.add_memory(
            namespace="deployment_info",
            content=content,
            metadata={
                "type": "system_architecture",
                "system_id": system_id,
                **architecture_info
            },
            user_id=user_id,
            system_id=system_id
        )
    
    async def store_incident(self, system_id: str, incident: Dict[str, Any], user_id: str):
        """存储故障案例"""
        content = f"""
故障时间: {incident.get('timestamp', datetime.now().isoformat())}
故障现象: {incident.get('symptoms', '')}
根因分析: {incident.get('root_cause', '')}
解决方案: {incident.get('solution', '')}
影响范围: {incident.get('impact', '')}
"""
        await self.add_memory(
            namespace="incident_history",
            content=content,
            metadata={
                "type": "incident",
                "system_id": system_id,
                **incident
            },
            user_id=user_id,
            system_id=system_id
        )
    
    async def store_user_preference(self, user_id: str, preference: Dict[str, Any]):
        """存储用户偏好"""
        content = f"""
用户偏好设置: {json.dumps(preference, ensure_ascii=False, indent=2)}
"""
        await self.add_memory(
            namespace="user_preferences",
            content=content,
            metadata={
                "type": "preference",
                **preference
            },
            user_id=user_id
        )
    
    async def get_diagnosis_context(self, issue: str, system_id: str, user_id: str) -> Dict[str, Any]:
        """获取诊断上下文"""
        # 1. 搜索系统架构信息
        system_memories = await self.search_memories(
            namespace="deployment_info",
            query=f"{system_id} {issue}",
            user_id=user_id,
            system_id=system_id
        )
        
        # 2. 搜索相似故障案例
        incident_memories = await self.search_memories(
            namespace="incident_history",
            query=issue,
            user_id=user_id,
            system_id=system_id
        )
        
        # 3. 搜索解决方案模式
        solution_memories = await self.search_memories(
            namespace="solution_patterns",
            query=issue,
            user_id=user_id,
            problem_type="general"
        )
        
        # 4. 获取用户偏好
        user_preferences = await self.get_all_memories(
            namespace="user_preferences",
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