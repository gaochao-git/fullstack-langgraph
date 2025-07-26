"""
动态定时任务调度器
负责从数据库读取定时任务配置，并动态注册到Celery Beat
"""

import json
import logging
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from celery_app.models import get_session, PeriodicTask
from celery_app.celery import app
from celery_app.agent_tasks import execute_agent_periodic_task

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DynamicScheduler:
    """动态任务调度器"""
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        self.registered_tasks = {}  # 记录已注册的任务
        
    def load_periodic_tasks_from_db(self):
        """从数据库加载定时任务配置"""
        session = get_session()
        try:
            # 只加载启用的智能体任务
            tasks = session.query(PeriodicTask).filter(
                PeriodicTask.task_enabled == True
            ).all()
            
            logger.info(f"从数据库加载到 {len(tasks)} 个启用的定时任务")
            return tasks
        except Exception as e:
            logger.error(f"加载数据库任务配置失败: {str(e)}")
            return []
        finally:
            session.close()
    
    def convert_to_celery_schedule(self, task_config):
        """将数据库配置转换为Celery调度配置"""
        try:
            if task_config.task_interval:
                # 间隔调度
                return {
                    'task': 'celery_app.agent_tasks.execute_agent_periodic_task',
                    'schedule': task_config.task_interval,
                    'args': (task_config.id,),
                    'options': {
                        'expires': 3600,  # 任务过期时间1小时
                    }
                }
            else:
                # Crontab调度
                cron_schedule = crontab(
                    minute=task_config.task_crontab_minute or '*',
                    hour=task_config.task_crontab_hour or '*',
                    day_of_week=task_config.task_crontab_day_of_week or '*',
                    day_of_month=task_config.task_crontab_day_of_month or '*',
                    month_of_year=task_config.task_crontab_month_of_year or '*'
                )
                
                return {
                    'task': 'celery_app.agent_tasks.execute_agent_periodic_task',
                    'schedule': cron_schedule,
                    'args': (task_config.id,),
                    'options': {
                        'expires': 3600,  # 任务过期时间1小时
                    }
                }
        except Exception as e:
            logger.error(f"转换调度配置失败 {task_config.task_name}: {str(e)}")
            return None
    
    def is_agent_task(self, task_config):
        """检查是否为智能体任务"""
        try:
            if not task_config.task_extra_config:
                return False
            
            extra_config = json.loads(task_config.task_extra_config)
            return extra_config.get('task_type') == 'agent'
        except (json.JSONDecodeError, AttributeError):
            return False
    
    def update_celery_beat_schedule(self):
        """更新Celery Beat调度配置"""
        tasks = self.load_periodic_tasks_from_db()
        new_schedule = {}
        
        for task_config in tasks:
            # 只处理智能体任务
            if not self.is_agent_task(task_config):
                logger.debug(f"跳过非智能体任务: {task_config.task_name}")
                continue
            
            schedule_config = self.convert_to_celery_schedule(task_config)
            if schedule_config:
                # 使用任务ID作为唯一键
                schedule_key = f'agent_task_{task_config.id}'
                new_schedule[schedule_key] = schedule_config
                logger.info(f"注册智能体定时任务: {task_config.task_name} (ID: {task_config.id})")
        
        # 更新Celery Beat调度表
        self.celery_app.conf.beat_schedule.update(new_schedule)
        
        # 移除已删除或禁用的任务
        current_keys = set(new_schedule.keys())
        registered_keys = set(self.registered_tasks.keys())
        removed_keys = registered_keys - current_keys
        
        for key in removed_keys:
            if key in self.celery_app.conf.beat_schedule:
                del self.celery_app.conf.beat_schedule[key]
                logger.info(f"移除定时任务: {key}")
        
        # 更新已注册任务记录
        self.registered_tasks = new_schedule
        
        logger.info(f"动态调度器更新完成，当前注册任务数: {len(new_schedule)}")
        return len(new_schedule)
    
    def start_periodic_update(self, interval_seconds=60):
        """启动定期更新调度"""
        logger.info(f"启动动态调度器，更新间隔: {interval_seconds}秒")
        
        # 立即执行一次更新
        self.update_celery_beat_schedule()
        
        # 注册定期更新任务
        @self.celery_app.task(bind=True)
        def update_schedule_task(self):
            """定期更新调度配置的任务"""
            try:
                scheduler = DynamicScheduler(self.celery_app)
                count = scheduler.update_celery_beat_schedule()
                logger.info(f"调度器定期更新完成，当前任务数: {count}")
                return {'status': 'success', 'task_count': count}
            except Exception as e:
                logger.error(f"调度器定期更新失败: {str(e)}")
                return {'status': 'error', 'error': str(e)}
        
        # 添加到Beat调度中
        self.celery_app.conf.beat_schedule['update_dynamic_schedule'] = {
            'task': f'{update_schedule_task.name}',
            'schedule': interval_seconds,
        }


# 全局调度器实例
scheduler = DynamicScheduler(app)

@app.task(bind=True)
def refresh_periodic_tasks_schedule(self):
    """手动刷新定时任务调度的任务"""
    try:
        count = scheduler.update_celery_beat_schedule()
        logger.info(f"手动刷新调度完成，当前任务数: {count}")
        return {'status': 'success', 'task_count': count, 'refresh_time': datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"手动刷新调度失败: {str(e)}")
        return {'status': 'error', 'error': str(e), 'refresh_time': datetime.now().isoformat()}

def initialize_scheduler():
    """初始化调度器"""
    try:
        # 启动定期更新（每60秒检查一次）
        scheduler.start_periodic_update(60)
        logger.info("动态任务调度器初始化成功")
        return True
    except Exception as e:
        logger.error(f"动态任务调度器初始化失败: {str(e)}")
        return False

# 在模块加载时自动初始化调度器 - 临时禁用以解决worker卡死问题
# if __name__ != '__main__':
#     initialize_scheduler()
print("动态调度器已禁用，避免worker启动时阻塞")