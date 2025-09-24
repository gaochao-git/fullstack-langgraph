"""
Agent 模块的 Celery 任务
包括智能体定时任务执行和健康检查
"""
import json
import requests
from datetime import datetime
from src.celery.celery import app
from src.celery.db_utils import get_db_session
from src.celery.sync_db_helpers import (
    test_database_connection_sync,
    count_registered_agents_sync
)
from src.apps.scheduled_task.celery_models import (
    CeleryPeriodicTaskConfig as PeriodicTask
)
from src.shared.core.logging import get_logger
from src.shared.db.models import now_shanghai

logger = get_logger(__name__)

DB_RETRY_MAX = 3  # 数据库重试次数


def record_periodic_task_result(task_name, execution_time, status, result_data):
    """记录定时任务执行结果到日志（原数据库记录功能已禁用）"""
    # 改为只记录日志，不写数据库
    logger.info(f"任务执行完成 - 任务: {task_name}, 状态: {status}, 时间: {execution_time}")
    if result_data:
        logger.debug(f"任务结果详情: {json.dumps(result_data, ensure_ascii=False)}")


@app.task(bind=True, soft_time_limit=60, time_limit=120)
def periodic_agent_health_check(self):
    """
    定期检查智能体服务健康状态
    """
    execution_time = now_shanghai()
    logger.info("执行智能体健康检查任务")
    
    try:
        # 使用同步方法检查Agent和数据库
        # 检查Agent数量（从数据库获取，避免依赖内存中的注册表）
        agent_count = count_registered_agents_sync()
        
        # 检查数据库连接
        db_ok = test_database_connection_sync()
        
        health_data = {
            "status": "ok" if db_ok and agent_count > 0 else "error",
            "agent_count": agent_count,
            "database": "connected" if db_ok else "disconnected",
            "timestamp": execution_time.isoformat()
        }
        
        # 记录健康检查结果
        if health_data.get("status") == "ok":
            logger.info(f"智能体服务健康检查通过: {agent_count}个Agent已注册")
            result = {
                'task_id': self.request.id,
                'check_time': execution_time.isoformat(),
                'status': 'SUCCESS',
                'health_data': health_data
            }
            record_periodic_task_result('periodic_agent_health_check', execution_time, 'SUCCESS', result)
            return result
        else:
            logger.warning(f"智能体服务健康检查异常: {health_data}")
            result = {
                'task_id': self.request.id,
                'check_time': execution_time.isoformat(),
                'status': 'WARNING',
                'health_data': health_data
            }
            record_periodic_task_result('periodic_agent_health_check', execution_time, 'WARNING', result)
            return result
            
    except Exception as e:
        error_msg = f"健康检查失败: {str(e)}"
        logger.error(error_msg)
        
        # 记录失败结果
        error_result = {
            'task_id': self.request.id,
            'check_time': execution_time.isoformat(),
            'error': error_msg,
            'status': 'FAILED'
        }
        record_periodic_task_result('periodic_agent_health_check', execution_time, 'FAILED', error_result)
        
        return error_result


def execute_agent_via_http(agent_url: str, agent_key: str, agent_id: str, message: str, user_name: str, task_timeout: int, thread_id: str = None):
    """
    通过HTTP请求执行智能体任务
    
    Args:
        agent_url: 智能体API地址
        agent_key: 智能体API密钥
        agent_id: 智能体ID
        message: 要发送的消息
        user_name: 用户名
        task_timeout: 任务超时时间
        thread_id: 会话ID（可选），如果提供则使用已有会话，否则创建新会话
    
    Returns:
        dict: 执行结果
    """
    try:
        # 1. 如果没有提供thread_id，则创建新会话
        if not thread_id:
            create_thread_url = f"{agent_url.rstrip('/')}/api/v1/chat/threads"
            thread_response = requests.post(
                create_thread_url,
                json={"agent_id": agent_id},
                headers={
                    "Authorization": f"Bearer {agent_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if thread_response.status_code != 200:
                return {
                    'status': 'FAILED',
                    'error': f'创建会话失败: HTTP {thread_response.status_code}'
                }
            
            thread_data = thread_response.json()
            if thread_data.get('status') != 'ok':
                return {
                    'status': 'FAILED',
                    'error': f"创建会话失败: {thread_data.get('msg', '未知错误')}"
                }
            
            thread_id = thread_data['data']['thread_id']
            logger.info(f"创建新会话成功，thread_id: {thread_id}")
        else:
            logger.info(f"使用已有会话，thread_id: {thread_id}")
        
        # 2. 发送消息
        completion_url = f"{agent_url.rstrip('/')}/api/v1/chat/threads/{thread_id}/completion"
        completion_response = requests.post(
            completion_url,
            json={
                "agent_id": agent_id,
                "user_name": user_name,
                "query": message,
                "config": {"selected_model": "deepseek-chat"},
                "chat_mode": "blocking"
            },
            headers={
                "Authorization": f"Bearer {agent_key}",
                "Content-Type": "application/json"
            },
            timeout=task_timeout
        )
        
        if completion_response.status_code != 200:
            return {
                'status': 'FAILED',
                'error': f'发送消息失败: HTTP {completion_response.status_code}'
            }
        
        completion_data = completion_response.json()
        if completion_data.get('status') != 'ok':
            return {
                'status': 'FAILED',
                'error': f"发送消息失败: {completion_data.get('msg', '未知错误')}"
            }
        
        logger.info(f"智能体任务执行成功，thread_id: {thread_id}")
        # 只返回必要的信息，避免结果太大
        return {
            'status': 'SUCCESS',
            'thread_id': thread_id,
            'message': '任务执行成功'
        }
        
    except requests.RequestException as e:
        error_msg = f"HTTP请求失败: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'FAILED',
            'error': error_msg
        }
    except Exception as e:
        error_msg = f"执行智能体任务异常: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'FAILED',
            'error': error_msg
        }


@app.task(bind=True, soft_time_limit=300, time_limit=360)
def execute_agent_periodic_task(self, task_config_id):
    """
    通用的智能体定时任务执行函数
    
    Args:
        task_config_id: 定时任务配置ID，从celery_periodic_task_configs表中读取配置
    """
    task_id = self.request.id
    execution_time = now_shanghai()
    
    # 默认值，避免except块中变量未定义
    max_retries = 1
    task_config_id_str = str(task_config_id)
    
    try:
        with get_db_session() as db:
            # 从数据库获取任务配置
            task_config = db.query(PeriodicTask).filter(PeriodicTask.id == task_config_id).first()
            logger.info(f"定时任务从数据库里面获取到的信息: {task_config}")
            
            if not task_config:
                error_msg = f"找不到任务配置，ID: {task_config_id}"
                logger.error(error_msg)
                return {
                    'task_id': task_id,
                    'error': error_msg,
                    'status': 'FAILED',
                    'execution_time': execution_time.isoformat()
                }
            
            # 检查任务是否启用
            if not task_config.task_enabled:
                logger.info(f"任务已禁用，跳过执行: {task_config.task_name}")
                return {
                    'task_id': task_id,
                    'task_name': task_config.task_name,
                    'message': '任务已禁用',
                    'status': 'SKIPPED',
                    'execution_time': execution_time.isoformat()
                }
            
            # 解析任务配置
            try:
                extra_config = json.loads(task_config.task_extra_config) if task_config.task_extra_config else {}
            except json.JSONDecodeError as e:
                error_msg = f"任务配置JSON解析失败: {str(e)}"
                logger.error(error_msg)
                record_periodic_task_result(f'execute_agent_{task_config_id}', execution_time, 'FAILED', {
                    'error': error_msg,
                    'task_config_id': task_config_id
                })
                return {
                    'task_id': task_id,
                    'error': error_msg,
                    'status': 'FAILED',
                    'execution_time': execution_time.isoformat()
                }
            
            # 验证是否为智能体任务
            if extra_config.get('task_type') != 'agent':
                error_msg = f"不是智能体任务类型: {extra_config.get('task_type')}"
                logger.error(error_msg)
                return {
                    'task_id': task_id,
                    'error': error_msg,
                    'status': 'FAILED',
                    'execution_time': execution_time.isoformat()
                }
            
            # 获取智能体配置
            agent_id = extra_config.get('agent_id')
            agent_url = extra_config.get('agent_url')
            agent_key = extra_config.get('agent_key')
            
            if not all([agent_id, agent_url, agent_key]):
                error_msg = f"缺少必要的智能体配置: agent_id={agent_id}, agent_url={agent_url}, agent_key={'***' if agent_key else None}"
                logger.error(error_msg)
                record_periodic_task_result(f'execute_agent_{task_config_id}', execution_time, 'FAILED', {
                    'error': error_msg,
                    'task_config_id': task_config_id
                })
                return {
                    'task_id': task_id,
                    'error': error_msg,
                    'status': 'FAILED',
                    'execution_time': execution_time.isoformat()
                }
            
            message = extra_config.get('message', '执行定时任务')
            # 使用create_by作为用户名，如果没有则默认system
            user_name = task_config.create_by if task_config.create_by else 'system'
            task_timeout = int(extra_config.get('task_timeout', 300))
            # 确保max_retries是整数
            try:
                max_retries = int(extra_config.get('max_retries', 1))
            except (TypeError, ValueError):
                max_retries = 1
            thread_id = extra_config.get('thread_id')  # 获取配置的会话ID
            
            logger.info(f"开始执行智能体定时任务: {task_config.task_name}, agent_id={agent_id}, agent_url={agent_url}, thread_id={thread_id}")
            
            # 通过HTTP请求执行智能体任务
            agent_result = execute_agent_via_http(
                agent_url=agent_url,
                agent_key=agent_key,
                agent_id=agent_id,
                message=message,
                user_name=user_name,
                task_timeout=task_timeout,
                thread_id=thread_id  # 传递会话ID
            )
            
            if agent_result and agent_result.get('status') == 'SUCCESS':
                # 简化返回结果，避免数据太大
                success_result = {
                    'task_id': task_id,
                    'task_config_id': task_config_id,
                    'task_name': task_config.task_name,
                    'agent_id': agent_id,
                    'thread_id': agent_result.get('thread_id'),
                    'status': 'SUCCESS',
                    'execution_time': execution_time.isoformat()
                }
                
                # 更新任务最后运行时间和运行次数
                task_config.task_last_run_time = execution_time
                task_config.task_run_count += 1
                task_config.update_time = now_shanghai()
                
                # 记录成功执行结果
                record_periodic_task_result(task_config.task_name, execution_time, 'SUCCESS', success_result)
                logger.info(f"智能体定时任务执行成功: {task_config.task_name}")
                return success_result
            else:
                # 任务执行失败
                error_msg = agent_result.get('error', '未知错误') if agent_result else '智能体调用失败'
                failed_result = {
                    'task_id': task_id,
                    'task_config_id': task_config_id,
                    'task_name': task_config.task_name,
                    'agent_id': agent_id,
                    'error': error_msg,
                    'status': 'FAILED',
                    'execution_time': execution_time.isoformat()
                }
                
                # 更新任务运行次数
                task_config.task_run_count += 1
                task_config.update_time = now_shanghai()
                
                # 记录失败结果
                record_periodic_task_result(task_config.task_name, execution_time, 'FAILED', failed_result)
                
                # 检查是否需要重试
                if self.request.retries < max_retries:
                    logger.info(f"任务执行失败，准备重试 ({self.request.retries + 1}/{max_retries}): {error_msg}")
                    raise self.retry(exc=Exception(error_msg), countdown=60 * (self.request.retries + 1))
                else:
                    logger.error(f"任务执行失败，已达最大重试次数: {error_msg}")
                    return failed_result
                    
    except Exception as e:
        error_msg = f"执行智能体定时任务异常: {str(e)}"
        logger.error(error_msg)
        
        # 记录异常结果
        error_result = {
            'task_id': task_id,
            'task_config_id': task_config_id_str,
            'error': error_msg,
            'status': 'ERROR',
            'execution_time': execution_time.isoformat()
        }
        record_periodic_task_result(f'execute_agent_{task_config_id_str}', execution_time, 'ERROR', error_result)
        
        # 检查是否需要重试
        if self.request.retries < max_retries:
            logger.info(f"任务执行异常，准备重试 ({self.request.retries + 1}/{max_retries}): {error_msg}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"任务执行异常，已达最大重试次数: {error_msg}")
            return error_result