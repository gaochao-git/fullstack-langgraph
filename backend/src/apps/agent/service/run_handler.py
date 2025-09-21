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
from .document_service import document_service
from ..utils import serialize_value
from .user_threads_db import (check_user_thread_exists,create_user_thread_mapping)
from ..llm_agents.agent_registry import AgentRegistry
from .agent_service import agent_service
from ..models import AgentDocumentSession
from ..llm_agents.hooks import create_token_usage_hook
logger = get_logger(__name__)

# 定义运行请求体
class RunCreate(BaseModel):
    agent_id: str  # 智能体ID（必需）
    user_name: str  # 用户名（必需）
    query: str  # 查询内容（必需）
    chat_mode: str = "streaming"  # 聊天模式：streaming 或 blocking
    file_ids: Optional[List[str]] = None  # 文件ID列表（可选）
    config: Optional[Dict[str, Any]] = None  # 配置信息（可选）
    

async def prepare_run(thread_id: str, request_body: RunCreate, request=None) -> tuple[str, dict, str]:
    """更新智能体使用统计，确保用户线程映射"""
    # 更新智能体使用统计
    agent_id = request_body.agent_id
    try:
        async with get_async_db_context() as async_db:
            await agent_service.increment_run_count(async_db, agent_id)
    except Exception as e:
        # 统计更新失败不影响主流程
        logger.error(f"更新智能体统计失败: {e}", exc_info=True)
    
    # 使用请求中的 user_name
    user_name = request_body.user_name
    try:
        await ensure_user_thread_mapping(user_name, thread_id, request_body)
    except Exception as e:
         # 不影响主流程，继续执行 
        logger.error(f"处理用户线程关联时出错: {e}", exc_info=True)


async def ensure_user_thread_mapping(user_name, thread_id, request_body):
    """
    确保用户和线程的归属已写入user_threads表，如不存在则自动写入。
    自动提取thread_title（取query内容前20字）。
    """
    exists = await check_user_thread_exists(user_name, thread_id)
    if not exists:
        # 使用 query 作为标题
        thread_title = request_body.query[:20] + "..." if len(request_body.query) > 20 else request_body.query
        
        # 从request_body中获取agent_id，内部作为agent_id使用
        agent_id = request_body.agent_id
        
        logger.info(f"创建用户线程映射: user_name={user_name}, thread_id={thread_id}, thread_title={thread_title}, agent_id={agent_id}")
        await create_user_thread_mapping(user_name, thread_id, thread_title, agent_id)

def prepare_config(request_body, thread_id):
    """准备配置 - 公共方法"""
    config = request_body.config or {}
    
    # 提取 stream_mode 和其他配置
    stream_mode = config.get("stream_mode", ["updates", "messages", "values"])
    selected_model = config.get("selected_model")
    
    # 构建新的配置结构
    new_config = {
        "configurable": {
            "thread_id": thread_id,
            "user_name": request_body.user_name,
            "agent_id": request_body.agent_id
        },
        "recursion_limit": config.get("recursion_limit", 100)
    }
    
    # 添加模型选择
    if selected_model:
        new_config["configurable"]["selected_model"] = selected_model
        
    return new_config, stream_mode


async def prepare_graph_input(request_body, config, thread_id):
    """准备图输入 - 构建消息格式并处理文档上下文"""
    # 构建消息格式的输入
    messages = [{"type": "human","content": request_body.query}]
    
    # 如果有文档，获取文档信息并添加到消息中
    docs_info = []
    if request_body.file_ids:
        logger.info(f"检测到关联文档 {len(request_body.file_ids)} 个: {request_body.file_ids}")
        
        # 使用异步方法获取文档元信息（不包含内容）
        async with get_async_db_context() as db:
            docs_info = await document_service.get_documents_info_async(db, request_body.file_ids)
        
        if docs_info:
            logger.info(f"成功获取 {len(docs_info)} 个文档的元信息")
            # 构建files数组，包含文件的完整信息
            files = []
            for doc in docs_info:
                files.append({
                    "file_id": doc['file_id'],
                    "file_name": doc['file_name'],
                    "file_size": doc['file_size']
                })
            
            # 将files信息添加到消息中，系统会自动转为additional_kwargs
            messages[0]["files"] = files
            logger.debug(f"已将文件信息添加到消息的 files 字段")
        else:
            logger.warning(f"未能获取到任何文档信息")
    
    graph_input = {"messages": messages}
    
    # 如果有关联的文档，将文档元信息添加到消息上下文中
    if docs_info:
            # 构建文档信息的提示
            files_summary = "\n".join([f"- {doc['file_name']} (ID: {doc['file_id']}, 大小: {doc['file_size']} bytes)" for doc in docs_info])
            
            # 在用户消息前插入文档元信息作为系统消息
            doc_message = {
                "type": "system",
                "content": f"""用户上传了以下文档供参考{files_summary}"""
            }
            graph_input["messages"].insert(0, doc_message)
            logger.info(f"已添加文档元信息，共 {len(docs_info)} 个文档")
            
            # 保存会话和文档的关联
            agent_id = config.get("configurable", {}).get("agent_id", "diagnostic_agent")
            user_name = config.get("configurable", {}).get("user_name", "system")
            await save_thread_file_associations(thread_id, request_body.file_ids, agent_id, user_name)
    
    return graph_input


async def process_stream_chunk(chunk, event_id):
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
            logger.error(f"未知的chunk格式，长度={len(chunk)}")
            raise BadRequestException("未知的chunk格式")
        
        serialized_data = serialize_value(data)
        
        # Check for interrupts
        has_interrupt = False
        if event_type == "updates" and isinstance(data, dict) and "__interrupt__" in data:
            logger.info(f"Interrupt detected: {data}")
            interrupt_data = data["__interrupt__"]
            
            # 检查 interrupt_data 是否为空
            if not interrupt_data or len(interrupt_data) == 0:
                logger.warning(f"检测到空的中断数据: {interrupt_data}")
            
            has_interrupt = True
        
        return f"id: {event_id}\nevent: {event_type}\ndata: {json.dumps(serialized_data, ensure_ascii=False)}\n\n", has_interrupt
    else:
        # Handle dict format (fallback)
        serializable_chunk = {}
        for key, value in chunk.items(): serializable_chunk[key] = serialize_value(value)
        event_type = list(serializable_chunk.keys())[0] if serializable_chunk else "data"
        return f"id: {event_id}\nevent: {event_type}\ndata: {json.dumps(serializable_chunk[event_type], ensure_ascii=False)}\n\n", False


async def execute_graph_request(request_body: RunCreate, thread_id: str, request=None, is_streaming: bool = True):
    """执行图请求的通用函数 - 支持流式和非流式"""
    # 准备运行（更新统计、确保线程映射）
    await prepare_run(thread_id, request_body, request)
    
    # 创建运行日志
    run_log_id = None
    try:
        from .run_log_service import run_log_service
        from src.shared.db.config import get_async_db_context
        
        # 获取客户端信息
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if hasattr(request, 'client') else None
            user_agent = request.headers.get('user-agent', None)
        
        async with get_async_db_context() as db:
            run_log = await run_log_service.create_run_log(
                db=db,
                agent_id=request_body.agent_id,
                thread_id=thread_id,
                user_name=request_body.user_name,
                ip_address=ip_address,
                user_agent=user_agent
            )
            run_log_id = run_log.id
            logger.info(f"创建运行日志: {run_log_id}")
    except Exception as e:
        # 日志创建失败不影响主流程
        logger.error(f"创建运行日志失败: {e}", exc_info=True)
    
    # 准备配置（返回 config, stream_mode）
    config, stream_modes = prepare_config(request_body, thread_id)
    
    # 准备输入（包括处理文档上下文）
    graph_input = await prepare_graph_input(request_body, config, thread_id)
    
    # 创建图
    graph = await AgentRegistry.create_agent(request_body.agent_id, config)
    logger.info(f"[Agent创建] 动态创建智能体graph: {graph}")
    
    if is_streaming:
        # 流式处理
        logger.info(f"Starting stream with modes: {stream_modes}")
        
        event_id = 0
        has_interrupt = False
        collected_messages = []  # 收集所有消息用于计算token
        
        # 获取LLM配置以计算token限制
        llm_config = None
        try:
            from ..llm_agents.agent_utils import get_llm_config_from_db
            llm_config = await get_llm_config_from_db(request_body.agent_id)
        except Exception as e:
            logger.warning(f"获取LLM配置失败: {e}")
        
        # 创建token使用监控器
        token_usage_hook = create_token_usage_hook(llm_config)
        
        async for chunk in graph.astream(graph_input, config=config, stream_mode=stream_modes, subgraphs=True):
            try:
                event_id += 1
                sse_data, chunk_has_interrupt = await process_stream_chunk(chunk, event_id)
                yield sse_data
                if chunk_has_interrupt: has_interrupt = True
                
                # 收集消息用于token统计
                if isinstance(chunk, tuple) and len(chunk) >= 2:
                    event_type, data = chunk[-2:]  # 获取最后两个元素
                    if event_type == "values" and isinstance(data, dict) and "messages" in data:
                        collected_messages = data["messages"]
                
            except Exception as e:
                logger.error(f"Serialization error: {e}, chunk type: {type(chunk)}, chunk: {chunk}", exc_info=True)
                event_id += 1
                yield f"id: {event_id}\nevent: error\ndata: {json.dumps({'error': str(e), 'chunk_type': str(type(chunk)), 'chunk': str(chunk)}, ensure_ascii=False)}\n\n"
        
        # 在流结束时发送token使用情况
        if collected_messages:
            total_tokens = token_usage_hook.count_messages_tokens(collected_messages)
            max_tokens = token_usage_hook.max_context_length
            usage_ratio = total_tokens / max_tokens
            
            event_id += 1
            token_usage_event = {
                "thread_id": thread_id,
                "token_usage": {
                    "used": total_tokens,
                    "total": max_tokens,
                    "percentage": round(usage_ratio * 100, 1),
                    "remaining": max_tokens - total_tokens
                }
            }
            yield f"id: {event_id}\nevent: token_usage\ndata: {json.dumps(token_usage_event, ensure_ascii=False)}\n\n"
            logger.info(f"📊 发送token使用情况: {total_tokens}/{max_tokens} ({usage_ratio*100:.1f}%)")
        
        # End event - only send if no interrupt occurred
        if not has_interrupt:
            event_id += 1
            yield f"id: {event_id}\nevent: end\ndata: {json.dumps({'status': 'completed'}, ensure_ascii=False)}\n\n"
        else:
            logger.info("Skipping end event due to interrupt - waiting for user approval")
    else:
        # 非流式处理
        result = await graph.ainvoke(graph_input, config=config, stream_mode=stream_modes)
        
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
        
        yield final_response


async def stream_run_standard(thread_id: str, request_body: RunCreate, request=None):
    """Standard LangGraph streaming endpoint - 支持动态智能体检查"""
    # 暂时禁用心跳以避免MCP CloseResourceError
    # TODO: 需要更好的解决方案来处理心跳与MCP工具的兼容性
    async def generate():
        """恢复原始的流式处理（暂时禁用心跳）"""
        try:
            # 使用通用执行函数，流式模式
            async for item in execute_graph_request(request_body, thread_id, request, is_streaming=True):
                yield item
            
            # 更新运行日志为成功
            try:
                from .run_log_service import run_log_service
                from src.shared.db.config import get_async_db_context
                from src.shared.db.models import now_shanghai
                
                async with get_async_db_context() as db:
                    await run_log_service.update_run_log(
                        db=db,
                        thread_id=thread_id,
                        run_status='success',
                        end_time=now_shanghai()
                    )
            except Exception as log_e:
                logger.error(f"更新运行日志失败: {log_e}")
                
        except Exception as e:
            logger.error(f"流式处理异常: {e}", exc_info=True)
            
            # 更新运行日志为失败
            try:
                from .run_log_service import run_log_service
                from src.shared.db.config import get_async_db_context
                from src.shared.db.models import now_shanghai
                
                async with get_async_db_context() as db:
                    await run_log_service.update_run_log(
                        db=db,
                        thread_id=thread_id,
                        run_status='failed',
                        end_time=now_shanghai(),
                        error_message=str(e)
                    )
            except Exception as log_e:
                logger.error(f"更新运行日志失败: {log_e}")
            
            yield f"event: error\n"
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"
    
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
    try:
        # 使用通用执行函数，非流式模式
        async for final_response in execute_graph_request(request_body, thread_id, request, is_streaming=False):
            # 非流式模式只会yield一次结果
            # 更新运行日志为成功
            try:
                from .run_log_service import run_log_service
                from src.shared.db.config import get_async_db_context
                from src.shared.db.models import now_shanghai
                
                async with get_async_db_context() as db:
                    await run_log_service.update_run_log(
                        db=db,
                        thread_id=thread_id,
                        run_status='success',
                        end_time=now_shanghai()
                    )
            except Exception as log_e:
                logger.error(f"更新运行日志失败: {log_e}")
                
            return success_response(final_response)
    except Exception as e:
        logger.error(f"非流式调用失败: {e}", exc_info=True)
        
        # 更新运行日志为失败
        try:
            from .run_log_service import run_log_service
            from src.shared.db.config import get_async_db_context
            from src.shared.db.models import now_shanghai
            
            async with get_async_db_context() as db:
                await run_log_service.update_run_log(
                    db=db,
                    thread_id=thread_id,
                    run_status='failed',
                    end_time=now_shanghai(),
                    error_message=str(e)
                )
        except Exception as log_e:
            logger.error(f"更新运行日志失败: {log_e}")
            
        raise BusinessException(f"处理请求时出错: {str(e)}", ResponseCode.INTERNAL_ERROR)


async def completion_handler(thread_id: str, request_body: RunCreate, request=None):
    """统一的补全处理函数 - 支持流式和非流式"""
    if request_body.chat_mode == "streaming":
        # 流式处理
        return await stream_run_standard(thread_id, request_body, request)
    elif request_body.chat_mode == "blocking":
        # 非流式处理
        return await invoke_run_standard(thread_id, request_body, request)
    else:
        raise BusinessException(f"chat_mode必须是 'streaming' 或 'blocking'", ResponseCode.BAD_REQUEST)


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