import time
import logging
import json
from datetime import datetime
from celery_app.celery import app
from celery_app.models import get_session, Task, PeriodicTaskRun
from celery.signals import task_prerun, task_postrun, task_failure

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 任务开始前的处理
@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, kwargs=None, **kw):
    if task.name.startswith('celery.'):
        return  # 跳过Celery内部任务
    
    session = get_session()
    try:
        # 检查任务是否已存在
        existing_task = session.query(Task).filter_by(task_id=task_id).first()
        
        if existing_task:
            # 更新现有任务
            existing_task.task_status = 'STARTED'
            existing_task.task_start_time = datetime.now()
            existing_task.task_retry_count += 1
            existing_task.update_by = 'system'  # 添加更新人
        else:
            # 创建新任务记录
            new_task = Task(
                task_id=task_id,
                task_name=task.name,
                task_status='STARTED',
                create_time=datetime.now(),
                task_start_time=datetime.now(),
                task_args=json.dumps(args) if args else None,
                task_kwargs=json.dumps(kwargs) if kwargs else None,
                create_by='system',  # 添加创建人
                update_by='system'   # 添加更新人
            )
            session.add(new_task)
        
        session.commit()
    except Exception as e:
        logger.error(f"任务预处理错误: {str(e)}")
        session.rollback()
    finally:
        session.close()

# 任务完成后的处理
@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, state=None, retval=None, **kw):
    if task.name.startswith('celery.'):
        return  # 跳过Celery内部任务
    
    session = get_session()
    try:
        task_record = session.query(Task).filter_by(task_id=task_id).first()
        if task_record:
            task_record.task_status = state
            task_record.task_complete_time = datetime.now()
            task_record.task_result = json.dumps(retval) if retval is not None else None
            task_record.update_by = 'system'  # 添加更新人
            session.commit()
    except Exception as e:
        logger.error(f"任务后处理错误: {str(e)}")
        session.rollback()
    finally:
        session.close()

# 任务失败处理
@task_failure.connect
def task_failure_handler(task_id=None, exception=None, traceback=None, **kw):
    session = get_session()
    try:
        task_record = session.query(Task).filter_by(task_id=task_id).first()
        if task_record:
            task_record.task_status = 'FAILURE'
            task_record.task_complete_time = datetime.now()
            task_record.task_traceback = str(traceback)
            session.commit()
    except Exception as e:
        logger.error(f"任务失败处理错误: {str(e)}")
        session.rollback()
    finally:
        session.close()

# 异步任务示例
@app.task(bind=True, max_retries=3)
def long_running_task(self, task_id, data):
    """
    一个模拟长时间运行的任务
    """
    logger.info(f"开始执行任务 {task_id}")
    try:
        # 模拟耗时操作
        time.sleep(5)
        
        # 模拟可能的失败
        if data.get('should_fail', False):
            raise Exception("任务执行失败")
            
        result = {
            'task_id': task_id,
            'processed_data': data.get('value', 0) * 2,
            'completed_at': datetime.now().isoformat()
        }
        logger.info(f"任务 {task_id} 执行完成")
        return result
        
    except Exception as exc:
        logger.error(f"任务 {task_id} 执行出错: {str(exc)}")
        # 重试任务
        self.retry(exc=exc, countdown=5)  # 5秒后重试

# 定时任务示例
@app.task
def periodic_task():
    """
    定期执行的任务
    """
    execution_time = datetime.now()
    logger.info(f"定时任务执行于: {execution_time.isoformat()}")
    
    # 执行定期操作，如清理临时文件、发送统计数据等
    result = {'status': 'completed', 'timestamp': execution_time.isoformat()}
    
    # 记录定时任务执行
    session = get_session()
    try:
        task_run = PeriodicTaskRun(
            task_name='periodic_task',
            task_schedule_time=execution_time,
            task_execute_time=execution_time,
            task_status='SUCCESS',
            task_result=json.dumps(result),
            create_by='system',  # 添加创建人
            update_by='system'   # 添加更新人
        )
        session.add(task_run)
        session.commit()
    except Exception as e:
        logger.error(f"记录定时任务执行错误: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return result

@app.task
def daily_report():
    """
    每日报告任务
    """
    execution_time = datetime.now()
    logger.info(f"生成每日报告: {execution_time.isoformat()}")
    
    # 生成报告逻辑
    report_data = {
        'date': execution_time.strftime('%Y-%m-%d'),
        'summary': '这是一个示例报告',
        'metrics': {
            'processed_items': 1000,
            'errors': 5,
            'success_rate': '99.5%'
        }
    }
    
    # 记录定时任务执行
    session = get_session()
    try:
        task_run = PeriodicTaskRun(
            task_name='daily_report',
            task_schedule_time=execution_time.replace(hour=8, minute=0, second=0, microsecond=0),
            task_execute_time=execution_time,
            task_status='SUCCESS',
            task_result=json.dumps(report_data)
        )
        session.add(task_run)
        session.commit()
    except Exception as e:
        logger.error(f"记录定时任务执行错误: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    # 可以在这里添加发送邮件或保存报告的逻辑
    return report_data

# 链式任务示例
@app.task
def process_data(data):
    """
    处理数据的任务
    """
    logger.info(f"处理数据: {data}")
    result = data * 2
    return result

@app.task
def save_result(result):
    """
    保存结果的任务
    """
    logger.info(f"保存结果: {result}")
    # 模拟保存到数据库
    return {'saved': True, 'value': result}

@app.task
def update_task_status(task_id, status):
    session = get_session()
    try:
        task = session.query(Task).filter_by(task_id=task_id).first()
        if task:
            task.task_status = status
            # update_time 会自动更新
            session.commit()
    finally:
        session.close()

# 智能体任务统一执行器
@app.task(bind=True, max_retries=3)
def execute_agent_task(self, agent_id, message, user="system", **kwargs):
    """
    执行智能体任务的统一入口
    支持并行处理多个智能体的定时任务
    """
    import requests
    
    execution_time = datetime.now()
    logger.info(f"开始执行智能体任务 - Agent: {agent_id}, Message: {message}")
    
    try:
        # 调用LangGraph API
        api_url = "http://localhost:8000/api/chat/stream"
        payload = {
            "message": message,
            "assistant_id": agent_id,
            "user": user,
            "stream_mode": ["messages"]  # 确保消息历史被记录
        }
        
        # 设置超时时间
        timeout = kwargs.get('timeout', 300)  # 默认5分钟超时
        
        response = requests.post(
            api_url, 
            json=payload, 
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            # 处理流式响应
            result_messages = []
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'content' in data:
                            result_messages.append(data['content'])
                    except json.JSONDecodeError:
                        continue
            
            final_result = {
                'agent_id': agent_id,
                'status': 'SUCCESS',
                'message': message,
                'response': '\n'.join(result_messages),
                'execution_time': execution_time.isoformat(),
                'user': user
            }
            
            logger.info(f"智能体任务执行成功 - Agent: {agent_id}")
            
        else:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        error_msg = f"智能体任务超时 - Agent: {agent_id}, 超时时间: {timeout}秒"
        logger.error(error_msg)
        final_result = {
            'agent_id': agent_id,
            'status': 'TIMEOUT',
            'message': message,
            'error': error_msg,
            'execution_time': execution_time.isoformat()
        }
        
    except Exception as exc:
        error_msg = f"智能体任务执行失败 - Agent: {agent_id}, Error: {str(exc)}"
        logger.error(error_msg)
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"智能体任务重试 - Agent: {agent_id}, 重试次数: {self.request.retries + 1}")
            self.retry(exc=exc, countdown=60)  # 1分钟后重试
            
        final_result = {
            'agent_id': agent_id,
            'status': 'FAILURE',
            'message': message,
            'error': error_msg,
            'execution_time': execution_time.isoformat(),
            'retries': self.request.retries
        }
    
    # 记录定时任务执行日志
    session = get_session()
    try:
        task_run = PeriodicTaskRun(
            task_name=f'agent_task_{agent_id}',
            task_schedule_time=execution_time,
            task_execute_time=datetime.now(),
            task_status=final_result['status'],
            task_result=json.dumps(final_result),
            create_by='system',
            update_by='system'
        )
        session.add(task_run)
        session.commit()
    except Exception as e:
        logger.error(f"记录智能体任务执行日志错误: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return final_result

# HTTP任务执行器
@app.task(bind=True, max_retries=3)
def execute_http_task(self, url, method="GET", headers=None, data=None, **kwargs):
    """
    执行HTTP任务的统一入口
    """
    import requests
    
    execution_time = datetime.now()
    logger.info(f"开始执行HTTP任务 - URL: {url}, Method: {method}")
    
    try:
        timeout = kwargs.get('timeout', 30)  # 默认30秒超时
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        else:
            raise Exception(f"不支持的HTTP方法: {method}")
            
        result = {
            'status': 'SUCCESS',
            'url': url,
            'method': method,
            'status_code': response.status_code,
            'response': response.text[:1000] if response.text else None,  # 限制响应长度
            'execution_time': execution_time.isoformat()
        }
        
        logger.info(f"HTTP任务执行成功 - URL: {url}, Status: {response.status_code}")
        
    except Exception as exc:
        error_msg = f"HTTP任务执行失败 - URL: {url}, Error: {str(exc)}"
        logger.error(error_msg)
        
        if self.request.retries < self.max_retries:
            logger.info(f"HTTP任务重试 - URL: {url}, 重试次数: {self.request.retries + 1}")
            self.retry(exc=exc, countdown=30)  # 30秒后重试
            
        result = {
            'status': 'FAILURE',
            'url': url,
            'method': method,
            'error': error_msg,
            'execution_time': execution_time.isoformat(),
            'retries': self.request.retries
        }
    
    # 记录任务执行日志
    session = get_session()
    try:
        task_run = PeriodicTaskRun(
            task_name=f'http_task_{url.replace("://", "_").replace("/", "_")}',
            task_schedule_time=execution_time,
            task_execute_time=datetime.now(),
            task_status=result['status'],
            task_result=json.dumps(result),
            create_by='system',
            update_by='system'
        )
        session.add(task_run)
        session.commit()
    except Exception as e:
        logger.error(f"记录HTTP任务执行日志错误: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return result 