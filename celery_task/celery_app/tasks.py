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
    
    session = None
    try:
        session = get_session()
        task_record = session.query(Task).filter_by(task_id=task_id).first()
        if task_record:
            task_record.task_status = state
            task_record.task_complete_time = datetime.now()
            task_record.task_result = json.dumps(retval) if retval is not None else None
            task_record.update_by = 'system'  # 添加更新人
            session.commit()
            logger.info(f"任务后处理完成: {task_id}")
    except Exception as e:
        logger.error(f"任务后处理错误: {str(e)}")
        if session:
            try:
                session.rollback()
            except:
                pass
    finally:
        if session:
            try:
                session.close()
            except Exception as e:
                logger.error(f"关闭数据库会话错误: {str(e)}")

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

# 保留信号处理器和核心功能，删除示例任务

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

# execute_agent_task 已删除，请使用 call_agent_task 替代

@app.task
def execute_http_task(url, method='GET', headers=None, body=None):
    """执行HTTP任务（占位函数）"""
    logger.warning(f"HTTP任务功能未实现: {method} {url}")
    return {
        'status': 'SKIPPED',
        'message': 'HTTP任务功能暂未实现',
        'url': url,
        'method': method
    } 