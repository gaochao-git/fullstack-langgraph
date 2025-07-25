#!/usr/bin/env python3
"""
实时监控 Celery 任务执行情况
"""
import pymysql
import time
import os
from datetime import datetime, timedelta

# MySQL 配置
DATABASE_CONFIG = {
    'host': '82.156.146.51',
    'port': 3306,
    'user': 'gaochao',
    'password': 'fffjjj',
    'database': 'celery_tasks',
    'charset': 'utf8mb4'
}

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_task_status():
    """获取任务状态"""
    try:
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        # 获取任务配置信息
        cursor.execute("""
            SELECT id, task_name, task_enabled, task_interval, 
                   task_crontab_minute, task_crontab_hour, task_run_count, task_last_run_time
            FROM celery_periodic_task_configs 
            WHERE task_enabled = 1
            ORDER BY id
        """)
        
        tasks = cursor.fetchall()
        
        # 获取最近的执行日志
        cursor.execute("""
            SELECT task_name, task_execute_time, task_status, 
                   LEFT(task_result, 100) as task_result_preview
            FROM celery_periodic_task_execution_logs 
            WHERE task_execute_time > %s
            ORDER BY task_execute_time DESC 
            LIMIT 10
        """, (datetime.now() - timedelta(minutes=30),))
        
        recent_logs = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return tasks, recent_logs
        
    except Exception as e:
        print(f"❌ 获取任务状态失败: {str(e)}")
        return [], []

def format_schedule(interval, minute, hour):
    """格式化调度信息"""
    if interval:
        return f"每 {interval} 秒"
    elif minute is not None and hour is not None:
        try:
            hour_int = int(hour) if hour != '*' else 0
            minute_int = int(minute) if minute != '*' else 0
            return f"每天 {hour_int:02d}:{minute_int:02d}"
        except:
            return f"Cron: {minute} {hour} * * *"
    else:
        return "未配置"

def calculate_next_run(interval, last_run):
    """计算下次运行时间"""
    if not interval:
        return "N/A"
    
    if last_run:
        next_run = last_run + timedelta(seconds=interval)
        now = datetime.now()
        if next_run > now:
            remaining = (next_run - now).total_seconds()
            return f"{int(remaining)}秒后"
        else:
            return "应该运行"
    else:
        return "等待首次运行"

def monitor_tasks():
    """实时监控任务"""
    print("🔍 Celery 任务实时监控器")
    print("按 Ctrl+C 退出监控")
    print("=" * 80)
    
    try:
        while True:
            clear_screen()
            print("🔍 Celery 任务实时监控器")
            print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            tasks, recent_logs = get_task_status()
            
            if tasks:
                print("📋 启用的定时任务:")
                print("-" * 80)
                print(f"{'ID':<3} {'任务名':<25} {'调度':<15} {'运行次数':<8} {'下次运行':<15}")
                print("-" * 80)
                
                for task in tasks:
                    task_id, name, enabled, interval, minute, hour, run_count, last_run = task
                    schedule = format_schedule(interval, minute, hour)
                    next_run = calculate_next_run(interval, last_run)
                    
                    # 截断长任务名
                    name_short = name[:22] + "..." if len(name) > 25 else name
                    
                    print(f"{task_id:<3} {name_short:<25} {schedule:<15} {run_count or 0:<8} {next_run:<15}")
            
            else:
                print("⚠️ 没有启用的定时任务")
            
            print("\n📊 最近30分钟的执行日志:")
            print("-" * 80)
            
            if recent_logs:
                print(f"{'任务名':<25} {'执行时间':<20} {'状态':<10} {'结果预览':<20}")
                print("-" * 80)
                
                for log in recent_logs:
                    task_name, execute_time, status, result_preview = log
                    
                    # 截断长名称和结果
                    name_short = task_name[:22] + "..." if len(task_name) > 25 else task_name
                    result_short = (result_preview[:17] + "...") if result_preview and len(result_preview) > 20 else (result_preview or "")
                    
                    # 状态颜色
                    status_display = "✅ " + status if status == "SUCCESS" else "❌ " + status
                    
                    time_str = execute_time.strftime('%H:%M:%S') if execute_time else "N/A"
                    
                    print(f"{name_short:<25} {time_str:<20} {status_display:<10} {result_short:<20}")
            else:
                print("📝 最近30分钟内没有执行记录")
            
            print("\n" + "=" * 80)
            print("💡 提示: 新添加的任务会在1分钟内被 Celery Beat 自动检测到")
            print("🔄 监控数据每5秒刷新一次...")
            
            # 等待5秒后刷新
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")
    except Exception as e:
        print(f"\n❌ 监控过程中出错: {str(e)}")

def quick_status():
    """快速查看任务状态（不循环）"""
    print("📊 任务状态快照")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tasks, recent_logs = get_task_status()
    
    if tasks:
        print(f"📋 启用的任务: {len(tasks)} 个")
        for task in tasks:
            task_id, name, enabled, interval, minute, hour, run_count, last_run = task
            schedule = format_schedule(interval, minute, hour)
            next_run = calculate_next_run(interval, last_run)
            
            print(f"  {task_id}. {name}")
            print(f"     调度: {schedule} | 运行次数: {run_count or 0} | 下次: {next_run}")
    
    if recent_logs:
        print(f"\n📊 最近执行: {len(recent_logs)} 条记录")
        for log in recent_logs[:3]:  # 只显示最近3条
            task_name, execute_time, status, result_preview = log
            time_str = execute_time.strftime('%H:%M:%S') if execute_time else "N/A"
            status_display = "✅" if status == "SUCCESS" else "❌"
            print(f"  {status_display} {task_name} ({time_str})")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        quick_status()
    else:
        monitor_tasks()