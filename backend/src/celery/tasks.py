import time
import json
from datetime import datetime
from src.celery.celery import app
from src.celery.db_utils import get_db_session
from src.apps.scheduled_task.celery_models import CeleryTaskRecord as Task
from celery.signals import task_prerun, task_postrun, task_failure
from src.celery.logger import get_logger
from src.shared.db.models import now_shanghai

# 使用统一的日志配置
logger = get_logger(__name__)

# 任务开始前的处理
@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, args=None, kwargs=None, **kw):
    if task.name.startswith('celery.'):
        return  # 跳过Celery内部任务
    
    try:
        with get_db_session() as db:
            # 检查任务是否已存在
            existing_task = db.query(Task).filter_by(task_id=task_id).first()
            
            if existing_task:
                # 更新现有任务
                existing_task.task_status = 'STARTED'
                existing_task.task_start_time = now_shanghai()
                existing_task.task_retry_count += 1
                existing_task.update_by = 'system'
                existing_task.update_time = now_shanghai()
            else:
                # 创建新任务记录
                new_task = Task(
                    task_id=task_id,
                    task_name=task.name,
                    task_status='STARTED',
                    task_start_time=now_shanghai(),
                    task_args=json.dumps(args) if args else None,
                    task_kwargs=json.dumps(kwargs) if kwargs else None,
                    create_by='system',
                    update_by='system'
                )
                db.add(new_task)
    except Exception as e:
        logger.error(f"任务预处理错误: {str(e)}")

# 任务完成后的处理
@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, state=None, retval=None, **kw):
    if task.name.startswith('celery.'):
        return  # 跳过Celery内部任务
    
    try:
        with get_db_session() as db:
            task_record = db.query(Task).filter_by(task_id=task_id).first()
            if task_record:
                task_record.task_status = state
                task_record.task_complete_time = now_shanghai()
                # 处理结果序列化，跳过不能序列化的对象（如Retry）
                if retval is not None:
                    try:
                        task_record.task_result = json.dumps(retval)
                    except (TypeError, ValueError):
                        # 如果不能序列化，存储简单的字符串表示
                        task_record.task_result = str(retval)
                else:
                    task_record.task_result = None
                task_record.update_by = 'system'
                task_record.update_time = now_shanghai()
                logger.info(f"任务后处理完成: {task_id}")
    except Exception as e:
        logger.error(f"任务后处理错误: {str(e)}")

# 任务失败处理
@task_failure.connect
def task_failure_handler(task_id=None, exception=None, traceback=None, **kw):
    try:
        with get_db_session() as db:
            task_record = db.query(Task).filter_by(task_id=task_id).first()
            if task_record:
                task_record.task_status = 'FAILURE'
                task_record.task_complete_time = now_shanghai()
                task_record.task_traceback = str(traceback) if traceback else None
                task_record.update_by = 'system'
                task_record.update_time = now_shanghai()
    except Exception as e:
        logger.error(f"任务失败处理错误: {str(e)}")

# 系统维护任务示例
@app.task(bind=True, name='system_maintenance')
def system_maintenance(self):
    """系统维护任务示例"""
    logger.info("执行系统维护任务...")
    time.sleep(2)
    return "系统维护完成"

# HTTP任务执行器
@app.task(bind=True, name='execute_http_task', max_retries=3)
def execute_http_task(self, url, method='GET', headers=None, data=None, timeout=30):
    """
    执行HTTP请求任务
    """
    import requests
    
    try:
        logger.info(f"执行HTTP任务: {method} {url}")
        
        # 发起HTTP请求
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if method in ['POST', 'PUT'] else None,
            params=data if method == 'GET' else None,
            timeout=timeout
        )
        
        # 检查响应状态
        response.raise_for_status()
        
        # 返回响应数据
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response.text
        }
        
        logger.info(f"HTTP任务成功: {url}, 状态码: {response.status_code}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP任务失败: {url}, 错误: {str(e)}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"HTTP任务重试: {url}, 第{self.request.retries + 1}次")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            raise