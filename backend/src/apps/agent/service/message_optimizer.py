"""
消息优化服务 - 处理大文档和长对话的优化策略

功能：
1. MapReduce：单次输入过长时分块处理
2. 消息压缩：多轮对话过长时压缩历史
3. 可配置开关：安全地集成到现有系统
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import tiktoken
import json

from src.shared.core.logging import get_logger
from src.shared.core.config import settings

logger = get_logger(__name__)


@dataclass
class OptimizerConfig:
    """优化器配置"""
    enabled: bool = False  # 总开关
    
    # MapReduce配置
    enable_map_reduce: bool = True
    single_message_threshold: int = 50000  # 单条消息超过此token数触发MapReduce
    chunk_size: int = 20000  # 每个chunk的大小
    chunk_overlap: int = 1000  # chunk之间的重叠
    map_reduce_all_roles: bool = False  # 是否对所有角色的消息进行MapReduce（默认只处理user消息）
    
    # 消息压缩配置
    enable_compression: bool = True
    total_context_threshold: float = 0.8  # 超过最大上下文的80%触发压缩
    compression_target: float = 0.6  # 压缩到最大上下文的60%
    
    # 保留策略
    keep_system_messages: bool = True  # 始终保留系统消息
    keep_recent_messages: int = 10  # 始终保留最近N条消息
    

class MessageOptimizer:
    """消息优化器"""
    
    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
    def count_tokens(self, text: str) -> int:
        """计算文本的token数"""
        try:
            return len(self.encoder.encode(text))
        except Exception:
            # 粗略估算：中文约1.5字符/token，英文约4字符/token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + english_chars / 4)
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            # 角色和内容的token
            total += self.count_tokens(msg.get("role", ""))
            total += self.count_tokens(msg.get("content", ""))
            # 消息格式的额外开销
            total += 4
        return total
    
    async def optimize_messages(
        self, 
        messages: List[Dict[str, str]], 
        max_context_length: int,
        llm_instance: Any = None
    ) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """
        优化消息列表
        
        Returns:
            (优化后的消息列表, 优化信息)
        """
        if not self.config.enabled:
            return messages, {"optimized": False, "reason": "optimizer_disabled"}
        
        optimization_info = {
            "optimized": False,
            "original_tokens": 0,
            "final_tokens": 0,
            "strategies_used": []
        }
        
        # 计算原始token数
        total_tokens = self.count_messages_tokens(messages)
        optimization_info["original_tokens"] = total_tokens
        
        # 1. 先检查是否有超长的单条消息需要MapReduce（不管总量多少）
        optimized_messages = messages.copy()
        if self.config.enable_map_reduce and llm_instance:
            optimized_messages = await self._apply_map_reduce_if_needed(
                optimized_messages, llm_instance, optimization_info
            )
        elif self.config.enable_map_reduce and not llm_instance:
            logger.warning("MapReduce 已启用但 LLM 实例不可用，跳过 MapReduce 处理")
        
        # 2. 检查总长度是否需要压缩
        current_tokens = self.count_messages_tokens(optimized_messages)
        if (self.config.enable_compression and 
            current_tokens > max_context_length * self.config.total_context_threshold):
            
            target_tokens = int(max_context_length * self.config.compression_target)
            optimized_messages = await self._compress_messages(
                optimized_messages, target_tokens, llm_instance, optimization_info
            )
        
        # 记录最终结果
        optimization_info["optimized"] = len(optimization_info["strategies_used"]) > 0
        optimization_info["final_tokens"] = self.count_messages_tokens(optimized_messages)
        
        # 如果没有进行任何优化，记录原因
        if not optimization_info["optimized"]:
            if total_tokens < max_context_length * 0.5:
                optimization_info["reason"] = "within_safe_range"
            else:
                optimization_info["reason"] = "no_optimization_needed"
        
        if optimization_info["optimized"]:
            # 计算优化效果
            reduction = optimization_info["original_tokens"] - optimization_info["final_tokens"]
            reduction_rate = (reduction / optimization_info["original_tokens"]) * 100
            
            logger.info(
                f"📊 消息优化完成:\n"
                f"  - 原始 tokens: {optimization_info['original_tokens']:,}\n"
                f"  - 优化后 tokens: {optimization_info['final_tokens']:,}\n"
                f"  - 减少 tokens: {reduction:,} ({reduction_rate:.1f}%)\n"
                f"  - 使用策略: {', '.join(optimization_info['strategies_used'])}\n"
                f"  - 上下文使用率: {(optimization_info['final_tokens'] / max_context_length * 100):.1f}%"
            )
        
        return optimized_messages, optimization_info
    
    async def _apply_map_reduce_if_needed(
        self,
        messages: List[Dict[str, str]],
        llm_instance: Any,
        optimization_info: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """对超长消息应用MapReduce"""
        result_messages = []
        
        for msg in messages:
            msg_tokens = self.count_tokens(msg.get("content", ""))
            
            # 获取消息角色（兼容 role 或 type 字段）
            msg_role = msg.get("role", msg.get("type", "")).lower()
            
            # 判断是否为用户消息
            # role 字段: user → 用户消息
            # type 字段: human → 用户消息
            is_user_message = False
            if "role" in msg:
                is_user_message = msg.get("role", "").lower() == "user"
            elif "type" in msg:
                is_user_message = msg.get("type", "").lower() == "human"
            
            # 调试日志：显示消息结构
            if msg_tokens > 100:  # 只对较长消息输出调试信息
                logger.debug(
                    f"消息分析 - tokens: {msg_tokens}, role/type: '{msg_role}', "
                    f"是用户消息: {is_user_message}, 阈值: {self.config.single_message_threshold}"
                )
            
            # 只处理用户消息，系统消息通常是重要的提示词不应被压缩
            if msg_tokens > self.config.single_message_threshold and is_user_message:
                # 需要MapReduce处理
                logger.info(
                    f"🔍 检测到超长消息:\n"
                    f"  - 消息长度: {msg_tokens:,} tokens\n"
                    f"  - 触发阈值: {self.config.single_message_threshold:,} tokens\n"
                    f"  - 启动 MapReduce 处理..."
                )
                
                try:
                    reduced_content = await self._map_reduce_content(
                        msg["content"], 
                        "请提取并总结关键信息，保留重要细节。",
                        llm_instance
                    )
                    
                    # 计算优化后的token数
                    reduced_tokens = self.count_tokens(reduced_content)
                    reduction_rate = ((msg_tokens - reduced_tokens) / msg_tokens) * 100
                    
                    logger.info(
                        f"✅ MapReduce 完成:\n"
                        f"  - 原始长度: {msg_tokens:,} tokens\n"
                        f"  - 优化后长度: {reduced_tokens:,} tokens\n"
                        f"  - 压缩率: {reduction_rate:.1f}%"
                    )
                    
                    # 保持原消息的字段结构（role 或 type）
                    optimized_msg = {}
                    if "role" in msg:
                        optimized_msg["role"] = msg["role"]
                    elif "type" in msg:
                        optimized_msg["type"] = msg["type"]
                    optimized_msg["content"] = f"[已优化的长文本]\n{reduced_content}"
                    
                    result_messages.append(optimized_msg)
                    
                    optimization_info["strategies_used"].append("map_reduce")
                    
                except Exception as e:
                    logger.error(f"MapReduce处理失败: {e}")
                    result_messages.append(msg)  # 失败时保留原消息
            elif msg_tokens > self.config.single_message_threshold and not is_user_message:
                # 超长但不是用户消息
                logger.info(
                    f"⚠️ 检测到超长非用户消息:\n"
                    f"  - 消息长度: {msg_tokens:,} tokens\n"
                    f"  - 消息类型: {msg_role}\n"
                    f"  - 跳过 MapReduce 处理（仅处理用户消息）"
                )
                result_messages.append(msg)
            else:
                result_messages.append(msg)
        
        return result_messages
    
    async def _map_reduce_content(
        self,
        content: str,
        instruction: str,
        llm_instance: Any
    ) -> str:
        """
        MapReduce处理长内容
        
        Map: 将内容分块，每块独立处理
        Reduce: 合并所有块的处理结果
        """
        # 分块
        chunks = self._split_text(content)
        total_chars = len(content)
        avg_chunk_size = total_chars // len(chunks) if chunks else 0
        
        logger.info(
            f"📄 MapReduce 分块信息:\n"
            f"  - 总字符数: {total_chars:,}\n"
            f"  - 分块数量: {len(chunks)}\n"
            f"  - 平均块大小: {avg_chunk_size:,} 字符\n"
            f"  - 块大小配置: {self.config.chunk_size:,} tokens"
        )
        
        # Map阶段：并行处理每个块
        map_tasks = []
        for i, chunk in enumerate(chunks):
            prompt = f"""
{instruction}

这是第 {i+1}/{len(chunks)} 部分：

{chunk}

提取的关键信息：
"""
            map_tasks.append(self._call_llm_async(llm_instance, prompt))
        
        # 并发执行，但限制并发数
        mapped_results = await self._run_with_concurrency(map_tasks, max_concurrent=3)
        
        # Reduce阶段：合并结果
        if len(mapped_results) == 1:
            return mapped_results[0]
        
        combined_text = "\n\n".join([
            f"=== 第 {i+1} 部分提取的信息 ===\n{result}"
            for i, result in enumerate(mapped_results)
        ])
        
        # 如果合并后still太长，递归处理
        if self.count_tokens(combined_text) > self.config.single_message_threshold:
            return await self._map_reduce_content(
                combined_text, 
                "请综合以下各部分的信息，生成统一的总结：",
                llm_instance
            )
        
        # 最终reduce
        reduce_prompt = f"""
请综合以下各部分提取的信息，生成一个完整的总结：

{combined_text}

综合总结：
"""
        
        return await self._call_llm_async(llm_instance, reduce_prompt)
    
    async def _compress_messages(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int,
        llm_instance: Any,
        optimization_info: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """压缩消息历史"""
        original_count = len(messages)
        original_tokens = self.count_messages_tokens(messages)
        
        logger.info(
            f"📦 开始压缩历史消息:\n"
            f"  - 原始消息数: {original_count}\n"
            f"  - 原始 tokens: {original_tokens:,}\n"
            f"  - 目标 tokens: {target_tokens:,}\n"
            f"  - 压缩策略: 保留系统消息 + 最近 {self.config.keep_recent_messages} 条消息"
        )
        # 分离不同类型的消息
        system_messages = []
        other_messages = []
        
        for msg in messages:
            msg_role = msg.get("role", msg.get("type", "")).lower()
            # system role 或 system type 都视为系统消息
            if msg_role == "system" and self.config.keep_system_messages:
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # 保留最近的消息
        if len(other_messages) <= self.config.keep_recent_messages:
            return messages
        
        recent_messages = other_messages[-self.config.keep_recent_messages:]
        historical_messages = other_messages[:-self.config.keep_recent_messages]
        
        # 对历史消息生成摘要
        if llm_instance and len(historical_messages) > 2:
            try:
                summary = await self._summarize_messages(historical_messages, llm_instance)
                
                # 创建摘要消息，保持字段格式一致
                summary_msg = {"content": f"[历史对话摘要]\n{summary}"}
                # 使用第一个消息的格式来决定用 role 还是 type
                if messages and "role" in messages[0]:
                    summary_msg["role"] = "system"
                elif messages and "type" in messages[0]:
                    summary_msg["type"] = "system"
                else:
                    summary_msg["role"] = "system"  # 默认使用 role
                
                compressed_messages = (
                    system_messages + 
                    [summary_msg] +
                    recent_messages
                )
                
                # 计算压缩效果
                compressed_count = len(compressed_messages)
                compressed_tokens = self.count_messages_tokens(compressed_messages)
                
                logger.info(
                    f"✅ 历史压缩完成:\n"
                    f"  - 消息数: {original_count} → {compressed_count}\n"
                    f"  - Tokens: {original_tokens:,} → {compressed_tokens:,}\n"
                    f"  - 压缩率: {((original_tokens - compressed_tokens) / original_tokens * 100):.1f}%\n"
                    f"  - 历史消息生成摘要: {len(historical_messages)} 条 → 1 条摘要"
                )
                
                optimization_info["strategies_used"].append("compression")
                return compressed_messages
                
            except Exception as e:
                logger.error(f"消息压缩失败: {e}")
        
        # 如果压缩失败，使用滑动窗口
        return self._sliding_window_compression(messages, target_tokens, optimization_info)
    
    def _sliding_window_compression(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int,
        optimization_info: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """滑动窗口压缩"""
        system_messages = []
        other_messages = []
        
        for m in messages:
            msg_role = m.get("role", m.get("type", "")).lower()
            if msg_role == "system":
                system_messages.append(m)
            else:
                other_messages.append(m)
        
        # 计算系统消息的token数
        system_tokens = self.count_messages_tokens(system_messages)
        available_tokens = target_tokens - system_tokens
        
        # 从后往前保留消息
        result = []
        current_tokens = 0
        
        for msg in reversed(other_messages):
            msg_tokens = self.count_tokens(msg.get("content", "")) + 10
            if current_tokens + msg_tokens <= available_tokens:
                result.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        optimization_info["strategies_used"].append("sliding_window")
        return system_messages + result
    
    def _split_text(self, text: str) -> List[str]:
        """智能文本分块"""
        chunks = []
        
        # 优先按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            if current_tokens + para_tokens <= self.config.chunk_size:
                current_chunk += para + "\n\n"
                current_tokens += para_tokens
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                if para_tokens > self.config.chunk_size:
                    # 段落太长，需要进一步分割
                    sub_chunks = self._split_long_text(para, self.config.chunk_size)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                    current_tokens = 0
                else:
                    current_chunk = para + "\n\n"
                    current_tokens = para_tokens
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_long_text(self, text: str, max_tokens: int) -> List[str]:
        """分割超长文本"""
        chunks = []
        sentences = text.replace('。', '。\n').replace('. ', '.\n').split('\n')
        
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens <= max_tokens:
                current_chunk += sentence
                current_tokens += sentence_tokens
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
                current_tokens = sentence_tokens
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def _summarize_messages(
        self,
        messages: List[Dict[str, str]],
        llm_instance: Any
    ) -> str:
        """生成消息摘要"""
        conversation_parts = []
        for msg in messages:
            # 获取角色，兼容 role 和 type
            role = msg.get('role', msg.get('type', 'unknown')).upper()
            content = msg.get('content', '')
            if len(content) > 500:
                conversation_parts.append(f"{role}: {content[:500]}...")
            else:
                conversation_parts.append(f"{role}: {content}")
        
        conversation = "\n".join(conversation_parts)
        
        prompt = f"""
请将以下对话历史总结为关键要点，保留重要信息和上下文：

{conversation}

关键要点总结：
"""
        
        return await self._call_llm_async(llm_instance, prompt)
    
    async def _call_llm_async(self, llm_instance: Any, prompt: str) -> str:
        """异步调用LLM"""
        try:
            # 根据不同的LLM实例类型调用
            if hasattr(llm_instance, 'ainvoke'):
                response = await llm_instance.ainvoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            elif hasattr(llm_instance, 'invoke'):
                # 同步方法，使用线程池
                import concurrent.futures
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    response = await loop.run_in_executor(
                        executor, llm_instance.invoke, prompt
                    )
                return response.content if hasattr(response, 'content') else str(response)
            else:
                raise ValueError("Unsupported LLM instance type")
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise
    
    async def _run_with_concurrency(
        self,
        tasks: List[asyncio.Task],
        max_concurrent: int = 3
    ) -> List[Any]:
        """限制并发执行任务"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[bounded_task(task) for task in tasks])


# 全局实例
message_optimizer = MessageOptimizer()


def get_optimizer_config() -> OptimizerConfig:
    """从配置文件或环境变量获取优化器配置"""
    return OptimizerConfig(
        enabled=getattr(settings, 'MESSAGE_OPTIMIZER_ENABLED', False),
        # 单条消息优化配置
        enable_map_reduce=getattr(settings, 'SINGLE_MSG_ENABLE_MAP_REDUCE', True),
        single_message_threshold=getattr(settings, 'SINGLE_MSG_TOKEN_THRESHOLD', 50000),
        chunk_size=getattr(settings, 'SINGLE_MSG_CHUNK_SIZE', 20000),
        # 多轮会话优化配置
        enable_compression=getattr(settings, 'MULTI_TURN_ENABLE_COMPRESSION', True),
        total_context_threshold=getattr(settings, 'MULTI_TURN_CONTEXT_THRESHOLD', 0.8),
        compression_target=getattr(settings, 'MULTI_TURN_COMPRESSION_TARGET', 0.6),
    )


def get_optimizer_llm():
    """获取消息优化器使用的 LLM 实例"""
    try:
        from langchain_openai import ChatOpenAI
        from src.shared.db.config import get_sync_db
        from src.apps.ai_model.models import AIModelConfig
        
        # 获取配置的模型名称
        model_name = getattr(settings, 'MESSAGE_OPTIMIZER_MODEL_NAME', 'deepseek-chat')
        
        # 从数据库获取模型配置
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            # 注意：model_type 字段存储的是实际的模型标识（如 deepseek-chat）
            # 而不是 name 字段（那是用户友好的显示名称）
            model = db.query(AIModelConfig).filter(
                AIModelConfig.model_type == model_name
            ).first()
            
            if not model:
                logger.warning(f"未找到配置的优化器模型: {model_name}")
                return None
                
            # 创建 ChatOpenAI 实例
            import httpx
            
            # 创建一个禁用SSL验证的httpx客户端
            # 注意：ChatOpenAI会管理这个client的生命周期
            http_client = httpx.Client(
                verify=False,  # 关闭 SSL 校验
                timeout=30.0
            )
            
            llm = ChatOpenAI(
                model=model.model_type,
                api_key=model.api_key_value,  # 注意：数据库字段是 api_key_value
                base_url=model.endpoint_url,   # 注意：数据库字段是 endpoint_url
                temperature=0.3,  # 降低温度以获得更稳定的摘要
                timeout=30,
                http_client=http_client
            )
            
            logger.info(f"成功创建优化器 LLM: {model_name}")
            return llm
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"创建优化器 LLM 失败: {e}")
        return None


async def optimize_messages_if_needed(
    graph_input: Dict[str, Any],
    max_context_length: Optional[int] = None
) -> None:
    """
    便捷函数：根据配置优化消息
    直接修改 graph_input 中的 messages
    
    Args:
        graph_input: 包含 messages 的输入字典
        max_context_length: 可选的上下文长度限制（如果不提供，将使用默认值）
    """
    # 检查是否启用
    config = get_optimizer_config()
    if not config.enabled:
        return
    
    if not graph_input or "messages" not in graph_input:
        return
    
    # 使用提供的上下文长度或默认值
    if max_context_length is None:
        max_context_length = 128000
        
        # 尝试从优化器模型配置获取上下文长度
        try:
            from src.shared.db.config import get_sync_db
            from src.apps.ai_model.models import AIModelConfig
            
            model_name = getattr(settings, 'MESSAGE_OPTIMIZER_MODEL_NAME', 'deepseek-chat')
            
            db_gen = get_sync_db()
            db = next(db_gen)
            try:
                model = db.query(AIModelConfig).filter(
                    AIModelConfig.model_type == model_name
                ).first()
                
                if model and model.config_data:
                    config_data = json.loads(model.config_data) if isinstance(model.config_data, str) else model.config_data
                    context_length = config_data.get("context_length")
                    if context_length:
                        max_context_length = int(context_length)
                        logger.info(f"使用优化器模型 {model_name} 的上下文长度: {max_context_length}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"获取优化器模型配置失败: {e}")
    
    # 获取 LLM 实例（如果需要的话）
    llm_instance = None
    if config.enable_map_reduce or config.enable_compression:
        llm_instance = get_optimizer_llm()
        if not llm_instance:
            logger.warning("无法获取优化器 LLM 实例，将跳过需要 LLM 的优化")
            # 如果无法获取 LLM，禁用需要 LLM 的功能
            config.enable_map_reduce = False
            config.enable_compression = False
        else:
            logger.info(f"✅ LLM 实例已准备就绪，MapReduce={config.enable_map_reduce}, Compression={config.enable_compression}")
    
    # 执行优化
    optimizer = message_optimizer
    optimizer.config = config
    
    messages = graph_input["messages"]
    message_count = len(messages)
    total_tokens = optimizer.count_messages_tokens(messages)
    
    
    # 分析每条消息的长度
    message_details = []
    max_single_tokens = 0
    for i, msg in enumerate(messages):
        msg_tokens = optimizer.count_tokens(msg.get("content", ""))
        max_single_tokens = max(max_single_tokens, msg_tokens)
        if msg_tokens > 100:  # 只记录较长的消息
            role = msg.get('role', msg.get('type', 'unknown'))  # 兼容 role 或 type 字段
            # 如果是第一条消息且角色未知，输出消息的键
            if i == 0 and role == 'unknown':
                msg_keys = list(msg.keys()) if isinstance(msg, dict) else []
                message_details.append(f"    - {role}[{i}]: {msg_tokens:,} tokens (keys: {msg_keys})")
            else:
                message_details.append(f"    - {role}[{i}]: {msg_tokens:,} tokens")
    
    log_message = (
        f"🚀 开始消息优化:\n"
        f"  - 消息数量: {message_count}\n"
        f"  - 总 tokens: {total_tokens:,}\n"
        f"  - 最大单条: {max_single_tokens:,} tokens\n"
        f"  - 上下文限制: {max_context_length:,}\n"
        f"  - 使用率: {(total_tokens / max_context_length * 100):.1f}%\n"
        f"  - MapReduce阈值: {config.single_message_threshold:,} tokens"
    )
    
    if message_details:
        log_message += f"\n  - 详细消息长度:\n" + "\n".join(message_details)
    
    logger.info(log_message)
    
    optimized_messages, info = await optimizer.optimize_messages(
        messages, 
        max_context_length,
        llm_instance
    )
    
    # 更新消息
    graph_input["messages"] = optimized_messages
    
    # 记录日志（简洁版，详细信息已在 optimize_messages 中输出）
    if info.get("optimized"):
        logger.info(
            f"🎯 优化器执行完成 - "
            f"策略: {', '.join(info.get('strategies_used', []))}"
        )