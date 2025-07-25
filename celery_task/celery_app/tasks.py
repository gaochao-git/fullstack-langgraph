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