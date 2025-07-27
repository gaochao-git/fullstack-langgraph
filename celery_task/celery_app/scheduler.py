import json
from datetime import datetime, timedelta
from celery.beat import Scheduler, ScheduleEntry
from celery import current_app
from celery.schedules import crontab, schedule
from celery_app.models import get_session, PeriodicTask

class DatabaseScheduler(Scheduler):
    """从数据库加载定时任务的调度器"""
    
    def __init__(self, *args, **kwargs):
        self._schedule = {}
        self._last_timestamp = datetime.now()
        super(DatabaseScheduler, self).__init__(*args, **kwargs)
    
    def setup_schedule(self):
        self.update_from_database()
    
    def update_from_database(self):
        """从数据库更新定时任务"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            session = get_session()
            try:
                db_tasks = session.query(PeriodicTask).filter_by(task_enabled=True).all()
                
                self._schedule = {}
                
                print(f"数据库调度器: 加载了 {len(db_tasks)} 个启用的任务")
                
                for task in db_tasks:
                    # 解析参数
                    args = json.loads(task.task_args) if task.task_args else []
                    kwargs = json.loads(task.task_kwargs) if task.task_kwargs else {}
                    
                    # 从 task_extra_config 中获取配置
                    if task.task_extra_config:
                        try:
                            extra_config = json.loads(task.task_extra_config)
                            task_type = extra_config.get('task_type', 'http')
                            agent_id = extra_config.get('agent_id')
                            task_timeout = extra_config.get('task_timeout')
                        except json.JSONDecodeError:
                            print(f"⚠️ 任务 {task.task_name} 的 task_extra_config JSON 解析失败，跳过该任务")
                            continue
                    else:
                        # 没有额外配置，使用默认值
                        task_type = 'http'
                        agent_id = None
                        task_timeout = None
                        extra_config = {}
                    
                    # 根据任务类型动态设置任务路径和参数
                    if task_type == 'agent':
                        # 智能体任务：使用统一的智能体任务执行器
                        task_path = 'celery_app.agent_tasks.execute_agent_periodic_task'
                        
                        # execute_agent_periodic_task 只需要任务配置ID
                        args = [task.id]  # 传递任务ID，函数内部读取配置
                        kwargs = {}
                        
                        print(f"🤖 智能体任务: {task.task_name} -> Agent: {agent_id}")
                        
                    elif task_type == 'http':
                        # HTTP任务：使用HTTP任务执行器
                        task_path = 'celery_app.tasks.execute_http_task'
                        
                        # 从 extra_config 或传统字段获取参数
                        url = extra_config.get('url', kwargs.get('url', ''))
                        method = extra_config.get('method', kwargs.get('method', 'GET'))
                        headers = extra_config.get('headers', kwargs.get('headers', None))
                        data = extra_config.get('data', kwargs.get('data', None))
                        timeout = extra_config.get('timeout', task_timeout)
                        # 可扩展配置：认证、代理等
                        auth = extra_config.get('auth', None)
                        verify_ssl = extra_config.get('verify_ssl', True)
                        
                        # 重新构造参数
                        args = [url, method, headers, data]
                        kwargs = {'timeout': timeout} if timeout else {}
                        
                        print(f"🌐 HTTP任务: {task.task_name} -> URL: {url}")
                        
                    else:
                        # system 或其他类型：使用原始任务路径
                        task_path = task.task_path
                        
                        # 如果有额外配置，合并到 kwargs 中
                        if extra_config:
                            kwargs.update(extra_config)
                            
                        print(f"⚙️ 系统任务: {task.task_name} -> Path: {task_path}")
                    
                    # 创建调度
                    if task.task_interval is not None:
                        # 间隔调度
                        schedule_obj = schedule(timedelta(seconds=task.task_interval))
                    else:
                        # Crontab 调度
                        schedule_obj = crontab(
                            minute=task.task_crontab_minute or '*',
                            hour=task.task_crontab_hour or '*',
                            day_of_week=task.task_crontab_day_of_week or '*',
                            day_of_month=task.task_crontab_day_of_month or '*',
                            month_of_year=task.task_crontab_month_of_year or '*'
                        )
                    
                    # 官方方案：让Celery自己处理时区转换
                    last_run_at = task.task_last_run_time
                    
                    # 从task_extra_config中获取队列配置
                    queue_name = 'priority_low'  # 默认队列
                    if task.task_extra_config:
                        try:
                            extra_config = json.loads(task.task_extra_config)
                            queue_name = extra_config.get('queue', 'priority_low')
                            
                            # 验证队列名称是否有效
                            valid_queues = ['system', 'priority_high', 'priority_low']
                            if queue_name not in valid_queues:
                                print(f"⚠️ 任务 {task.task_name} 配置了无效队列 {queue_name}，使用默认队列 priority_low")
                                queue_name = 'priority_low'
                            else:
                                print(f"✅ 任务 {task.task_name} 将路由到队列: {queue_name}")
                                
                        except json.JSONDecodeError:
                            print(f"⚠️ 任务 {task.task_name} 的task_extra_config解析失败，使用默认队列")
                    
                    # 创建ScheduleEntry对象，添加队列配置
                    entry = ScheduleEntry(
                        name=task.task_name,
                        task=task_path,
                        schedule=schedule_obj,
                        args=args,
                        kwargs=kwargs,
                        options={
                            'expires': 60.0,
                            'queue': queue_name,  # 指定队列
                            # 简化路由配置，使用默认exchange
                        },
                        last_run_at=last_run_at,
                        total_run_count=task.task_run_count
                    )
                    
                    print(f"📋 加载任务: {task.task_name}")
                    print(f"   上次运行: {task.task_last_run_time}")
                    print(f"   运行次数: {task.task_run_count}")
                    print(f"   间隔: {task.task_interval}秒")
                    print(f"   当前时间(UTC): {datetime.now()}")
                    
                    # 添加到调度中
                    self._schedule[task.task_name] = entry
                
                self._last_timestamp = datetime.now()
                break  # 成功则退出重试循环
                
            except Exception as e:
                retry_count += 1
                print(f"更新定时任务时出错 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count >= max_retries:
                    print(f"更新定时任务最终失败，使用空调度: {e}")
                    self._schedule = {}
                    self._last_timestamp = datetime.now()
            finally:
                session.close()
    
    @property
    def schedule(self):
        """返回当前的调度配置"""
        return self._schedule
    
    def tick(self, *args, **kwargs):
        # Celery官方推荐：每个beat周期检查配置变化
        # 通过检查数据库时间戳来判断是否需要重新加载
        try:
            if self._should_reload_schedule():
                print("🔄 发现配置变化，重新加载任务...")
                self.update_from_database()
        except Exception as e:
            print(f"⚠️ 检查配置更新失败: {str(e)}")
        
        return super(DatabaseScheduler, self).tick(*args, **kwargs)
    
    def _should_reload_schedule(self):
        """检查是否需要重新加载调度配置"""
        # 每30秒检查一次数据库变化
        if datetime.now() - self._last_timestamp < timedelta(seconds=30):
            return False
        
        session = get_session()
        try:
            # 检查数据库中任务的最新更新时间
            latest_update = session.query(PeriodicTask.update_time).filter(
                PeriodicTask.task_enabled == True
            ).order_by(PeriodicTask.update_time.desc()).first()
            
            if latest_update and latest_update[0] > self._last_timestamp:
                return True
            
            return False
        except Exception as e:
            print(f"⚠️ 检查数据库变化失败: {str(e)}")
            return False
        finally:
            session.close() 
        