"""
智能体相关的 Celery 任务
"""
import sys
import os
import json
import logging
import requests
from datetime import datetime
from celery_app.celery import app
from celery_app.models import get_session, PeriodicTaskRun, PeriodicTask

# 添加 backend 项目路径到 Python 路径
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 智能体 API 配置
AGENT_API_BASE_URL = os.getenv('AGENT_API_BASE_URL', 'http://192.168.1.10:8000')


@app.task(bind=True, max_retries=0, soft_time_limit=300, time_limit=360)
def call_agent_task(self, agent_id, message, user_name="system", conversation_id=None):
    """
    调用智能体的异步任务,参数从celery_periodic_task_configs表里获取的
    
    Args:
        agent_id: 智能体ID
        message: 发送给智能体的消息
        user_name: 用户名
        conversation_id: 会话ID（可选）
    """
    task_id = self.request.id
    execution_time = datetime.now()
    
    logger.info(f"开始调用智能体任务 {task_id}: agent_id={agent_id}, user={user_name}")
    
    try:
        # 第一步：创建线程
        if not conversation_id:
            thread_response = requests.post(
                f"{AGENT_API_BASE_URL}/threads",
                json={"metadata": {}},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if thread_response.status_code == 200:
                thread_data = thread_response.json()
                conversation_id = thread_data.get("thread_id")
                logger.info(f"创建新线程: {conversation_id}")
            else:
                raise Exception(f"创建线程失败: HTTP {thread_response.status_code}")
        
        # 第二步：发送消息进行对话
        chat_data = {
            "input": {
                "messages": [
                    {
                        "type": "human",
                        "content": message,
                        "id": str(int(datetime.now().timestamp() * 1000))
                    }
                ],
                "user_name": user_name
            },
            "config": {
                "configurable": {
                    "selected_model": "qwen2.5-72b-instruct"  # 默认模型
                }
            },
            "stream_mode": ["messages", "values", "updates"],  # 包含消息历史模式
            "assistant_id": agent_id  # 直接使用agent_id
        }
        
        api_url = f"{AGENT_API_BASE_URL}/threads/{conversation_id}/runs/stream"
        logger.info(f"调用智能体对话API: {api_url}")
        
        # 根据消息复杂度动态调整超时时间
        message_length = len(message)
        if message_length < 50:
            timeout = 120  # 简单消息2分钟
        elif message_length < 200:
            timeout = 180  # 中等消息3分钟
        else:
            timeout = 300  # 复杂消息5分钟
        
        logger.info(f"消息长度: {message_length}, 设置超时: {timeout}秒")
        
        response = requests.post(
            api_url,
            json=chat_data,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        
        if response.status_code == 200:
            # LangGraph API 返回的是流式数据，需要解析
            response_text = response.text
            logger.info(f"智能体调用成功: {agent_id}")
            
            # 尝试从流式响应中提取AI的回复内容
            ai_response = ""
            try:
                # 流式响应通常是多行JSON，每行一个事件
                lines = response_text.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        data_str = line[6:]  # 去掉 'data: ' 前缀
                        if data_str.strip():
                            try:
                                data = json.loads(data_str)
                                # 查找AI消息
                                if isinstance(data, list) and len(data) > 0:
                                    for item in data:
                                        if isinstance(item, dict) and 'messages' in item:
                                            messages = item['messages']
                                            for msg in messages:
                                                if msg.get('type') == 'ai':
                                                    ai_response = msg.get('content', '')
                                                    break
                            except json.JSONDecodeError:
                                continue
                
                # 如果没有找到AI回复，使用原始响应
                if not ai_response:
                    ai_response = f"任务执行完成，原始响应: {response_text[:200]}..."
                    
            except Exception as e:
                ai_response = f"响应解析失败: {str(e)}, 原始响应: {response_text[:100]}..."
            
            # 构建返回结果
            result = {
                'task_id': task_id,
                'agent_id': agent_id,
                'user_name': user_name,
                'message': message,
                'response': ai_response,
                'conversation_id': conversation_id,
                'status': 'SUCCESS',
                'execution_time': execution_time.isoformat(),
                'api_response_code': response.status_code
            }
            
            # 记录任务执行结果
            record_agent_task_result(task_id, agent_id, 'SUCCESS', result)
            
            return result
            
        else:
            error_msg = f"智能体API调用失败: HTTP {response.status_code}, {response.text}"
            logger.error(error_msg)
            
            # 记录失败结果
            error_result = {
                'task_id': task_id,
                'agent_id': agent_id,
                'error': error_msg,
                'status': 'FAILED',
                'execution_time': execution_time.isoformat(),
                'api_response_code': response.status_code
            }
            record_agent_task_result(task_id, agent_id, 'FAILED', error_result)
            
            # 不重试，直接返回失败结果
            return error_result
            
    except requests.exceptions.RequestException as e:
        error_msg = f"智能体API请求异常: {str(e)}"
        logger.error(error_msg)
        
        # 记录失败结果
        error_result = {
            'task_id': task_id,
            'agent_id': agent_id,
            'error': error_msg,
            'status': 'FAILED',
            'execution_time': execution_time.isoformat()
        }
        record_agent_task_result(task_id, agent_id, 'FAILED', error_result)
        
        # 不重试，直接返回失败结果
        return error_result
        
    except Exception as exc:
        error_msg = f"智能体任务执行出错: {str(exc)}"
        logger.error(error_msg)
        
        # 记录失败结果
        error_result = {
            'task_id': task_id,
            'agent_id': agent_id,
            'error': error_msg,
            'status': 'FAILED',
            'execution_time': execution_time.isoformat()
        }
        record_agent_task_result(task_id, agent_id, 'FAILED', error_result)
        
        # 不重试，直接返回失败结果
        return error_result


@app.task
def periodic_agent_health_check():
    """
    定期检查所有智能体的健康状态
    """
    execution_time = datetime.now()
    logger.info(f"开始执行智能体健康检查任务: {execution_time.isoformat()}")
    
    try:
        # 获取所有智能体列表
        api_url = f"{AGENT_API_BASE_URL}/api/agents/"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            agents = response.json()
            
            health_report = {
                'check_time': execution_time.isoformat(),
                'total_agents': len(agents),
                'enabled_agents': 0,
                'disabled_agents': 0,
                'agent_details': [],
                'status': 'SUCCESS'
            }
            
            for agent in agents:
                agent_detail = {
                    'agent_id': agent.get('id'),
                    'name': agent.get('display_name'),
                    'enabled': agent.get('enabled'),
                    'status': agent.get('status'),
                    'last_used': agent.get('last_used'),
                    'total_runs': agent.get('total_runs', 0)
                }
                
                health_report['agent_details'].append(agent_detail)
                
                if agent.get('enabled'):
                    health_report['enabled_agents'] += 1
                else:
                    health_report['disabled_agents'] += 1
            
            logger.info(f"智能体健康检查完成: {health_report['total_agents']} 个智能体")
            
            # 记录定时任务执行
            record_periodic_task_result('periodic_agent_health_check', execution_time, 'SUCCESS', health_report)
            
            return health_report
            
        else:
            error_msg = f"获取智能体列表失败: HTTP {response.status_code}"
            logger.error(error_msg)
            
            error_result = {
                'check_time': execution_time.isoformat(),
                'error': error_msg,
                'status': 'FAILED'
            }
            record_periodic_task_result('periodic_agent_health_check', execution_time, 'FAILED', error_result)
            
            return error_result
            
    except Exception as e:
        error_msg = f"智能体健康检查异常: {str(e)}"
        logger.error(error_msg)
        
        error_result = {
            'check_time': execution_time.isoformat(),
            'error': error_msg,
            'status': 'FAILED'
        }
        record_periodic_task_result('periodic_agent_health_check', execution_time, 'FAILED', error_result)
        
        return error_result



@app.task(bind=True, max_retries=3, soft_time_limit=300, time_limit=360)
def execute_agent_periodic_task(self, task_config_id):
    """
    通用的智能体定时任务执行函数
    
    Args:
        task_config_id: 定时任务配置ID，从celery_periodic_task_configs表中读取配置
    """
    task_id = self.request.id
    execution_time = datetime.now()
    
    session = get_session()
    
    try:
        # 从数据库获取任务配置
        task_config = session.query(PeriodicTask).filter(PeriodicTask.id == task_config_id).first()
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
        
        logger.info(f"开始执行智能体定时任务: {task_config.task_name}, agent_id={agent_id}")
        
        # 调用智能体任务
        result = call_agent_task.apply_async(
            args=[agent_id, message, user_name],
            kwargs={'conversation_id': conversation_id}
        )
        
        # 等待任务完成
        timeout = extra_config.get('task_timeout', 300)
        agent_result = result.get(timeout=timeout)
        
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
            task_config.task_run_count = (task_config.task_run_count or 0) + 1
            session.commit()
            
            logger.info(f"智能体定时任务执行成功: {task_config.task_name}")
            record_periodic_task_result(f'execute_agent_{task_config_id}', execution_time, 'SUCCESS', success_result)
            
            return success_result
        else:
            error_msg = f"智能体任务执行失败: {agent_result}"
            logger.error(error_msg)
            
            error_result = {
                'task_id': task_id,
                'task_config_id': task_config_id,
                'task_name': task_config.task_name,
                'agent_id': agent_id,
                'error': error_msg,
                'agent_result': agent_result,
                'status': 'FAILED',
                'execution_time': execution_time.isoformat()
            }
            
            record_periodic_task_result(f'execute_agent_{task_config_id}', execution_time, 'FAILED', error_result)
            return error_result
    
    except Exception as exc:
        error_msg = f"智能体定时任务执行异常: {str(exc)}"
        logger.error(error_msg)
        
        error_result = {
            'task_id': task_id,
            'task_config_id': task_config_id,
            'error': error_msg,
            'status': 'FAILED',
            'execution_time': execution_time.isoformat()
        }
        
        record_periodic_task_result(f'execute_agent_{task_config_id}', execution_time, 'FAILED', error_result)
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"任务失败，将在60秒后重试 (第{self.request.retries + 1}次重试)")
            raise self.retry(countdown=60, exc=exc)
        
        return error_result
    
    finally:
        session.close()


def record_agent_task_result(task_id, agent_id, status, result_data):
    """记录智能体任务执行结果到数据库"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        session = get_session()
        try:
            task_run = PeriodicTaskRun(
                task_name=f'call_agent_{agent_id}',
                task_schedule_time=datetime.now(),
                task_execute_time=datetime.now(),
                task_status=status,
                task_result=json.dumps(result_data, ensure_ascii=False),
                create_by='system',
                update_by='system'
            )
            session.add(task_run)
            session.commit()
            logger.info(f"成功记录智能体任务结果: {task_id}")
            break
        except Exception as e:
            retry_count += 1
            logger.warning(f"记录智能体任务结果失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            session.rollback()
            if retry_count >= max_retries:
                logger.error(f"记录智能体任务结果最终失败: {str(e)}")
        finally:
            session.close()


def record_periodic_task_result(task_name, execution_time, status, result_data):
    """记录定时任务执行结果到数据库"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        session = get_session()
        try:
            task_run = PeriodicTaskRun(
                task_name=task_name,
                task_schedule_time=execution_time,
                task_execute_time=execution_time,
                task_status=status,
                task_result=json.dumps(result_data, ensure_ascii=False),
                create_by='system',
                update_by='system'
            )
            session.add(task_run)
            session.commit()
            logger.info(f"成功记录定时任务结果: {task_name}")
            break
        except Exception as e:
            retry_count += 1
            logger.warning(f"记录定时任务结果失败 (尝试 {retry_count}/{max_retries}): {str(e)}")
            session.rollback()
            if retry_count >= max_retries:
                logger.error(f"记录定时任务结果最终失败: {str(e)}")
        finally:
            session.close()