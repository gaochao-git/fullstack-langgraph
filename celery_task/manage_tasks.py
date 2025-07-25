#!/usr/bin/env python3
"""
管理 Celery 定时任务的工具脚本
"""
import pymysql
import sys
from datetime import datetime

# MySQL 配置
DATABASE_CONFIG = {
    'host': '82.156.146.51',
    'port': 3306,
    'user': 'gaochao',
    'password': 'fffjjj',
    'database': 'celery_tasks',
    'charset': 'utf8mb4'
}

def list_tasks():
    """列出所有任务"""
    try:
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT id, task_name, task_description, task_enabled, task_interval,
                   task_crontab_minute, task_crontab_hour, task_run_count,
                   create_time, task_last_run_time
            FROM celery_periodic_task_configs 
            ORDER BY id
        """)
        
        tasks = cursor.fetchall()
        
        print(f"\n📋 定时任务列表 (共 {len(tasks)} 个任务):")
        print("=" * 100)
        
        for task in tasks:
            task_id, name, desc, enabled, interval, minute, hour, run_count, create_time, last_run = task
            status = "✅ 启用" if enabled else "❌ 禁用"
            
            if interval:
                schedule = f"每 {interval} 秒"
            elif minute is not None and hour is not None:
                # 处理字符串类型的 minute 和 hour
                try:
                    hour_int = int(hour) if hour != '*' else 0
                    minute_int = int(minute) if minute != '*' else 0
                    schedule = f"每天 {hour_int:02d}:{minute_int:02d}"
                except:
                    schedule = f"Cron: {minute} {hour} * * *"
            else:
                schedule = "未配置"
            
            print(f"\nID: {task_id}")
            print(f"名称: {name}")
            print(f"状态: {status}")
            print(f"调度: {schedule}")
            print(f"运行次数: {run_count or 0}")
            print(f"描述: {desc or '无描述'}")
            print(f"创建时间: {create_time}")
            print(f"最后运行: {last_run or '从未运行'}")
            print("-" * 50)
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 获取任务列表失败: {str(e)}")

def enable_task(task_id):
    """启用任务"""
    try:
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("UPDATE celery_periodic_task_configs SET task_enabled = 1 WHERE id = %s", (task_id,))
        rows_affected = cursor.rowcount
        connection.commit()
        
        if rows_affected > 0:
            print(f"✅ 任务 ID {task_id} 已启用")
        else:
            print(f"❌ 未找到 ID 为 {task_id} 的任务")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 启用任务失败: {str(e)}")

def disable_task(task_id):
    """禁用任务"""
    try:
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("UPDATE celery_periodic_task_configs SET task_enabled = 0 WHERE id = %s", (task_id,))
        rows_affected = cursor.rowcount
        connection.commit()
        
        if rows_affected > 0:
            print(f"✅ 任务 ID {task_id} 已禁用")
        else:
            print(f"❌ 未找到 ID 为 {task_id} 的任务")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 禁用任务失败: {str(e)}")

def delete_task(task_id):
    """删除任务"""
    try:
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        # 先获取任务信息
        cursor.execute("SELECT task_name FROM celery_periodic_task_configs WHERE id = %s", (task_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ 未找到 ID 为 {task_id} 的任务")
            return
        
        task_name = result[0]
        
        # 确认删除
        confirm = input(f"⚠️ 确定要删除任务 '{task_name}' (ID: {task_id}) 吗? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 取消删除")
            return
        
        cursor.execute("DELETE FROM celery_periodic_task_configs WHERE id = %s", (task_id,))
        connection.commit()
        
        print(f"✅ 任务 '{task_name}' (ID: {task_id}) 已删除")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 删除任务失败: {str(e)}")

def view_logs(limit=10):
    """查看执行日志"""
    try:
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT id, task_name, task_execute_time, task_status, task_result
            FROM celery_periodic_task_execution_logs 
            ORDER BY id DESC 
            LIMIT %s
        """, (limit,))
        
        logs = cursor.fetchall()
        
        print(f"\n📊 最近 {len(logs)} 条执行日志:")
        print("=" * 80)
        
        for log in logs:
            log_id, task_name, execute_time, status, result = log
            print(f"\nID: {log_id}")
            print(f"任务: {task_name}")
            print(f"执行时间: {execute_time}")
            print(f"状态: {status}")
            if result:
                result_preview = result[:100] + "..." if len(result) > 100 else result
                print(f"结果: {result_preview}")
            print("-" * 40)
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 获取执行日志失败: {str(e)}")

def print_usage():
    """打印使用说明"""
    print("🔧 Celery 定时任务管理工具")
    print("=" * 40)
    print("用法:")
    print("  python manage_tasks.py list                    # 列出所有任务")
    print("  python manage_tasks.py enable <task_id>        # 启用任务")
    print("  python manage_tasks.py disable <task_id>       # 禁用任务")
    print("  python manage_tasks.py delete <task_id>        # 删除任务")
    print("  python manage_tasks.py logs [limit]            # 查看执行日志")
    print("")
    print("示例:")
    print("  python manage_tasks.py list")
    print("  python manage_tasks.py enable 3")
    print("  python manage_tasks.py logs 20")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_tasks()
    elif command == 'enable' and len(sys.argv) >= 3:
        task_id = int(sys.argv[2])
        enable_task(task_id)
    elif command == 'disable' and len(sys.argv) >= 3:
        task_id = int(sys.argv[2])
        disable_task(task_id)
    elif command == 'delete' and len(sys.argv) >= 3:
        task_id = int(sys.argv[2])
        delete_task(task_id)
    elif command == 'logs':
        limit = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        view_logs(limit)
    else:
        print("❌ 无效的命令或参数")
        print_usage()

if __name__ == '__main__':
    main()