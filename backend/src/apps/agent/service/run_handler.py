"""
Agent 运行处理模块
处理 LangGraph Agent 的流式和非流式运行请求
"""
import json
from typing import Dict, Any, List
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode, success_response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from src.shared.db.config import get_async_db_context
from ..checkpoint_factory import create_checkpointer
from .document_service import document_service
from src.shared.db.config import get_sync_db
from ..utils import (prepare_graph_config, serialize_value)
from .user_threads_db import (check_user_thread_exists,create_user_thread_mapping)
from ..llm_agents.agent_registry import AgentRegistry
from .agent_config_service import AgentConfigService
from .agent_service import agent_service
from ..models import AgentDocumentSession
logger = get_logger(__name__)

# 定义运行请求体
class RunCreate(BaseModel):
    assistant_id: str  # 智能体ID（必需）
    input: Dict[str, Any]  # 输入消息（必需）
    config: Dict[str, Any]  # 配置信息（必需）
    stream_mode: List[str] = ["values"]  # 流式模式（必需，有默认值）
    command: Optional[Dict[str, Any]] = None
    

async def prepare_run(thread_id: str, request_body: RunCreate, request=None) -> tuple[str, dict, str]:
    """验证和准备运行参数 - 公共方法，提取stream_run_standard和invoke_run_standard的重复逻辑"""
    # 更新智能体使用统计
    agent_id = request_body.assistant_id
    try:
        async with get_async_db_context() as async_db:
            await agent_service.increment_run_count(async_db, agent_id)
            logger.info(f"✅ 已更新智能体 {agent_id} 的使用统计")
    except Exception as e:
        # 统计更新失败不影响主流程
        logger.error(f"更新智能体统计失败: {e}", exc_info=True)
    # 用户线程映射
    current_user = None
    if request and hasattr(request.state, 'current_user'): current_user = request.state.current_user
    if not current_user: raise BusinessException("无法获取用户信息", ResponseCode.BAD_REQUEST)
    # 获取用户名
    user_name = current_user.get('username')
    try:
        await ensure_user_thread_mapping(user_name, thread_id, request_body)
    except Exception as e:
         # 不影响主流程，继续执行 
        logger.error(f"处理用户线程关联时出错: {e}", exc_info=True)
    return agent_id, agent_config, user_name


async def ensure_user_thread_mapping(user_name, thread_id, request_body):
    """
    确保用户和线程的归属已写入user_threads表，如不存在则自动写入。
    自动提取thread_title（取消息内容前20字）。
    """
    logger.info(f"[ensure_user_thread_mapping] called with user_name={user_name}, thread_id={thread_id}")
    exists = await check_user_thread_exists(user_name, thread_id)
    logger.info(f"[ensure_user_thread_mapping] exists={exists}")
    if not exists:
        thread_title = None
        if hasattr(request_body, 'input') and request_body.input and "messages" in request_body.input:
            messages = request_body.input["messages"]
            if messages and len(messages) > 0:
                last_msg = messages[-1]
                if isinstance(last_msg, dict) and "content" in last_msg:
                    content = str(last_msg["content"])
                    thread_title = content[:20] + "..." if len(content) > 20 else content
        
        # 从request_body中获取assistant_id，内部作为agent_id使用
        agent_id = getattr(request_body, 'assistant_id', None)
        
        logger.info(f"[ensure_user_thread_mapping] creating mapping: user_name={user_name}, thread_id={thread_id}, thread_title={thread_title}, agent_id={agent_id}")
        await create_user_thread_mapping(user_name, thread_id, thread_title, agent_id)

async def process_stream_chunk(chunk, event_id, thread_id):
    """处理单个流式数据块"""    
    # Handle tuple format from LangGraph streaming
    if isinstance(chunk, tuple) and len(chunk) >= 2:
        if len(chunk) == 2:
            # 标准格式: (event_type, data)
            event_type, data = chunk
        elif len(chunk) == 3:
            # 子图格式: (namespace, event_type, data)
            namespace, event_type, data = chunk
        else:
            # 未知格式，尝试获取最后两个元素
            event_type, data = chunk[-2:]
            logger.warning(f"⚠️ 未知的chunk格式，长度={len(chunk)}, 尝试使用后两个元素")
        
        serialized_data = serialize_value(data)
        
        # Save messages to thread history from LangGraph state
        if event_type == "values" and isinstance(data, dict) and "messages" in data:
            # 不再操作thread_messages
            pass
        
        # Also save messages from updates events (when nodes return message updates)
        elif event_type == "updates" and isinstance(data, dict):
            for node_name, node_data in data.items():
                if isinstance(node_data, dict) and "messages" in node_data:
                    # 不再操作thread_messages
                    pass
                break  # Only process the first node with messages
        
        # Check for interrupts
        has_interrupt = False
        if event_type == "updates" and isinstance(data, dict) and "__interrupt__" in data:
            logger.info(f"Interrupt detected: {data}")
            interrupt_data = data["__interrupt__"]
            
            # 检查 interrupt_data 是否为空
            if interrupt_data and len(interrupt_data) > 0:
                # 不再操作thread_interrupts
                pass
            else:
                logger.warning(f"⚠️ 检测到空的中断数据: {interrupt_data}")
                
                # 处理空的中断数据：创建工具审批请求
                # 这通常发生在 create_react_agent 使用 interrupt_before=["tools"] 时
                # 不再操作thread_interrupts
                pass
            
            has_interrupt = True
        
        return f"id: {event_id}\nevent: {event_type}\ndata: {json.dumps(serialized_data, ensure_ascii=False)}\n\n", has_interrupt
    else:
        # Handle dict format (fallback)
        serializable_chunk = {}
        for key, value in chunk.items():
            serializable_chunk[key] = serialize_value(value)
        
        event_type = list(serializable_chunk.keys())[0] if serializable_chunk else "data"
        return f"id: {event_id}\nevent: {event_type}\ndata: {json.dumps(serializable_chunk[event_type], ensure_ascii=False)}\n\n", False

async def stream_with_graph_postgres(graph, request_body, thread_id):
    """PostgreSQL模式专用的图流媒体处理函数"""
    config, graph_input, stream_modes, checkpoint = prepare_graph_config(request_body, thread_id)
    
    # 从消息中获取 file_ids
    file_ids = None
    
    if graph_input and "messages" in graph_input:
        messages = graph_input["messages"]
        if messages and len(messages) > 0:
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                # 从消息本身获取 file_ids
                file_ids = last_msg.get("file_ids")
    
    # 如果有关联的文档，将文档内容添加到消息上下文中
    if file_ids:
        logger.info(f"检测到关联文档: {file_ids}, 文档数量: {len(file_ids) if isinstance(file_ids, list) else 'N/A'}")
        
        
        # 获取文档上下文
        doc_context = document_service.get_document_context(file_ids)
        if doc_context:
            # 在用户消息前插入文档上下文作为系统消息
            doc_message = {
                "type": "system",
                "content": f"请参考以下文档内容回答用户问题：\n\n{doc_context}"
            }
            graph_input["messages"].insert(0, doc_message)
            logger.info(f"已添加文档上下文，长度: {len(doc_context)} 字符")
            
            # 保存会话和文档的关联
            agent_id = config.get("configurable", {}).get("agent_id", "diagnostic_agent")
            user_name = config.get("configurable", {}).get("user_name", "system")
            await save_thread_file_associations(thread_id, file_ids, agent_id, user_name)
    
    
    logger.info(f"Starting stream with modes: {stream_modes}, checkpoint: {checkpoint}")
    
    event_id = 0
    has_interrupt = False
    
    async for chunk in graph.astream(graph_input, config=config, stream_mode=stream_modes, subgraphs=True):
        try:
            event_id += 1
            sse_data, chunk_has_interrupt = await process_stream_chunk(chunk, event_id, thread_id)
            yield sse_data
            if chunk_has_interrupt:
                has_interrupt = True
        except Exception as e:
            logger.error(f"Serialization error: {e}, chunk type: {type(chunk)}, chunk: {chunk}", exc_info=True)
            event_id += 1
            yield f"id: {event_id}\nevent: error\ndata: {json.dumps({'error': str(e), 'chunk_type': str(type(chunk)), 'chunk': str(chunk)}, ensure_ascii=False)}\n\n"
    
    # End event - only send if no interrupt occurred
    if not has_interrupt:
        event_id += 1
        yield f"id: {event_id}\nevent: end\ndata: {json.dumps({'status': 'completed'}, ensure_ascii=False)}\n\n"
    else:
        logger.info("Skipping end event due to interrupt - waiting for user approval")

async def handle_chat_streaming(request_body, thread_id):
    """处理PostgreSQL模式的流式响应 - 完全基于数据库配置"""    
    # 从 assistant_id 获取内部使用的 agent_id
    agent_id = request_body.assistant_id    
    # 按照官方模式：在async with内完成整个请求周期
    async with create_checkpointer() as checkpointer:
        # 将agent_id添加到config中
        if not request_body.config: request_body.config = {}
        if not request_body.config.get("configurable"): request_body.config["configurable"] = {}
        request_body.config["configurable"]["agent_id"] = agent_id
        
        # 使用注册中心动态创建 Agent
        graph = await AgentRegistry.create_agent(agent_id, request_body.config, checkpointer)
        logger.info(f"[Agent创建] 动态创建智能体graph: {graph}")
        
        # 在同一个async with内执行完整的流式处理
        async for item in stream_with_graph_postgres(graph, request_body, thread_id):
            yield item

async def stream_run_standard(thread_id: str, request_body: RunCreate, request=None):
    """Standard LangGraph streaming endpoint - 支持动态智能体检查"""
    
    # 使用公共方法验证和准备运行参数
    await prepare_run(thread_id, request_body, request)

    async def generate():
        try:
            async for item in handle_chat_streaming(request_body, thread_id):
                yield item
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error in streaming: {e}")
            logger.error(f"Full traceback: {error_details}")
            yield f"event: error\n"
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'traceback': error_details}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/event-stream"
        }
    )


async def invoke_run_standard(thread_id: str, request_body: RunCreate, request=None):
    """Standard LangGraph non-streaming endpoint - 非流式调用"""    
    await prepare_run(thread_id, request_body, request)    
    agent_id = request_body.assistant_id
    return await handle_chat_invoke(thread_id, request_body, agent_id)


async def handle_chat_invoke(thread_id: str, request_body: RunCreate, agent_id: str):
    """PostgreSQL 模式下的非流式处理"""
    async with create_checkpointer() as checkpointer:
        # 准备配置和输入
        config, graph_input, _, checkpoint = prepare_graph_config(request_body, thread_id)
        
        # 在配置中添加 agent_id
        config["configurable"]["agent_id"] = agent_id
        
        # 使用注册中心动态创建 Agent
        graph = await AgentRegistry.create_agent(agent_id, config, checkpointer)
        
        # 从消息中获取 file_ids（如果有）
        file_ids = None
        if graph_input and "messages" in graph_input:
            messages = graph_input["messages"]
            if messages and len(messages) > 0:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    # 从消息本身获取 file_ids
                    file_ids = last_msg.get("file_ids")
        
        # 如果有文档，添加文档上下文
        if file_ids:
            logger.info(f"非流式调用检测到关联文档: {file_ids}, 文档数量: {len(file_ids) if isinstance(file_ids, list) else 'N/A'}")
            # 获取文档上下文
            doc_context = document_service.get_document_context(file_ids)
            if doc_context:
                # 在用户消息前插入文档上下文作为系统消息
                doc_message = {
                    "type": "system",
                    "content": f"请参考以下文档内容回答用户问题：\n\n{doc_context}"
                }
                graph_input["messages"].insert(0, doc_message)
                logger.info(f"已添加文档上下文，长度: {len(doc_context)} 字符")
        
        # user_name 从 config.configurable 获取
        user_name = None
        if request_body.config and request_body.config.get("configurable"):
            user_name = request_body.config["configurable"].get("user_name")
        
        if file_ids and user_name:
            await save_thread_file_associations(thread_id, file_ids, agent_id, user_name)
        
        # 非流式调用
        try:
            result = await graph.ainvoke(graph_input, config=config)
            
            # 处理结果
            final_response = {
                "thread_id": thread_id,
                "status": "completed",
                "result": result
            }
            
            # 如果结果中有messages，提取最后一条AI消息
            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                # 找到最后一条AI消息
                for message in reversed(messages):
                    # 检查 role 或 type 字段
                    is_ai_message = False
                    if hasattr(message, "role") and message.role == "assistant":
                        is_ai_message = True
                    elif hasattr(message, "type") and message.type == "ai":
                        is_ai_message = True
                    
                    if is_ai_message:
                        final_response["last_message"] = {
                            "content": getattr(message, "content", str(message)),
                            "type": "ai"  # 统一使用 type，与 LangGraph 消息格式保持一致
                        }
                        break
            
            # 检查是否有中断
            state = await checkpointer.aget(config)
            if state:
                # state 可能是一个字典或对象
                next_nodes = state.get("next") if isinstance(state, dict) else getattr(state, "next", None)
                if next_nodes:
                    final_response["status"] = "interrupted"
                    final_response["interrupted_at"] = list(next_nodes)
            
            return success_response(final_response)
            
        except Exception as e:
            logger.error(f"非流式调用失败: {e}", exc_info=True)
            raise BusinessException(f"处理请求时出错: {str(e)}", ResponseCode.INTERNAL_ERROR)


async def save_thread_file_associations(thread_id: str, file_ids: List[str], agent_id: str, user_name: str) -> None:
    """
    保存会话和文档的关联关系
    
    Args:
        thread_id: 会话线程ID
        file_ids: 文件ID列表
        agent_id: 智能体ID
        user_name: 用户名
    """    
    try:
        async with get_async_db_context() as db:
            for file_id in file_ids:
                # 检查是否已存在关联
                result = await db.execute(
                    select(AgentDocumentSession).where(
                        AgentDocumentSession.thread_id == thread_id,
                        AgentDocumentSession.file_id == file_id
                    )
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    # 创建新的关联
                    session = AgentDocumentSession(
                        thread_id=thread_id,
                        file_id=file_id,
                        agent_id=agent_id,
                        create_by=user_name
                    )
                    db.add(session)
            
            await db.commit()
            logger.info(f"✅ 保存会话文档关联成功: thread_id={thread_id}, files={file_ids}")
    except Exception as e:
        logger.error(f"保存会话文档关联失败: {e}", exc_info=True)
        # 不影响主流程


async def get_thread_file_ids(thread_id: str) -> List[str]:
    """
    获取会话关联的文件ID列表
    
    Args:
        thread_id: 会话线程ID
        
    Returns:
        文件ID列表
    """
    
    
    try:
        async with get_async_db_context() as db:
            result = await db.execute(
                select(AgentDocumentSession.file_id)
                .where(AgentDocumentSession.thread_id == thread_id)
                .order_by(AgentDocumentSession.create_time)
            )
            
            file_ids = [row[0] for row in result.fetchall()]
            logger.info(f"✅ 获取会话文档关联成功: thread_id={thread_id}, files={file_ids}")
            return file_ids
    except Exception as e:
        logger.error(f"获取会话文档关联失败: {e}", exc_info=True)
        return []