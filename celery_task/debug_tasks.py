#!/usr/bin/env python3
"""
Celery 任务调试工具
用于检查当前运行的任务、队列状态和worker状态
"""

import sys
import os
from datetime import datetime
from celery_app.celery import app

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def get_active_tasks():
    """获取所有活跃的任务"""
    print("=== 活跃任务检查 ===")
    try:
        # 获取所有worker的活跃任务
        active_tasks = app.control.inspect().active()
        
        if not active_tasks:
            print("❌ 没有找到活跃的worker或任务")
            return
        
        total_active = 0
        for worker_name, tasks in active_tasks.items():
            print(f"\n📍 Worker: {worker_name}")
            print(f"   活跃任务数: {len(tasks)}")
            
            for task in tasks:
                total_active += 1
                task_id = task.get('id', 'N/A')
                task_name = task.get('name', 'N/A')
                task_args = task.get('args', [])
                task_kwargs = task.get('kwargs', {})
                time_start = task.get('time_start', 'N/A')
                
                # 转换时间戳为人类可读格式
                readable_time = 'N/A'
                if time_start != 'N/A':
                    try:
                        readable_time = datetime.fromtimestamp(time_start).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        readable_time = f"{time_start} (转换失败)"
                
                print(f"   🔄 任务ID: {task_id}")
                print(f"      任务名: {task_name}")
                print(f"      开始时间: {readable_time}")
                print(f"      参数: {task_args}")
                print(f"      关键字参数: {task_kwargs}")
                print(f"      ---")
        
        print(f"\n📊 总活跃任务数: {total_active}")
        
    except Exception as e:
        print(f"❌ 获取活跃任务失败: {str(e)}")

def get_scheduled_tasks():
    """获取计划任务"""
    print("\n=== 计划任务检查 ===")
    try:
        scheduled_tasks = app.control.inspect().scheduled()
        
        if not scheduled_tasks:
            print("❌ 没有找到计划任务")
            return
        
        total_scheduled = 0
        for worker_name, tasks in scheduled_tasks.items():
            print(f"\n📍 Worker: {worker_name}")
            print(f"   计划任务数: {len(tasks)}")
            
            for task in tasks:
                total_scheduled += 1
                task_id = task.get('request', {}).get('id', 'N/A')
                task_name = task.get('request', {}).get('task', 'N/A')
                eta = task.get('eta', 'N/A')
                
                print(f"   ⏰ 任务ID: {task_id}")
                print(f"      任务名: {task_name}")
                print(f"      执行时间: {eta}")
                print(f"      ---")
        
        print(f"\n📊 总计划任务数: {total_scheduled}")
        
    except Exception as e:
        print(f"❌ 获取计划任务失败: {str(e)}")

def get_reserved_tasks():
    """获取保留任务（队列中等待执行的任务）"""
    print("\n=== 队列任务检查 ===")
    try:
        reserved_tasks = app.control.inspect().reserved()
        
        if not reserved_tasks:
            print("❌ 没有找到队列任务")
            return
        
        total_reserved = 0
        for worker_name, tasks in reserved_tasks.items():
            print(f"\n📍 Worker: {worker_name}")
            print(f"   队列任务数: {len(tasks)}")
            
            for task in tasks:
                total_reserved += 1
                task_id = task.get('id', 'N/A')
                task_name = task.get('name', 'N/A')
                task_args = task.get('args', [])
                
                print(f"   📦 任务ID: {task_id}")
                print(f"      任务名: {task_name}")
                print(f"      参数: {task_args}")
                print(f"      ---")
        
        print(f"\n📊 总队列任务数: {total_reserved}")
        
    except Exception as e:
        print(f"❌ 获取队列任务失败: {str(e)}")

def get_worker_stats():
    """获取worker统计信息"""
    print("\n=== Worker 统计信息 ===")
    try:
        stats = app.control.inspect().stats()
        
        if not stats:
            print("❌ 没有找到worker统计信息")
            return
        
        for worker_name, worker_stats in stats.items():
            print(f"\n📍 Worker: {worker_name}")
            print(f"   状态: {'🟢 运行中' if worker_stats else '🔴 异常'}")
            
            if worker_stats:
                total_tasks = worker_stats.get('total', {})
                pool = worker_stats.get('pool', {})
                
                print(f"   总任务数: {total_tasks}")
                print(f"   进程池信息: {pool}")
                print(f"   时钟: {worker_stats.get('clock', 'N/A')}")
                print(f"   负荷: {worker_stats.get('rusage', {})}")
        
    except Exception as e:
        print(f"❌ 获取worker统计失败: {str(e)}")

def check_redis_connection():
    """检查Redis连接"""
    print("\n=== Redis 连接检查 ===")
    try:
        import redis
        from celery_app.config import broker_url
        
        # 解析Redis URL
        if broker_url.startswith('redis://'):
            redis_url = broker_url
        else:
            redis_url = broker_url
        
        r = redis.from_url(redis_url)
        
        # 测试连接
        r.ping()
        print("✅ Redis连接正常")
        
        # 检查队列长度
        queue_length = r.llen('celery')
        print(f"📊 默认队列长度: {queue_length}")
        
        # 检查所有键
        keys = r.keys('celery*')
        print(f"📊 Celery相关键数量: {len(keys)}")
        
        for key in keys[:10]:  # 只显示前10个
            key_type = r.type(key).decode()
            if key_type == 'list':
                length = r.llen(key)
                print(f"   📝 {key.decode()}: {key_type} (长度: {length})")
            else:
                print(f"   📝 {key.decode()}: {key_type}")
        
    except Exception as e:
        print(f"❌ Redis连接检查失败: {str(e)}")

def check_database_tasks():
    """检查数据库中的任务记录"""
    print("\n=== 数据库任务记录检查 ===")
    try:
        from celery_app.models import get_session, Task
        from sqlalchemy import func
        
        session = get_session()
        
        # 统计各状态的任务数量
        status_counts = session.query(
            Task.task_status, 
            func.count(Task.id).label('count')
        ).group_by(Task.task_status).all()
        
        print("📊 任务状态统计:")
        for status, count in status_counts:
            print(f"   {status}: {count}")
        
        # 查找长时间运行的任务
        from datetime import datetime, timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        long_running = session.query(Task).filter(
            Task.task_status == 'STARTED',
            Task.task_start_time < one_hour_ago
        ).all()
        
        if long_running:
            print(f"\n⚠️  发现 {len(long_running)} 个长时间运行的任务:")
            for task in long_running:
                print(f"   🔄 {task.task_id} - {task.task_name}")
                print(f"      开始时间: {task.task_start_time}")
                print(f"      运行时长: {datetime.now() - task.task_start_time}")
        else:
            print("\n✅ 没有发现长时间运行的任务")
        
        session.close()
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {str(e)}")

def main():
    """主函数"""
    print(f"🔍 Celery 任务调试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 执行所有检查
    get_active_tasks()
    get_scheduled_tasks() 
    get_reserved_tasks()
    get_worker_stats()
    check_redis_connection()
    check_database_tasks()
    
    print("\n" + "=" * 60)
    print("🎯 调试建议:")
    print("1. 如果有长时间运行的任务，可能是API调用阻塞")
    print("2. 如果队列积压严重，考虑增加worker或优化任务")
    print("3. 如果Redis连接异常，检查Redis服务状态")
    print("4. 如果数据库任务状态异常，可能需要清理僵尸任务")

if __name__ == '__main__':
    main()