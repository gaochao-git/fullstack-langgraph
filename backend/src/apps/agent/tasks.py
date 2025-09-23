"""
Agent 模块的 Celery 任务
包括智能体定时任务执行和健康检查
"""
import json
from datetime import datetime
from src.celery.celery import app
from src.celery.db_utils import get_db_session
from src.celery.sync_db_helpers import (
    test_database_connection_sync,
    count_registered_agents_sync
)
from src.apps.scheduled_task.celery_models import (
    CeleryPeriodicTaskRun as PeriodicTaskRun, 
    CeleryPeriodicTaskConfig as PeriodicTask
)
from src.shared.core.logging import get_logger
from src.shared.db.models import now_shanghai
from .service.agent_sync_executor import execute_agent_sync

logger = get_logger(__name__)

DB_RETRY_MAX = 3  # 数据库重试次数


def record_periodic_task_result(task_name, execution_time, status, result_data):
    """记录定时任务执行结果到数据库"""
    retry_count = 0
    
    while retry_count < DB_RETRY_MAX:
        try:
            with get_db_session() as db:
                # 查找任务配置
                task_config = db.query(PeriodicTask).filter_by(task_name=task_name).first()
                if not task_config:
                    logger.warning(f"找不到任务配置: {task_name}")
                    return
                    
                task_run = PeriodicTaskRun(
                    task_config_id=task_config.id,
                    run_time=execution_time,
                    status=status,
                    result=json.dumps(result_data, ensure_ascii=False) if result_data else None,
                    execution_time=int((datetime.now() - execution_time).total_seconds())
                )
                db.add(task_run)
                logger.info(f"成功记录定时任务结果: {task_name}")
                break
        except Exception as e:
            retry_count += 1
            logger.error(f"记录任务结果失败 (尝试 {retry_count}/{DB_RETRY_MAX}): {str(e)}")
            if retry_count >= DB_RETRY_MAX:
                logger.error(f"记录任务结果最终失败: {str(e)}")


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
    max_retries = 3
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
            if not agent_id:
                error_msg = "缺少智能体ID配置"
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
            user_name = extra_config.get('user', 'system')
            conversation_id = extra_config.get('conversation_id')
            task_timeout = extra_config.get('task_timeout', 300)
            max_retries = extra_config.get('max_retries', 3)
            
            logger.info(f"开始执行智能体定时任务: {task_config.task_name}, agent_id={agent_id}")
            
            # 调用智能体执行函数（使用优化的同步执行器）
            agent_result = execute_agent_sync(
                agent_id=agent_id,
                message=message,
                user_name=user_name,
                conversation_id=conversation_id,
                timeout=task_timeout
            )
            
            if agent_result and agent_result.get('status') == 'SUCCESS':
                success_result = {
                    'task_id': task_id,
                    'task_config_id': task_config_id,
                    'task_name': task_config.task_name,
                    'agent_id': agent_id,
                    'agent_result': agent_result,
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